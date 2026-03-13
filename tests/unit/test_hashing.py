import tempfile
from pathlib import Path

from bubble_sim.utils.hashing import (
    canonical_json_hash,
    canonical_yaml_hash,
    sha256_bytes,
    sha256_file,
    sha256_text,
)


def test_sha256_bytes():
    h = sha256_bytes(b"hello")
    assert h.startswith("sha256:")
    assert len(h) == 71  # "sha256:" + 64 hex chars


def test_sha256_text():
    h = sha256_text("hello")
    assert h == sha256_bytes(b"hello")


def test_sha256_file():
    with tempfile.NamedTemporaryFile(delete=False) as f:
        f.write(b"hello")
        f.flush()
        file_path = f.name
    try:
        h = sha256_file(file_path)
        assert h == sha256_bytes(b"hello")
    finally:
        Path(file_path).unlink()


def test_canonical_json_hash():
    d1 = {"a": 1, "b": 2}
    d2 = {"b": 2, "a": 1}
    assert canonical_json_hash(d1) == canonical_json_hash(d2)


def test_canonical_yaml_hash():
    d1 = {"a": 1, "b": 2}
    d2 = {"b": 2, "a": 1}
    assert canonical_yaml_hash(d1) == canonical_yaml_hash(d2)
