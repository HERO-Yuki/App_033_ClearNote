@echo off
chcp 65001 > nul
cd /d "%~dp0"

if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
) else if exist .venv\Scripts\activate.bat (
    call .venv\Scripts\activate.bat
)

echo.
echo >>> QuickNote を起動します...
echo.
python main.py

if %errorlevel% neq 0 (
    echo.
    echo [エラー] 起動に失敗しました。
    echo Python および必要なライブラリがインストールされているか確認してください。
    echo   pip install -r requirements.txt
    echo.
    pause
)
