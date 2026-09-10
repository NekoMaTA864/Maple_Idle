"""
《新楓之谷：放置遠征隊 (MapleStory Idle)》- PySide6 現代桌面版入口程式 (pyside_main.py)
特色：
- 現代深色科技主題 (Qt6 QSS)
- 高解析度自適應視窗 (1180 x 760)
- 支援 24 職業、120 招技能、5 選 3 自由配置
- QPainter 硬體抗鋸齒戰鬥畫布
- 關閉視窗時自動存檔
"""

import os
import sys
import time

# 自動將 src/ 目錄注入 sys.path，確保所有內部模組引用無縫銜接
SRC_DIR = os.path.dirname(os.path.abspath(__file__))
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)
ROOT_DIR = os.path.dirname(SRC_DIR)
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

# 初始化 PySide6
from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from player_data import Player, get_default_save_path
from combat_system import CombatManager
from sound import sound_mgr
from pyside_ui import MainWindow, QSS_DARK_THEME


def main():
    # 高 DPI 螢幕適配
    QApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    app = QApplication(sys.argv)
    app.setFont(QFont("Microsoft YaHei UI", 9))
    app.setStyleSheet(QSS_DARK_THEME)

    player = Player()
    combat_mgr = CombatManager(player)

    # 讀取存檔與離線掛機結算 (優先讀取 src/saves/savegame.json，向下相容根目錄)
    save_file = get_default_save_path()
    offline_report = player.load_from_file(save_file, combat_mgr)

    window = MainWindow(player, combat_mgr, sound_mgr)
    window.show()

    # 離線結算彈窗提示
    if offline_report:
        msg = QMessageBox(window)
        msg.setWindowTitle("遠征隊離線收益結算")
        mins = int(offline_report['seconds'] // 60)
        secs = int(offline_report['seconds'] % 60)
        loot_str = ", ".join(offline_report['loots']) if offline_report['loots'] else "無"
        info_text = (
            f"<b>歡迎冒險家歸隊！</b><br><br>"
            f"離線累積時間: <b>{mins} 分 {secs} 秒</b><br>"
            f"擊敗怪物數量: <b>{offline_report['kills']} 隻</b><br>"
            f"獲得經驗值: <b style='color: #63b3ed;'>+{offline_report['exp']} EXP</b><br>"
            f"獲得金幣: <b style='color: #ecc94b;'>+{offline_report['gold']} 金幣</b><br>"
            f"拾獲神裝: <b style='color: #9f7aea;'>{loot_str}</b>"
        )
        msg.setText(info_text)
        msg.setStyleSheet(QSS_DARK_THEME)
        msg.exec()

    exit_code = app.exec()

    # 結束時自動安全存檔
    player.save_to_file(save_file, combat_mgr)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
