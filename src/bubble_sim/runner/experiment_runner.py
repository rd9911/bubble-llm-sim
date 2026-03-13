from __future__ import annotations

import json
import random
from typing import Any

from bubble_sim.agents.core import LabSubjectAgent
from bubble_sim.runner.agent_runner import PeriodRunner
from bubble_sim.data.schemas import QuizRecord, MarketOutcomeRecord

class ExperimentRunner:
    """Orchestrates session executions over explicit configurations."""

    def __init__(
        self,
        period_runner: PeriodRunner,
        manifest: dict[str, Any],
        subjects: list[LabSubjectAgent],
        trace_writer: Any
    ) -> None:
        self.period_runner = period_runner
        self.manifest = manifest
        self.run_id = self.manifest.get("run_id", "default_run_id")
        self.subjects = subjects
        self.trace_writer = trace_writer

    def run_session(self, session_id: str, treatment_cap: int, num_periods: int, rng: random.Random) -> None:
        
        # 1. Deliver instructions
        inst_file = f"src/bubble_sim/prompts/instructions/lab_mp2021_cap{treatment_cap}.md"
        with open(inst_file, "r") as f:
            instructions = f.read()
            
        for subject in self.subjects:
            subject.add_message(instructions)
            
        # 2. Comprehension quiz
        quiz_file = f"src/bubble_sim/prompts/instructions/quiz_cap{treatment_cap}.json"
        with open(quiz_file, "r") as f:
            quiz_data = json.load(f)
            
        for subject in self.subjects:
            for q_idx, q in enumerate(quiz_data):
                passed = False
                attempts = 0
                while not passed:
                    attempts += 1
                    ans = subject.get_quiz_answer(f"Question {q_idx+1}: {q['text']}")
                    ans_lower = ans.lower().strip() if ans else ""
                    correct_lower = q["correct_answer"].lower().strip()
                    
                    is_correct = correct_lower in ans_lower
                    
                    if hasattr(self.trace_writer, "write"):
                        try:
                            self.trace_writer.write(QuizRecord(
                                subject_id=subject.assistant_id,
                                session_id=session_id,
                                attempt_index=attempts,
                                question_id=q["id"],
                                answer_submitted=ans or "",
                                answer_correct=is_correct
                            ))
                        except Exception: pass
                    
                    if is_correct:
                        subject.add_message("Correct.")
                        passed = True
                    else:
                        if attempts >= 3:
                            subject.add_message(f"Incorrect. The correct answer was: {q['correct_answer']}.")
                            passed = True
                        else:
                            subject.add_message("Incorrect. Please rethink your answer based on the instructions.")

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

        cumulative_gains = {s.assistant_id: 0 for s in self.subjects}
        
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
                    group[0].assistant_id: 1,
                    group[1].assistant_id: 2,
                    group[2].assistant_id: 3,
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
                    sid = subject.assistant_id
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
