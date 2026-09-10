"""
《新楓之谷：放置遠征隊》一鍵洗潛能配置彈窗 (auto_cube_dialog.py)
"""
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QMessageBox
)
from item_system import POTENTIAL_RANK_INFO, SLOT_NAMES
from ui_styles import QSS_DARK_THEME


class AutoCubeDialog(QDialog):
    """正統新楓之谷一鍵洗潛能配置彈窗 (支援主潛能與附加潛能)"""
    def __init__(self, item, player, slot_k=None, is_bonus=False, on_cube_done=None, parent=None):
        super().__init__(parent)
        self.item = item
        self.player = player
        self.slot_k = slot_k
        self.is_bonus = is_bonus
        self.on_cube_done = on_cube_done

        pot_type_str = "附加潛能" if is_bonus else "主潛能"
        self.setWindowTitle(f"【一鍵洗{pot_type_str}】 - {item.base_name if item else slot_k}")
        self.resize(480, 440)
        self.setMinimumSize(420, 380)
        self.setStyleSheet(QSS_DARK_THEME)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(12)

        # 獲取當前階級
        cur_rank = "rare"
        if slot_k and hasattr(player, "slot_potentials") and slot_k in player.slot_potentials:
            cur_rank = player.slot_potentials[slot_k]["bonus" if is_bonus else "main"].get("rank", "rare")
        elif item:
            cur_rank = getattr(item, "potential_rank", "rare")

        cur_rank_name = POTENTIAL_RANK_INFO.get(cur_rank, {}).get("name", cur_rank)
        cur_qcol = POTENTIAL_RANK_INFO.get(cur_rank, {}).get("qcolor", "#9f7aea")
        target_title = item.base_name if item else SLOT_NAMES.get(slot_k, slot_k)
        header = QLabel(f"<b style='font-size: 14px;'>目標：{target_title} ({pot_type_str})</b><br>當前階級: <b style='color: {cur_qcol}; font-size: 13px;'>[{cur_rank_name}]</b> | 擁有金幣: <b style='color: #ffd700;'>${player.gold:,}</b>")
        layout.addWidget(header)

        # 選擇方塊類型
        row1 = QHBoxLayout()
        row1.addWidget(QLabel("使用的方塊:"))
        self.combo_cube = QComboBox()
        if not is_bonus:
            self.combo_cube.addItem("閃耀方塊 ($30,000 / 次，上限 傳奇)", "bright")
            self.combo_cube.addItem("楓方塊 ($6,000 / 次，上限 稀有)", "mystic")
        else:
            self.combo_cube.addItem("閃耀附加方塊 ($50,000 / 次，上限 傳奇)", "bonus_bright")
            self.combo_cube.addItem("可疑附加方塊 ($15,000 / 次，上限 稀有)", "bonus_occult")
        self.combo_cube.setStyleSheet("background-color: #1a202c; color: #ecc94b; border: 1px solid #4a5568; padding: 4px;")
        row1.addWidget(self.combo_cube)
        layout.addLayout(row1)

        # 目標階級
        row2 = QHBoxLayout()
        row2.addWidget(QLabel("目標潛能階級:"))
        self.combo_rank = QComboBox()
        self.combo_rank.addItem("傳奇 (Legendary) [最高階級]", "legendary")
        self.combo_rank.addItem("罕見 (Unique)", "unique")
        self.combo_rank.addItem("稀有 (Epic)", "epic")
        self.combo_rank.setStyleSheet("background-color: #1a202c; color: #48bb78; border: 1px solid #4a5568; padding: 4px;")
        row2.addWidget(self.combo_rank)
        layout.addLayout(row2)

        # 指定詞條關鍵字
        row3 = QHBoxLayout()
        row3.addWidget(QLabel("鎖定詞條關鍵字:"))
        self.combo_stat = QComboBox()
        self.combo_stat.addItem("不限 (升至目標階級即停止)", "")
        self.combo_stat.addItem("攻擊力 (攻擊力% 或 固定攻擊力)", "攻擊力")
        self.combo_stat.addItem("BOSS (BOSS傷害%)", "BOSS")
        self.combo_stat.addItem("無視 (無視防禦%)", "無視")
        self.combo_stat.addItem("暴擊 (暴擊率% 或 暴擊傷害%)", "暴擊")
        self.combo_stat.addItem("全屬性 (全屬性%)", "全屬性")
        self.combo_stat.addItem("傷害 (總傷害%)", "傷害")
        self.combo_stat.addItem("冷卻 (冷卻時間減少)", "冷卻")
        self.combo_stat.addItem("掉寶 (掉寶率%)", "掉寶")
        self.combo_stat.addItem("楓幣 (楓幣獲得量%)", "楓幣")
        self.combo_stat.setStyleSheet("background-color: #1a202c; color: #e2e8f0; border: 1px solid #4a5568; padding: 4px;")
        row3.addWidget(self.combo_stat)
        layout.addLayout(row3)

        # 最大洗練次數限制
        row4 = QHBoxLayout()
        row4.addWidget(QLabel("單次最大次數:"))
        self.combo_max = QComboBox()
        self.combo_max.addItem("⚡ 洗到出目標為止 (直到達成或金幣用盡)", 999999)
        self.combo_max.addItem("最多洗 20 次", 20)
        self.combo_max.addItem("最多洗 50 次", 50)
        self.combo_max.addItem("最多洗 100 次", 100)
        self.combo_max.setStyleSheet("background-color: #1a202c; color: #cbd5e1; border: 1px solid #4a5568; padding: 4px;")
        row4.addWidget(self.combo_max)
        layout.addLayout(row4)

        tip_lbl = QLabel("<span style='color: #718096; font-size: 11px;'>※ 潛能永久鎖定於欄位，達成目標階級（或含指定詞條）將自動停止並結算金幣。</span>")
        layout.addWidget(tip_lbl)

        layout.addStretch()

        # 按鈕列
        btn_box = QHBoxLayout()
        self.btn_start = QPushButton(f"🔮 開始一鍵洗{pot_type_str}")
        self.btn_start.setStyleSheet("background-color: #2b6cb0; color: #ffffff; border: 1px solid #4299e1; padding: 8px; font-weight: bold;")
        self.btn_start.clicked.connect(self._run_auto_cube)
        btn_box.addWidget(self.btn_start)

        btn_cancel = QPushButton("取消")
        btn_cancel.setStyleSheet("background-color: #2d3748; color: #cbd5e1; border: 1px solid #4a5568; padding: 8px;")
        btn_cancel.clicked.connect(self.reject)
        btn_box.addWidget(btn_cancel)
        layout.addLayout(btn_box)

    def _run_auto_cube(self):
        cube_type = self.combo_cube.currentData()
        target_rank = self.combo_rank.currentData()
        stat_kw = self.combo_stat.currentData()
        stat_kw = stat_kw if stat_kw else None
        max_c = self.combo_max.currentData()

        if self.slot_k:
            from player_gear import auto_cube_slot
            success, msg = auto_cube_slot(
                self.player,
                self.slot_k,
                cube_type=cube_type,
                target_rank=target_rank,
                target_stat_keyword=stat_kw,
                is_bonus=self.is_bonus,
                max_cubes=max_c
            )
        else:
            from player_gear import auto_cube_item
            success, msg = auto_cube_item(
                self.player,
                self.item,
                cube_type=cube_type,
                target_rank=target_rank,
                target_stat_keyword=stat_kw,
                max_cubes=max_c
            )

        if success:
            QMessageBox.information(self, "一鍵洗潛結果", msg)
        else:
            QMessageBox.warning(self, "一鍵洗潛中斷/失敗", msg)

        if self.on_cube_done:
            self.on_cube_done()
        self.accept()


# =========================================================================
