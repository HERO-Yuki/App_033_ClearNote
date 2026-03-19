"""
Gemini APIを使ったタイトル自動生成
"""
from __future__ import annotations

import os
import re


def _clean_title(raw: str) -> str:
    """Geminiの回答からタイトル文字列のみを抽出する"""
    raw = raw.strip()
    # コードブロックや引用符の除去
    raw = re.sub(r"^[`\"'#*]+|[`\"'#*]+$", "", raw)
    raw = re.sub(r"\s+", " ", raw).strip()
    return raw or "無題"


def generate_title(content: str, config: dict) -> str:
    """
    本文からGemini APIでタイトルを生成して返す。
    失敗した場合は本文の最初の行をフォールバックとして使用する。
    """
    fallback = _fallback_title(content)

    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not api_key:
        return fallback

    ai_cfg = config.get("ai", {})
    model_name = ai_cfg.get("model", "gemini-2.5-flash")
    max_chars = ai_cfg.get("max_content_for_title", 500)

    try:
        import google.generativeai as genai  # type: ignore

        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(model_name)

        snippet = content[:max_chars]
        prompt = (
            "以下のメモに対して、Obsidianのノートタイトルとして最適な短いタイトルを"
            "日本語で1行だけ返してください。記号や引用符は使わないこと。\n\n"
            f"--- メモ ---\n{snippet}"
        )
        response = model.generate_content(prompt)
        raw = response.text or ""
        return _clean_title(raw) or fallback

    except Exception:
        return fallback


def _fallback_title(content: str) -> str:
    """本文先頭行をタイトルとして使う"""
    first_line = content.splitlines()[0].strip() if content.strip() else ""
    first_line = re.sub(r"^#+\s*", "", first_line)
    return first_line[:60] if first_line else "無題"
