import json
from pathlib import Path

from bubble_sim.utils.manifest import (
    create_manifest,
    generate_run_id,
    save_manifest,
    validate_manifest,
)


def test_generate_run_id():
    run_id = generate_run_id("My Exp", "Pol-1", 42)
    assert "my_exp" in run_id
    assert "pol_1" in run_id or "pol1" in run_id
    assert "seed42" in run_id


def test_manifest_creation_and_validation(tmp_path):
    run_id = generate_run_id("test", "test", 42)
    manifest = create_manifest(
        run_id=run_id,
        experiment_details={"name": "test", "description": "test"},
        environment_details={"env_name": "test"},
        policy_details={"model_id": "test"},
        dataset_details={"dataset_name": "test"},
        seeds={"global_seed": 42},
        outputs_details={"trace_path": "traces.jsonl"},
    )

    schema_path = Path(__file__).parent.parent.parent / "manifest.schema.json"

    # Validation should succeed
    validate_manifest(manifest, schema_path)

    out_path = tmp_path / "manifest.json"
    save_manifest(manifest, out_path)
    assert out_path.exists()

    with open(out_path) as f:
        loaded = json.load(f)
    assert loaded["run_id"] == run_id
