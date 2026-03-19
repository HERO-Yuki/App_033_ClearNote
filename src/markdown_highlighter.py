"""
Markdownの見出し・インライン要素をカラー表示するシンタックスハイライター
フォントサイズは変えず、色のみ変更する (Catppuccin Mocha パレット準拠)
"""
from __future__ import annotations

import re
from PyQt6.QtCore import QRegularExpression
from PyQt6.QtGui import QSyntaxHighlighter, QTextCharFormat, QColor, QFont


def _fmt(color: str, bold: bool = False) -> QTextCharFormat:
    f = QTextCharFormat()
    f.setForeground(QColor(color))
    if bold:
        f.setFontWeight(QFont.Weight.Bold)
    return f


# Catppuccin Mocha カラー定義
_RULES: list[tuple[str, QTextCharFormat]] = [
    # H1  (#  ...)
    (r"^#\s.*$",    _fmt("#cba6f7", bold=True)),   # mauve
    # H2  (##  ...)
    (r"^##\s.*$",   _fmt("#89b4fa", bold=True)),   # blue
    # H3+ (### ...)
    (r"^#{3,}\s.*$", _fmt("#94e2d5", bold=True)),  # teal
    # Bold  **text**
    (r"\*\*[^*]+\*\*", _fmt("#f9e2af")),           # yellow
    # Italic  *text*  (bold の後にチェック)
    (r"(?<!\*)\*(?!\*)[^*]+\*(?!\*)", _fmt("#a6e3a1")),  # green
    # Inline code  `code`
    (r"`[^`]+`",    _fmt("#f38ba8")),              # red
    # Blockquote  > ...
    (r"^>.*$",      _fmt("#6c7086")),              # overlay0
    # Horizontal rule  --- / ***
    (r"^[-*]{3,}\s*$", _fmt("#45475a")),           # surface1
    # List item  - / * / +
    (r"^(\s*[-*+])\s", _fmt("#fab387")),           # peach (先頭マーカーのみ)
    # Numbered list  1.
    (r"^\s*\d+\.\s", _fmt("#fab387")),             # peach
]


class MarkdownHighlighter(QSyntaxHighlighter):
    def __init__(self, parent):
        super().__init__(parent)
        self._rules = [
            (QRegularExpression(pattern), fmt)
            for pattern, fmt in _RULES
        ]
        # H1/H2 は H3+ より先にマッチするよう順序を保持済み
        # ただし H2 が H1 ルールにも部分一致しないよう後から上書きが必要
        # → H2(##) は H1(#) より長いので QRegularExpression の先頭一致で問題なし

    def highlightBlock(self, text: str):
        for pattern, fmt in self._rules:
            it = pattern.globalMatch(text)
            while it.hasNext():
                m = it.next()
                self.setFormat(m.capturedStart(), m.capturedLength(), fmt)
