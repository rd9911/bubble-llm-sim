Below is the implementation spec for refactoring `bubble-llm-sim` into a paper-faithful reproduction mode aligned with the repeated lab design and participant instructions in Appendix A.

The main design changes are these:

Your current codebase is already close on the asset and payoff mechanics, but it is still wrong on the most important experimental dimensions. In the paper’s lab design, each period is **not** played as a sequential interactive turn loop among visible traders. Instead, once the first price is drawn, the three market positions are conceptually assigned, the three corresponding prices are generated, and **all three participants submit their buy/no-buy decisions simultaneously and privately**. A decision only becomes payoff-relevant if all earlier positions bought; this simultaneous elicitation is used precisely to prevent inference from timing and to observe all subjects’ contingent decisions at the realized price. Subjects are re-matched each period under anonymous stranger matching, play 10 or 20 independent periods depending on treatment, receive 1 ECU each period, and after each period are told whether they were actually proposed to trade, at what price, and their current-period and cumulative gains. The experiment starts only after every participant answers the comprehension quiz correctly.   

# Implementation spec: refactor `bubble-llm-sim` into paper-faithful lab mode

## 1. Objective

Create a new primary execution mode, called something like `lab_repeated_mp2021`, that reproduces the repeated experimental design described in the Hong–Moinas–Pouget paper (you can find it in the main directory by the name "paper.pdf") and uses the Appendix A participant instructions as the behavioral interface for LLM subjects. In this mode, the system must simulate LLMs as direct analogues of human lab participants, not as strategic analysts, archetyped traders, or free-form agents. The design must preserve only features that improve fidelity to the experiment. Everything else should be removed, disabled, or isolated behind legacy compatibility flags. The instructions shown to agents must reflect the participant-facing lab rules: worthless asset, outside financier, one ECU initial endowment each period, simultaneous private decisions, stranger matching, repeated independent periods, and the exact price-to-position probability information and quiz gating described in Appendix A.   

## 2. Non-negotiable behavioral fidelity requirements

The following must be treated as invariants in the new mode.

There are exactly three traders per market. The asset has zero dividend and zero fundamental value, which is common knowledge. The first price is exogenous, is a power of 10, and is drawn from the truncated geometric rule with cap either 1 or 10,000 depending on treatment. If trader (i) buys at price (P_i), the next potential trader is offered (10P_i). Trader profits are 0 if they are not actually proposed to trade or refuse to buy, +9 net trading profit if they buy and successfully resell, and -1 net trading profit if they buy and cannot resell. Equivalently in payoff language used in the instructions, refusing leaves the player with 1 ECU, a successful resale leaves them with 10 ECU, and a failed purchase leaves them with 0 ECU.   

The four repeated-game treatments must exist exactly as: cap=1 with 10 periods, cap=10,000 with 10 periods, cap=1 with 20 periods, cap=10,000 with 20 periods. The paper reports session counts and sample sizes by treatment; you do not need to replicate exact subject counts unless you are reproducing cohort structure, but treatment semantics must match exactly. 

Positions are randomly assigned each period with equal ex-ante probability of being first, second, or third. Participants are not told their position directly. Instead, they infer partial information from the price they are shown, and for the cap=10,000 treatment the experiment explicitly provides a lookup-style description of the conditional probabilities of being in each position at each possible observed price so subjects do not need to apply Bayes’ rule themselves. That information must be explicitly included in the agent-facing instructions.   

Decisions are simultaneous and private, not sequentially observed. The simulation must therefore stop representing the environment as “Trader 1 decides, then Trader 2 decides if needed, then Trader 3 decides if needed” for the purpose of agent interaction. The correct implementation is: draw first price, assign positions, derive the three private offered prices, elicit all three decisions independently from the three agents, then resolve which of those decisions become payoff-relevant ex post.  

The experiment must include a pre-period comprehension gate. No participant may enter the first period until they have answered all comprehension questions correctly. In the human lab, the experiment started only once all subjects answered all questions correctly. In the LLM simulation, implement this as a subject-level quiz pass requirement before the first trading period, with strict logging of attempts and corrections.  

