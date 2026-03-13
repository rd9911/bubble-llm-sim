from __future__ import annotations

import datetime
import json
import platform
import subprocess
from pathlib import Path
from typing import Any

import jsonschema

from bubble_sim.version import __version__


def _get_git_info() -> dict[str, Any]:
    try:
        commit = subprocess.check_output(["git", "rev-parse", "HEAD"]).decode("utf-8").strip()
        branch = (
            subprocess.check_output(["git", "rev-parse", "--abbrev-ref", "HEAD"])
            .decode("utf-8")
            .strip()
        )
        status = subprocess.check_output(["git", "status", "--porcelain"]).decode("utf-8").strip()
        is_dirty = len(status) > 0
        return {"commit": commit, "branch": branch, "is_dirty": is_dirty}
    except Exception:
        return {"commit": "unknown", "branch": "unknown", "is_dirty": False}


def _get_runtime_info() -> dict[str, Any]:
    return {
        "python_version": platform.python_version(),
        "platform": platform.platform(),
        "hostname": platform.node(),
    }


def generate_run_id(experiment_name: str, policy_id: str, global_seed: int) -> str:
    timestamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")

    def _clean(s: str) -> str:
        s = s.lower().replace(" ", "_")
        return "".join(c for c in s if c.isalnum() or c == "_")

    exp = _clean(experiment_name)
    pol = _clean(policy_id)
    return f"{timestamp}_{exp}_{pol}_seed{global_seed}"


def create_manifest(
    run_id: str,
    experiment_details: dict[str, Any],
    environment_details: dict[str, Any],
    policy_details: dict[str, Any],
    dataset_details: dict[str, Any],
    seeds: dict[str, int],
    outputs_details: dict[str, Any],
) -> dict[str, Any]:
    return {
        "manifest_version": "1.0",
        "run_id": run_id,
        "created_at_utc": datetime.datetime.now(datetime.timezone.utc).strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        ),
        "git": _get_git_info(),
        "code": {"package_version": __version__},
        "experiment": experiment_details,
        "environment": environment_details,
        "policy": policy_details,
        "dataset": dataset_details,
        "seeds": seeds,
        "runtime": _get_runtime_info(),
        "outputs": outputs_details,
    }


def validate_manifest(manifest: dict[str, Any], schema_path: str | Path) -> None:
    with open(schema_path, encoding="utf-8") as f:
        schema = json.load(f)
    jsonschema.validate(instance=manifest, schema=schema)


def save_manifest(manifest: dict[str, Any], out_path: str | Path) -> None:
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
