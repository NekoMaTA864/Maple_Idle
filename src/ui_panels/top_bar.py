"""
新楓之谷：放置遠征隊 - 頂部狀態列面板模組 (top_bar.py)
"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QProgressBar, QPushButton, QSlider


def build_top_bar(win) -> QFrame:
    """建構頂部狀態列 UI"""
    bar = QFrame()
    bar.setStyleSheet("background-color: #141824; border: 1px solid #2a3447; border-radius: 6px; padding: 4px 8px;")
    layout = QHBoxLayout(bar)
    layout.setContentsMargins(6, 4, 6, 4)

    title = QLabel("<b>【新楓之谷：放置遠征隊 - MapleStory Idle】</b>")
    title.setStyleSheet("color: #f6ad55; font-size: 14px;")
    layout.addWidget(title)

    layout.addSpacing(16)
    win.lbl_level = QLabel(f"遠征隊等級: Lv.{win.player.level}")
    win.lbl_level.setStyleSheet("color: #e2e8f0; font-weight: bold;")
    layout.addWidget(win.lbl_level)

    win.bar_exp = QProgressBar()
    win.bar_exp.setFixedWidth(130)
    win.bar_exp.setFixedHeight(16)
    win.bar_exp.setStyleSheet("QProgressBar::chunk { background-color: #3182ce; }")
    layout.addWidget(win.bar_exp)

    win.lbl_gold = QLabel(f"行囊金幣: {win.player.gold:,}")
    win.lbl_gold.setStyleSheet("color: #ecc94b; font-weight: bold;")
    layout.addWidget(win.lbl_gold)

    layout.addStretch()

    btn_guide = QPushButton("📖 玩法百科 & 機率表")
    btn_guide.setStyleSheet("background-color: #2b4c7e; color: #ffd700; border: 1.5px solid #ecc94b; font-weight: bold; padding: 4px 10px; border-radius: 4px;")
    btn_guide.setToolTip("點擊查看裝備潛能部位限制、內潛數值表、黃金轉蛋機全獎池、萌獸與寵物特權機率")
    btn_guide.clicked.connect(win._open_game_guide_dialog)
    layout.addWidget(btn_guide)

    layout.addSpacing(6)

    btn_save = QPushButton("手動存檔 [S]")
    btn_save.clicked.connect(win._manual_save)
    layout.addWidget(btn_save)

    layout.addSpacing(10)
    win.lbl_vol_icon = QLabel("🔊")
    win.lbl_vol_icon.setStyleSheet("color: #ecc94b; font-size: 13px;")
    layout.addWidget(win.lbl_vol_icon)

    win.slider_volume = QSlider(Qt.Horizontal)
    win.slider_volume.setRange(0, 100)
    vol_int = int(win.sound_mgr.volume * 100) if hasattr(win, 'sound_mgr') else 35
    win.slider_volume.setValue(vol_int)
    win.slider_volume.setFixedWidth(75)
    win.slider_volume.setToolTip("音效音量調整 (0% ~ 100%)")
    win.slider_volume.setStyleSheet("""
        QSlider::groove:horizontal {
            height: 5px;
            background: #232a3b;
            border-radius: 2px;
        }
        QSlider::sub-page:horizontal {
            background: #d69e2e;
            border-radius: 2px;
        }
        QSlider::handle:horizontal {
            background: #ecc94b;
            border: 1px solid #b7791f;
            width: 12px;
            margin-top: -4px;
            margin-bottom: -4px;
            border-radius: 6px;
        }
        QSlider::handle:horizontal:hover {
            background: #faf089;
        }
    """)
    win.slider_volume.valueChanged.connect(win._on_volume_changed)
    layout.addWidget(win.slider_volume)

    win.lbl_vol_val = QLabel(f"{vol_int}%")
    win.lbl_vol_val.setFixedWidth(34)
    win.lbl_vol_val.setStyleSheet("color: #cbd5e1; font-size: 11px;")
    layout.addWidget(win.lbl_vol_val)

    win.btn_mute = QPushButton("靜音 [M]")
    win.btn_mute.clicked.connect(win._toggle_mute)
    layout.addWidget(win.btn_mute)

    return bar


def update_top_bar(win, force=False):
    """更新頂部狀態列資訊（附帶狀態比對快取）"""
    top_state = (win.player.level, win.player.exp, win.player.gold, win.player.free_points)
    if not force and top_state == win._last_top_state:
        return
    win._last_top_state = top_state

    win.lbl_level.setText(f"遠征隊等級: Lv.{win.player.level}")
    win.bar_exp.setMaximum(1000)
    exp_pct = max(0.0, min(1.0, win.player.exp / max(1, win.player.exp_to_next)))
    win.bar_exp.setValue(int(exp_pct * 1000))
    win.bar_exp.setFormat(f"{exp_pct * 100:.1f}%")
    win.lbl_gold.setText(f"行囊金幣: {win.player.gold:,}")
    if hasattr(win, 'tab_widget') and win.tab_widget.count() > 5:
        win.tab_widget.setTabText(5, f"[加點+{win.player.free_points}]" if win.player.free_points > 0 else "[加點]")
