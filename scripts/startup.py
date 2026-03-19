"""
Windows スタートアップ登録・解除スクリプト

使い方:
    python scripts/startup.py           # 登録
    python scripts/startup.py --remove  # 解除
    python scripts/startup.py --status  # 現在の状態確認
"""
from __future__ import annotations

import sys
import winreg
from pathlib import Path

APP_NAME = "ClearNote"
REG_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"

BASE_DIR = Path(__file__).parent.parent
MAIN_PY = BASE_DIR / "main.py"
PYTHONW = Path(sys.executable).parent / "pythonw.exe"


def _startup_value() -> str:
    return f'"{PYTHONW}" "{MAIN_PY}"'


def register():
    value = _startup_value()
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, REG_KEY, access=winreg.KEY_SET_VALUE) as key:
        winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, value)
    print(f"[OK] スタートアップに登録しました")
    print(f"     {value}")


def remove():
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, REG_KEY, access=winreg.KEY_SET_VALUE) as key:
            winreg.DeleteValue(key, APP_NAME)
        print(f"[OK] スタートアップから解除しました")
    except FileNotFoundError:
        print(f"[INFO] 登録されていませんでした")


def status():
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, REG_KEY) as key:
            value, _ = winreg.QueryValueEx(key, APP_NAME)
        print(f"[登録済み] {value}")
    except FileNotFoundError:
        print(f"[未登録]")


if __name__ == "__main__":
    if "--remove" in sys.argv:
        remove()
    elif "--status" in sys.argv:
        status()
    else:
        register()
