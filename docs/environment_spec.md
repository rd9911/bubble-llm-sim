# BubbleGameEnv v1 Specification

## 1. Purpose
The purpose of `BubbleGameEnv v1` is to provide a finite sequential decision environment for testing whether LLM-based agents can organically reproduce target empirical patterns from the Moinas and Pouget Bubble Game:
1. Positive speculation on a valueless asset.
2. Different behavioral patterns under capped vs uncapped price regimes.
3. The snowball effect (willingness to speculate rises as chances of resale rise).

The environment frames the game as sequential trading of a commonly known valueless asset.

## 2. Canonical Treatment Set
The environment implements two required treatments:
- **Treatment A — No cap (`uncapped`)**: There is no maximum price cap. A bubble equilibrium can exist at Nash equilibrium.
- **Treatment B — Cap (`capped`)**: There is a known maximum price. Bubbles that continue to the cap are irrational under backward induction.

## 3. State Schema
The decision state is explicitly structured to support deterministic transitions and reproducible prompting.

```python
@dataclass(frozen=True)
class BubbleGameState:
    episode_id: str
    step_index: int
    offered_price: int
    price_index: int
    price_path: tuple[int, ...]
    cap_type: str                # "capped" | "uncapped"
    max_price: int | None
    asset_value: int             # fixed at 0 in v1
    limited_liability: bool      # fixed True in v1
    n_traders_total: int
    realized_position: int | None
    position_uncertainty: bool   # fixed True for canonical bubble treatment
    can_infer_from_price: bool   # fixed True
    previous_actions: tuple[str, ...]
    game_continues_if_buy: bool
    done: bool
```

## 4. Action Schema
The environment uses a strict binary action space.
```python
Action = Literal["buy", "no_buy"]
```

## 5. Transition Rules
Transitions govern the progression of the sequence:
- **Initial state**: At reset, select the treatment config, instantiate exogenous price path, select the realized point in the sequence, and expose the first decision state to the incoming trader.
- **If `no_buy`**: The game ends immediately. The current trader does not buy, and no asset changes hands. Assuming the asset was held by someone before, that previous holder is stuck with it.
- **If `buy`**: Ownership passes forward. The *next* trader in the sequence is offered the *next* exogenous price. If the sequence is exhausted at the current node, the buyer is stuck with the worthless asset, and the game ends.
- **Terminal conditions**: The game terminates either when a trader selects `no_buy` or when the sequence is fully evaluated (final trader reached).

## 6. Payoff Rules
Traders operate under limited liability (`limited_liability=True`) and face explicit payoffs:
- If trader chooses `no_buy`: `Payoff = 0`
- If trader buys at price `P_t` and later resells at `P_{t+1}`: `Payoff = P_{t+1} - P_t`
- If trader buys and becomes the final holder (due to sequence end or next trader choosing `no_buy`): `Payoff = -P_t`

## 7. Price-Path Defaults
The canonical exponential progression replicates the core experimental condition.
- **Default price path**: `price_path = (1, 10, 100, 1000, 10000)`
- **Capped Default**: `max_price = 10000`
- **Uncapped Default**: `max_price = None`

## 8. Information Structure
The agent receives partial observability, reflecting the laboratory condition.
- **Observed**: Current offered price, price evolution rule, treatment regime (capped/uncapped), and the understanding that price reveals partial constraints on position.
- **Not Observed**: Exact position in the sequence, future actions of later traders, hidden random draws.
- **Decision Mode**: Direct response. The agent only decides for the current observed node, without evaluating a full strategy map in one pass.
- **Policy Role**: Each decision invokes a prompt-conditioned archetyped trader policy (`policy(state: BubbleGameState, agent_profile: TraderProfile) -> PolicyOutput`).

## 9. Exclusions from v1
To maintain strict experimental fidelity, the following are excluded from v1:
- Social feeds, inter-agent chat, and long-horizon memory.
- Reflection modules.
- Endogenous price formation or continuous-time market microstructure.
- Multi-asset portfolios.
- Full strategy-method elicitation (deferred).

## 10. Open Extension Points
Future extensions may cleanly build on this spec:
- Extension to the **strategy method** (eliciting decisions at every possible node simultaneously).
- Configurable multiplier and path lengths for prices.
- Additional diagnostic policy outputs (`confidence`, `belief_resell`, `reason_short`).
- Evaluation hooks for computing exact buy-rate slopes and tracking terminal holder frequencies.
