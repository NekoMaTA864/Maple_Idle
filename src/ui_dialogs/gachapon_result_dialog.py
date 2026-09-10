"""
《新楓之谷：放置遠征隊》黃金轉蛋機抽獎結果彈窗 (gachapon_result_dialog.py)
"""
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QScrollArea, QWidget, QGridLayout
)
from PySide6.QtCore import Qt
from ui_styles import QSS_DARK_THEME


class GachaponResultDialog(QDialog):
    """黃金轉蛋機抽獎結果彈窗 (支援單抽與十連抽卡牌開獎展示)"""
    def __init__(self, results, draw_count=10, on_draw_again=None, parent=None):
        super().__init__(parent)
        self.results = results or []
        self.draw_count = draw_count
        self.on_draw_again = on_draw_again

        self.setWindowTitle("🎰 楓之谷【黃金轉蛋機】開獎報告")
        self.resize(680, 520)
        self.setMinimumSize(580, 420)
        self.setStyleSheet(QSS_DARK_THEME)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        # 頂部開獎橫幅
        header_frame = QFrame()
        header_frame.setStyleSheet("background-color: #1a1625; border: 1.5px solid #d69e2e; border-radius: 6px; padding: 10px;")
        h_lay = QVBoxLayout(header_frame)
        h_lay.setSpacing(4)
        lbl_title = QLabel(f"<b style='color: #ffd700; font-size: 16px;'>🎰 黃金轉蛋機 · {self.draw_count} 連抽開獎報告</b>")
        h_lay.addWidget(lbl_title)

        jackpot_cnt = sum(1 for r in self.results if "特殊種子" in r.get("name", "") or "傳奇大獎" in r.get("name", ""))
        equip_cnt = sum(1 for r in self.results if r.get("type") == "item")
        scroll_cnt = sum(1 for r in self.results if r.get("type") == "scroll")
        cube_cnt = sum(1 for r in self.results if r.get("type") == "resource")
        sym_cnt = sum(1 for r in self.results if r.get("type") == "symbol")

        stat_desc = f"獲得：{len(self.results)} 項獎勵 (神裝 {equip_cnt} 件、卷軸 {scroll_cnt} 張、方塊 {cube_cnt} 份、符號 {sym_cnt} 份)"
        if jackpot_cnt > 0:
            stat_desc += f" ｜ <b style='color: #ecc94b; font-size: 12px;'>★ 歐氣爆發！包含 {jackpot_cnt} 件極品特等大獎！</b>"
        lbl_sub = QLabel(f"<span style='color: #cbd5e1; font-size: 11px;'>{stat_desc}</span>")
        h_lay.addWidget(lbl_sub)
        layout.addWidget(header_frame)

        # 獎勵卡牌展示區 (滾動網格)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("background-color: #0e121b; border: 1px solid #232a3b; border-radius: 6px;")

        cards_widget = QWidget()
        grid = QGridLayout(cards_widget)
        grid.setSpacing(8)
        grid.setContentsMargins(8, 8, 8, 8)

        cols = 5 if len(self.results) >= 5 else max(1, len(self.results))
        for idx, res in enumerate(self.results):
            r_type = res.get("type", "item")
            r_name = res.get("name", "")
            r_color = res.get("color", "#4299e1")
            r_desc = res.get("desc", "")
            is_seed = "特殊種子" in r_name
            is_jackpot = ("特殊種子" in r_name or "傳奇大獎" in r_name)

            card = QFrame()
            if is_seed:
                card.setStyleSheet("background-color: #2b141e; border: 2px solid #fc8181; border-radius: 6px; padding: 4px;")
            elif is_jackpot:
                card.setStyleSheet("background-color: #261e14; border: 2px solid #ecc94b; border-radius: 6px; padding: 4px;")
            elif r_type == "item_lost":
                card.setStyleSheet("background-color: #231215; border: 1.5px dashed #e53e3e; border-radius: 6px; padding: 4px;")
            else:
                card.setStyleSheet(f"background-color: #141824; border: 1.5px solid {r_color}; border-radius: 6px; padding: 4px;")

            c_lay = QVBoxLayout(card)
            c_lay.setContentsMargins(4, 5, 4, 5)
            c_lay.setSpacing(3)

            # 頂部類別標籤
            badge_text = "【超絕大獎】"
            if is_seed:
                badge_text = "【種子神戒】"
            elif "傳奇大獎" in r_name:
                badge_text = "【傳奇神裝】"
            elif "稀有神裝" in r_name:
                badge_text = "【高級裝備】"
            elif "艾比卷軸" in r_name:
                badge_text = "【艾比卷軸】"
            elif "方塊" in r_name:
                badge_text = "【鍛造方塊】"
            elif "符號" in r_name:
                badge_text = "【秘法碎片】"
            elif r_type == "item_lost":
                badge_text = "【行囊已滿】"

            lbl_badge = QLabel(f"<b style='color: {r_color}; font-size: 10px;'>{badge_text}</b>")
            lbl_badge.setAlignment(Qt.AlignCenter)
            c_lay.addWidget(lbl_badge)

            # 物品名稱 (去掉前綴【...】)
            clean_name = r_name
            if "】" in clean_name:
                clean_name = clean_name.split("】", 1)[1]

            lbl_name = QLabel(f"<b style='color: #ffffff; font-size: 11px;'>{clean_name}</b>")
            lbl_name.setAlignment(Qt.AlignCenter)
            lbl_name.setWordWrap(True)
            c_lay.addWidget(lbl_name)

            # 簡要說明
            lbl_desc = QLabel(r_desc)
            lbl_desc.setAlignment(Qt.AlignCenter)
            lbl_desc.setStyleSheet("color: #a0aec0; font-size: 9px;")
            lbl_desc.setWordWrap(True)
            c_lay.addWidget(lbl_desc)

            card.setToolTip(f"{r_name}\n{r_desc}")
            card.setMinimumSize(100, 92)
            row = idx // cols
            col = idx % cols
            grid.addWidget(card, row, col)

        scroll.setWidget(cards_widget)
        layout.addWidget(scroll, stretch=1)

        # 底部操作列 (再來一次 & 確認收下)
        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)

        cost_txt = "$100,000" if self.draw_count == 1 else "$900,000"
        btn_again = QPushButton(f"🎰 再抽一次 ({self.draw_count}連抽 {cost_txt})")
        btn_again.setStyleSheet("background-color: #d69e2e; color: #1a202c; border: 1.5px solid #ecc94b; font-weight: bold; padding: 8px 16px; border-radius: 4px; font-size: 12px;")
        btn_again.clicked.connect(self._draw_again_clicked)
        btn_row.addWidget(btn_again, stretch=1)

        btn_ok = QPushButton("確認收下")
        btn_ok.setStyleSheet("background-color: #2b6cb0; color: #ffffff; border: 1px solid #4299e1; font-weight: bold; padding: 8px 24px; border-radius: 4px; font-size: 12px;")
        btn_ok.clicked.connect(self.accept)
        btn_row.addWidget(btn_ok, stretch=1)

        layout.addLayout(btn_row)

    def _draw_again_clicked(self):
        self.accept()
        if self.on_draw_again:
            self.on_draw_again()
