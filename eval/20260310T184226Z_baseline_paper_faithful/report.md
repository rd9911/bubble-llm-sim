# Evaluation Report: 20260310T184226Z_baseline_paper_faithful

## Run Health
- **n_episodes**: 11

## Micro Fidelity
- **total_buckets**: 4
- **sparse_bucket_fraction**: 0.75
- **weighted_js_divergence**: 0.03484015548985887
- **weighted_kl_divergence**: 0.11692552715067234
- **mean_absolute_buy_rate_gap**: 0.1634146341463414

## Macro Fidelity
- **bubble_depth_gap**: -1.5
- **snowball_slope_error**: -0.4500000000000001
- **treatment_gap_error**: -0.7000000000000001
- **terminal_holder_gap**: -0.20909090909090908
- **raw_mean_bubble_depth**: 1.0
- **raw_terminal_holder_freq**: 0.09090909090909091
- **raw_snowball_slope**: -0.2500000000000001
- **raw_treatment_gap**: -0.55

## Calibration
- **dummy_calib**: 0.0

## Promotion Gates
**Overall**: ✅ PASSED
- gate1_operational: ✅
- gate2_micro: ✅
- gate3_macro: ✅
- gate4_heldout: ✅

## Scorecard
### Behavior
- fidelity: 🟢 green
