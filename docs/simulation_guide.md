# Simulation Guide

How to run the Bubble Game LLM Simulator, replicate the Moinas & Pouget (2013) results, and conduct independent experiments.

---

## Prerequisites

```bash
# 1. Clone and install
git clone https://github.com/your-org/bubble-llm-sim.git
cd bubble-llm-sim
pip install -e ".[dev]"

# 2. Set your OpenAI API key in .env
echo "OPENAI_API_KEY=sk-your-key-here" > .env

# 3. Verify installation
bubble-sim version
make check
```

---

## Part 1: Replicating the Moinas & Pouget (2013) Paper

### Background

The Bubble Game (Moinas & Pouget 2013) studies speculative bubbles in a sequential trading game where:
- An asset with **zero intrinsic value** is traded among participants.
- Each participant decides to **buy** or **not buy** at the offered price.
- If you buy at price P, the next participant is offered the asset at **10×P**.
- If they buy, you profit (9×P). If they don't (or you're last), you lose P.
- Participants **don't know their position** in the sequence.

The paper ran **234 subjects** across **4 treatments**:

| Treatment | Price Cap (K) | Price Path | Subjects | Key Finding |
|-----------|--------------|------------|----------|-------------|
| K=1 | 1 | 1 → 10 | 60 | ~90% buy at P=1, ~30% at P=10 |
| K=100 | 100 | 1 → 10 → 100 | 54 | Snowball effect visible |
| K=10,000 | 10,000 | 1 → … → 10,000 | 63 | Strong snowball, 0% at cap |
| K=∞ | ∞ | 1 → 10 → … | 57 | 100% buy when sure not last |

### Step 1: Ingest the Human Baseline Data

```bash
bubble-sim ingest-human \
  --input-path data/raw/moinas_pouget_2013.csv \
  --dataset-name human_mp2013 \
  --output-dir data/clean
```

This converts the raw CSV into the canonical Parquet format used by the evaluation pipeline.

### Step 2: Create Train/Test Splits

```bash
# Held-out treatment split (reserves one treatment for validation)
bubble-sim split \
  --dataset-dir data/clean/human_mp2013 \
  --split-name heldout_treatment_v1 \
  --method heldout_treatment

# Random episode split (standard cross-validation)
bubble-sim split \
  --dataset-dir data/clean/human_mp2013 \
  --split-name random_episode_v1 \
  --method random_episode
```

### Step 3: Run the Replication Simulation

The pre-built config mirrors the paper's 4 treatments exactly:

```bash
bubble-sim simulate-lab \
  --config configs/experiments/mp2021_cap10000_rep10.yaml \
  --subjects 72 \
  --sessions 1
```

This will:
1. Load the paper-faithful prompt (v5) that mirrors the actual experimental instructions.
2. Run GPT-4o as a simulated participant for each treatment.
3. Write JSONL traces and checkpoints to `runs/<run_id>/`.

**To run a smaller test first** (e.g., 5 episodes per treatment):

```bash
bubble-sim simulate-lab \
  --config configs/experiments/mp2021_cap10000_rep10.yaml \
  --subjects 3 \
  --sessions 1
```

### Step 4: Evaluate Against Human Data

```bash
bubble-sim eval-lab \
  --run-dir runs/<your-run-id>
```

### Step 5: Generate Comparison Report

```bash
bubble-sim report-lab \
  --run-dir runs/<your-run-id>
```

### What to Look For

The key empirical signatures to check in the replication:

