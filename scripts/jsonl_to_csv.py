import pandas as pd
import json
import argparse
import sys
from pathlib import Path

def flatten_traces(input_path, output_path):
    """
    Flattens JSONL traces into a unified CSV structure.
    Merges detailed step records with summary transition records.
    """
    detail_records = {}
    summary_records = {}

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
                print(f"Warning: Skipping invalid JSON line: {line[:100]}...")
                continue
            
            run_id = record.get('run_id')
            episode_id = record.get('episode_id')
            step_index = record.get('step_index')
            
            if run_id is None or episode_id is None or step_index is None:
                # Try to get them from nested state if available (though snippet shows them at top level in both)
                state = record.get('state', {})
                episode_id = episode_id or state.get('episode_id')
                step_index = step_index if step_index is not None else state.get('step_index')
            
            key = (run_id, episode_id, step_index)

            if 'state' in record:
                # Detail record
                detail_records[key] = record
            else:
                # Summary record
                summary_records[key] = record

    # Merge records
    flattened_data = []
    all_keys = set(detail_records.keys()) | set(summary_records.keys())

    for key in sorted(all_keys):
        det = detail_records.get(key, {})
        sum_ = summary_records.get(key, {})
        
        # Merge basic fields
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

        # Flatten summary/outcomes
        row['reward'] = sum_.get('reward')
        row['done'] = sum_.get('done')
        row['terminal_reason'] = sum_.get('terminal_reason')

        # Flatten metadata
        row['model_id'] = det.get('model_id')
        row['prompt_template_id'] = det.get('prompt_template_id')
        row['prompt_template_hash'] = det.get('prompt_template_hash')
        row['retry_count'] = det.get('retry_count')
        row['fallback_used'] = det.get('fallback_used')
        row['parse_success'] = det.get('parse_success')

        flattened_data.append(row)

    if not flattened_data:
        print("Error: No valid records found to convert.")
        sys.exit(1)

    df = pd.DataFrame(flattened_data)
    
    # Ensure run_id, episode_id, step_index are first
    cols = ['run_id', 'episode_id', 'step_index']
    other_cols = [c for c in df.columns if c not in cols]
    df = df[cols + other_cols]
    
    df.to_csv(output_path, index=False)
    print(f"Successfully converted {len(flattened_data)} records to {output_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Convert JSONL traces to unified CSV.")
    parser.add_argument("input", help="Path to input JSONL file")
    parser.add_argument("output", help="Path to output CSV file")
    args = parser.parse_args()
    
    flatten_traces(args.input, args.output)
