import os
import yaml
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent


def load_config(config_path: str | None = None) -> dict:
    if config_path is None:
        config_path = BASE_DIR / "config.yaml"
    path = Path(config_path)
    if not path.exists():
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def get(config: dict, *keys, default=None):
    """ネストしたキーを安全に取得する。例: get(config, 'obsidian', 'vault_path')"""
    val = config
    for key in keys:
        if not isinstance(val, dict):
            return default
        val = val.get(key, default)
    return val
