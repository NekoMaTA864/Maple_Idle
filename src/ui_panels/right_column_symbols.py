"""
新楓之谷：放置遠征隊 - 右欄面板：符文/符號系統子模組 (right_column_symbols.py)
從 right_column.py 拆分而出，負責 ARC / AUT 符號工坊的 UI 建構與刷新。
"""

from PySide6.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QWidget
from player_symbols import ARC_SYMBOLS_DATA, AUT_SYMBOLS_DATA


def build_symbol_ui_structure(win):
    """在符文系統容器內建立 ARC / AUT UI 結構"""
    sym_header_frame = QFrame()
    sym_header_frame.setStyleSheet("background-color: #10141f; border: 1px solid #232936; border-radius: 4px; padding: 4px;")
    sh_layout = QVBoxLayout(sym_header_frame)
    sh_layout.setContentsMargins(6, 4, 6, 4)
    sh_layout.setSpacing(2)

    win.lbl_sym_totals = QLabel("秘法符文 (ARC): 0  |  原初符文 (AUT): 0")
    win.lbl_sym_totals.setStyleSheet("color: #68d391; font-size: 11px; font-weight: bold;")
    sh_layout.addWidget(win.lbl_sym_totals)

    win.lbl_sym_stats = QLabel("全隊加成: 攻+0 | HP+0 | 防+0")
    win.lbl_sym_stats.setStyleSheet("color: #cbd5e1; font-size: 10px;")
    sh_layout.addWidget(win.lbl_sym_stats)

    win.btn_auto_upg_symbols = QPushButton("⚡ 一鍵強化所有符號")
    win.btn_auto_upg_symbols.setStyleSheet("background-color: #2b6cb0; color: #ffffff; border: 1px solid #63b3ed; font-weight: bold; padding: 4px; font-size: 11px; border-radius: 3px;")
    win.btn_auto_upg_symbols.clicked.connect(win._auto_upgrade_all_symbols)
    sh_layout.addWidget(win.btn_auto_upg_symbols)

    win.symbol_layout.addWidget(sym_header_frame)

    win.symbol_cards_container = QWidget()
    win.sym_list_layout = QVBoxLayout(win.symbol_cards_container)
    win.sym_list_layout.setContentsMargins(0, 0, 0, 0)
    win.sym_list_layout.setSpacing(4)

    win.symbol_ui_items = {}

    lbl_arc_sec = QLabel("<b style='color: #4299e1;'>【奧術之河 秘法符號 (ARC)】</b>")
    lbl_arc_sec.setStyleSheet("padding-top: 2px;")
    win.sym_list_layout.addWidget(lbl_arc_sec)

    for sym_key, s_data in ARC_SYMBOLS_DATA.items():
        _create_symbol_card(win, sym_key, s_data, is_arc=True)

    lbl_aut_sec = QLabel("<b style='color: #ed8936;'>【格蘭帝斯 原初符號 (AUT)】</b>")
    lbl_aut_sec.setStyleSheet("padding-top: 6px;")
    win.sym_list_layout.addWidget(lbl_aut_sec)

    for sym_key, s_data in AUT_SYMBOLS_DATA.items():
        _create_symbol_card(win, sym_key, s_data, is_arc=False)

    win.symbol_layout.addWidget(win.symbol_cards_container)


def _create_symbol_card(win, sym_key: str, s_data: dict, is_arc: bool):
    """建立單張符號卡片"""
    card = QFrame()
    card.setStyleSheet("background-color: #151926; border: 1px solid #2a3447; border-radius: 4px; padding: 4px;")
    card_layout = QHBoxLayout(card)
    card_layout.setContentsMargins(6, 4, 6, 4)
    card_layout.setSpacing(6)

    info_layout = QVBoxLayout()
    info_layout.setSpacing(2)

    lbl_title = QLabel()
    lbl_title.setStyleSheet("font-size: 11px; font-weight: bold;")
    info_layout.addWidget(lbl_title)

    lbl_stats = QLabel()
    lbl_stats.setStyleSheet("color: #a0aec0; font-size: 10px;")
    info_layout.addWidget(lbl_stats)

    lbl_frags = QLabel()
    lbl_frags.setStyleSheet("color: #cbd5e0; font-size: 10px;")
    info_layout.addWidget(lbl_frags)

    card_layout.addLayout(info_layout, stretch=1)

    btn_upg = QPushButton("升級")
    btn_upg.setFixedWidth(75)
    btn_upg.setStyleSheet("background-color: #2d3748; color: #e2e8f0; border: 1px solid #4a5568; font-size: 10px; padding: 4px;")
    btn_upg.clicked.connect(lambda _, k=sym_key: win._upgrade_symbol(k))
    card_layout.addWidget(btn_upg)

    win.sym_list_layout.addWidget(card)
    win.symbol_ui_items[sym_key] = {
        "card": card,
        "title": lbl_title,
        "stats": lbl_stats,
        "frags": lbl_frags,
        "btn": btn_upg,
        "is_arc": is_arc,
        "data": s_data
    }


