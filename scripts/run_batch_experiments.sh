#!/bin/bash
# Batch simulation script for Bubble Game LLM experiments
# Total estimated cost: ~$7.00

set -e # Exit immediately if a command fails

echo "Starting batch simulation... Estimated total cost: ~$7.00"

# 1. cap1_rep10: 1 session with 12 subjects, 2 sessions with 18 subjects
echo "Running cap1_rep10 (12 subjects, 1 session)"
python3 src/bubble_sim/cli.py simulate-lab --config configs/experiments/mp2021_cap1_rep10.yaml --subjects 12 --sessions 1

echo "Running cap1_rep10 (18 subjects, 2 sessions)"
python3 src/bubble_sim/cli.py simulate-lab --config configs/experiments/mp2021_cap1_rep10.yaml --subjects 18 --sessions 2

# 2. cap1_rep20: 1 session with 12 subjects
echo "Running cap1_rep20 (12 subjects, 1 session)"
python3 src/bubble_sim/cli.py simulate-lab --config configs/experiments/mp2021_cap1_rep20.yaml --subjects 12 --sessions 1

# 3. cap10000_rep10: 3 sessions with 18 subjects
echo "Running cap10000_rep10 (18 subjects, 3 sessions)"
python3 src/bubble_sim/cli.py simulate-lab --config configs/experiments/mp2021_cap10000_rep10.yaml --subjects 18 --sessions 3

# 4. cap10000_rep20: 1 session with 28 subjects
# Note: 28 is not divisible by 3, but the CLI requires subjects % 3 == 0. 
# Adjusting to 30 subjects to satisfy protocol requirements.
echo "Running cap10000_rep20 (30 subjects, 1 session)"
python3 src/bubble_sim/cli.py simulate-lab --config configs/experiments/mp2021_cap10000_rep20.yaml --subjects 18 --sessions 1

echo "All batch simulations completed."
