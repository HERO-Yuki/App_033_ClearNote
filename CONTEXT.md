# CONTEXT.md - App_033 ClearNote

## プロジェクト概要

ホットキーで呼び出せる Drafts (iOS) 風のデスクトップクイックメモアプリ。  
Python + PyQt6 で構築し、Dropbox で管理している Obsidian Vault へ Markdown を保存する。

## 主要コンポーネント

| ファイル | 役割 |
|---|---|
| `main.py` | エントリポイント。QApplication / システムトレイ / ホットキー登録 / 保存パイプライン |
| `src/note_window.py` | PyQt6 クイック入力ウィンドウ（フレームレス、最前面、ダークUI） |
| `src/note_saver.py` | Markdown ファイル生成・保存・ファイル名重複回避 |
| `src/ai_service.py` | Gemini API によるタイトル自動生成（失敗時は本文1行目にフォールバック） |
| `src/template_manager.py` | `templates/` フォルダのテンプレート管理・プレースホルダー展開 |
| `src/history_manager.py` | 直近メモ履歴の JSON 保持・読み書き |
| `src/config_manager.py` | `config.yaml` の読み込みユーティリティ |
| `src/dropbox_detector.py` | Dropboxインストールパス自動検出 (`%APPDATA%\Dropbox\info.json` を参照) |

## 設定ファイル

- `config.yaml` : vault_path (`"auto"` でDropbox自動検出) / inbox_folder / hotkey / テンプレート設定 / UI サイズ
- `.env` : `GEMINI_API_KEY`（git 管理外）

## データフロー

```
ホットキー押下
  → keyboard コールバック (別スレッド)
  → AppSignals.show_window.emit()
  → NoteWindow.show_window() (GUIスレッド)
  → ユーザーが入力・保存
  → NoteWindow._request_save()
  → threading.Thread: ClearNoteApp._do_save()
    → generate_title() [Gemini API]
    → save_note() [Vault へファイル書き込み]
    → HistoryManager.add()
    → AppSignals.save_success.emit()
  → NoteWindow.on_save_success() → ウィンドウを閉じる
  → QSystemTrayIcon.showMessage() で通知
```

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

## テンプレート

`templates/` フォルダに `.md` ファイルを追加すると自動認識される。  
利用可能なプレースホルダー: `{{date}}`, `{{datetime}}`, `{{year}}`, `{{month}}`, `{{day}}`

## 依存技術

- `PyQt6` : GUI・システムトレイ
- `keyboard` : グローバルホットキー（Windows では管理者権限が必要な場合あり）
- `google-generativeai` : Gemini タイトル生成
- `pyyaml`, `python-dotenv`

## 開発メモ

- `keyboard` ライブラリのコールバックは非GUIスレッドで実行されるため、
  `QObject.pyqtSignal` + `AppSignals` を経由して GUIスレッドに転送している
- `NoteWindow` はフレームレスウィンドウのため独自ドラッグ移動を実装
- 保存処理は別スレッドで実行し、Gemini API のレイテンシ中も UI をブロックしない
- history.json は `.gitignore` で管理対象外
