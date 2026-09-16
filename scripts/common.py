"""Shared project paths, schemas and recoverable writes. Python 3.10+."""
from __future__ import annotations
import hashlib
import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path

SCHEMAS = {
    "cards": ("卡牌", ["key", "名称", "稀有度", "类型", "费用", "描述", "升级后费用", "升级后描述", "备注"]),
    "keywords": ("关键词", ["关键词", "描述", "备注"]),
    "powers": ("状态", ["key", "名称", "描述", "关联卡牌"]),
    "relics": ("遗物", ["key", "名称", "遗物池", "稀有度", "描述", "备注"]),
}
def stamp():
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")

def encode(value):
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")

def digest(value):
    return hashlib.sha256(encode(value)).hexdigest()

def file_hash(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def read_json(path, default=None):
    path = Path(path)
    return json.loads(path.read_text(encoding="utf-8-sig")) if path.exists() else default

def inside(root, value):
    root = Path(root).resolve()
    path = (root / Path(os.fspath(value).replace("\\", "/")).expanduser()).resolve()
    if not path.is_relative_to(root):
        raise ValueError(f"Path is outside project: {path}")
    return path

def atomic_write(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix=".moddev-", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(data)
        os.replace(name, path)
    finally:
        if os.path.exists(name):
            os.unlink(name)

def transaction(changes, backup_dir=None, *, create_only=False):
    """Preflight all destinations; restore original bytes on ordinary write failure."""
    changes = {Path(p).resolve(): data for p, data in changes.items()}
    original = {}
    for path in changes:
        if create_only and path.exists():
            raise FileExistsError(f"Existing file preserved: {path}")
        original[path] = path.read_bytes() if path.exists() else None
    if backup_dir is not None:
        backup_dir = Path(backup_dir)
        backup_dir.mkdir(parents=True, exist_ok=False)
        manifest = []
        for i, (path, data) in enumerate(original.items()):
            name = f"{i:04d}.bak" if data is not None else None
            if name:
                atomic_write(backup_dir / name, data)
            manifest.append({"path": str(path), "backup": name})
        atomic_write(backup_dir / "manifest.json", encode(manifest))
    written = []
    try:
        for path, data in changes.items():
            atomic_write(path, data)
            written.append(path)
    except Exception as error:
        failures = []
        for path in reversed(written):
            try:
                if original[path] is None:
                    path.unlink(missing_ok=True)
                else:
                    atomic_write(path, original[path])
            except Exception as rollback_error:
                failures.append(f"{path}: {rollback_error}")
        if failures:
            raise RuntimeError(f"Write failed: {error}; restore backup manually: {failures}") from error
        raise

class Project:
    def __init__(self, config):
        self.config_path = Path(config).resolve()
        self.data = read_json(self.config_path)
        if not isinstance(self.data, dict) or self.data.get("schema_version") != 1:
            raise ValueError("Expected schema_version=1 project config")
        self.root = (self.config_path.parent / Path(self.data.get("project_root", ".").replace("\\", "/")).expanduser()).resolve()
        self.workbook = self.path(self.data["workbook"])
        self.state = self.path(self.data.get("state_dir", ".moddev"))
        self.manifest = self.path(self.data.get("asset_manifest", ".moddev/assets.json"))
        self.progress = self.state / "progress.json"

    def path(self, value):
        return inside(self.root, value)

    def context_hash(self):
        return digest(self.data)

    def baseline_path(self, kind):
        return self.state / "snapshots" / kind / "current.json"

    def baseline(self, kind):
        return read_json(self.baseline_path(kind), {"schema_version": 1, "entries": {}})

