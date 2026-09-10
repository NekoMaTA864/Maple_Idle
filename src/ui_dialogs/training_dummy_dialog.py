"""
《新楓之谷：放置遠征隊》木樁測試設定彈窗 (training_dummy_dialog.py)
"""
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QSpinBox
)
from ui_styles import QSS_DARK_THEME


class TrainingDummyDialog(QDialog):
    """設定可重複測試輸出的木樁怪物。"""
    def __init__(self, player, on_apply, parent=None):
        super().__init__(parent)
        self.on_apply = on_apply
        self.setWindowTitle("木樁測試設定")
        self.setMinimumWidth(360)
        self.setStyleSheet(QSS_DARK_THEME)

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("<b style='font-size: 14px; color: #ecc94b;'>自定義木樁地區</b>"))
        layout.addWidget(QLabel("木樁會在擊破後立即重置，戰鬥統計可用來比較隊伍輸出。"))

        # 快速預設情境按鈕 (三大實戰環境)
        presets_layout = QHBoxLayout()
        btn_preset_mob = QPushButton("🌾 小怪割草 (20%防/3怪)")
        btn_preset_mob.setStyleSheet("background-color: #2b4c3f; color: #a3e635; font-weight: bold;")
        btn_preset_mid = QPushButton("⚔️ 中級王 (100%防/1怪)")
        btn_preset_mid.setStyleSheet("background-color: #3b3a61; color: #60a5fa; font-weight: bold;")
        btn_preset_end = QPushButton("👑 頂級王 (300%防/單體靶)")
        btn_preset_end.setStyleSheet("background-color: #4a2840; color: #f472b6; font-weight: bold;")

        btn_preset_mob.clicked.connect(lambda: self._set_preset(20, 3, False))
        btn_preset_mid.clicked.connect(lambda: self._set_preset(100, 1, True))
        btn_preset_end.clicked.connect(lambda: self._set_preset(300, 1, True))

        presets_layout.addWidget(btn_preset_mob)
        presets_layout.addWidget(btn_preset_mid)
        presets_layout.addWidget(btn_preset_end)
        layout.addLayout(presets_layout)

        self.level = QSpinBox()
        self.level.setRange(1, 300)
        self.level.setValue(max(1, player.level))
        self.hp = QSpinBox()
        self.hp.setRange(100, 2_000_000_000)
        self.hp.setSingleStep(100_000)
        self.hp.setValue(50_000_000)
        self.attack = QSpinBox()
        self.attack.setRange(0, 2_000_000)
        self.attack.setSingleStep(100)
        self.attack.setValue(0)
        self.defense = QSpinBox()
        self.defense.setRange(0, 1000)
        self.defense.setSingleStep(10)
        self.defense.setValue(300)
        self.defense.setSuffix("%")
        self.count = QSpinBox()
        self.count.setRange(1, 5)
        self.count.setValue(1)
        for label, control in [
            ("木樁等級", self.level),
            ("木樁 HP", self.hp),
            ("木樁攻擊", self.attack),
            ("正統防禦率%", self.defense),
            ("群怪數量 (1~5隻)", self.count),
        ]:
            row = QHBoxLayout()
            row.addWidget(QLabel(label))
            row.addWidget(control)
            layout.addLayout(row)

        tip_lbl = QLabel("<span style='color: #a0aec0; font-size: 11px;'>* 新楓之谷正統防禦率：小怪 20% | 中級首領 100% | 戴米安/黑魔法師 300% (極度考驗無視防禦)</span>")
        tip_lbl.setWordWrap(True)
        layout.addWidget(tip_lbl)

        buttons = QHBoxLayout()
        apply_button = QPushButton("開始木樁測試")
        apply_button.clicked.connect(self._apply)
        cancel_button = QPushButton("取消")
        cancel_button.clicked.connect(self.reject)
        buttons.addWidget(apply_button)
        buttons.addWidget(cancel_button)
        layout.addLayout(buttons)

    def _set_preset(self, def_rate, count, is_boss):
        self.defense.setValue(def_rate)
        self.count.setValue(count)
        self._is_boss_preset = is_boss

    def _apply(self):
        is_boss = getattr(self, "_is_boss_preset", self.defense.value() >= 100)
        self.on_apply(self.level.value(), self.hp.value(), self.attack.value(), self.defense.value(), self.count.value(), is_boss=is_boss)
        self.accept()


