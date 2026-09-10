"""
新楓之谷：放置遠征隊 - 右欄面板：轉蛋屋/商店子模組 (right_column_shop.py)
從 right_column.py 拆分而出，負責黃金轉蛋機、艾比卷軸與潛能方塊商店的 UI。
"""

from PySide6.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QSizePolicy
from PySide6.QtCore import Qt
from item_system import ABBY_SCROLLS, CUBE_COSTS


def _clear_layout(layout):
    """遞迴清理佈局內的所有子元件"""
    while layout.count() > 0:
        child = layout.takeAt(0)
        if child.widget():
            child.widget().deleteLater()
        elif child.layout():
            _clear_layout(child.layout())


def render_shop_content(win):
    """渲染楓之谷商城與黃金轉蛋屋"""
    _clear_layout(win.shop_layout)

    # 1. 黃金轉蛋機大獎告示牌
    gacha_box = QFrame()
    gacha_box.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
    gacha_box.setStyleSheet("background-color: #1a1625; border: 1.5px solid #d69e2e; border-radius: 6px; padding: 8px;")
    gb_lay = QVBoxLayout(gacha_box)
    gb_lay.setSpacing(6)

    gb_lay.addWidget(QLabel("<b style='color: #ffd700; font-size: 14px;'>🎰 楓之谷【黃金轉蛋機】</b>"))
    lbl_jackpot_info = QLabel(
        "<span style='color: #cbd5e1; font-size: 11px;'>"
        "★ 大獎：頂級神裝、Boss 飾品、永恆神裝、特殊種子戒指<br/>"
        "★ 副產物：艾比卷軸、潛能方塊、秘法符號碎片"
        "</span>"
    )
    lbl_jackpot_info.setWordWrap(True)
    gb_lay.addWidget(lbl_jackpot_info)

    gacha_btn_row = QHBoxLayout()
    gacha_btn_row.setSpacing(8)

    btn_draw_1 = QPushButton("單抽 ($100,000)")
    btn_draw_1.setStyleSheet("background-color: #2b6cb0; color: #ffffff; border: 1px solid #4299e1; font-weight: bold; padding: 6px; border-radius: 4px;")
    btn_draw_1.clicked.connect(lambda: win._draw_gachapon(1))
    gacha_btn_row.addWidget(btn_draw_1)

    btn_draw_10 = QPushButton("十連抽 ($900,000 9折優惠)")
    btn_draw_10.setStyleSheet("background-color: #d69e2e; color: #1a202c; border: 1px solid #ecc94b; font-weight: bold; padding: 6px; border-radius: 4px;")
    btn_draw_10.clicked.connect(lambda: win._draw_gachapon(10))
    gacha_btn_row.addWidget(btn_draw_10)

    gb_lay.addLayout(gacha_btn_row)

    # 1.2 最近一次抽獎紀錄預覽
    if hasattr(win, "last_gachapon_results") and win.last_gachapon_results:
        res_box = QFrame()
        res_box.setStyleSheet("background-color: #12101b; border: 1px solid #744210; border-radius: 4px; padding: 6px;")
        rb_lay = QVBoxLayout(res_box)
        rb_lay.setContentsMargins(6, 4, 6, 4)
        rb_lay.setSpacing(3)

        rb_head = QHBoxLayout()
        rb_head.addWidget(QLabel(f"<b style='color: #ffd700; font-size: 11px;'>📋 最近開獎紀錄 ({len(win.last_gachapon_results)} 項)：</b>"))
        btn_view_dlg = QPushButton("🔍 放大卡牌報告")
        btn_view_dlg.setStyleSheet("background-color: #2b4c7e; color: #ffd700; border: 1px solid #ffd700; font-size: 9px; padding: 2px 6px; border-radius: 3px; font-weight: bold;")
        btn_view_dlg.clicked.connect(win._show_last_gacha_dialog)
        rb_head.addStretch()
        rb_head.addWidget(btn_view_dlg)
        rb_lay.addLayout(rb_head)

        for r in win.last_gachapon_results[:5]:
            r_col = r.get("color", "#cbd5e1")
            r_name = r.get("name", "")
            lbl_r = QLabel(f"<span style='color: {r_col}; font-size: 10px;'>• {r_name}</span>")
            rb_lay.addWidget(lbl_r)
        if len(win.last_gachapon_results) > 5:
            rb_lay.addWidget(QLabel(f"<span style='color: #718096; font-size: 9px;'>... 還有 {len(win.last_gachapon_results) - 5} 項獎勵 (點擊上方按鈕查看完整卡牌)</span>"))

        gb_lay.addWidget(res_box)

    win.shop_layout.addWidget(gacha_box)

    # 2. 艾比卷軸專賣店 (僅販售極電與宿命R)
    scroll_box = QFrame()
    scroll_box.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
    scroll_box.setStyleSheet("background-color: #161c28; border: 1px solid #2b4c7e; border-radius: 6px; padding: 8px;")
    sb_lay = QVBoxLayout(scroll_box)
    sb_lay.setSpacing(6)
    sb_lay.addWidget(QLabel("<b style='color: #63b3ed; font-size: 13px;'>📜 艾比卷軸</b>"))

    for s_type, s_info in ABBY_SCROLLS.items():
        row_f = QFrame()
        row_f.setStyleSheet("background-color: #11141e; border: 1px solid #232a3b; border-radius: 4px; padding: 4px;")
        rf_lay = QHBoxLayout(row_f)
        rf_lay.setContentsMargins(6, 4, 6, 4)

        r, g, b = s_info["color"]
        cur_stock = win.player.abby_scrolls.get(s_type, 0)
        lbl_s = QLabel(f"<b style='color: rgb({r},{g},{b}); font-size: 11px;'>【{s_info['name']}】</b> "
                       f"<span style='color: #a0aec0; font-size: 10px;'>庫存: {cur_stock} 張</span>")
        rf_lay.addWidget(lbl_s)
        rf_lay.addStretch()

        if s_type in ["electric", "R", "innocence"]:
            btn_buy1 = QPushButton(f"購買 1張 (${s_info['cost']:,})")
            btn_buy1.setStyleSheet("background-color: #2b6cb0; color: #ffffff; border: 1px solid #4299e1; font-size: 10px; padding: 3px 6px; border-radius: 3px;")
            btn_buy1.clicked.connect(lambda _, st=s_type: win._buy_shop_scroll(st, 1))
            rf_lay.addWidget(btn_buy1)

            sell_prices = {"electric": 30000, "R": 80000}
            if s_type in sell_prices and cur_stock > 0:
                sell_p = sell_prices[s_type]
                btn_sell = QPushButton(f"出售 (+${sell_p:,})")
                btn_sell.setStyleSheet("background-color: #744210; color: #feebc8; border: 1px solid #d69e2e; font-size: 10px; padding: 3px 6px; border-radius: 3px; font-weight: bold;")
                btn_sell.clicked.connect(lambda _, st=s_type: win._sell_shop_scroll(st, 1))
                rf_lay.addWidget(btn_sell)
        else:
            lbl_lock = QLabel("<span style='color: #ecc94b; font-size: 10px; font-weight: bold;'>[轉蛋/首領限定]</span>")
            rf_lay.addWidget(lbl_lock)

        sb_lay.addWidget(row_f)

    win.shop_layout.addWidget(scroll_box)

    # 3. 潛能方塊專賣店
    cube_box = QFrame()
    cube_box.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
    cube_box.setStyleSheet("background-color: #161c28; border: 1px solid #2b4c7e; border-radius: 6px; padding: 8px;")
    cb_lay = QVBoxLayout(cube_box)
    cb_lay.setSpacing(6)
    cb_lay.addWidget(QLabel("<b style='color: #ecc94b; font-size: 13px;'>🎲 潛能鍛造方塊專賣店 (洗出頂標詞條)</b>"))

    cube_info_map = {
        "mystic": ("楓方塊", "#63b3ed", "重置主潛能 (上限 稀有 Epic)"),
        "bright": ("閃耀方塊", "#ffd700", "重置主潛能 (上限 傳奇 Legendary)"),
        "bonus_occult": ("可疑附加方塊", "#a0aec0", "重置附加潛能 (上限 稀有 Epic)"),
        "bonus_bright": ("閃耀附加方塊", "#48bb78", "重置附加潛能 (上限 傳奇 Legendary)"),
    }

    for c_key, c_cost in CUBE_COSTS.items():
        c_name, c_col, c_desc = cube_info_map.get(c_key, (c_key, "#ffffff", ""))
        row_f = QFrame()
        row_f.setStyleSheet("background-color: #11141e; border: 1px solid #232a3b; border-radius: 4px; padding: 4px;")
        rf_lay = QHBoxLayout(row_f)
        rf_lay.setContentsMargins(6, 4, 6, 4)

        cur_c_stock = win.player.cube_inventory.get(c_key, 0)
        lbl_c = QLabel(f"<b style='color: {c_col}; font-size: 11px;'>【{c_name}】</b> "
                       f"<span style='color: #a0aec0; font-size: 10px;'>庫存: {cur_c_stock} | {c_desc}</span>")
        rf_lay.addWidget(lbl_c)
        rf_lay.addStretch()

        btn_buy_c = QPushButton(f"購買 1顆 (${c_cost:,})")
        btn_buy_c.setStyleSheet("background-color: #2b6cb0; color: #ffffff; border: 1px solid #4299e1; font-size: 10px; padding: 3px 6px; border-radius: 3px;")
        btn_buy_c.clicked.connect(lambda _, ck=c_key: win._buy_shop_cube(ck, 1))
        rf_lay.addWidget(btn_buy_c)

        cb_lay.addWidget(row_f)

    # 3.2 萌獸專屬：神奇萌獸方塊
    row_fam_c = QFrame()
    row_fam_c.setStyleSheet("background-color: #11141e; border: 1px solid #702459; border-radius: 4px; padding: 4px;")
    rf_lay_c = QHBoxLayout(row_fam_c)
    rf_lay_c.setContentsMargins(6, 4, 6, 4)
    fam_c_stock = win.player.familiar_manager.familiar_cubes if hasattr(win.player, "familiar_manager") else 0
    lbl_fc = QLabel(f"<b style='color: #f687b3; font-size: 11px;'>【神奇萌獸方塊】</b> "
                    f"<span style='color: #a0aec0; font-size: 10px;'>庫存: {fam_c_stock} | 重置萌獸潛能 (洗出雙終/三終神級詞條)</span>")
    rf_lay_c.addWidget(lbl_fc)
    rf_lay_c.addStretch()

    btn_buy_fc = QPushButton("購買 1顆 ($50,000)")
    btn_buy_fc.setStyleSheet("background-color: #702459; color: #ffffff; border: 1px solid #b83280; font-size: 10px; padding: 3px 6px; border-radius: 3px; font-weight: bold;")
    btn_buy_fc.clicked.connect(lambda: win._buy_shop_familiar_cube(1))
    rf_lay_c.addWidget(btn_buy_fc)

    cb_lay.addWidget(row_fam_c)
    win.shop_layout.addWidget(cube_box)

    # 4. 🐾 寵物與專屬裝備專賣店
    from pet_system import BASIC_PET_SHOP_CATALOG, PET_EQUIP_CATALOG, LUNA_PET_EQUIP_CATALOG
    pet_box = QFrame()
    pet_box.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
    pet_box.setStyleSheet("background-color: #161c28; border: 1px solid #319795; border-radius: 6px; padding: 8px;")
    pb_lay = QVBoxLayout(pet_box)
    pb_lay.setSpacing(6)
    pb_lay.addWidget(QLabel("<b style='color: #4fd1c5; font-size: 13px;'>🐾 寵物與專屬裝備專賣店 (基本寵物 · 飾品 · 卷軸)</b>"))

    # 4.1 基本寵物
    for p_id, p_info in BASIC_PET_SHOP_CATALOG.items():
        row_p = QFrame()
        row_p.setStyleSheet("background-color: #11141e; border: 1px solid #232a3b; border-radius: 4px; padding: 4px;")
        rp_lay = QHBoxLayout(row_p)
        rp_lay.setContentsMargins(6, 4, 6, 4)

        has_pet = any(p.pet_id == p_id for p in win.player.pet_manager.pets) if hasattr(win.player, "pet_manager") else False
        p_tag = "<span style='color: #68d391; font-size: 10px;'>[已擁有]</span>" if has_pet else ""
        lbl_p = QLabel(f"<b style='color: #81e6d9; font-size: 11px;'>【{p_info['name']}】</b> {p_tag} "
                       f"<span style='color: #a0aec0; font-size: 10px;'>自動喝水(閾值{int(p_info['auto_hp']*100)}%) | 飾品攻+{p_info['equip_atk']}</span>")
        rp_lay.addWidget(lbl_p)
        rp_lay.addStretch()

        btn_buy_p = QPushButton(f"購買 (${p_info['cost']:,})")
        btn_buy_p.setStyleSheet("background-color: #234e52; color: #e6fffa; border: 1px solid #38b2ac; font-size: 10px; padding: 3px 6px; border-radius: 3px; font-weight: bold;")
        btn_buy_p.clicked.connect(lambda _, pk=p_id: win._buy_shop_basic_pet(pk))
        rp_lay.addWidget(btn_buy_p)
        pb_lay.addWidget(row_p)

    # 4.2 一般寵物裝備
    for eq_id, eq_info in PET_EQUIP_CATALOG.items():
        row_e = QFrame()
        row_e.setStyleSheet("background-color: #11141e; border: 1px solid #232a3b; border-radius: 4px; padding: 4px;")
        re_lay = QHBoxLayout(row_e)
        re_lay.setContentsMargins(6, 4, 6, 4)

        lbl_e = QLabel(f"<b style='color: #f6ad55; font-size: 11px;'>🎀【{eq_info['name']}】</b> "
                       f"<span style='color: #a0aec0; font-size: 10px;'>{eq_info['desc']}</span>")
        re_lay.addWidget(lbl_e)
        re_lay.addStretch()

        btn_buy_e = QPushButton(f"購買並裝備 (${eq_info['cost']:,})")
        btn_buy_e.setStyleSheet("background-color: #744210; color: #fffff0; border: 1px solid #d69e2e; font-size: 10px; padding: 3px 6px; border-radius: 3px;")
        btn_buy_e.clicked.connect(lambda _, ek=eq_id: win._buy_shop_pet_equip(ek))
        re_lay.addWidget(btn_buy_e)
        pb_lay.addWidget(row_e)

    # 4.3 月光小寵物 (P寵) 專屬神裝
    for eq_id, eq_info in LUNA_PET_EQUIP_CATALOG.items():
        row_le = QFrame()
        row_le.setStyleSheet("background-color: #1a162b; border: 1px solid #9f7aea; border-radius: 4px; padding: 4px;")
        rle_lay = QHBoxLayout(row_le)
        rle_lay.setContentsMargins(6, 4, 6, 4)

        lbl_le = QLabel(f"<b style='color: #b794f4; font-size: 11px;'>✨【{eq_info['name']}】</b> "
                        f"<span style='color: #cbd5e1; font-size: 10px;'>{eq_info['desc']}</span>")
        rle_lay.addWidget(lbl_le)
        rle_lay.addStretch()

        btn_buy_le = QPushButton(f"購買裝備 (${eq_info['cost']:,})")
        btn_buy_le.setStyleSheet("background-color: #553c9a; color: #faf5ff; border: 1px solid #b794f4; font-size: 10px; padding: 3px 6px; border-radius: 3px; font-weight: bold;")
        btn_buy_le.clicked.connect(lambda _, ek=eq_id: win._buy_shop_pet_equip(ek))
        rle_lay.addWidget(btn_buy_le)
        pb_lay.addWidget(row_le)

    # 4.3 寵物衝卷
    row_ps = QFrame()
    row_ps.setStyleSheet("background-color: #11141e; border: 1px solid #232a3b; border-radius: 4px; padding: 4px;")
    rps_lay = QHBoxLayout(row_ps)
    rps_lay.setContentsMargins(6, 4, 6, 4)
    lbl_ps = QLabel("<b style='color: #cbd5e0; font-size: 11px;'>📜【寵物飾品攻擊卷軸 100%】</b> "
                    "<span style='color: #a0aec0; font-size: 10px;'>為出戰寵物裝備注入 +3 攻擊力</span>")
    rps_lay.addWidget(lbl_ps)
    rps_lay.addStretch()

    btn_buy_ps = QPushButton("購買並強化 ($50,000)")
    btn_buy_ps.setStyleSheet("background-color: #2b6cb0; color: #ffffff; border: 1px solid #4299e1; font-size: 10px; padding: 3px 6px; border-radius: 3px;")
    btn_buy_ps.clicked.connect(win._buy_shop_pet_scroll)
    rps_lay.addWidget(btn_buy_ps)
    pb_lay.addWidget(row_ps)

    win.shop_layout.addWidget(pet_box)
