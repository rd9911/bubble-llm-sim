import sys

files = [
    "src/bubble_sim/runner/checkpoints.py",
    "src/bubble_sim/runner/experiment_runner.py",
    "src/bubble_sim/runner/progress.py"
]

for file in files:
    with open(file, "r") as f:
        text = f.read()
    
    # Remove bad multiline escaped docstrings
    text = text.replace('"""Manages resumable episode trackers safely avoiding explicit crash \\\n    restarts completely."""', '"""Manages resumable episode trackers safely avoiding explicit crash restarts completely."""')
    text = text.replace('"""Orchestrates sequential batch executions securely interacting directly \\\n    over explicit Episode configurations."""', '"""Orchestrates sequential batch executions securely interacting directly over explicit Episode configurations."""')
    text = text.replace('"""Executes isolated structural episodes validating bounds continuously \\\n        logging telemetry securely."""', '"""Executes isolated structural episodes validating bounds continuously logging telemetry securely."""')
    text = text.replace('"""Safely calculate clean averages computing structural health outputs \\\n        directly to the metrics outputs cleanly resolving metrics.json"""', '"""Safely calculate clean averages computing structural health outputs directly to the metrics outputs cleanly resolving metrics.json"""')
    text = text.replace('\\\n', '') # Fallback drop dangling slashes
    
    with open(file, "w") as f:
        f.write(text)
