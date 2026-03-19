# App_033 ClearNote

ホットキーで呼び出せる Drafts (iOS) 風デスクトップメモアプリ。  
テキストを入力してすぐに Obsidian Vault (Dropbox 管理) へ Markdown として保存します。

**GitHub:** https://github.com/HERO-Yuki/App_033_ClearNote

---

## 機能

- **ホットキー起動** : デフォルト `Ctrl+Shift+Space` でどこからでも呼び出せる
- **システムトレイ常駐** : バックグラウンドで待機、最小リソース消費
- **Markdown ハイライト** : 見出し・太字・コードなどをリアルタイムでカラー表示
- **Gemini AI タイトル生成** : `gemini-2.5-flash` で本文から最適なタイトルを自動生成
- **Dropbox 自動検出** : `%APPDATA%\Dropbox\info.json` を読み取りVaultパスを自動解決
- **テンプレート** : default / diary / idea / todo の 4 種類（カスタマイズ可能）
- **タグ付け** : カンマ区切りで入力、Obsidianフロントマターに記録
- **履歴** : 直近メモをトレイメニューから確認可能
- **フォント設定** : `config.yaml` でフォントファミリー・サイズを変更可能

---

## セットアップ

### 1. 依存ライブラリのインストール

```bash
pip install -r requirements.txt
```

#### Windows で DLL ブロックエラーが出る場合

```powershell
Get-ChildItem -Path "$env:LOCALAPPDATA\Programs\Python\Python314\Lib\site-packages\PyQt6" -Recurse -Include "*.dll","*.pyd" | Unblock-File
```

### 2. 環境変数の設定

`.env` ファイルに Gemini API キーを記入：

```
GEMINI_API_KEY=your_api_key_here
```

> API キーなしでも動作します（タイトルは本文1行目を使用）

### 3. config.yaml の確認

デフォルト設定でそのまま動作します。必要に応じて変更してください。

```yaml
obsidian:
  vault_path: "auto"          # Dropboxを自動検出
                              # → Dropbox/アプリ/remotely-save/sin-Vault
                              # 手動指定する場合は絶対パスを記入
  inbox_folder: "000_Inbox"   # Vault内の保存先フォルダ

hotkey: "ctrl+shift+space"    # 好みのホットキーに変更可能

ai:
  model: "gemini-2.5-flash"   # 2026年3月現在の推奨安定版

ui:
  font_family: "Zen Kaku Gothic New"  # フォント (未インストール時は自動フォールバック)
  font_size: 12
```

### 4. 起動

```bash
python main.py
```

---

## 使い方

| 操作 | 動作 |
|---|---|
| `Ctrl+Shift+Space` | クイックノートウィンドウを開く |
| `Ctrl+S` / 保存ボタン | Gemini でタイトル生成 → Vault に保存 |
| `Esc` / ✕ボタン | ウィンドウを閉じる（保存しない） |
| トレイアイコン右クリック → 終了 | **アプリを完全に終了する** |
| トレイアイコンダブルクリック | ウィンドウを開く |

> **ウィンドウの ✕ はアプリを終了しません。** 常駐を終了するにはトレイアイコンから「✕ 終了 (アプリを完全に閉じる)」を選んでください。

保存先: `Dropbox/アプリ/remotely-save/sin-Vault/000_Inbox/<タイトル>.md`

---

## Markdown ハイライト

入力中にリアルタイムで色がつきます（フォントサイズは変わりません）。

| 記法 | 色 |
|---|---|
| `# 見出し1` | 紫 |
| `## 見出し2` | 青 |
| `### 見出し3+` | ティール |
| `**太字**` | 黄 |
| `` `コード` `` | 赤 |
| `> 引用` | グレー |
| `- リスト` | ピーチ |

---

## テンプレートのカスタマイズ

`templates/` フォルダに `.md` ファイルを追加するだけで自動認識されます。

利用可能なプレースホルダー:

| プレースホルダー | 展開例 |
|---|---|
| `{{date}}` | `2026-03-19` |
| `{{datetime}}` | `2026-03-19T14:30:22` |
| `{{year}}` / `{{month}}` / `{{day}}` | `2026` / `03` / `19` |

---

## ディレクトリ構成

```
App_033_QuickNote/
├── main.py                      # エントリポイント・トレイ・ホットキー・保存パイプライン
├── config.yaml                  # 全設定（vault_path / hotkey / AI / UI / font）
├── .env                         # GEMINI_API_KEY（git管理外）
├── requirements.txt
├── src/
│   ├── note_window.py           # PyQt6 フレームレス入力ウィンドウ（ダークUI）
│   ├── markdown_highlighter.py  # Markdown シンタックスハイライター
│   ├── note_saver.py            # Markdown生成・ファイル保存・重複回避
│   ├── ai_service.py            # Gemini APIタイトル生成（キャッシュ・warmup付き）
│   ├── dropbox_detector.py      # Dropboxパス自動検出
│   ├── template_manager.py      # templates/ 管理・プレースホルダー展開
│   ├── history_manager.py       # history.json への履歴保持
│   └── config_manager.py        # config.yaml 読み込みユーティリティ
├── templates/
│   ├── default.md
│   ├── diary.md
│   ├── idea.md
│   └── todo.md
├── docs/                        # icon.png を置くとトレイアイコンに使用される
├── tests/
└── history.json                 # 履歴（自動生成・git管理外）
```

---

## 注意事項

- Windows 環境推奨（`keyboard` ライブラリは管理者権限が必要な場合あり）
- ホットキーが効かない場合は管理者権限で起動してください
- `gemini-2.0-flash` は 2026年時点で Deprecated のため `gemini-2.5-flash` を使用
- 「Zen Kaku Gothic New」を使う場合は [Google Fonts](https://fonts.google.com/specimen/Zen+Kaku+Gothic+New) からインストールしてください
