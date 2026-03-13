# Agent SDK Simulation Design

Currently, the `bubble-sim` project uses a **stateless, functional policy layer** via `OpenAIPolicyClient`. This means the environment (`BubbleGameEnv`) tracks the entire state, and at every step, we build a fresh prompt string containing the game history and ask the LLM for an action. The LLM has no memory between turns other than what we explicitly put in the prompt.

If we transition to using **OpenAI's Agent SDK** (such as the Assistants API or Swarm) to replicate Moinas and Pouget's Bubble Game, the architecture shifts from a functional loop to a **Stateful Multi-Agent System**.

## Why Use an Agent SDK?

In the current Option A setup, we explicitly control the context window. An Agent SDK handles conversational memory, tools, and state automatically. This is powerful for:
1. **Chain of Thought Preservation:** Agents can "think out loud" in previous turns and refer back to their own logic.
2. **Tool Use:** Agents can interact with the environment through functions rather than relying on strict JSON parsing.
3. **Emergent Behavior:** Agents can maintain a continuous internal monologue across multiple rounds or games, simulating human learning and fatigue.

---

## The Proposed Architecture

### 1. The Agents

Instead of passing a `trader_profile` string into a prompt, we would instantiate distinct `Agent` objects at the start of the experiment.

```python
# Conceptual Agent SDK Initialization
from openai import OpenAI

client = OpenAI()

def create_trader_agent(profile):
    return client.beta.assistants.create(
        name=f"Trader_{profile.id}",
        instructions=f"""
        You are participating in an experimental market. 
        Your trait is: {profile.risk_attitude}.
        When offered an asset, consider the price history, use the 'submit_decision' tool to buy or pass.
        """,
        model="gpt-4o",
        tools=[{"type": "function", "function": submit_decision_tool_schema}]
    )
```

In the Bubble Game, since each trader only acts *once* per episode, the immediate benefit of a stateful thread per episode is limited. **However**, if the same Agent plays *multiple* episodes sequentially (like humans doing practice rounds), maintaining an ongoing Thread for that Agent becomes highly valuable for observing learning curves.

### 2. The Environment as a Moderator

The `BubbleGameEnv` transitions from simply updating state variables to acting as the **Moderator** or **Orchestrator** of the agents. 

Instead of generating strings, the Orchestrator posts messages to the Agents' individualized Threads.

```python
# Conceptual Orchestrator Loop
thread = client.beta.threads.create()

# The Moderator informs the agent of their turn
client.beta.threads.messages.create(
    thread_id=thread.id,
    role="user",
    content=f"You are offered the asset at price {current_price}. The prior price path was {price_path}. Do you buy?"
)

# Run the agent
run = client.beta.threads.runs.create_and_poll(
    thread_id=thread.id,
    assistant_id=trader_agent.id
)
```

### 3. Tool Calling for Actions

Currently, we rely on the LLM generating a strictly formatted JSON object (`{"action": "buy"}`). With an Agent SDK, we define **Tools** (Functions). 

The LLM does not generate a JSON string in its response body; instead, it invokes a tool: `submit_decision(decision="buy", confidence=0.8, rationale="...")`.

The Orchestrator captures this tool call, executes the environment step, and (optionally) returns the result to the Agent.

```python
# Handling the Tool Call
if run.status == 'requires_action':
    for tool_call in run.required_action.submit_tool_outputs.tool_calls:
        if tool_call.function.name == "submit_decision":
            args = json.loads(tool_call.function.arguments)
            # Apply to BubbleGameEnv
            env.step(args["decision"])
```

---

## How the Final Design Looks

To replicate Moinas & Pouget (2013) using this pattern, the pipeline would look like this:

1. **Initialization:**
   - The CLI loads the config.
   - For an $N$-player game, the Runner instantiates $N$ distinct OpenAI Assistants (Agents), each with specific system instructions representing their assigned archetypes.
   - The Runner creates $N$ distinct Threads (memory buffers) for the agents.

2. **The Simulation Loop (`EpisodeRunner`):**
   - **Step 0:** The game starts. The asset is at $P_0$.
   - **Step 1:** The Runner adds a Message to Agent 1's Thread: *"You are offered the asset at $1. Will you buy?"*
   - Agent 1 thinks, then calls the tool `submit_decision(decision="buy")`.
   - The Runner registers the buy, calculates the next price ($10), and moves to Agent 2.
   - **Step 2:** The Runner adds a Message to Agent 2's Thread: *"You are offered the asset at $10. The price history is [1, 10]. Will you buy?"*
   - ... and so on.

3. **Multi-Episode Learning:**
   - If replicating experiments where humans play multiple times, the Runner does *not* clear the Threads. 
   - In Episode 2, the Runner messages Agent 1: *"A new game has started. You are offered the asset at $10. Last game, you bought at $10 and made a profit. Will you buy?"*
   - The SDK handles the massive context accumulation automatically.

### Pros and Cons for Bubble Game Replication

**Pros of Agent SDK:**
- **Natural Tool Use:** Function calling is far more reliable than strict JSON prompting.
- **Continuous Memory:** Crucial if testing how agents learn across multiple repetitions of the Bubble Game (which humans do in reality).
- **Multi-Agent Interaction:** If you expand the game to allow traders to chat with each other before buying, the Agent SDK handles multi-agent thread orchestration beautifully.

**Cons of Agent SDK:**
- **Latency & Cost:** Stateful Assistants API rounds trip can be slower and occasionally more opaque than direct chat completion calls.
- **Reproducibility Challenges:** Because the SDK manages contextual memory under the hood (sometimes truncating or summarizing if context gets too long), achieving strict, cryptographic reproducibility (Phase 0.2 requirements) becomes mathematically harder than in our current stateless, purely functional design.
