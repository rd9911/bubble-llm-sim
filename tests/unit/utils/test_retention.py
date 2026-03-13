import time

from bubble_sim.utils.retention import (
    RetentionConfig,
    identify_expired_runs,
)


def test_retention_config_defaults():
    cfg = RetentionConfig()
    assert cfg.keep_failed_runs_days == 30
    assert cfg.keep_eval_artifacts_days == 365


def test_identify_expired(tmp_path):
    old = tmp_path / "old_run"
    old.mkdir()
    new = tmp_path / "new_run"
    new.mkdir()
    # backdate the old run
    import os

    old_time = time.time() - (60 * 86400)
    os.utime(old, (old_time, old_time))

    expired = identify_expired_runs(tmp_path, max_age_days=30)
    assert old in expired
    assert new not in expired


def test_empty_dir(tmp_path):
    expired = identify_expired_runs(tmp_path / "nonexistent")
    assert expired == []
