from __future__ import annotations

import random
from typing import Any

from bubble_sim.agents.core import LabSubjectAgent
from bubble_sim.env.bubble_game import (
    BuyDecision, 
    MarketRealization, 
    resolve_market, 
    get_price_draw,
    position_beliefs_from_observed_price
)
import math
from bubble_sim.data.schemas import LabDecisionRecordV2

class PeriodRunner:
    def __init__(self, trace_writer: Any, fallback_action: str = "no_buy"):
        self.trace_writer = trace_writer
        self.fallback_action = fallback_action

    def run_period_for_market(
        self,
        session_id: str,
        period_index: int,
        market_id: str,
        group_subjects: list[LabSubjectAgent],
        treatment_cap: int,
        assigned_positions: dict[str, int], 
        rng: random.Random,
        previous_cumulative_gains: dict[str, int],
        decision_prompt_template: str,
        info_table: str
    ) -> MarketRealization:
        
        # 1. Draw first price
        price_draw = get_price_draw(treatment_cap, rng)
        first_price = price_draw.first_price
        
        subject_ids = tuple(agent.conversation_id for agent in group_subjects)
        
        # 2. Assign positions & prices
        decisions: dict[str, BuyDecision] = {}
        
        for agent in group_subjects:
            agent_id = agent.conversation_id
            pos = assigned_positions[agent_id]
            
            if pos == 1:
                offered_price = first_price
            elif pos == 2:
                offered_price = first_price * 10
            else:
                offered_price = first_price * 100
            
            prompt = decision_prompt_template.format(
                period_number=period_index + 1,
                offered_price=offered_price,
                information_table=info_table
            )
            
            raw_decision = agent.get_decision(prompt)
            if raw_decision and raw_decision.get("action") in ["buy", "no_buy"]:
                decision = BuyDecision(
                    action=raw_decision["action"],
                    confidence=raw_decision.get("confidence"),
                    belief_success_resale=raw_decision.get("belief_success_resale"),
                    reasoning=raw_decision.get("reasoning"),
                    reasoning_tokens=raw_decision.get("_reasoning_tokens"),
                    rationale_short=raw_decision.get("rationale_short")
                )
            else:
                decision = BuyDecision(action=self.fallback_action)
                
            decisions[agent_id] = decision
            
        # 3. Resolve the market
        realization = resolve_market(
            subject_ids=subject_ids,
            decisions=decisions,
            first_price=first_price,
            assigned_positions=assigned_positions, # type: ignore
            previous_cumulative_gains=previous_cumulative_gains
        )
        
        # 4. Write decision records
        if hasattr(self.trace_writer, "write"):
            for agent in group_subjects:
                agent_id = agent.conversation_id
                decision = decisions[agent_id]
                
                
                try:
                    rec = LabDecisionRecordV2(
                        session_id=session_id,
                        cap_value=treatment_cap,
                        period_index=period_index,
                        subject_id=agent_id,
                        group_id=hash(market_id) % 100000, # Mock group ID or we need to pass it
                        payoff_this_period=realization.feedback_by_subject[agent_id].period_gain,
                        cumulative_payoff=realization.feedback_by_subject[agent_id].cumulative_gain,
                        position=assigned_positions[agent_id],
                        offered_price=realization.offered_price_by_subject[agent_id],
                        action=1 if decision.action == "buy" else 0,
                        step=int(round(math.log10((treatment_cap * 100) / realization.offered_price_by_subject[agent_id]))),
                        confidence=decision.confidence,
                        belief_success_resale=decision.belief_success_resale,
                        reasoning=decision.reasoning,
                        reasoning_tokens=decision.reasoning_tokens,
                        rationale_short=decision.rationale_short,
                        archetype_id=agent.archetype_id,
                    )
                    self.trace_writer.write(rec)
                except Exception:
                    pass
        
        return realization
