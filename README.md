# App_033 ClearNote

ホットキーで呼び出せる Drafts (iOS) 風デスクトップメモアプリ。  
テキストを入力してすぐに Obsidian Vault (Dropbox 管理) へ Markdown として保存します。

**GitHub:** https://github.com/HERO-Yuki/App_033_ClearNote

---

## 機能

- **ホットキー起動** : デフォルト `Ctrl+Shift+Space` でどこからでも呼び出せる
- **システムトレイ常駐** : バックグラウンドで待機、最小リソース消費
- **Gemini AI タイトル生成** : `gemini-2.5-flash` で本文から最適なタイトルを自動生成
- **Dropbox 自動検出** : `%APPDATA%\Dropbox\info.json` を読み取りVaultパスを自動解決
- **テンプレート** : default / diary / idea / todo の 4 種類（カスタマイズ可能）
- **タグ付け** : カンマ区切りで入力、Obsidianフロントマターに記録
- **履歴** : 直近 20 件のメモをトレイメニューから確認可能

---

## セットアップ

### 1. 依存ライブラリのインストール

```bash
pip install -r requirements.txt
```

### 2. 環境変数の設定

`.env` ファイルに Gemini API キーを記入：

```
GEMINI_API_KEY=your_api_key_here
```

> API キーなしでも動作します（タイトルは本文1行目を使用）

### 3. config.yaml の確認

デフォルト設定でそのまま動作します。保存先は自動検出されます。

```yaml
obsidian:
  vault_path: "auto"        # Dropboxを自動検出
                            # → Dropbox/アプリ/remotely-save/sin-Vault
                            # 手動指定する場合は絶対パスを記入
  inbox_folder: "000_Inbox" # Vault内の保存先フォルダ

hotkey: "ctrl+shift+space"  # 好みのホットキーに変更可能

ai:
  model: "gemini-2.5-flash" # 2026年3月現在の推奨安定版
```

### 4. 起動

```bash
python main.py
```

---

## 使い方

1. `python main.py` を実行 → システムトレイにアイコン表示
2. `Ctrl+Shift+Space` → クイックノートウィンドウが画面中央に表示
3. テンプレート・タグを選択してメモを入力
4. `Ctrl+S` または「保存」ボタン → Gemini がタイトルを生成して Vault に保存
5. `Esc` またはタイトルバーの ✕ で閉じる（保存なし）

保存先: `Dropbox/アプリ/remotely-save/sin-Vault/000_Inbox/<タイトル>.md`

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
├── main.py                  # エントリポイント・トレイ・ホットキー・保存パイプライン
├── config.yaml              # 全設定（vault_path / hotkey / AI / UI）
├── .env                     # GEMINI_API_KEY（git管理外）
├── requirements.txt
├── src/
│   ├── note_window.py       # PyQt6 フレームレス入力ウィンドウ（ダークUI）
│   ├── note_saver.py        # Markdown生成・ファイル保存・重複回避
│   ├── ai_service.py        # Gemini APIタイトル生成（失敗時フォールバック付き）
│   ├── dropbox_detector.py  # Dropboxパス自動検出
│   ├── template_manager.py  # templates/ 管理・プレースホルダー展開
│   ├── history_manager.py   # history.json への履歴保持
│   └── config_manager.py    # config.yaml 読み込みユーティリティ
├── templates/
│   ├── default.md
│   ├── diary.md
│   ├── idea.md
│   └── todo.md
├── docs/                    # icon.png を置くとトレイアイコンに使用される
├── tests/
└── history.json             # 履歴（自動生成・git管理外）
```

---

## 注意事項

- Windows 環境推奨（`keyboard` ライブラリは管理者権限が必要な場合あり）
- ホットキーが効かない場合は管理者権限で起動してください
- `gemini-2.0-flash` は 2026年時点で Deprecated のため `gemini-2.5-flash` を使用
