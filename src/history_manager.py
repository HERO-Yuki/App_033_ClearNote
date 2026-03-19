"""
直近ノート履歴の保持・読み書き (JSON形式)
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


class HistoryManager:
    def __init__(self, history_path: str | Path, max_entries: int = 20):
        self.history_path = Path(history_path)
        self.max_entries = max_entries
        self._entries: list[dict] = self._load()

    def _load(self) -> list[dict]:
        if not self.history_path.exists():
            return []
        try:
            with open(self.history_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data if isinstance(data, list) else []
        except (json.JSONDecodeError, OSError):
            return []

    def _save(self):
        try:
            with open(self.history_path, "w", encoding="utf-8") as f:
                json.dump(self._entries, f, ensure_ascii=False, indent=2)
        except OSError:
            pass

    def add(self, title: str, filepath: str, tags: list[str] | None = None):
        """新しいエントリを先頭に追加し、上限を超えたら末尾を削除する"""
        entry = {
            "title": title,
            "filepath": filepath,
            "tags": tags or [],
            "saved_at": datetime.now().isoformat(timespec="seconds"),
        }
        # 同一ファイルパスの重複を除去
        self._entries = [e for e in self._entries if e.get("filepath") != filepath]
        self._entries.insert(0, entry)
        if len(self._entries) > self.max_entries:
            self._entries = self._entries[: self.max_entries]
        self._save()

    def get_recent(self, n: int = 5) -> list[dict]:
        """直近n件のエントリを返す"""
        return self._entries[:n]

    def all(self) -> list[dict]:
        return list(self._entries)