## 3. High-level architecture changes

Your current architecture is “one persistent assistant per trader across an episode, with sequential turn-taking.” Replace the execution concept of an `Episode` with a richer hierarchy:

`Subject`
A persistent simulated participant for an entire session/treatment. A subject corresponds to one Assistant plus one Thread if you keep the current Assistants API design.

`Session`
A cohort of subjects assigned to one treatment configuration. A session runs 10 or 20 periods with stranger matching among its subjects.

`Period`
One independent repetition of the bubble game within a session. Each period rematches subjects into anonymous groups of three, draws one first price per group, assigns positions, elicits simultaneous decisions, settles payoffs, and returns limited feedback.

`Market`
One group-of-three realization inside a period.

This change matters because the paper’s repeated design is about **learning across periods by the same subject**, with random rematching each period, not about an isolated one-off market episode. The subject—not the market slot—is the persistence unit. The paper also emphasizes that payoffs from past periods affect future behavior, and after each period subjects see only their own realized feedback and cumulative gains.  

## 4. Required codebase refactor by module

## `src/bubble_sim/env/`

### Replace the current sequential interaction semantics

`bubble_game.py` should be redesigned around a “realized partial-strategy method” period resolver.

Add two layers:

`PriceDraw`

* `cap_first_price: Literal[1, 10000]`
* `first_price: int`
* `distribution_support: list[int]`
* `distribution_probs: list[float]`

`MarketRealization`

* `subject_ids: tuple[str, str, str]`
* `assigned_positions: dict[str, Literal[1,2,3]]`
* `offered_price_by_subject: dict[str, int]`
* `decision_by_subject: dict[str, BuyDecision]`
* `decision_relevant_by_subject: dict[str, bool]`
* `realized_trade_path_depth: int`
* `realized_bubble_size: Literal["none","small","medium","large"]`
* `payoff_by_subject: dict[str, int]`
* `feedback_by_subject: dict[str, SubjectFeedback]`

The environment resolution algorithm must become:

1. Randomly group subjects into triples.
2. For each group, randomly assign positions 1/2/3 uniformly.
3. Draw (P_1) from the treatment-specific distribution.
4. Generate private prices (P_1, P_2=10P_1, P_3=100P_1) according to assigned positions.
5. Elicit buy/no_buy from all three subjects independently and without exposing others’ choices.
6. Resolve the realized path:

   * first position relevant if assigned first;
   * second position relevant only if first bought;
   * third position relevant only if first and second bought.
7. Compute payoffs according to the lab rules.
8. Generate participant feedback with only allowed information.

This is the single most important mechanical change because the paper’s lab implementation uses simultaneous private choice elicitation to prevent timing inference and to observe each subject’s decision at the realized offered price even when earlier buyers would have stopped the market.  

### Add treatment-specific price support

For `cap_first_price=10000`, the first-price support and probabilities must be:

* 1 with 1/2
* 10 with 1/4
* 100 with 1/8
* 1,000 with 1/16
* 10,000 with 1/16 

For `cap_first_price=1`, define the equivalent truncated support as only 1 for the first trader, so realized private prices in the market are 1, 10, and 100. The paper interprets this treatment as the special case where observed price perfectly reveals position and yields only two steps of iterated reasoning.  

### Add public probability tables for observed price

Implement a pure function:
`position_beliefs_from_observed_price(cap_first_price: int, observed_price: int) -> PositionBelief`

For `cap=10000`, the Appendix A instruction table must be encoded exactly:

* price 1: sure first
* price 10: 1/3 first, 2/3 second, 0 third
* price 100 or 1,000: 1/7 first, 2/7 second, 4/7 third
* price 10,000: 1/4 first, 1/4 second, 1/2 third
* price 100,000: 0 first, 1/2 second, 1/2 third
* price 1,000,000: sure third 

For `cap=1`, encode the perfect-revelation mapping:

* 1 => first
* 10 => second
* 100 => third  

## `src/bubble_sim/agents/`

### Replace “trader assistant” abstraction with “subject assistant”

