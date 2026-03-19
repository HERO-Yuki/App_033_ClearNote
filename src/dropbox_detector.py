"""
Dropboxのインストールパスを自動検出するユーティリティ
Dropboxは %APPDATA%\Dropbox\info.json にパスを記録している。
"""
from __future__ import annotations

import json
import os
from pathlib import Path


def find_dropbox_root() -> Path | None:
    """
    Dropboxのルートフォルダパスを返す。
    見つからない場合は None を返す。
    """
    candidates = [
        Path(os.environ.get("APPDATA", "")) / "Dropbox" / "info.json",
        Path(os.environ.get("LOCALAPPDATA", "")) / "Dropbox" / "info.json",
    ]
    for info_path in candidates:
        if not info_path.exists():
            continue
        try:
            with open(info_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            # personal または business アカウントのパスを取得
            for account_type in ("personal", "business"):
                entry = data.get(account_type, {})
                raw_path = entry.get("path")
                if raw_path:
                    p = Path(raw_path)
                    if p.exists():
                        return p
        except (json.JSONDecodeError, OSError):
            continue
    return None


def resolve_vault_path(config_vault_path: str) -> str:
    """
    config.yaml の vault_path を解決する。
    - "auto" または空文字の場合: Dropboxを自動検出してデフォルトパスを返す
    - それ以外: そのまま返す
    """
    if config_vault_path and config_vault_path.lower() != "auto":
        return config_vault_path

    dropbox_root = find_dropbox_root()
    if dropbox_root is None:
        raise RuntimeError(
            "Dropbox のインストールパスを自動検出できませんでした。\n"
            "config.yaml の obsidian.vault_path に手動でパスを設定してください。"
        )
    # デフォルト: Dropbox/アプリ/remotely-save/sin-Vault
    return str(dropbox_root / "アプリ" / "remotely-save" / "sin-Vault")
