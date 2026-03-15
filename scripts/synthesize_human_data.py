import csv
import random
from pathlib import Path

# Data from the user's provided tables

# Figure 2: Likelihood of bubbles (%)
# Each row: [No, Small, Medium, Large]
CAP1_BUBBLE_PROBS = [
    [10, 40, 45, 5],   # Period 1
    [15, 50, 25, 10],  # 2
    [15, 55, 30, 0],   # 3
    [25, 25, 35, 15],  # 4
    [25, 40, 30, 5],   # 5
    [25, 45, 25, 5],   # 6
    [10, 50, 35, 5],   # 7
    [15, 50, 35, 0],   # 8
    [30, 35, 25, 10],  # 9
    [40, 35, 25, 0],   # 10
]

CAP10000_BUBBLE_PROBS = [
    [17, 29, 17, 37],  # 1
    [4, 38, 25, 33],   # 2
    [8, 21, 33, 38],   # 3
    [12, 25, 21, 42],  # 4
    [21, 21, 21, 37],  # 5
    [21, 25, 29, 25],  # 6
    [17, 21, 17, 45],  # 7
    [12, 21, 17, 50],  # 8
    [12, 4, 38, 46],   # 9
    [4, 25, 29, 42],   # 10
]

# Breakdown of subjects
# 132 subjects total
DESIGN = {
    "K1": {
        "10_reps": {"subjects": 48, "reps": 10},
        "20_reps": {"subjects": 12, "reps": 20},
        "max_steps": 2,
        "prices": [1, 10, 100],
    },
    "K10000": {
        "10_reps": {"subjects": 54, "reps": 10},
        "20_reps": {"subjects": 18, "reps": 20},
        "max_steps": 6,
        "prices": [1, 10, 100, 1000, 10000, 100000, 1000000],
    }
}

def sample_outcome(probs):
    r = random.random() * 100
    cum = 0
    for i, p in enumerate(probs):
        cum += p
        if r <= cum:
            return ["no_bubble", "small", "medium", "large"][i]
    return "no_bubble"

def get_actions(outcome):
    if outcome == "no_bubble":
        return ["no_buy"]
    if outcome == "small":
        return ["buy", "no_buy"]
    if outcome == "medium":
        return ["buy", "buy", "no_buy"]
    if outcome == "large":
        return ["buy", "buy", "buy"]
    return ["no_buy"]

def synthesize():
    output_path = Path("data/raw/synthetic_mp2013_aligned.csv")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    rows = []
    
    # We'll use a globally unique session_id for each market (episode)
    global_market_id = 1
    subject_counter = 1

    for treatment_name, configs in DESIGN.items():
        for rep_type in ["10_reps", "20_reps"]:
            cfg = configs[rep_type]
            n_subjects = cfg["subjects"]
            n_reps = cfg["reps"]
            n_groups = n_subjects // 3
            
            # Create persistent subjects for this treatment/rep combo
            subjects = [f"SYN_S{subject_counter + i:03d}" for i in range(n_subjects)]
            subject_counter += n_subjects
            
            # Prices
            max_p_list = DESIGN[treatment_name]["prices"]
            max_steps = DESIGN[treatment_name]["max_steps"]
            cap_val = 1 if treatment_name == "K1" else 10000

            for rep_idx in range(n_reps):
                # Stranger matching: shuffle subjects each rep
                shuffled_subjects = list(subjects)
                random.shuffle(shuffled_subjects)
                
                # Probs for this period (1-indexed in table, 0-indexed here)
                # If rep > 10, we wrap around or use the 10th period as proxy
                p_idx = min(rep_idx, 9)
                probs = CAP1_BUBBLE_PROBS[p_idx] if treatment_name == "K1" else CAP10000_BUBBLE_PROBS[p_idx]
                
                for group_idx in range(n_groups):
                    group = shuffled_subjects[group_idx*3 : (group_idx+1)*3]
                    
                    outcome = sample_outcome(probs)
                    actions = get_actions(outcome)
                    
                    # For Cap=10000, the first price varies. 
                    # But Figure 2 is an aggregate. 
                    # For simplicity and to match the "max steps" logic, 
                    # we'll assume the starting price for T1 is a draw.
                    # In Cap 1, it's always 1.
                    # In Cap 10000, it could be 1, 10, 100, 1000, 10000.
                    # We'll pick one randomly to reflect the variety.
                    if treatment_name == "K1":
                        start_idx = 0
                    else:
                        start_idx = random.randint(0, 4) # 1 to 10000
                    
                    for i, action in enumerate(actions):
                        p_idx_in_path = start_idx + i
                        price = max_p_list[p_idx_in_path]
                        steps = max_steps - p_idx_in_path
                        
                        rows.append({
                            "subject_id": group[i],
                            "session_id": f"SYN_M{global_market_id:05d}",
                            "treatment": treatment_name,
                            "cap_value": cap_val,
                            "cap_type": "capped",
                            "offered_price": price,
                            "price_index": p_idx_in_path,
                            "prob_not_last": 1.0 if p_idx_in_path < len(max_p_list)-1 else 0.0, # Placeholder
                            "steps_of_reasoning": steps,
                            "action": action,
                            "risk_aversion_score": 0.5 # Placeholder
                        })
                    
                    global_market_id += 1

    with open(output_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    
    print(f"Synthesized {len(rows)} rows into {output_path}")

if __name__ == "__main__":
    synthesize()