Rename conceptual objects accordingly. The assistant is not “Trader 2” or “Trader 3”; it is a participant who may occupy different positions across periods and does not know their position directly.

Create a new class, for example:
`LabSubjectAgent`

Responsibilities:

* own one Assistant ID and one Thread ID
* ingest the Appendix A instructions once at session start
* take and pass the comprehension quiz before period 1
* receive a period-specific prompt with only allowed information
* return a constrained buy/no_buy decision plus optional metadata
* receive post-period feedback in the restricted lab format

### Hard-disable features that break design fidelity

Remove or disable in lab mode:

* any role/archetype prompt
* any instruction that frames the model as an analyst, economist, or optimizer
* any multi-asset or market-microstructure concepts
* any memory summaries that reveal hidden state not available to human subjects
* any cross-subject shared memory
* any visibility into other subjects’ past decisions
* any hidden chain-of-thought logging as part of evaluation
* any planner/explainer subagent structure

The subject should behave as a participant following instructions, not as a simulator-aware optimizer.

### Keep structured tool output, but simplify schema

The current `submit_decision` tool is good, but in lab-faithful mode it should be narrowed. The required action is binary. Optional confidence and belief fields are acceptable only if they are clearly marked as **research-side instrumentation not shown to the subject and not used to alter payoffs or instructions**.

Recommended schema:

* `action: "buy" | "no_buy"`
* `confidence: float | null`
* `belief_success_resale: float | null`
* `rationale_short: str | null`

Do not require detailed rationale (but if Agent provides it, save it). Human subjects were not required to explain themselves, and coercing extensive written rationales may distort behavior.

## `src/bubble_sim/runner/`

### `agent_runner.py`

This file needs the largest conceptual rewrite.

Current logic likely iterates through a price track sequentially and prompts agents turn by turn. Replace with:

`run_period_for_market(group_subjects, treatment, rng) -> MarketRealization`

The prompting order can still be sequential in code for API convenience, but the content must be written as simultaneous and private. Each subject prompt must explicitly state that decisions are made simultaneously and privately and that they do not observe others’ choices before deciding. The prompt must not reveal whether the subject’s decision will become relevant.

### `experiment_runner.py`

Promote this into a session orchestrator.

Add session-level responsibilities:

* instantiate `N` subjects for a treatment
* deliver full instructions once at session start
* run comprehension quiz until each subject passes
* run `num_periods` periods
* stranger-match subjects each period into triples
* preserve each subject’s own thread across periods
* append only allowed private feedback after each period
* save session-, period-, market-, and subject-level parquet artifacts

Stranger matching should reshuffle subjects every period and should avoid deterministic repeated groupings when possible. The paper uses anonymous random rematching in a stranger design.  

### Add a hard separation between instructions, decision prompt, and feedback prompt

The most reliable setup is:

1. **Session initialization message**
   Full participant instructions.

2. **Quiz messages**
   One or multiple messages until all answers correct.

3. **Per-period decision message**
   Minimal, standardized, no theory, no coaching.

4. **Per-period feedback message**
   Only what the lab would reveal.

This structure will greatly reduce prompt drift.

## `src/bubble_sim/data/`

### Expand schemas

Your current `DecisionRecord` and `EpisodeRecord` are too narrow for the lab design.

Add or rename records to include:

`SubjectRecord`

* `subject_id`
* `session_id`
* `treatment_cap`
* `num_periods`
* `model_name`
* `assistant_id_hash`
* `quiz_attempt_count`
* `quiz_passed`
* `seed`

`PeriodAssignmentRecord`

* `session_id`
* `period_index`
* `market_id`
* `subject_id`
* `assigned_position`
* `offered_price`
* `belief_first`
* `belief_second`
* `belief_third`

`DecisionRecord`

* `session_id`
* `period_index`
* `market_id`
* `subject_id`
* `action`
* `confidence`
* `belief_success_resale`
* `decision_relevant`
* `actual_proposed_to_trade`
* `payoff_this_period`
* `cumulative_payoff`
* `bubble_size`
* `first_price_draw`
* `cap_first_price`

`QuizRecord`

