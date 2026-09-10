"""
《新楓之谷：放置遠征隊》套裝效果總覽彈窗 (set_bonus_dialog.py)
"""
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QPushButton,
    QFrame, QScrollArea, QWidget
)
from item_system import SET_DEFINITIONS
from ui_styles import QSS_DARK_THEME


class SetBonusDialog(QDialog):
    """按需查看目前穿戴套裝與下一階效果。"""
    def __init__(self, player, parent=None):
        super().__init__(parent)
        self.setWindowTitle("套裝效果總覽")
        self.resize(580, 680)
        self.setMinimumSize(480, 420)
        self.setStyleSheet(QSS_DARK_THEME)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(8)
        layout.addWidget(QLabel("<b style='font-size: 15px; color: #ecc94b;'>目前穿戴套裝效果</b>"))

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(8, 8, 8, 8)
        content_layout.setSpacing(8)

        active_sets = player.get_active_sets()
        if not active_sets:
            content_layout.addWidget(QLabel("目前尚未啟動任何套裝效果。"))
        else:
            for active in active_sets:
                set_id = active.get("set_id", "")
                set_def = SET_DEFINITIONS.get(set_id, {})
                r, g, b = active.get("color", (236, 201, 75))
                frame = QFrame()
                frame.setStyleSheet(
                    f"background-color: #131924; border: 1px solid rgb({r},{g},{b}); "
                    "border-radius: 5px; padding: 6px;"
                )
                frame_layout = QVBoxLayout(frame)
                frame_layout.addWidget(QLabel(
                    f"<b style='color: rgb({r},{g},{b}); font-size: 13px;'>"
                    f"【{active['name']}】</b> 已穿戴 {active['count']} 件"
                ))
                for tier, tier_data in sorted(set_def.get("tiers", {}).items()):
                    enabled = active["count"] >= tier
                    color = "#68d391" if enabled else "#718096"
                    state = "已啟動" if enabled else f"還差 {tier - active['count']} 件"
                    frame_layout.addWidget(QLabel(
                        f"<span style='color: {color};'>[{tier}件套] {tier_data.get('desc', '')} ({state})</span>"
                    ))
                content_layout.addWidget(frame)
        content_layout.addStretch()
        scroll.setWidget(content)
        layout.addWidget(scroll, 1)

        close_button = QPushButton("關閉")
        close_button.clicked.connect(self.accept)
        layout.addWidget(close_button)


