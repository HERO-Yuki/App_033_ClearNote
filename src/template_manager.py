"""
テンプレート管理 - templates/ フォルダのMarkdownテンプレートを読み込む
"""
from __future__ import annotations

from datetime import datetime
from pathlib import Path


class TemplateManager:
    def __init__(self, templates_dir: str | Path):
        self.templates_dir = Path(templates_dir)

    def list_templates(self) -> list[str]:
        """利用可能なテンプレート名の一覧を返す (拡張子なし)"""
        if not self.templates_dir.exists():
            return ["default"]
        names = [p.stem for p in sorted(self.templates_dir.glob("*.md"))]
        # "default" を先頭に
        if "default" in names:
            names.remove("default")
            names.insert(0, "default")
        return names if names else ["default"]

    def get_body(self, name: str) -> str:
        """
        テンプレートのbody部分(--- 以降のフロントマターを除いた部分)を返す。
        テンプレートが存在しない場合は空文字列を返す。
        """
        path = self.templates_dir / f"{name}.md"
        if not path.exists():
            return ""

        raw = path.read_text(encoding="utf-8")

        # フロントマター (---...---) があれば除去
        if raw.startswith("---"):
            end = raw.find("---", 3)
            if end != -1:
                raw = raw[end + 3:].lstrip("\n")

        # プレースホルダーの置換
        now = datetime.now()
        raw = raw.replace("{{date}}", now.strftime("%Y-%m-%d"))
        raw = raw.replace("{{datetime}}", now.strftime("%Y-%m-%dT%H:%M:%S"))
        raw = raw.replace("{{year}}", now.strftime("%Y"))
        raw = raw.replace("{{month}}", now.strftime("%m"))
        raw = raw.replace("{{day}}", now.strftime("%d"))

        return raw.strip()