* `subject_id`
* `session_id`
* `attempt_index`
* `question_id`
* `answer_submitted`
* `answer_correct`

`MarketOutcomeRecord`

* `session_id`
* `period_index`
* `market_id`
* `first_price_draw`
* `bubble_depth`
* `bubble_size`
* `num_buys_all_elicited`
* `num_buys_realized`
* `terminal_holder_position`
* `treatment_cap`

This will let you evaluate both observed choices and realized outcomes cleanly.

## `src/bubble_sim/experiments/`

### Replace generic YAML configs with exact treatment configs

Define canonical configs:

* `mp2021_cap1_rep10.yaml`
* `mp2021_cap10000_rep10.yaml`
* `mp2021_cap1_rep20.yaml`
* `mp2021_cap10000_rep20.yaml`

Each should specify:

* `mode: lab_repeated_mp2021`
* `cap_first_price`
* `num_periods`
* `group_size: 3`
* `subject_endowment_per_period: 1`
* `exchange_rate_eur_per_ecu: 1`
* `decision_protocol: simultaneous_private_partial_strategy`
* `feedback_protocol: own_realized_info_only`
* `quiz_required: true`
* `stranger_matching: true`

Do not expose arbitrary price tracks in lab mode. The first-price process must come from the treatment definition, not from a user-supplied sequential track, because the paper’s distribution is part of the design. 

## `src/bubble_sim/eval/`

Your evaluation stack is already strong. Keep it, but align its units with the new data model.

Add treatment-aware evaluation slices:

* by cap treatment
* by period index
* by observed price
* by whether subject is sure to be last or not
* by first-time vs repeated exposure to max price
* by realized and elicited decision distinctions

Add fidelity checks that specifically verify:

* simultaneous-elicitation compliance
* quiz-pass-before-period-1 compliance
* subject-only feedback compliance
* stranger rematching compliance
* correct position-belief table exposure
* no leakage of hidden position or others’ actions

These should be treated as operational gates, not just descriptive metrics.

## 5. Prompting and instruction design

## Session-level instruction message

At the beginning of a session, each subject agent must receive a stable instruction message that reproduces the participant-facing experimental instructions in modernized but faithful form.

The content must include all of these points:

You are participating in a market game with groups of three players. Each period you have 1 ECU. Your task is only to decide whether to buy or not buy a worthless asset. The asset pays no dividend. If you buy at price (P) and successfully resell to the next trader at price (10P), your final payoff for that period is 10 ECU. If you buy and cannot resell, your final payoff is 0 ECU. If you refuse to buy, your payoff is 1 ECU. If you are not actually reached because an earlier trader refused, your payoff is also 1 ECU. Players do not initially know their market position. Positions are random with equal probability of being first, second, or third. Decisions are made simultaneously and privately. If you choose to buy, you automatically attempt to resell to the next potential trader. Groups are anonymous and randomly rematched each period. After each period you will be told whether you were actually proposed to trade, at what price, your gain for the period, and your cumulative gain.  

For the `cap=10000` treatment, the same session instructions must also include the observed-price information table exactly as provided in Appendix A:

* 1 ⇒ sure first
* 10 ⇒ 1/3 first, 2/3 second, sure not third
* 100 or 1,000 ⇒ 1/7 first, 2/7 second, 4/7 third
* 10,000 ⇒ 1/4 first, 1/4 second, 1/2 third
* 100,000 ⇒ 0 first, 1/2 second, 1/2 third
* 1,000,000 ⇒ sure third 

For the `cap=1` treatment, provide the simplified perfect-revelation version:

* 1 ⇒ sure first
* 10 ⇒ sure second
* 100 ⇒ sure third 

The instruction message must also say:

* do not assume access to information beyond what is stated
* do not assume anything about the personalities or intelligence of other players
* make each decision using only the instructions, your past personal feedback, and the information shown in the current period
* there is no dividend and no hidden fundamental value

This last framing is not quoted directly from the appendix, but it is an implementation safeguard against model over-interpretation and is consistent with the experiment’s design.

## Quiz gate