def render_symbol_content(win):
    """渲染秘法與真實符號工坊 (符文系統)"""
    total_arc = win.player.get_total_arc()
    total_aut = win.player.get_total_aut()
    sym_atk = int(win.player.get_symbol_stat_sum("attack"))
    sym_hp = int(win.player.get_symbol_stat_sum("hp"))
    sym_def = int(win.player.get_symbol_stat_sum("defense"))

    win.lbl_sym_totals.setText(f"秘法符文 (ARC): {total_arc}  |  原初符文 (AUT): {total_aut}")
    win.lbl_sym_stats.setText(f"全隊加成: 攻+{sym_atk:,} | HP+{sym_hp:,} | 防+{sym_def:,}")

    can_auto_upg_any = False
    for sym_key, ui in win.symbol_ui_items.items():
        is_arc = ui["is_arc"]
        s_data = ui["data"]
        cur_lvl = win.player.arc_symbols.get(sym_key, 0) if is_arc else win.player.aut_symbols.get(sym_key, 0)
        cur_frags = win.player.symbol_fragments.get(sym_key, 0)
        max_lvl = s_data["max_lvl"]
        tag_color = "#63b3ed" if is_arc else "#f6ad55"

        if cur_lvl == 0:
            ui["title"].setText(f"<b style='color: #718096;'>{s_data['name']} [未解鎖]</b>")
            ui["stats"].setText(f"<span style='color: #718096;'>需通關對應地圖或獲得首個碎片解鎖</span>")
            ui["frags"].setText(f"<span style='color: #718096;'>持有碎片: {cur_frags}</span>")
            ui["btn"].setText("未解鎖")
            ui["btn"].setEnabled(False)
            ui["btn"].setStyleSheet("background-color: #1a202c; color: #4a5568; border: 1px solid #2d3748; font-size: 10px;")
        else:
            power_name = "ARC" if is_arc else "AUT"
            base_power = s_data["base_arc"] if is_arc else s_data["base_aut"]
            power_per_lvl = s_data["arc_per_lvl"] if is_arc else s_data["aut_per_lvl"]
            cur_power = base_power + (cur_lvl - 1) * power_per_lvl
            cur_atk = cur_lvl * s_data["stat_atk"]
            cur_hp = cur_lvl * s_data["stat_hp"]

            ui["title"].setText(f"<b style='color: {tag_color};'>{s_data['name']}</b> <span style='color: #ffd700;'>Lv.{cur_lvl}/{max_lvl}</span>")
            ui["stats"].setText(f"<span style='color: #68d391;'>{power_name} +{cur_power}</span> | 攻+{cur_atk} | HP+{cur_hp}")

            if cur_lvl >= max_lvl:
                ui["frags"].setText(f"<b style='color: #ecc94b;'>已達最高等級 (MAX)</b>")
                ui["btn"].setText("已滿級")
                ui["btn"].setEnabled(False)
                ui["btn"].setStyleSheet("background-color: #1a202c; color: #ffd700; border: 1px solid #d69e2e; font-size: 10px;")
            else:
                req_frags, req_gold, _ = win.player.get_symbol_upgrade_req(sym_key)
                can_upg = (cur_frags >= req_frags) and (win.player.gold >= req_gold)
                if can_upg:
                    can_auto_upg_any = True
                frag_color = "#68d391" if cur_frags >= req_frags else "#fc8181"
                ui["frags"].setText(f"碎片: <b style='color: {frag_color};'>{cur_frags}/{req_frags}</b> | 費用: ${req_gold:,}")
                ui["btn"].setText("升級")
                ui["btn"].setEnabled(can_upg)
                if can_upg:
                    ui["btn"].setStyleSheet("background-color: #2b6cb0; color: #ffffff; border: 1px solid #4299e1; font-weight: bold; font-size: 10px;")
                else:
                    ui["btn"].setStyleSheet("background-color: #1a202c; color: #718096; border: 1px solid #2d3748; font-size: 10px;")

    win.btn_auto_upg_symbols.setEnabled(can_auto_upg_any)
