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
from bubble_sim.data.schemas import LabDecisionRecord

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
        
        subject_ids = tuple(agent.assistant_id for agent in group_subjects)
        
        # 2. Assign positions & prices
        decisions: dict[str, BuyDecision] = {}
        
        for agent in group_subjects:
            agent_id = agent.assistant_id
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
                agent_id = agent.assistant_id
                decision = decisions[agent_id]
                
                try:
                    rec = LabDecisionRecord(
                        session_id=session_id,
                        period_index=period_index,
                        market_id=market_id,
                        subject_id=agent_id,
                        action=decision.action,
                        confidence=decision.confidence,
                        belief_success_resale=decision.belief_success_resale,
                        decision_relevant=realization.decision_relevant_by_subject[agent_id],
                        actual_proposed_to_trade=realization.feedback_by_subject[agent_id].actually_proposed,
                        payoff_this_period=realization.feedback_by_subject[agent_id].period_gain,
                        cumulative_payoff=realization.feedback_by_subject[agent_id].cumulative_gain,
                        bubble_size=realization.realized_bubble_size,
                        first_price_draw=first_price,
                        cap_first_price=treatment_cap
                    )
                    self.trace_writer.write(rec)
                except Exception:
                    pass
        
        return realization
