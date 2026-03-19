# CONTEXT.md - App_033 ClearNote

## プロジェクト概要

ホットキーで呼び出せる Drafts (iOS) 風のデスクトップクイックメモアプリ。  
Python + PyQt6 で構築し、Dropbox で管理している Obsidian Vault へ Markdown を保存する。

- **GitHub:** https://github.com/HERO-Yuki/App_033_ClearNote
- **起動コマンド:** `python main.py`
- **実際の保存先:** `Dropbox/アプリ/remotely-save/sin-Vault/000_Inbox/`

---

## 主要コンポーネント

| ファイル | 役割 |
|---|---|
| `main.py` | エントリポイント。QApplication / システムトレイ / ホットキー登録 / 保存パイプライン |
| `src/note_window.py` | PyQt6 クイック入力ウィンドウ（フレームレス・最前面・ダークUI） |
| `src/note_saver.py` | Markdown ファイル生成・保存・ファイル名重複回避 |
| `src/ai_service.py` | Gemini 2.5 Flash APIによるタイトル自動生成（失敗時は本文1行目にフォールバック） |
| `src/dropbox_detector.py` | `%APPDATA%\Dropbox\info.json` を読み取りDropboxパスを自動検出 |
| `src/template_manager.py` | `templates/` フォルダのテンプレート管理・プレースホルダー展開 |
| `src/history_manager.py` | 直近メモ履歴の JSON 保持・読み書き |
| `src/config_manager.py` | `config.yaml` の読み込みユーティリティ |

---

## 設定ファイル

- `config.yaml` : vault_path（`"auto"` でDropbox自動検出）/ inbox_folder / hotkey / AI設定 / UI サイズ
- `.env` : `GEMINI_API_KEY`（git 管理外）

### 主要な config.yaml キー

```yaml
hotkey: "ctrl+shift+space"

obsidian:
  vault_path: "auto"        # "auto" → Dropbox/アプリ/remotely-save/sin-Vault
  inbox_folder: "000_Inbox"

note:
  filename_format: "title"  # "title"=AIタイトル or 1行目, "timestamp"=日時
  auto_title_with_ai: true

ai:
  model: "gemini-2.5-flash" # 2026年3月時点の安定版推奨モデル
```

---

## データフロー

```
ホットキー押下
  → keyboard コールバック (別スレッド)
  → AppSignals.show_window.emit()          ← スレッド境界をシグナルで越える
  → NoteWindow.show_window() (GUIスレッド)
  → ユーザーが入力・保存 (Ctrl+S)
  → NoteWindow._request_save()
  → threading.Thread: ClearNoteApp._do_save()
      → resolve_vault_path()               ← "auto" → 実パスに解決
      → generate_title() [Gemini 2.5 Flash API]
      → save_note()      [Vault へ .md 書き込み]
      → HistoryManager.add()
      → AppSignals.save_success.emit()
  → NoteWindow.on_save_success() → ウィンドウを閉じる
  → QSystemTrayIcon.showMessage() で保存完了通知
```

---

## 保存される Markdown 形式

```markdown
---
created: 2026-03-19T14:30:22
tags: [idea, project]
template: idea
---

# Gemini が生成したタイトル

本文テキスト...
```

---

## テンプレート

`templates/` フォルダに `.md` ファイルを追加すると自動認識される（再起動不要）。

利用可能なプレースホルダー: `{{date}}`, `{{datetime}}`, `{{year}}`, `{{month}}`, `{{day}}`

同梱テンプレート: `default` / `diary` / `idea` / `todo`

---

## 依存技術

| ライブラリ | 用途 |
|---|---|
| `PyQt6` | GUI・システムトレイ・シグナル |
| `keyboard` | グローバルホットキー（Windows では管理者権限が必要な場合あり） |
| `google-generativeai` | Gemini 2.5 Flash タイトル生成 |
| `pyyaml` | config.yaml 読み込み |
| `python-dotenv` | .env 読み込み |

---

## 開発メモ・設計上の注意点

- `keyboard` ライブラリのコールバックは非GUIスレッドで実行されるため、`AppSignals`（`QObject` 派生）の `pyqtSignal` を経由してGUIスレッドに転送している
- `NoteWindow` はフレームレスウィンドウのため、タイトルバー部分に `mousePressEvent` / `mouseMoveEvent` を設定して独自ドラッグ移動を実装
- 保存処理（Gemini API呼び出し含む）は `threading.Thread` で非同期実行し、API レイテンシ中も UI をブロックしない
- エラーハンドリングは `ClearNoteApp._do_save()` 内で一元管理し、`AppSignals.save_error` 経由で UI に通知
- `history.json` は `.gitignore` で管理対象外

---

## コードレビュー履歴（2026-03-19）

| 種別 | ファイル | 内容 |
|---|---|---|
| バグ修正 | `note_window.py` | `_save_in_thread` が存在しない `_on_save_done()` を呼んでいた → 削除 |
| デッドコード削除 | `note_window.py` | 未使用の `NoteSignals` クラス・`saved` シグナル・`QSize`/`QColor`/`QPalette`/`QIcon` を削除 |
| 型ヒント修正 | `note_window.py` | `on_save` の型ヒントを正しい3引数シグネチャに修正 |
| 未使用インポート削除 | `main.py` | `os`・`Qt`・`SRC_DIR` を削除 |
| インポート整理 | `template_manager.py` | `datetime` インポートをメソッド内から先頭に移動 |
| 冗長コード修正 | `ai_service.py` | `config.get("ai", {})` の重複呼び出しを `ai_cfg` で統一 |
| モデル更新 | `ai_service.py`, `config.yaml` | `gemini-2.0-flash`（Deprecated）→ `gemini-2.5-flash`（安定版）に変更 |
