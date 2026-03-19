"""
クイックノート入力ウィンドウ (PyQt6)
ホットキーで呼び出され、テキストを入力してMarkdownとして保存する。
"""
from __future__ import annotations

import threading
from typing import TYPE_CHECKING, Callable

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QKeySequence, QShortcut
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextEdit,
    QLineEdit, QPushButton, QLabel, QComboBox,
    QFrame, QSizeGrip, QApplication, QMenu, QToolButton,
)

if TYPE_CHECKING:
    from src.template_manager import TemplateManager
    from src.history_manager import HistoryManager


class NoteWindow(QWidget):
    """Drafts風クイック入力ウィンドウ"""

    def __init__(
        self,
        config: dict,
        template_manager: "TemplateManager",
        history_manager: "HistoryManager",
        on_save: Callable[[str, list[str], str], None],
    ):
        super().__init__()
        self.config = config
        self.template_manager = template_manager
        self.history_manager = history_manager
        self.on_save = on_save

        self._setup_window()
        self._setup_ui()
        self._setup_shortcuts()
        self._apply_dark_style()

    def _setup_window(self):
        self.setWindowTitle("ClearNote")
        w = self.config.get("ui", {}).get("window_width", 680)
        h = self.config.get("ui", {}).get("window_height", 460)
        self.resize(w, h)
        self.setWindowFlags(
            Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)
        self._center_on_screen()

        self._drag_pos = None

    def _center_on_screen(self):
        screen = QApplication.primaryScreen()
        if screen:
            geo = screen.availableGeometry()
            self.move(
                geo.center().x() - self.width() // 2,
                geo.center().y() - self.height() // 2,
            )

    def _setup_ui(self):
        font_size = self.config.get("ui", {}).get("font_size", 14)
        main_font = QFont("Segoe UI", font_size)
        small_font = QFont("Segoe UI", 10)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── タイトルバー ──
        title_bar = QFrame()
        title_bar.setObjectName("titleBar")
        title_bar.setFixedHeight(40)
        tb_layout = QHBoxLayout(title_bar)
        tb_layout.setContentsMargins(12, 0, 8, 0)

        lbl = QLabel("✏  ClearNote")
        lbl.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        lbl.setObjectName("titleLabel")
        tb_layout.addWidget(lbl)
        tb_layout.addStretch()

        close_btn = QPushButton("✕")
        close_btn.setObjectName("closeBtn")
        close_btn.setFixedSize(28, 28)
        close_btn.clicked.connect(self.hide_window)
        tb_layout.addWidget(close_btn)

        title_bar.mousePressEvent = self._drag_start
        title_bar.mouseMoveEvent = self._drag_move
        root.addWidget(title_bar)

        # ── オプションバー ──
        opt_bar = QFrame()
        opt_bar.setObjectName("optBar")
        opt_layout = QHBoxLayout(opt_bar)
        opt_layout.setContentsMargins(12, 6, 12, 6)
        opt_layout.setSpacing(8)

        template_lbl = QLabel("テンプレート:")
        template_lbl.setFont(small_font)
        template_lbl.setObjectName("optLabel")
        opt_layout.addWidget(template_lbl)

        self.template_combo = QComboBox()
        self.template_combo.setFont(small_font)
        self.template_combo.setObjectName("templateCombo")
        self.template_combo.setFixedWidth(150)
        self._populate_templates()
        self.template_combo.currentTextChanged.connect(self._on_template_changed)
        opt_layout.addWidget(self.template_combo)

        opt_layout.addSpacing(16)

        tag_lbl = QLabel("タグ:")
        tag_lbl.setFont(small_font)
        tag_lbl.setObjectName("optLabel")
        opt_layout.addWidget(tag_lbl)

        self.tag_input = QLineEdit()
        self.tag_input.setFont(small_font)
        self.tag_input.setPlaceholderText("idea, project, work  (カンマ区切り)")
        self.tag_input.setObjectName("tagInput")
        opt_layout.addWidget(self.tag_input)

        root.addWidget(opt_bar)

        # ── 区切り線 ──
        root.addWidget(self._make_separator())

        # ── テキストエリア ──
        self.text_edit = QTextEdit()
        self.text_edit.setFont(main_font)
        self.text_edit.setPlaceholderText("メモを入力... (Ctrl+S で保存、Esc でキャンセル)")
        self.text_edit.setObjectName("textEdit")
        self.text_edit.setAcceptRichText(False)
        root.addWidget(self.text_edit)

        # ── 区切り線 ──
        root.addWidget(self._make_separator())

        # ── 下部バー ──
        bottom_bar = QFrame()
        bottom_bar.setObjectName("bottomBar")
        bottom_layout = QHBoxLayout(bottom_bar)
        bottom_layout.setContentsMargins(12, 6, 12, 6)
        bottom_layout.setSpacing(8)

        self.history_btn = QToolButton()
        self.history_btn.setText("🕐 履歴")
        self.history_btn.setFont(small_font)
        self.history_btn.setObjectName("historyBtn")
        self.history_btn.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        self.history_btn.setMenu(self._build_history_menu())
        bottom_layout.addWidget(self.history_btn)

        bottom_layout.addStretch()

        self.status_label = QLabel("")
        self.status_label.setFont(small_font)
        self.status_label.setObjectName("statusLabel")
        bottom_layout.addWidget(self.status_label)

        cancel_btn = QPushButton("キャンセル (Esc)")
        cancel_btn.setFont(small_font)
        cancel_btn.setObjectName("cancelBtn")
        cancel_btn.clicked.connect(self.hide_window)
        bottom_layout.addWidget(cancel_btn)

        self.save_btn = QPushButton("保存 (Ctrl+S)")
        self.save_btn.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        self.save_btn.setObjectName("saveBtn")
        self.save_btn.clicked.connect(self._request_save)
        bottom_layout.addWidget(self.save_btn)

        root.addWidget(bottom_bar)

        # リサイズグリップ
        grip = QSizeGrip(self)
        grip.setFixedSize(16, 16)
        bottom_layout.addWidget(grip, 0, Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignRight)

    def _make_separator(self) -> QFrame:
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setObjectName("separator")
        return line

    def _setup_shortcuts(self):
        QShortcut(QKeySequence("Ctrl+S"), self, activated=self._request_save)
        QShortcut(QKeySequence("Escape"), self, activated=self.hide_window)

    def _apply_dark_style(self):
        self.setStyleSheet("""
            QWidget {
                background-color: #1e1e2e;
                color: #cdd6f4;
            }
            #titleBar {
                background-color: #181825;
                border-bottom: 1px solid #313244;
            }
            #titleLabel {
                color: #cba6f7;
            }
            #closeBtn {
                background: transparent;
                color: #6c7086;
                border: none;
                border-radius: 4px;
                font-size: 14px;
            }
            #closeBtn:hover {
                background-color: #f38ba8;
                color: #1e1e2e;
            }
            #optBar, #bottomBar {
                background-color: #181825;
            }
            #optLabel, #statusLabel {
                color: #6c7086;
            }
            #separator {
                color: #313244;
                background-color: #313244;
                max-height: 1px;
            }
            QComboBox, QLineEdit {
                background-color: #313244;
                color: #cdd6f4;
                border: 1px solid #45475a;
                border-radius: 4px;
                padding: 3px 6px;
                selection-background-color: #89b4fa;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox QAbstractItemView {
                background-color: #313244;
                color: #cdd6f4;
                selection-background-color: #45475a;
            }
            #textEdit {
                background-color: #1e1e2e;
                color: #cdd6f4;
                border: none;
                padding: 12px 16px;
                selection-background-color: #89b4fa;
                selection-color: #1e1e2e;
            }
            #saveBtn {
                background-color: #89b4fa;
                color: #1e1e2e;
                border: none;
                border-radius: 5px;
                padding: 5px 16px;
            }
            #saveBtn:hover {
                background-color: #b4d0ff;
            }
            #saveBtn:disabled {
                background-color: #45475a;
                color: #6c7086;
            }
            #cancelBtn {
                background-color: #313244;
                color: #cdd6f4;
                border: none;
                border-radius: 5px;
                padding: 5px 12px;
            }
            #cancelBtn:hover {
                background-color: #45475a;
            }
            #historyBtn {
                background-color: #313244;
                color: #cdd6f4;
                border: none;
                border-radius: 5px;
                padding: 5px 10px;
            }
            #historyBtn:hover {
                background-color: #45475a;
            }
            QMenu {
                background-color: #313244;
                color: #cdd6f4;
                border: 1px solid #45475a;
            }
            QMenu::item:selected {
                background-color: #45475a;
            }
        """)

    # ── テンプレート ──────────────────────────

    def _populate_templates(self):
        self.template_combo.clear()
        for name in self.template_manager.list_templates():
            self.template_combo.addItem(name)
        default = self.config.get("note", {}).get("default_template", "default")
        idx = self.template_combo.findText(default)
        if idx >= 0:
            self.template_combo.setCurrentIndex(idx)

    def _on_template_changed(self, name: str):
        content = self.template_manager.get_body(name)
        if content:
            self.text_edit.setPlainText(content)

    # ── 履歴 ─────────────────────────────────

    def _build_history_menu(self) -> QMenu:
        menu = QMenu(self)
        entries = self.history_manager.get_recent(5)
        if not entries:
            action = menu.addAction("(履歴なし)")
            action.setEnabled(False)
        else:
            for entry in entries:
                title = entry.get("title", "無題")
                action = menu.addAction(title)
                filepath = entry.get("filepath", "")
                action.setData(filepath)
        return menu

    def _refresh_history_menu(self):
        self.history_btn.setMenu(self._build_history_menu())

    # ── ドラッグ移動 ──────────────────────────

    def _drag_start(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()

    def _drag_move(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton and self._drag_pos:
            self.move(event.globalPosition().toPoint() - self._drag_pos)

    # ── 表示・非表示 ──────────────────────────

    def show_window(self):
        self._center_on_screen()
        self._populate_templates()
        self._refresh_history_menu()
        self.show()
        self.raise_()
        self.activateWindow()
        self.text_edit.setFocus()

    def hide_window(self):
        self.hide()
        self.text_edit.clear()
        self.tag_input.clear()
        self.status_label.setText("")

    # ── 保存 ─────────────────────────────────

    def _request_save(self):
        content = self.text_edit.toPlainText().strip()
        if not content:
            self.status_label.setText("テキストを入力してください")
            return

        tags_raw = self.tag_input.text().strip()
        tags = [t.strip() for t in tags_raw.split(",") if t.strip()] if tags_raw else []
        template_name = self.template_combo.currentText()

        self.save_btn.setEnabled(False)
        self.status_label.setText("保存中...")

        thread = threading.Thread(
            target=self._save_in_thread,
            args=(content, tags, template_name),
            daemon=True,
        )
        thread.start()

    def _save_in_thread(self, content: str, tags: list[str], template_name: str):
        self.on_save(content, tags, template_name)

    def on_save_success(self, title: str, filepath: str):
        """メインスレッドから呼ばれる (保存成功時)"""
        self.save_btn.setEnabled(True)
        self._refresh_history_menu()
        self.hide_window()

    def on_save_error(self, message: str):
        """メインスレッドから呼ばれる (保存失敗時)"""
        self.save_btn.setEnabled(True)
        self.status_label.setText(f"エラー: {message}")
