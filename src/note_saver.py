"""
Markdownファイルの生成・保存ロジック
"""
from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path


def _sanitize_filename(name: str, max_len: int = 60) -> str:
    """ファイル名として使えない文字を除去し、長さを制限する"""
    name = re.sub(r'[\\/:*?"<>|]', "", name)
    name = re.sub(r"\s+", " ", name).strip()
    return name[:max_len] if name else "untitled"


def _build_frontmatter(tags: list[str], template_name: str, created: datetime) -> str:
    tag_str = ", ".join(tags) if tags else ""
    lines = [
        "---",
        f'created: {created.strftime("%Y-%m-%dT%H:%M:%S")}',
    ]
    if tag_str:
        lines.append(f"tags: [{tag_str}]")
    if template_name and template_name != "default":
        lines.append(f"template: {template_name}")
    lines.append("---")
    return "\n".join(lines)


def build_markdown(title: str, body: str, tags: list[str], template_name: str) -> str:
    """保存するMarkdown文字列を組み立てる"""
    now = datetime.now()
    frontmatter = _build_frontmatter(tags, template_name, now)
    return f"{frontmatter}\n\n# {title}\n\n{body}\n"


def resolve_filepath(
    title: str,
    vault_path: str,
    inbox_folder: str,
    filename_format: str = "title",
) -> Path:
    """保存先パスを解決する (重複時は連番を付与)"""
    base = Path(vault_path) / inbox_folder
    base.mkdir(parents=True, exist_ok=True)

    if filename_format == "timestamp":
        stem = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    else:
        stem = _sanitize_filename(title) or datetime.now().strftime("%Y-%m-%d_%H%M%S")

    filepath = base / f"{stem}.md"
    counter = 1
    while filepath.exists():
        filepath = base / f"{stem}_{counter}.md"
        counter += 1

    return filepath


def save_note(
    title: str,
    body: str,
    tags: list[str],
    template_name: str,
    vault_path: str,
    inbox_folder: str,
    filename_format: str = "title",
) -> Path:
    """MarkdownをObsidian Vaultへ保存し、保存先パスを返す"""
    filepath = resolve_filepath(title, vault_path, inbox_folder, filename_format)
    content = build_markdown(title, body, tags, template_name)
    filepath.write_text(content, encoding="utf-8")
    return filepath
