# Bubble Game LLM Simulation Framework (`bubble-sim`)

A rigorously structured Python framework for evaluating Large Language Models as proxy participants in behavioral economics experiments, specifically simulating the [Moinas and Pouget (2013) Bubble Game](https://doi.org/10.1111/jofi.12020).

## Project Purpose

Can an LLM reproduce **the decision structure and stylized facts** of human speculation under position uncertainty? This framework is designed to find out.

Instead of just checking if an LLM can "play a game," `bubble-sim` focuses on **algorithmic fidelity**—testing whether LLMs reproduce the exact behavioral signatures of the human experiment:
- The treatment contrast between "capped" and "uncapped" price regimes.
- The "snowball effect" (the probability of speculatively buying a valueless asset increasing as a function of inferred position in the sequence).
- Variations across rational-choice models (QRE / CH / ABEE).

This project is based on an simulation design that uses prompt-based conditioning and archetype assignment without weight updates to test robust, reproducible multi-agent behavior.

## Key Features & Architecture

The framework provides a complete experimental pipeline:

1. **Canonical Data Ingestion**: Clean schemas for both human baseline data and generated agent traces (`data/ingest_human.py`, `data/ingest_agent.py`), stored in Parquet/JSONL.
2. **Deterministic Environment**: The `BubbleGameEnv` strictly models the Moinas and Pouget sequential trading mechanics with exact step definitions and state transitions (`env/engine.py`).
3. **Stateful Agent Interface**: Uses the OpenAI Assistants API (`agents/core.py`) providing:
   - Persistent conversational Threads mimicking human multi-episode learning.
   - Formal Tool Calling (`submit_decision`) instead of brittle JSON prompting.
4. **Structured Evaluation**:
   - **Micro metrics** (Weighted JS Divergence, Mean Absolute Buy-rate Gap) measure distributional decision fidelity (`eval/micro.py`).
   - **Macro metrics** (Bubble Incidence/Depth Gap, Snowball Slope Error, Terminal Holder Gap) measure emergent stylized facts (`eval/macro.py`).
5. **Rigorous Experimentation**:
   - Sweep baselines, calibrate Option A settings (sampling, prompt templates, archetype mixtures), and generate robust multi-seed final comparison matrices (`experiments/`).
6. **Robustness & Ablation Tools**: Stability scorecards test the variance across decoding parameters, prompt phrasing variants, and random seeds (`robustness/`).
7. **Safe-by-Default Governance**: Built-in redaction strings (stripping API keys, emails), configurable retention rules, and structured data minimization (`utils/redaction.py`).

## Installation

The project uses modern `pyproject.toml` packaging. Install the base runtime and strictly what you need for inference:

```bash
# Clone the repository
git clone https://github.com/your-org/bubble-llm-sim.git
cd bubble-llm-sim

# Install development tools (pytest, ruff, black)
pip install -e ".[dev]"

# Install specific inference providers if needed:
pip install -e ".[openai]"
pip install -e ".[vllm]"
pip install -e ".[hf]"
```

## CLI Usage

The framework exposes a unified Typer CLI (`bubble-sim`) for repeatable, manifest-driven experiments.

**Ingest Human Data:**
```bash
bubble-sim ingest-human --input-path docs/raw.csv --dataset-name human_v1 --output-dir data/clean
```

**Create Train/Val/Test Splits:**
```bash
bubble-sim split --dataset-dir data/clean/human_v1 --split-name heldout_treatment_v1 --method heldout_treatment
```

**Run an Experiment Simulation (Lab Mode):**
```bash
bubble-sim simulate-lab --config configs/experiments/mp2021_cap10000_rep10.yaml --subjects 72 --sessions 1
```

**Evaluate a Run (Lab Fidelity Constraints):**
```bash
bubble-sim eval-lab --run-dir runs/20260310T120000Z_lab_cap10000
```

**Generate Final Comparison Report:**
```bash
bubble-sim report-lab --run-dir runs/20260310T120000Z_lab_cap10000
```

## Development Workflow

A clean development cycle ensures the simulator remains a defensible scientific instrument.

```bash
make format  # Runs black and ruff --fix
make lint    # Runs ruff and black --check
make test    # Runs the pytest suite
make check   # Runs lint and test
```

*Every public module must pass rigorous unit tests, ensuring deterministic seed derivation and stable evaluation mathematics.*

## Data Governance & Safety

Running LLMs over behavioral data requires discipline. Please review `docs/data_governance.md` for project rules:
1. **Minimization**: We replace real participant IDs with pseudonymous `trader_id`s during ingestion.
2. **Redaction**: `utils/redaction.py` automatically scrubs API keys and auth headers from all saved trace logs.
3. **Retention**: Helper tools auto-purge failed/incomplete runs after 30 days.

---

*For detailed methodologies on Option A prompting and evaluation rationales, refer to the inline documentation within `policies/prompt_templates.py` and `eval/evaluator.py`.*
