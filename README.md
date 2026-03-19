# App_033 ClearNote

ホットキーで呼び出せる Drafts 風デスクトップメモアプリ。  
テキストを入力してすぐに Obsidian Vault (Dropbox 管理) へ Markdown として保存します。

## 機能

- **ホットキー起動** : デフォルト `Ctrl+Shift+Space` でどこからでも呼び出せる
- **システムトレイ常駐** : バックグラウンドで待機、最小リソース消費
- **Gemini AI タイトル生成** : 本文から自動的に最適なタイトルを生成
- **テンプレート** : default / diary / idea / todo の 4 種類（カスタマイズ可能）
- **タグ付け** : カンマ区切りでタグを入力、フロントマターに記録
- **保存先設定** : `config.yaml` で Obsidian Vault パスと保存フォルダを指定
- **履歴** : 直近 20 件のメモをトレイメニューから確認可能

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

### 3. config.yaml の編集

```yaml
obsidian:
  vault_path: "auto"        # Dropboxを自動検出 → Dropbox/アプリ/remotely-save/sin-Vault
                            # 手動指定する場合は絶対パスを記入
  inbox_folder: "000_Inbox" # Vault内の保存先フォルダ

hotkey: "ctrl+shift+space"  # ← 好みのホットキーに変更
```

### 4. 起動

```bash
python main.py
```

## 使い方

1. `python main.py` を実行 → システムトレイにアイコン表示
2. `Ctrl+Shift+Space` を押す → クイックノートウィンドウが開く
3. テンプレート・タグを選択してメモを入力
4. `Ctrl+S` または「保存」ボタン → Gemini がタイトルを生成して Vault に保存
5. `Esc` またはタイトルバーの ✕ で閉じる（保存なし）

## テンプレートのカスタマイズ

`templates/` フォルダに `.md` ファイルを追加するだけで自動認識されます。  
プレースホルダー: `{{date}}`, `{{datetime}}`, `{{year}}`, `{{month}}`, `{{day}}`

## ディレクトリ構成

```
App_033_ClearNote/
├── main.py              # エントリポイント
├── config.yaml          # 設定ファイル
├── .env                 # API キー（git管理外）
├── requirements.txt
├── src/
│   ├── note_window.py   # UIウィンドウ
│   ├── note_saver.py    # Markdown保存
│   ├── ai_service.py    # Gemini タイトル生成
│   ├── template_manager.py
│   ├── history_manager.py
│   └── config_manager.py
├── templates/           # メモテンプレート
└── history.json         # 履歴（自動生成）
```

## 注意事項

- Windows 環境推奨（`keyboard` ライブラリは管理者権限が必要な場合あり）
- ホットキーが効かない場合は管理者権限で実行してください
