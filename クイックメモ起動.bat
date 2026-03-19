@echo off
chcp 65001 > nul
cd /d "%~dp0"

:: ── 管理者権限チェック & UAC昇格 ──────────────────────────────────────────
:: keyboard ライブラリのグローバルホットキー登録に管理者権限が必要
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo 管理者権限で再起動します...
    powershell -Command "Start-Process -FilePath '%~f0' -Verb RunAs"
    exit /b
)

:: ── venv 有効化 ────────────────────────────────────────────────────────────
if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
) else if exist .venv\Scripts\activate.bat (
    call .venv\Scripts\activate.bat
)

:: ── 起動 ──────────────────────────────────────────────────────────────────
echo.
echo ============================================================
echo   ClearNote を起動します
echo ============================================================
echo.
echo   このアプリはシステムトレイに常駐します。
echo   ウィンドウは表示されません。
echo.
echo   【操作方法】
echo     Ctrl+Shift+Space  メモウィンドウを開く
echo     トレイアイコン右クリック  メニュー表示
echo     トレイアイコン ダブルクリック  メモウィンドウを開く
echo.
echo   タスクバー右下のシステムトレイを確認してください。
echo ============================================================
echo.

start "" pythonw main.py

echo 起動しました。このウィンドウは閉じても構いません。
timeout /t 5 > nul