Before period 1, each subject must complete the comprehension quiz. The experiment only starts once all subjects pass. The paper explicitly states this common-understanding gate, and Appendix A lists the questions.  

Implement the exact questions from Appendix A for the cap=10,000 treatment:

1. Is it possible to be first and be proposed to buy at a price of 100,000?
   Correct: No.

2. If you are proposed to buy at a price of 1, are you sure to be first?
   Correct: Yes.

3. If you are proposed to buy at a price of 100,000, are you sure to be second?
   Correct: No.

4. If you are proposed to buy at a price of 100, are you sure to be third?
   Correct: No.

5. If you are proposed to buy at a price of 1,000,000, are you sure to be third?
   Correct: Yes.

6. If you accept to buy at 100, you will propose to resell at
   Correct: 1,000.

7. If you are first, buy at 100, and resell at 1,000, your payoff in the game is
   Correct: 10 euros.

8. If you are first, buy at 100, and find nobody to resell to at 1,000, your payoff in the game is
   Correct: 0 euro.

9. If you refuse to buy, your payoff is
   Correct: 1 euro. 

For the `cap=1` treatment, either derive a simplified isomorphic quiz or, better, keep the same conceptual question set but rewrite the price-position items so they fit the cap=1 information structure.

Quiz implementation rules:

* no trading periods until pass
* if an answer is wrong, the subject receives corrective feedback and is asked again
* log all attempts
* once all subjects pass, mark session as ready

## Period decision prompt

Each period decision prompt should be minimal and standardized. It should contain only:

* period number and total periods
* your currently observed offered price
* the information table reminder for that treatment
* a reminder that decisions are simultaneous and private
* a reminder of payoff consequences:

  * buy and successful resale ⇒ 10 ECU
  * buy and failed resale ⇒ 0 ECU
  * no_buy ⇒ 1 ECU
* cumulative gain so far if the lab showed it before the decision; otherwise do not include it
* required tool call schema

Do not include:

* explicit strategic advice
* formal backward induction arguments
* market theory
* summaries of other subjects’ behavior
* hidden realized position
* whether the subject was actually reached before all decisions are in

The prompt should read as a lab decision screen, not as an agent coaching memo.

## Feedback prompt

After each period, send each subject only what the experiment would reveal. Based on the paper, after each replication participants are informed whether they were actually proposed to trade and on their trading gains at the current replication and over all past replications. Appendix A also says subjects are told whether they were proposed to buy and at what price.  

So the feedback message should include only:

* whether you were actually proposed to buy
* if yes, the price at which you were proposed to buy
* your gain for this period
* your cumulative gain so far

Do not reveal:

* who was first/second/third
* what others chose
* whether a later trader would have bought if reached
* the full market path
* the first price draw unless equivalent to the subject’s own observed price

This restriction matters because the paper later argues that subjects who do not buy are not told what later players would have done; that absence of counterfactual observation is important for the learning interpretation. 

## 6. Thread and memory policy

Your current persistent-thread design is useful, but it must be disciplined.

Keep one persistent thread per subject for the full session. That thread should contain:

* initial instructions
* quiz interaction
* each period’s decision prompt
* each period’s personal feedback

Do not inject synthesized memory summaries that infer hidden structure beyond the subject’s own experience.

Do not let the assistant browse or call tools beyond `submit_decision`.

Do not place system messages that encourage “optimal play,” equilibrium reasoning, or exploitation of simulator artifacts.

The model should learn only from:

* initial instructions
* quiz corrections
* private personal feedback over time

That matches the experiment’s logic of adaptive learning across repeated periods. 

## 7. Remove or isolate current incompatible mechanics

The following current behaviors are incompatible with the paper-faithful mode and must be removed or hidden behind a legacy mode flag:

Sequential prompting tied to visible turn order.
This directly violates the simultaneous private decision protocol. 

Predetermined visible “price track” episode mechanics.
The correct design draws the first price from the treatment distribution and derives the rest from position.

Agent identity tied to fixed market position.
Subjects change position every period and do not know it directly.

Any persistent identity of counterparties across periods.
The matching is anonymous and randomly reshuffled in stranger design. 

