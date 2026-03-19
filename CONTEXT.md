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
| `src/markdown_highlighter.py` | QSyntaxHighlighter による Markdown 見出し・インライン要素のカラー表示 |
| `src/note_saver.py` | Markdown ファイル生成・保存・ファイル名重複回避 |
| `src/ai_service.py` | Gemini 2.5 Flash APIによるタイトル自動生成・クライアントキャッシュ・warmup |
| `src/dropbox_detector.py` | `%APPDATA%\Dropbox\info.json` を読み取りDropboxパスを自動検出 |
| `src/template_manager.py` | `templates/` フォルダのテンプレート管理・プレースホルダー展開 |
| `src/history_manager.py` | 直近メモ履歴の JSON 保持・読み書き |
| `src/config_manager.py` | `config.yaml` の読み込みユーティリティ |

---

## 設定ファイル

- `config.yaml` : vault_path（`"auto"` でDropbox自動検出）/ inbox_folder / hotkey / AI設定 / UI設定
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

ui:
  font_family: "Zen Kaku Gothic New"  # 未インストール時は Yu Gothic → Meiryo → Segoe UI へフォールバック
  font_size: 12
  window_width: 680
  window_height: 460
  history_max: 10
```

---

## データフロー

```
起動時 (main.py)
  → resolve_vault_path() でVaultパスを事前解決・キャッシュ
  → ai_warmup() バックグラウンドでGeminiクライアントを事前初期化
  → ホットキー登録スレッド起動
  → システムトレイ表示

ホットキー押下
  → keyboard コールバック (別スレッド)
  → AppSignals.show_window.emit()          ← スレッド境界をシグナルで越える
  → NoteWindow.show_window() (GUIスレッド)
  → ユーザーが入力・保存 (Ctrl+S)
  → NoteWindow._request_save()
  → threading.Thread: ClearNoteApp._do_save()
      → self._vault_path  (キャッシュ済みパスを使用)
      → generate_title()  [Gemini 2.5 Flash / キャッシュ済みクライアント]
      → save_note()       [Vault へ .md 書き込み]
      → HistoryManager.add()
      → AppSignals.save_success.emit()
  → NoteWindow.on_save_success() → ウィンドウを閉じる
  → QSystemTrayIcon.showMessage() で保存完了通知

終了
  → トレイアイコン右クリック → "✕ 終了 (アプリを完全に閉じる)"
```

---

## Markdown ハイライト仕様

`MarkdownHighlighter` (Catppuccin Mocha パレット) がリアルタイムで着色する。フォントサイズは変更しない。

| 要素 | 色 | コード |
|---|---|---|
| `# 見出し1` | Mauve | `#cba6f7` |
| `## 見出し2` | Blue | `#89b4fa` |
| `### 見出し3+` | Teal | `#94e2d5` |
| `**太字**` | Yellow | `#f9e2af` |
| `*斜体*` | Green | `#a6e3a1` |
| `` `コード` `` | Red | `#f38ba8` |
| `> 引用` | Overlay0 | `#6c7086` |
| `- リスト` | Peach | `#fab387` |

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
| `PyQt6` | GUI・システムトレイ・シグナル・SyntaxHighlighter |
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
- Gemini クライアントは `(api_key, model_name)` をキーに `_model_cache` でキャッシュ。初回保存後は毎回の初期化コストがなくなる
- Vault パスは `ClearNoteApp.__init__` で一度だけ解決してインスタンス変数 `_vault_path` に保存
- `history.json` は `.gitignore` で管理対象外
- PyQt6 DLL が Windows のアプリケーション制御ポリシーでブロックされる場合は以下で解除：
  ```powershell
  Get-ChildItem -Path "<site-packages>\PyQt6" -Recurse -Include "*.dll","*.pyd" | Unblock-File
  ```
