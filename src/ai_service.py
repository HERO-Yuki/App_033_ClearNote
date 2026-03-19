"""
Gemini APIを使ったタイトル自動生成
初回呼び出し時にクライアントを初期化してキャッシュし、2回目以降の保存を高速化する。
"""
from __future__ import annotations

import os
import re
from typing import Any

# モジュールレベルでキャッシュ: (api_key, model_name) → GenerativeModel
_model_cache: dict[tuple[str, str], Any] = {}


def _get_model(api_key: str, model_name: str) -> Any:
    """Gemini GenerativeModel を取得する。同じキー・モデルなら再利用する。"""
    key = (api_key, model_name)
    if key not in _model_cache:
        import google.generativeai as genai  # type: ignore
        genai.configure(api_key=api_key)
        _model_cache[key] = genai.GenerativeModel(model_name)
    return _model_cache[key]


def _clean_title(raw: str) -> str:
    """Geminiの回答からタイトル文字列のみを抽出する"""
    raw = raw.strip()
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
        model = _get_model(api_key, model_name)
        snippet = content[:max_chars]
        prompt = (
            "以下のメモに対して、Obsidianのノートタイトルとして最適な短いタイトルを"
            "日本語で1行だけ返してください。記号や引用符は使わないこと。\n\n"
            f"--- メモ ---\n{snippet}"
        )
        response = model.generate_content(prompt)  # type: ignore
        raw = response.text or ""
        return _clean_title(raw) or fallback

    except Exception:
        return fallback


def warmup(config: dict) -> None:
    """
    アプリ起動時に呼び出してGeminiクライアントを事前初期化する。
    APIキーがなければ何もしない。
    """
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not api_key:
        return
    try:
        model_name = config.get("ai", {}).get("model", "gemini-2.5-flash")
        _get_model(api_key, model_name)
    except Exception:
        pass


def _fallback_title(content: str) -> str:
    """本文先頭行をタイトルとして使う"""
    first_line = content.splitlines()[0].strip() if content.strip() else ""
    first_line = re.sub(r"^#+\s*", "", first_line)
    return first_line[:60] if first_line else "無題"