Any memory injection containing other agents’ behavior, market-wide explanations, or hidden-state summaries.
Subjects only receive own realized feedback.

Any UI or prompt element that tells the subject “you are trader 1/2/3.”
That destroys the information structure.

Any additional reward shaping, auxiliary loss, or coaching based on human-fit metrics during simulation.
Evaluation must happen after the run, not inside the agent’s experience.

## 8. Recommended CLI and config changes

Add a dedicated command family rather than overloading the old episode interface.

Recommended examples:

`bubble-sim simulate-lab --config mp2021_cap10000_rep10.yaml --subjects 72 --sessions 1`

`bubble-sim eval-lab --run-id ...`

`bubble-sim report-lab --run-id ...`

The CLI should reject incompatible flags in lab mode, such as manual price track injection or visible sequential stepping.

## 9. Recommended file additions

Add a `prompts/` or `instructions/` folder even if you currently keep prompt text inline. You want text assets to be auditable.

Recommended files:

* `instructions/lab_mp2021_cap10000.md`
* `instructions/lab_mp2021_cap1.md`
* `instructions/quiz_cap10000.json`
* `instructions/quiz_cap1.json`
* `instructions/decision_screen_template.md`
* `instructions/feedback_template.md`

This makes the protocol inspectable and versioned.

## 10. Validation checklist developers must pass before trusting results

Before using the refactor for scientific runs, verify these invariants:

A subject who observes 1,000,000 in the cap=10,000 treatment is told they are sure to be last, and nothing in the prompt contradicts that. 

A subject who observes 100,000 is not told they are sure to be second; they are told 1/2 second and 1/2 third. 

All three subjects in a market can produce a recorded decision even if the realized market stops at the first trader. This is required by the partial-strategy simultaneous design. 

No subject sees another subject’s decision before submitting their own.

No subject begins period 1 without passing the quiz.

Period feedback reveals only own realized information and cumulative gain, not hidden counterfactuals.

Session matching changes across periods and does not preserve fixed triples.

The first-price distribution matches the treatment definition exactly. 

Payoffs are 10/1/0 in final period wealth terms, corresponding to +9/0/-1 trading-profit terms.

## 11. What not to do

Do not tell the model the backward-induction theorem or that the rational equilibrium is no trade. The paper discusses that analytically, but the participants were not instructed with equilibrium theory; they were given game rules and probability information. Your aim is participant-faithful behavior, not theorem-aware behavior. 

Do not ask the model to imitate “average humans” or “boundedly rational investors.” That introduces an extra behavioral layer not present in the experiment.

Do not provide chain-of-thought or require elaborate prose. Use the structured binary action output and optional lightweight metadata only.

Do not conflate “elicited decision” with “realized proposal.” Both need to be recorded separately.

## 12. Minimum viable implementation order

Build in this order:

1. Refactor environment resolution to simultaneous private elicitation.
2. Introduce subject/session/period abstractions and stranger matching.
3. Add exact treatment configs and first-price distributions.
4. Add session instructions with price-position information tables.
5. Implement the comprehension quiz gate.
6. Restrict per-period prompts and feedback to lab-valid information only.
7. Expand schemas and save richer parquet traces.
8. Update evaluation to use subject-period-market semantics.
9. Remove legacy incompatible flags from lab mode.
10. Run smoke tests, then full treatment sweeps.

## 13. Developer-ready acceptance criterion

The refactor is complete when a developer can point to one canonical lab mode in which:

* each subject receives Appendix-A-style instructions,
* each subject must pass the comprehension quiz before period 1,
* each period uses anonymous stranger rematching into groups of three,
* one first price is drawn per market from the treatment distribution,
* all three subjects decide simultaneously and privately at their realized offered prices,
* only the realized path affects payoffs,
* each subject receives only own realized feedback plus cumulative gains,
* and all outputs are saved in a way your existing fidelity metrics can consume.

That is the design you need if the goal is to make the LLMs face the same information structure and repeated-learning environment as the human participants in the paper.

I can next turn this into a line-by-line engineering task list mapped directly onto your existing files.
