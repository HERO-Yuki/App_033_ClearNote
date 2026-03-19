"""
App_033 ClearNote
ホットキーで呼び出せるObsidian向けDrafts風クイックメモアプリ

起動方法:
    python main.py
"""
from __future__ import annotations

import sys
import threading
from pathlib import Path

from dotenv import load_dotenv
from PyQt6.QtCore import QTimer, pyqtSignal, QObject
from PyQt6.QtGui import QIcon, QAction
from PyQt6.QtWidgets import QApplication, QSystemTrayIcon, QMenu, QMessageBox

BASE_DIR = Path(__file__).parent
sys.path.insert(0, str(BASE_DIR))

from src.config_manager import load_config, get
from src.template_manager import TemplateManager
from src.history_manager import HistoryManager
from src.note_window import NoteWindow
from src.ai_service import generate_title
from src.note_saver import save_note
from src.dropbox_detector import resolve_vault_path


# ── シグナルブリッジ (別スレッド→GUIスレッド) ──────────────────────────────
class AppSignals(QObject):
    show_window = pyqtSignal()
    save_success = pyqtSignal(str, str)   # (title, filepath)
    save_error = pyqtSignal(str)          # message


# ── メインアプリ ────────────────────────────────────────────────────────────
class ClearNoteApp:
    def __init__(self, config: dict):
        self.config = config
        self.signals = AppSignals()

        self.template_manager = TemplateManager(BASE_DIR / "templates")
        history_max = get(config, "ui", "history_max", default=20)
        self.history_manager = HistoryManager(
            BASE_DIR / "history.json", max_entries=history_max
        )

        self.window = NoteWindow(
            config=config,
            template_manager=self.template_manager,
            history_manager=self.history_manager,
            on_save=self._do_save,
        )

        self.tray = self._create_tray()

        # シグナル接続
        self.signals.show_window.connect(self.window.show_window)
        self.signals.save_success.connect(self._on_save_success)
        self.signals.save_error.connect(self.window.on_save_error)

    # ── システムトレイ ────────────────────────────────────────────────────

    def _create_tray(self) -> QSystemTrayIcon:
        icon_path = BASE_DIR / "docs" / "icon.png"
        if icon_path.exists():
            icon = QIcon(str(icon_path))
        else:
            icon = QApplication.style().standardIcon(
                QApplication.style().StandardPixmap.SP_FileIcon  # type: ignore
            )

        tray = QSystemTrayIcon(icon)
        tray.setToolTip("ClearNote - ホットキーでメモを起動")

        menu = QMenu()

        open_action = QAction("✏  ClearNote を開く", menu)
        open_action.triggered.connect(self.window.show_window)
        menu.addAction(open_action)

        menu.addSeparator()

        about_action = QAction("ℹ  バージョン情報", menu)
        about_action.triggered.connect(self._show_about)
        menu.addAction(about_action)

        menu.addSeparator()

        quit_action = QAction("✕  終了", menu)
        quit_action.triggered.connect(QApplication.quit)
        menu.addAction(quit_action)

        tray.setContextMenu(menu)
        tray.activated.connect(self._on_tray_activated)
        tray.show()
        return tray

    def _on_tray_activated(self, reason: QSystemTrayIcon.ActivationReason):
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.window.show_window()

    def _show_about(self):
        version = get(self.config, "app", "version", default="0.1.0")
        hotkey = self.config.get("hotkey", "ctrl+shift+space")
        QMessageBox.about(
            None,  # type: ignore
            "ClearNote",
            f"<b>App_033 ClearNote</b> v{version}<br><br>"
            f"ホットキー: <code>{hotkey}</code><br>"
            "Obsidian Vault へ Markdown メモを素早く保存するアプリです。",
        )

    # ── ホットキー登録 ────────────────────────────────────────────────────

    def register_hotkey(self):
        hotkey = self.config.get("hotkey", "ctrl+shift+space")
        try:
            import keyboard  # type: ignore

            keyboard.add_hotkey(hotkey, self._hotkey_triggered, suppress=False)
            print(f"[ClearNote] ホットキー登録完了: {hotkey}")
        except Exception as e:
            print(f"[ClearNote] ホットキー登録失敗: {e}")
            self.tray.showMessage(
                "ClearNote",
                f"ホットキー登録に失敗しました: {e}\nトレイアイコンからメモを開いてください。",
                QSystemTrayIcon.MessageIcon.Warning,
                3000,
            )

    def _hotkey_triggered(self):
        """keyboard ライブラリのコールバック (非GUIスレッド)"""
        self.signals.show_window.emit()

    # ── 保存パイプライン ──────────────────────────────────────────────────

    def _do_save(self, content: str, tags: list[str], template_name: str):
        """
        別スレッドで実行される保存処理:
        1. Gemini でタイトル生成 (auto_title_with_ai=true の場合)
        2. Markdown ファイルを Vault に書き込む
        3. 履歴に追加
        4. 完了/エラーシグナルを emit
        """
        try:
            auto_title = get(self.config, "note", "auto_title_with_ai", default=True)
            if auto_title:
                title = generate_title(content, self.config)
            else:
                from src.ai_service import _fallback_title
                title = _fallback_title(content)

            vault_path_raw = get(self.config, "obsidian", "vault_path", default="auto")
            vault_path = resolve_vault_path(vault_path_raw)
            inbox_folder = get(self.config, "obsidian", "inbox_folder", default="000_Inbox")
            filename_format = get(self.config, "note", "filename_format", default="title")

            filepath = save_note(
                title=title,
                body=content,
                tags=tags,
                template_name=template_name,
                vault_path=vault_path,
                inbox_folder=inbox_folder,
                filename_format=filename_format,
            )

            self.history_manager.add(title, str(filepath), tags)
            self.signals.save_success.emit(title, str(filepath))

        except Exception as e:
            self.signals.save_error.emit(str(e))

    def _on_save_success(self, title: str, filepath: str):
        self.window.on_save_success(title, filepath)
        self.tray.showMessage(
            "ClearNote - 保存完了",
            f"「{title}」を保存しました",
            QSystemTrayIcon.MessageIcon.Information,
            2500,
        )


# ── エントリポイント ────────────────────────────────────────────────────────

def main():
    load_dotenv(BASE_DIR / ".env")

    config = load_config(BASE_DIR / "config.yaml")
    app_name = get(config, "app", "name", default="ClearNote")
    print(f"[{app_name}] 起動中...")

    # PyQt6 アプリ
    qt_app = QApplication.instance() or QApplication(sys.argv)
    qt_app.setQuitOnLastWindowClosed(False)
    qt_app.setApplicationName(app_name)

    quick_note = ClearNoteApp(config)

    # ホットキーを別スレッドで登録 (keyboard は blocking loop を持つため)
    hotkey_thread = threading.Thread(
        target=quick_note.register_hotkey, daemon=True
    )
    hotkey_thread.start()

    # 起動通知
    QTimer.singleShot(
        800,
        lambda: quick_note.tray.showMessage(
            app_name,
            f"起動しました。ホットキー: {config.get('hotkey', 'ctrl+shift+space')}",
            QSystemTrayIcon.MessageIcon.Information,
            2000,
        ),
    )

    sys.exit(qt_app.exec())


if __name__ == "__main__":
    main()
