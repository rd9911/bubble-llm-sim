from __future__ import annotations

import json
import random
from typing import Any

from bubble_sim.agents.core import LabSubjectAgent
from bubble_sim.runner.agent_runner import PeriodRunner
from bubble_sim.data.schemas import QuizRecord, MarketOutcomeRecord, SubjectRecord

MAX_QUIZ_ATTEMPTS = 3  # total attempts allowed for the full quiz


class ExperimentRunner:
    """Orchestrates session executions over explicit configurations."""

    def __init__(
        self,
        period_runner: PeriodRunner,
        manifest: dict[str, Any],
        subjects: list[LabSubjectAgent],
        trace_writer: Any,
        agent_factory: Any | None = None,
    ) -> None:
        self.period_runner = period_runner
        self.manifest = manifest
        self.run_id = self.manifest.get("run_id", "default_run_id")
        self.subjects = subjects
        self.trace_writer = trace_writer
        # agent_factory(index: int) -> LabSubjectAgent  — used to create
        # replacement agents when one fails the comprehension quiz
        self.agent_factory = agent_factory

    # ------------------------------------------------------------------
    # Quiz helpers
    # ------------------------------------------------------------------

    def _deliver_instructions(self, subject: LabSubjectAgent, instructions: str) -> None:
        """Send the game instructions to a single subject."""
        subject.add_message(instructions)

    def _run_quiz_for_subject(
        self,
        subject: LabSubjectAgent,
        quiz_data: list[dict],
        session_id: str,
        instructions: str,
    ) -> bool:
        """
        Administer the comprehension quiz to a single subject in bulk.
        Returns True if the subject answered ALL questions correctly,
        False if they exhausted MAX_QUIZ_ATTEMPTS without a perfect score.
        """
        prompt = "Please answer the following comprehension questions based on the instructions.\n\n"
        for q_idx, q in enumerate(quiz_data):
            prompt += f"Question ID: {q['id']}\nText: {q['text']}\n"
            if "choices" in q:
                prompt += f"Choices: {', '.join(q['choices'])}\n"
            prompt += "\n"

        for attempt in range(1, MAX_QUIZ_ATTEMPTS + 1):
            ans_dict = subject.get_quiz_answers(prompt)
            if not ans_dict or "answers" not in ans_dict:
                subject.add_message("Failed to parse answers. Please try again.")
                continue

            all_correct = True
            for q in quiz_data:
                q_id = q["id"]
                submitted_answer = ""
                submitted_rationale = None
                # Find the answer in the returned list
                for ans_item in ans_dict.get("answers", []):
                    if ans_item.get("question_id") == q_id:
                        submitted_answer = ans_item.get("answer", "")
                        submitted_rationale = ans_item.get("rationale", None)
                        break

                correct_lower = q["correct_answer"].lower().strip()
                ans_lower = submitted_answer.lower().strip()
                is_correct = correct_lower in ans_lower
                if not is_correct:
                    all_correct = False

                # Log every attempt
                if hasattr(self.trace_writer, "write"):
                    try:
                        self.trace_writer.write(QuizRecord(
                            subject_id=subject.conversation_id,
                            session_id=session_id,
                            attempt_index=attempt,
                            question_id=q["id"],
                            answer_submitted=submitted_answer,
                            answer_correct=is_correct,
                            rationale=submitted_rationale,
                            archetype_id=subject.archetype_id,
                        ))
                    except Exception:
                        pass

            if all_correct:
                subject.add_message("All answers are correct.")
                return True
            else:
                if attempt < MAX_QUIZ_ATTEMPTS:
                    subject.add_message(
                        "You made at least one mistake. Here are the instructions again:\n\n" +
                        instructions +
                        "\n\nPlease rethink and submit your answers for all questions again."
                    )

        # Failed the quiz after max attempts
        return False

    def run_session(self, session_id: str, treatment_cap: int, num_periods: int, rng: random.Random) -> None:
        
        # 1. Deliver instructions
        inst_file = f"src/bubble_sim/prompts/instructions/lab_mp2021_cap{treatment_cap}.md"
        with open(inst_file, "r") as f:
            instructions = f.read()

        for subject in self.subjects:
            self._deliver_instructions(subject, instructions)

        # 2. Comprehension quiz — every agent must pass ALL questions
        quiz_file = f"src/bubble_sim/prompts/instructions/quiz_cap{treatment_cap}.json"
        with open(quiz_file, "r") as f:
            quiz_data = json.load(f)

        qualified_subjects: list[LabSubjectAgent] = []
        replacement_counter = 0

        for subject in self.subjects:
            passed = self._run_quiz_for_subject(subject, quiz_data, session_id, instructions)
            if passed:
                qualified_subjects.append(subject)
                print(f"  [QUIZ] {subject.conversation_id[:20]}… PASSED")
            else:
                print(f"  [QUIZ] {subject.conversation_id[:20]}… FAILED — excluding")
                subject.teardown()

        # Fill empty slots with replacement agents (if factory available)
        required_count = len(self.subjects)
        while len(qualified_subjects) < required_count and self.agent_factory is not None:
            replacement_counter += 1
            print(f"  [QUIZ] Spawning replacement agent #{replacement_counter}")
            new_agent = self.agent_factory(replacement_counter)
            self._deliver_instructions(new_agent, instructions)
            passed = self._run_quiz_for_subject(new_agent, quiz_data, session_id, instructions)
            if passed:
                qualified_subjects.append(new_agent)
                print(f"  [QUIZ] Replacement {new_agent.conversation_id[:20]}… PASSED")
            else:
                print(f"  [QUIZ] Replacement {new_agent.conversation_id[:20]}… FAILED — excluding")
                new_agent.teardown()

        if len(qualified_subjects) < required_count:
            deficit = required_count - len(qualified_subjects)
            print(f"  [WARNING] {deficit} agent(s) could not pass the quiz. "
                  f"Proceeding with {len(qualified_subjects)} subjects.")

        # Use only qualified subjects for the rest of the session
        self.subjects = qualified_subjects

        # Log SubjectRecords
        if hasattr(self.trace_writer, "write"):
            for subject in self.subjects:
                try:
                    self.trace_writer.write(SubjectRecord(
                        subject_id=subject.conversation_id,
                        session_id=session_id,
                        treatment_cap=treatment_cap,
                        num_periods=num_periods,
                        model_name=subject.model,
                        assistant_id_hash="responses_api",
                        quiz_attempt_count=1, # simplified
                        quiz_passed=True,
                        seed=None,
                        archetype_id=subject.archetype_id,
                    ))
                except Exception:
                    pass

        # 3. Periods
        with open("src/bubble_sim/prompts/instructions/decision_screen_template.md", "r") as f:
            decision_template = f.read()
            
        decision_template = decision_template.replace("{total_periods}", str(num_periods))
            
        with open("src/bubble_sim/prompts/instructions/feedback_template.md", "r") as f:
            feedback_template = f.read()
            
        info_table = ""
        if treatment_cap == 10000:
            info_table = "* 1 ⇒ sure first\n* 10 ⇒ 1/3 first, 2/3 second, sure not third\n* 100 or 1,000 ⇒ 1/7 first, 2/7 second, 4/7 third\n* 10,000 ⇒ 1/4 first, 1/4 second, 1/2 third\n* 100,000 ⇒ 0 first, 1/2 second, 1/2 third\n* 1,000,000 ⇒ sure third"
        else:
            info_table = "* 1 ⇒ sure first\n* 10 ⇒ sure second\n* 100 ⇒ sure third"

        cumulative_gains = {s.conversation_id: 0 for s in self.subjects}
        
        for period_idx in range(num_periods):
            # Stranger match into triples
            shuffled = list(self.subjects)
            rng.shuffle(shuffled)
            
            groups = [shuffled[i:i+3] for i in range(0, len(shuffled), 3)]
            
            for m_idx, group in enumerate(groups):
                if len(group) != 3: 
                    continue # Should be exactly 3
                    
                market_id = f"{session_id}_p{period_idx}_m{m_idx}"
                assigned_positions = {
                    group[0].conversation_id: 1,
                    group[1].conversation_id: 2,
                    group[2].conversation_id: 3,
                }
                
                realization = self.period_runner.run_period_for_market(
                    session_id=session_id,
                    period_index=period_idx,
                    market_id=market_id,
                    group_subjects=group,
                    treatment_cap=treatment_cap,
                    assigned_positions=assigned_positions,
                    rng=rng,
                    previous_cumulative_gains=cumulative_gains,
                    decision_prompt_template=decision_template,
                    info_table=info_table
                )
                
                for subject in group:
                    sid = subject.conversation_id
                    fb = realization.feedback_by_subject[sid]
                    cumulative_gains[sid] = fb.cumulative_gain
                    
                    if fb.actually_proposed:
                        fb_text = f"You were proposed to trade at a price of {fb.proposed_price}."
                    else:
                        fb_text = "You were not reached to trade this period."
                        
                    msg = feedback_template.format(
                        period_number=period_idx + 1,
                        actually_proposed_text=fb_text,
                        period_gain=fb.period_gain,
                        cumulative_gain=fb.cumulative_gain
                    )
                    subject.add_message(msg)
                
                # Write market outcome
                if hasattr(self.trace_writer, "write"):
                    term_pos = None
                    # Very simple inference
                    if realization.realized_bubble_size == "large": term_pos = 3
                    elif realization.realized_bubble_size == "medium": term_pos = 2
                    elif realization.realized_bubble_size == "small": term_pos = 1
                    
                    num_buys_all_elicited = sum(1 for d in realization.decision_by_subject.values() if d.action == "buy")
                    
                    num_buys_realized = 0
                    if realization.realized_bubble_size == "large": num_buys_realized = 3
                    elif realization.realized_bubble_size == "medium": num_buys_realized = 2
                    elif realization.realized_bubble_size == "small": num_buys_realized = 1
                    
                    try:
                        self.trace_writer.write(MarketOutcomeRecord(
                            session_id=session_id,
                            period_index=period_idx,
                            market_id=market_id,
                            first_price_draw=list(realization.offered_price_by_subject.values())[0],
                            bubble_depth=realization.realized_trade_path_depth,
                            bubble_size=realization.realized_bubble_size,
                            num_buys_all_elicited=num_buys_all_elicited,
                            num_buys_realized=num_buys_realized,
                            terminal_holder_position=term_pos,
                            treatment_cap=treatment_cap
                        ))
                    except Exception: pass
