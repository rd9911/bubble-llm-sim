# The Bubble Game Simulator: A Student's Guide

Welcome! If you are reading this, you are probably trying to understand how this simulation codebase is put together. This project is a computational replica of an experimental economics game (specifically, the "Bubble Game" by Moinas and Pouget). Instead of using real human participants in a lab, we use Artificial Intelligence—specifically Large Language Models (LLMs) like GPT-4—to play the game.

This document will walk you through the codebase step-by-step, treating the simulation as a story. We will start from the moment you type a command into your terminal and follow the code all the way through to where the final data is saved.

---

## 1. The Entry Point: Setting Up the Game
**File to look at:** `src/bubble_sim/cli.py`

When you want to run a simulation, you type a command into your terminal, like this:
`bubble-sim simulate-lab --config mp2021_cap10000_rep10.yaml`

The `cli.py` file (CLI stands for Command Line Interface) acts as the front door to the application. Here is what it does:
1. **Reads the Recipe:** It reads your YAML configuration file. This file tells the simulation exactly what to do: how many episodes (games) to play, what the price of the asset is at each step, and what kind of AI model to use.
2. **Hires the Players:** It sets up an OpenAI "Assistant" for each participant required in the game (using the instructions you provided in the config).
3. **Builds the Table:** It creates the environment (the game board).
4. **Starts the Clock:** It hands everything over to the `ExperimentRunner` and tells it to start playing.

---

## 2. The Game Board: The Environment
**Files to look at:** `src/bubble_sim/env/bubble_game.py` and `src/bubble_sim/env/state.py`

Imagine a physical board game. The board itself knows the rules, knows whose turn it is, and knows what happens when a player makes a move. In our code, this is the `BubbleGameEnv` (Environment).

Our environment is the mathematical resolver of the game mechanics.
- Instead of taking turns step-by-step, the game works through **Periods**.
- The environment uses a `resolve_market()` function.
- It takes the independent decisions of all three players (their private `buy` or `no_buy` choices).
- It applies the rules of the Bubble Game to these choices all at once to determine who actually got to trade, and what their final payoffs are.

*Why design it this way?* By keeping the rules (Environment) completely separate from the players (Agents), we ensure the game is perfectly fair and mathematically sound, regardless of whether a human, an AI, or a random number generator is playing.

---

## 3. The Players: Simulation Agents
**File to look at:** `src/bubble_sim/agents/core.py`

In an economics lab, humans sit at computers and make choices. In our simulation, `SimulationAgent` objects make the choices.

### How do they work?
Our agents are built using the **OpenAI Assistants API**. This is a powerful system that gives the AI two crucial abilities:
1. **Persistent Memory (Threads):** Every agent is assigned a "Thread." You can think of a Thread as an ongoing conversation history. When the game moves to Episode 2, the agent remembers what happened in Episode 1 because it's all saved in the Thread. This allows the AI to learn from past mistakes, just like a human would.
2. **Tool Calling:** We don't just ask the AI to text us "I want to buy." We give the AI a digital button to press, called a "Tool." In `core.py`, you will see a tool called `submit_decision`. The agent is forced to use this tool, submitting its action (`buy` or `no_buy`) along with its confidence and a logical rationale in a strict, computer-readable format (JSON).

When it is an agent's turn to play, the code sends a message to the agent's Thread describing the game board, and waits for the agent to "press the button" using the tool.

---

## 4. The Referee: The Period Runner
**File to look at:** `src/bubble_sim/runner/agent_runner.py`

If the Environment is the calculator and the Agents are the players, the `PeriodRunner` is the referee or the orchestrator.

### The Game Loop
The `PeriodRunner` runs the mechanics of a single period:
1. It draws the current period's starting price.
2. It assigns the three participants to anonymous positions (First, Second, Third) without telling them.
3. It asks all three `LabSubjectAgent`s simultaneously: *"Here is your observed price. What is your choice?"*
4. All three Agents wake up, use their `submit_decision` tool, and reply independently.
5. The `PeriodRunner` takes all three actions and submits them to the Environment's resolver function.
6. The Environment calculates the realized path and returns the payoffs and allowed feedback.
7. The `PeriodRunner` delivers the restricted feedback to each player's Thread.

*Why design it this way?* The `AgentRunner` separates the "thinking" from the "doing." The Environment never talks directly to the AI, and the AI never touches the Environment directly. The Runner acts as a secure bridge, preventing the AI from cheating or breaking the game rules.

---

## 5. Taking Notes: Emitting Traces
**Files to look at:** `src/bubble_sim/runner/agent_runner.py` and `src/bubble_sim/runner/events.py`

In a real lab, scientists record every single click a participant makes. We do the exact same thing through **Tracing**.

Every time the referee (`AgentRunner`) asks an AI for a decision, it writes down exactly what happened. It creates a `PolicyCallEvent` (or a dictionary that looks like one) that records:
- What the AI was asked.
- What the AI decided.
- The AI's hidden reasoning (rationale).

Every time the environment changes state, the runner writes down a `TransitionEvent`. All of these notes are appended line-by-line into a file called `traces.jsonl`.

*Why design it this way?* Because LLMs are unpredictable. If an AI does something strange in Episode 15, we need an exact, second-by-second transcript of what the AI was thinking and seeing at that exact moment to debug it. 

---

## Conclusion: The Full Lifecycle
To summarize the entire application:

1. **`cli.py`** reads your settings and sets up the room.
2. **`cli.py`** calls **`ExperimentRunner`**, which loops over the requested rounds (e.g., 10 periods). It first gives everyone instructions and forces them to pass a comprehension quiz.
3. Inside each period, **`PeriodRunner`** asks all **`LabSubjectAgent`**s for a decision simultaneously.
4. The **`LabSubjectAgent`** talks to the OpenAI API, uses the `submit_decision` tool, and returns an action.
5. The **`PeriodRunner`** feeds all actions to the **`BubbleGameEnv`**'s resolver.
6. The resolver calculates the exact payoffs and allowed feedback.
7. The **`PeriodRunner`** writes everything down in `traces.jsonl`.
8. Once all periods are done, you have a folder full of data ready to be evaluated against human participants!

By structuring the code this way, we ensure that the experimental physics are completely rigid and true to the original paper's simultaneous protocol, while the AI participants remain endlessly flexible and trackable.
