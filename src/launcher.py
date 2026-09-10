# -*- coding: utf-8 -*-
"""
MapleStory Idle - Save Reset Utility

遊戲本體與技能沙盒改由根目錄的 .bat 直接呼叫 runtime\\python\\python.exe
啟動（見 啟動遊戲.bat / 技能特效沙盒.bat），此檔案現在只保留存檔重置工具，
供 重置為全新存檔.bat 呼叫。
"""

import sys
import os
import shutil
from datetime import datetime

if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass
if hasattr(sys.stderr, 'reconfigure'):
    try:
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

SRC_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(SRC_DIR)


def safe_input(prompt: str = "") -> str:
    try:
        return input(prompt)
    except (EOFError, KeyboardInterrupt):
        return ""


def print_banner(title: str):
    print("=" * 68)
    print("       【新楓之谷：放置遠征隊 - MapleStory Idle】")
    print(f"                 {title}")
    print("=" * 68)
    print()


def reset_save():
    print_banner("全新開局 / 存檔重置與備份工具")
    print("此工具將為您重置遊戲進度，以全新 Lv.1 冒險隊伍開局！")
    print("(原有存檔將由系統自動建立時間戳記備份，安全無虞)")
    print()

    try:
        choice = safe_input("確定要重置為全新存檔嗎？(輸入 Y 確認，其他任意鍵取消): ").strip().upper()
    except Exception:
        choice = ""

    if choice != "Y":
        print("\n已取消操作，現有存檔未作任何變動。")
        safe_input("\n請按 Enter 鍵退出...")
        return

    saves_dir = os.path.join(SRC_DIR, "saves")
    backups_dir = os.path.join(saves_dir, "backups")
    os.makedirs(backups_dir, exist_ok=True)

    save_file = os.path.join(saves_dir, "savegame.json")
    root_save = os.path.join(ROOT_DIR, "savegame.json")

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    backed_up = False

    if os.path.exists(save_file):
        bk_path = os.path.join(backups_dir, f"savegame_{ts}.json")
        shutil.copy2(save_file, bk_path)
        os.remove(save_file)
        backed_up = True

    if os.path.exists(root_save):
        bk_path = os.path.join(backups_dir, f"savegame_root_{ts}.json")
        shutil.copy2(root_save, bk_path)
        os.remove(root_save)
        backed_up = True

    print()
    print("=" * 68)
    if backed_up:
        print(f"[成功] 原有存檔已成功備份至: src/saves/backups/savegame_{ts}.json")
    else:
        print("[提示] 原先未偵測到存檔。")
    print("[成功] 存檔已重置完畢！")
    print("下次點擊【啟動遊戲.bat】時，將自動建立全新的 Lv.1 冒險隊伍開局！")
    print("=" * 68)
    print()
    safe_input("請按 Enter 鍵完成...")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1].lower() in ("--reset", "--reset-save", "-r"):
        reset_save()
    else:
        reset_save()