- `echo >` で作成した `__init__.py` は UTF-16 になるため `SyntaxError: null bytes`。`[System.IO.File]::WriteAllText(..., [Encoding]::UTF8)` で修正する

---

## 変更履歴

### 2026-03-19 初期実装 + コードレビュー

| 種別 | ファイル | 内容 |
|---|---|---|
| バグ修正 | `note_window.py` | `_save_in_thread` が存在しない `_on_save_done()` を呼んでいた → 削除 |
| デッドコード削除 | `note_window.py` | 未使用の `NoteSignals` クラス・`saved` シグナル・`QSize`/`QColor`/`QPalette`/`QIcon` を削除 |
| 型ヒント修正 | `note_window.py` | `on_save` の型ヒントを正しい3引数シグネチャに修正 |
| 未使用インポート削除 | `main.py` | `os`・`Qt`・`SRC_DIR` を削除 |
| インポート整理 | `template_manager.py` | `datetime` インポートをメソッド内から先頭に移動 |
| 冗長コード修正 | `ai_service.py` | `config.get("ai", {})` の重複呼び出しを `ai_cfg` で統一 |
| モデル更新 | `ai_service.py`, `config.yaml` | `gemini-2.0-flash`（Deprecated）→ `gemini-2.5-flash`（安定版）に変更 |
| エンコーディング修正 | `src/__init__.py`, `tests/__init__.py` | PowerShell `echo >` による UTF-16 → UTF-8 に修正 |

### 2026-03-19 機能追加・改善

| 種別 | ファイル | 内容 |
|---|---|---|
| 新規 | `src/markdown_highlighter.py` | Markdown 見出し・インライン要素のカラーハイライト |
| 機能追加 | `config.yaml`, `note_window.py` | `ui.font_family` / `ui.font_size: 12` を設定可能に |
| 高速化 | `src/ai_service.py` | Gemini クライアントをキャッシュ・`warmup()` で事前初期化 |
| 高速化 | `main.py` | Vault パスを起動時に解決してキャッシュ |
| UX改善 | `main.py` | トレイ終了メニューに「アプリを完全に閉じる」を明記 |

### 2026-03-19 UI/UX改良（桜井政博氏の視点導入）

| 種別 | ファイル | 内容 |
|---|---|---|
| UX改善 | `note_window.py` | QTimer.singleShot(0)で確実なフォーカス設定（遅さは罪） |
| UI強調 | `note_window.py` | 保存ボタンを12pt太字・高さ38pxに拡大（大事なものをより大きく） |
| 配色改善 | `note_window.py` | タイトルバーを#11111bに暗色化、bottomBarに境界線追加（色による区分） |
| 配色改善 | `note_window.py` | テキストエリアのpadding拡大（20px 24px）で入力の心地よさ向上 |
| 絵文字追加 | `note_window.py` | ボタンに絵文字追加：💾保存、✕キャンセル、⏳処理中など（言語がなくてもわかるように） |
| フィードバック強化 | `note_window.py` | 保存中にボタンテキストを「⏳ 処理中...」に変更（やり過ぎてちょうどよい） |
| フィードバック強化 | `note_window.py` | 保存完了時に「✅ 保存完了！」表示+150msディレイで達成感演出 |
| エラー表示改善 | `note_window.py` | エラー表示に❌絵文字追加、警告に⚠絵文字追加 |

### 2026-03-19 入力体験の改善

| 種別 | ファイル | 内容 |
|---|---|---|
| UX改善 | `note_window.py` | QTextEditのプレースホルダー削除で入力時の被り問題を解消 |
| UX改善 | `note_window.py` | タグ入力欄のオートコンプリート無効化 |
| UX改善 | `note_window.py` | テンプレートコンボボックスのNoInsertポリシー設定 |

### 2026-03-19 コード品質改善

| 種別 | ファイル | 内容 |
|---|---|---|
| リファクタ | `ai_service.py` | 型ヒントの改善（Any型を明示的に使用） |