1. **Snowball effect**: Buy rate should increase as the number of reasoning steps increases (moving away from the price cap).
2. **Position uncertainty matters**: Participants who are *sure not to be last* should buy more than those who *might be last*.
3. **Treatment contrast**: Buy rate should be higher in the uncapped (K=∞) treatment than in capped treatments when participants are sure not to be last.
4. **Zero buying at cap**: When the offered price equals the maximum cap, nobody should buy (they know they're last).

---

## Part 2: Running Independent Experiments

### Option A: Different Model

Create a new config that swaps the model backend:

```yaml
# configs/experiments/independent_gpt35.yaml
experiment:
  name: independent_gpt35_turbo
  description: "Independent run with GPT-3.5 Turbo"

agent:
  model: "gpt-3.5-turbo"
  instructions: "You are a trader in a sequential market..."

runner:
  fallback_action: no_buy
  max_retries: 2

treatments:
  - name: K100_capped
    cap_type: capped
    price_path: [1, 10, 100]
    max_price: 100
    episodes: 100

  - name: Kinf_uncapped
    cap_type: uncapped
    price_path: [1, 10, 100, 1000, 10000, 100000, 1000000]
    max_price: null
    episodes: 100

seeds:
  global_seed: 123
```

Then run:

```bash
bubble-sim simulate-lab --config configs/experiments/independent_gpt35.yaml --subjects 72 --sessions 1
```

### Option B: Local Open-Source Model (via vLLM)

```yaml
# configs/experiments/independent_llama.yaml
experiment:
  name: independent_llama3_70b
  description: "Independent run with Llama 3 70B via vLLM"

agent:
  model: "meta-llama/Meta-Llama-3-70B-Instruct"
  instructions: "You are a trader in a sequential market..."

runner:
  fallback_action: no_buy
  max_retries: 3

treatments:
  - name: K10000_capped
    cap_type: capped
    price_path: [1, 10, 100, 1000, 10000]
    max_price: 10000
    episodes: 200

seeds:
  global_seed: 7
```

Start vLLM first, then run:

```bash
# Terminal 1: Start vLLM server
python -m vllm.entrypoints.openai.api_server \
  --model meta-llama/Meta-Llama-3-70B-Instruct \
  --port 8000

# Terminal 2: Run simulation
bubble-sim simulate-lab --config configs/experiments/independent_llama.yaml --subjects 72 --sessions 1
```

### Option C: Different Instructions Strategy

Use an archetype-conditioned set of instructions instead of generic ones:

```yaml
agent:
  instructions: |
    You are an aggressive speculative trader who relies heavily on technical trends.
    You believe you can always find a greater fool.
```

This adds behavioral profiles to each simulated participant, testing whether persona conditioning changes speculation patterns.

### Option D: Custom Treatments

Design your own experimental treatments by modifying the `treatments` section:

```yaml
treatments:
  # Novel treatment: very long price path
  - name: K1000000_deep
    cap_type: capped
    price_path: [1, 10, 100, 1000, 10000, 100000, 1000000]
    max_price: 1000000
    episodes: 100

  # Novel treatment: small cap, many episodes
  - name: K10_small
    cap_type: capped
    price_path: [1, 10]
    max_price: 10
    episodes: 500
```

---

## Part 3: Comparing Results

### Cross-Model Comparison

After running multiple configs, evaluate each against the same human baseline:

```bash
# Evaluate GPT-4o run
bubble-sim eval-lab --run-dir runs/gpt4o_run

# Evaluate GPT-3.5 run
bubble-sim eval-lab --run-dir runs/gpt35_run

# Evaluate Llama run
bubble-sim eval-lab --run-dir runs/llama_run

# Generate final comparison (Run report per directory or aggregate later)
bubble-sim report-lab --run-dir runs/gpt4o_run
```

### Key Metrics to Compare

| Metric | What It Measures | Good Score |
|--------|-----------------|------------|
| **JS Divergence** | Distribution match of buy rates | < 0.05 |
| **Buy-Rate MAE** | Absolute gap per price level | < 0.10 |
| **Snowball Slope Error** | Gradient of buy rate vs position | < 0.05 |
| **Bubble Incidence Gap** | Fraction of episodes forming bubbles | < 0.10 |
| **Terminal Holder Gap** | Who gets stuck holding | < 0.10 |

---

## Output Structure

After running a simulation, the output directory will contain:

```
runs/
└── 20260309T150000Z_baseline_paper_faithful/
    ├── K1_capped/
    │   ├── traces.jsonl          # Per-step decisions and transitions
    │   ├── checkpoint.json       # Resumable progress tracker
    │   └── metrics.json          # Aggregate run health stats
    ├── K100_capped/
    │   └── ...
    ├── K10000_capped/
    │   └── ...
    └── Kinf_uncapped/
        └── ...
```

Each line in `traces.jsonl` is either a **PolicyCallEvent** (LLM request/response) or a **TransitionEvent** (environment state change).

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| `ImportError: openai` | Run `pip install openai` |
| API rate limits | Reduce episodes or add delays in config |
| Parse failures | Check `traces.jsonl` for raw LLM responses; consider using `bubble_prompt_v3_strict_json` |
| Resuming a crashed run | Just re-run the same command — checkpointing will skip completed episodes |
| Different Python version | The project requires Python 3.11+; check with `python3 --version` |
