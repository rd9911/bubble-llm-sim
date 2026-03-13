# Data Governance

## Data Minimization Checklist

### Before Ingestion
- Remove direct personal identifiers
- Store subject keys separately from behavioral data
- Ingest only fields needed for simulation/evaluation

### During Canonicalization
- Replace raw participant IDs with pseudonymous `trader_id`
- Drop free-text fields not needed for evaluation
- Avoid storing unnecessary timestamps

### During Simulation
- Do not log secrets or API keys
- Store prompt hashes and sampled renders, not full prompts per trace row
- Redact secrets from all logged text via `utils/redaction.py`

### During Reporting
- Aggregate results where possible
- Avoid publishing row-level human data unless approved

## Redaction Policy
- API keys, auth headers, emails are redacted automatically
- `redact_trace_row()` applied to all trace artifacts before storage
- Raw model text retained; participant identifiers never copied verbatim

## Access Control Tiers

| Tier | Location | Access |
|------|----------|--------|
| 1 — Raw data | `data/raw/` | Project owner / approved researchers only |
| 2 — Clean canonical | `data/clean/` | Restricted, broader if approved |
| 3 — Run artifacts | `runs/`, `eval/` | Internal project team |
| 4 — Public results | `final_results/` | Shareable if fully redacted and aggregated |

## Retention Rules

| Artifact | Default Retention |
|----------|-------------------|
| Raw data | Duration of approved research use |
| Failed/incomplete runs | 30 days |
| Prompt samples | 90 days |
| Evaluation artifacts | 365 days |
| Final results | Indefinite (for reproducibility) |

## Safe-by-Default Config

```yaml
logging:
  store_raw_prompts_per_trace: false
  store_prompt_samples: true
  redact_secrets: true
  redact_identifiers: true

retention:
  keep_failed_runs_days: 30
  keep_prompt_samples_days: 90
  keep_eval_artifacts_days: 365
```
