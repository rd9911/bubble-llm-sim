from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

import orjson
import yaml


def sha256_bytes(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def sha256_text(text: str) -> str:
    return sha256_bytes(text.encode("utf-8"))


def sha256_file(path: str | Path, chunk_size: int = 1024 * 1024) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(chunk_size):
            h.update(chunk)
    return "sha256:" + h.hexdigest()


def canonical_json_hash(obj: Any) -> str:
    data = orjson.dumps(obj, option=orjson.OPT_SORT_KEYS)
    return sha256_bytes(data)


def canonical_yaml_hash(obj: Any) -> str:
    text = yaml.safe_dump(obj, sort_keys=True)
    return sha256_text(text)
