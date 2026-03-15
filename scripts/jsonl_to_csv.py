import pandas as pd
import json
import argparse
import sys
from pathlib import Path

def convert_traces(input_path, output_path):
    """
    Converts JSONL traces to a unified CSV.
    Supports both legacy step traces and new lab session traces.
    Filters out questionnaire (quiz) responses.
    """
    records = []
    
    # Store summary info for merging if needed (mainly for legacy)
    legacy_details = {}
    legacy_summaries = {}
    
    input_file = Path(input_path)
    if not input_file.exists():
        print(f"Error: Input file {input_path} not found.")
        sys.exit(1)

    with open(input_path, 'r') as f:
        for line in f:
            if not line.strip():
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue
            
            # --- Filter Logic ---
            # Skip QuizRecords (contain answer_correct)
            if 'answer_correct' in record:
                continue
                
            # --- Lab Trace Logic ---
            # Detect LabDecisionRecord (has both subject_id and action)
            if 'subject_id' in record and 'action' in record:
                records.append(record)
                continue
            
            # --- Legacy Trace Logic ---
            # Detect Legacy Step Records
            run_id = record.get('run_id')
            episode_id = record.get('episode_id')
            step_index = record.get('step_index')
            
            if run_id and episode_id and step_index is not None:
                key = (run_id, episode_id, step_index)
                if 'state' in record:
                    legacy_details[key] = record
                else:
                    legacy_summaries[key] = record

    # Process legacy merges
    if legacy_details:
        all_legacy_keys = set(legacy_details.keys()) | set(legacy_summaries.keys())
        for key in sorted(all_legacy_keys):
            det = legacy_details.get(key, {})
            sum_ = legacy_summaries.get(key, {})
            
            row = {
                'run_id': key[0],
                'episode_id': key[1],
                'step_index': key[2],
            }
            
            # Flatten config
            config = det.get('config', {})
            row['treatment_name'] = config.get('treatment_name')
            row['n_traders_total'] = config.get('n_traders_total')
            row['price_path'] = json.dumps(config.get('price_path')) if config.get('price_path') else None
            row['max_price'] = config.get('max_price')

            # Flatten state
            state = det.get('state', {})
            row['offered_price'] = state.get('offered_price')
            row['cap_type'] = state.get('cap_type')
            row['price_index'] = state.get('price_index')
            row['position_uncertainty'] = state.get('position_uncertainty')

            # Flatten profile
            profile = det.get('profile', {})
            row['trader_id'] = profile.get('trader_id')

            # Flatten output
            output = det.get('output', {})
            row['action'] = output.get('action') or sum_.get('action')
            row['rationale'] = output.get('rationale')
            
            raw = output.get('raw', {})
            row['confidence'] = raw.get('confidence')
            row['belief_resell'] = raw.get('belief_resell')
            row['rationale_short'] = raw.get('rationale_short')

            # Outcomes
            row['reward'] = sum_.get('reward')
            row['done'] = sum_.get('done')
            row['terminal_reason'] = sum_.get('terminal_reason')

            # Metadata
            row['model_id'] = det.get('model_id')
            row['parse_success'] = det.get('parse_success')

            records.append(row)

    if not records:
        print("Error: No valid records found to convert.")
        sys.exit(1)

    df = pd.DataFrame(records)
    
    # Order columns logically
    priority_cols = ['session_id', 'period_index', 'market_id', 'subject_id', 'run_id', 'episode_id', 'step_index', 'action']
    cols = [c for c in priority_cols if c in df.columns]
    other_cols = [c for c in df.columns if c not in cols]
    df = df[cols + other_cols]
    
    df.to_csv(output_path, index=False)
    print(f"Successfully converted {len(records)} records to {output_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Convert JSONL traces to unified CSV.")
    parser.add_argument("input", help="Path to input JSONL file")
    parser.add_argument("output", help="Path to output CSV file")
    args = parser.parse_args()
    
    convert_traces(args.input, args.output)
