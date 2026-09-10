"""
新楓之谷：放置遠征隊 - 右欄面板模組 (right_column.py)
包含三模式切換 (隊伍職業、轉蛋屋/商城、符文/符號系統)、技能配置，以及底部智慧加點

「轉蛋屋/商店」與「符文/符號系統」兩大模式的 UI 建構與刷新已分別拆至
right_column_shop.py / right_column_symbols.py，本檔只保留三模式切換的
外殼、隊伍職業選擇、技能配置與底部加點面板。
"""

from PySide6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QPushButton,
    QScrollArea, QTabWidget, QWidget
)
from classes import (
    EXPLORER_CLASSES, CYGNUS_CLASSES, RESISTANCE_CLASSES, ALL_CLASSES
)
from combat_system import get_skill_priority
from ui_panels.right_column_shop import render_shop_content as _render_shop_content
from ui_panels.right_column_symbols import (
    build_symbol_ui_structure as _build_symbol_ui_structure,
    render_symbol_content as _render_symbol_content,
)
from ui_dialogs import SpecialSystemsDialog


def build_right_column(win) -> QFrame:
    """建構右欄 UI (包含三模式切換：隊伍職業 vs 轉蛋屋/商店 vs 符文/符號系統)"""
    col = QFrame()
    col.setStyleSheet("background-color: #141824; border: 1px solid #2a3447; border-radius: 6px;")
    layout = QVBoxLayout(col)
    layout.setContentsMargins(8, 8, 8, 8)
    layout.setSpacing(6)

    # 1. 最頂部三大模式切換列：[⚔️ 隊伍職業] vs [🏪 轉蛋屋/商店] vs [🔮 符文/符號系統]
    win.right_mode = getattr(win, "right_mode", "team")
    mode_bar = QWidget()
    mb_lay = QHBoxLayout(mode_bar)
    mb_lay.setContentsMargins(0, 0, 0, 0)
    mb_lay.setSpacing(4)

    win.btn_mode_team = QPushButton("⚔️ 隊伍職業")
    win.btn_mode_team.clicked.connect(lambda: win._switch_right_mode("team"))
    mb_lay.addWidget(win.btn_mode_team)

    win.btn_mode_shop = QPushButton("🏪 轉蛋屋/商店")
    win.btn_mode_shop.clicked.connect(lambda: win._switch_right_mode("shop"))
    mb_lay.addWidget(win.btn_mode_shop)

    win.btn_mode_symbol = QPushButton("🔮 符文/符號系統")
    win.btn_mode_symbol.clicked.connect(lambda: win._switch_right_mode("symbol"))
    mb_lay.addWidget(win.btn_mode_symbol)

    win.btn_mode_special = QPushButton("✨ 內潛/寵物/萌獸")
    win.btn_mode_special.setStyleSheet("background-color: #553c9a; color: #fbd38d; font-weight: bold;")
    win.btn_mode_special.clicked.connect(lambda: SpecialSystemsDialog(win.player, sound_mgr=win.sound_mgr, parent=win).exec())
    mb_lay.addWidget(win.btn_mode_special)

    layout.addWidget(mode_bar)

    # 2. 隊伍席位頁籤切換：7 席位 (主角 + 6 隨行夥伴)
    win.class_faction_filter = getattr(win, "class_faction_filter", "all")
    win.tab_widget = QTabWidget()
    win.tab_widget.addTab(QWidget(), "👑 主角")
    for i in range(1, 7):
        win.tab_widget.addTab(QWidget(), f"夥伴{i}")
    win.tab_widget.currentChanged.connect(win._on_tab_changed)
    layout.addWidget(win.tab_widget)

    # 3. 內容滾動區
    scroll = QScrollArea()
    win.right_scroll = scroll
    scroll.setWidgetResizable(True)
    scroll.setStyleSheet("border: none; background-color: transparent;")
    win.right_content_area = QWidget()
    win.right_content_layout = QVBoxLayout(win.right_content_area)
    win.right_content_layout.setContentsMargins(2, 2, 2, 2)
    win.right_content_layout.setSpacing(6)

    # A. 陣營快速篩選列 (全部 / 冒險家 / 皇家 / 反抗軍)
    win.faction_filter_box = QWidget()
    ff_layout = QHBoxLayout(win.faction_filter_box)
    ff_layout.setContentsMargins(0, 0, 0, 0)
    ff_layout.setSpacing(4)
    win.filter_btns = {}
    for fid, f_name in [("all", "全部 (24)"), ("explorer", "冒險家 (15)"), ("cygnus", "皇家 (5)"), ("resistance", "反抗軍 (4)")]:
        fb = QPushButton(f_name)
        fb.setStyleSheet("background-color: #1e2535; color: #cbd5e1; border: 1px solid #2d3748; padding: 4px 6px; font-size: 11px;")
        fb.clicked.connect(lambda _, f=fid: win._set_class_filter(f))
        win.filter_btns[fid] = fb
        ff_layout.addWidget(fb)
    win.right_content_layout.addWidget(win.faction_filter_box)

    # B. 職業選擇網格容器
    win.class_grid_container = QWidget()
    win.class_grid_layout = QGridLayout(win.class_grid_container)
    win.class_grid_layout.setSpacing(4)
    win.class_grid_layout.setContentsMargins(0, 0, 0, 0)
    win.right_content_layout.addWidget(win.class_grid_container)

    # C. 技能自選配置容器
    win.lbl_skill_title = QLabel("<b>【技能庫配置】 (全技能解鎖就緒):</b>")
    win.lbl_skill_title.setStyleSheet("color: #f6ad55; font-size: 12px;")
    win.right_content_layout.addWidget(win.lbl_skill_title)

    win.skill_cards_container = QWidget()
    win.sc_layout = QVBoxLayout(win.skill_cards_container)
    win.sc_layout.setContentsMargins(0, 0, 0, 0)
    win.sc_layout.setSpacing(4)
    win.right_content_layout.addWidget(win.skill_cards_container)

    # D. 商店與轉蛋屋專用容器
    win.shop_container = QWidget()
    win.shop_layout = QVBoxLayout(win.shop_container)
    win.shop_layout.setContentsMargins(0, 0, 0, 0)
    win.shop_layout.setSpacing(8)
    win.right_content_layout.addWidget(win.shop_container)

    # E. 秘法與真實符號系統 (符文系統) 專用容器
    win.symbol_container = QWidget()
    win.symbol_layout = QVBoxLayout(win.symbol_container)
    win.symbol_layout.setContentsMargins(0, 0, 0, 0)
    win.symbol_layout.setSpacing(6)
    _build_symbol_ui_structure(win)
    win.right_content_layout.addWidget(win.symbol_container)

    win.right_content_layout.addStretch()
    scroll.setWidget(win.right_content_area)
    layout.addWidget(scroll, stretch=1)

    # 4. 右下常駐智慧加點面板 (整合一鍵全點/均衡/防禦，並為四屬性添加詳細 Tooltip 懸停說明)
    win.stat_quick_box = QWidget()
    win.stat_quick_box.setStyleSheet("background-color: #171c28; border: 1px solid #ffd700; border-radius: 6px; padding: 6px;")
    sq_layout = QVBoxLayout(win.stat_quick_box)
    sq_layout.setContentsMargins(6, 6, 6, 6)
    sq_layout.setSpacing(5)

    win.lbl_free_points = QLabel(f"<b>【遠征共用加點】 (剩餘: {win.player.free_points} 點)</b>")
    win.lbl_free_points.setStyleSheet("color: #ffd700; font-size: 12px;")
    sq_layout.addWidget(win.lbl_free_points)

    # 一鍵智慧極速加點列
    smart_row = QHBoxLayout()
    smart_row.setSpacing(4)

    win.btn_quick_atk = QPushButton("⚡ 全點攻擊")
    win.btn_quick_atk.setToolTip("【全點攻擊】將所有未分配點數全部投入【攻擊】，極致提升隊伍傷害輸出！")
    win.btn_quick_atk.setStyleSheet("background-color: #c53030; color: #fff5f5; border: 1px solid #e53e3e; padding: 4px 6px; font-weight: bold; font-size: 11px; border-radius: 3px;")
    win.btn_quick_atk.clicked.connect(lambda: win._auto_alloc("all_atk"))
    smart_row.addWidget(win.btn_quick_atk)

    win.btn_quick_bal = QPushButton("⚖ 均衡分配")
    win.btn_quick_bal.setToolTip("【均衡分配】平均分配所有未分配點數至攻擊、防禦、生命、技巧！")
    win.btn_quick_bal.setStyleSheet("background-color: #2b6cb0; color: #ebf8ff; border: 1px solid #4299e1; padding: 4px 6px; font-weight: bold; font-size: 11px; border-radius: 3px;")
    win.btn_quick_bal.clicked.connect(lambda: win._auto_alloc("balanced"))
    smart_row.addWidget(win.btn_quick_bal)

    win.btn_quick_def = QPushButton("🛡 生存防禦")
    win.btn_quick_def.setToolTip("【生存防禦】優先將未分配點數平均分配給【生命】與【防禦】，大幅強化隊伍生存續航！")
    win.btn_quick_def.setStyleSheet("background-color: #234e52; color: #e6fffa; border: 1px solid #319795; padding: 4px 6px; font-weight: bold; font-size: 11px; border-radius: 3px;")
    win.btn_quick_def.clicked.connect(lambda: win._auto_alloc("defensive"))
    smart_row.addWidget(win.btn_quick_def)

    sq_layout.addLayout(smart_row)

    # 四項屬性加點按鈕列 (附帶懸停 Tooltip 作用說明)
    pt_btns_layout = QHBoxLayout()
    pt_btns_layout.setSpacing(4)
    win.stat_add_btns = {}

    stat_configs = [
        ("atk", "攻擊", "【攻擊 +1】\n作用：增加隊伍全體基礎傷害（+3.6 / 點），全隊享有各職業專精乘數加成。"),
        ("def", "防禦", "【防禦 +1】\n作用：增加隊伍全體防禦力（+1.8 / 點），大幅減免受到的怪物傷害。"),
        ("hp", "生命", "【生命 +1】\n作用：增加隊伍全體最大生命上限（+22 HP / 點），強化生存續航。"),
        ("crit", "技巧", "【技巧 +1】\n作用：提升全隊暴擊率（+0.5% / 點），並同時縮短全體隊員攻擊間隔（大幅提升攻擊速度！）。")
    ]

    for stat_k, s_cn, tooltip_txt in stat_configs:
        b = QPushButton(f"{s_cn} +1")
        b.setToolTip(tooltip_txt)
        b.setStyleSheet("background-color: #1e293b; color: #e2e8f0; border: 1px solid #334155; padding: 5px 2px; font-size: 11px; font-weight: bold; border-radius: 3px;")
        b.clicked.connect(lambda _, k=stat_k: win._add_stat(k))
        win.stat_add_btns[stat_k] = b
        pt_btns_layout.addWidget(b)

    sq_layout.addLayout(pt_btns_layout)
    layout.addWidget(win.stat_quick_box)

    return col


def update_right_column(win, force=False):
    """即時更新右欄加點面板與動態狀態（附帶狀態比對快取）"""
    cur_mode = getattr(win, "right_mode", "team")

    # 1. 常駐遠征共用加點面板更新
    pts_state = (
        win.player.free_points,
        win.player.stat_atk,
        win.player.stat_def,
        win.player.stat_hp,
        win.player.stat_crit,
    )
    if force or pts_state != getattr(win, "_last_right_state", None):
        win._last_right_state = pts_state
        has_pts = (win.player.free_points > 0)
        if hasattr(win, "lbl_free_points"):
            win.lbl_free_points.setText(
                f"<b>【遠征共用加點】 (剩餘: {win.player.free_points} 點)</b> "
                f"<span style='font-size: 10px; color: #a0aec0;'>[攻:{win.player.stat_atk} 防:{win.player.stat_def} 生:{win.player.stat_hp} 技:{win.player.stat_crit}]</span>"
            )
        if hasattr(win, "btn_quick_atk"):
            win.btn_quick_atk.setEnabled(has_pts)
        if hasattr(win, "btn_quick_bal"):
            win.btn_quick_bal.setEnabled(has_pts)
        if hasattr(win, "btn_quick_def"):
            win.btn_quick_def.setEnabled(has_pts)
        if hasattr(win, "stat_add_btns"):
            for k in ["atk", "def", "hp", "crit"]:
                if k in win.stat_add_btns:
                    win.stat_add_btns[k].setEnabled(has_pts)

    # 2. 符文/符號系統即時自動刷新 (比照加點系統，戰鬥中掉落碎片、升級或金幣增加時自動更新卡片與按鈕)
    if cur_mode == "symbol" and hasattr(win, "symbol_ui_items") and win.symbol_ui_items:
        sym_state = (
            win.player.gold,
            tuple(sorted(win.player.arc_symbols.items())),
            tuple(sorted(win.player.aut_symbols.items())),
            tuple(sorted(win.player.symbol_fragments.items())),
        )
        if force or sym_state != getattr(win, "_last_symbol_state", None):
            win._last_symbol_state = sym_state
            _render_symbol_content(win)



def refresh_right_panel(win):
    """刷新右欄面板內容（支援隊伍配置模式、商店轉蛋模式、符文系統切換）"""
    cur_mode = getattr(win, "right_mode", "team")

    # 1. 更新頂部模式按鈕外觀
    modes = [("team", win.btn_mode_team, "#2b4c7e", "#ffd700"),
             ("shop", win.btn_mode_shop, "#b7791f", "#ecc94b"),
             ("symbol", win.btn_mode_symbol, "#553c9a", "#d6bcfa")]

    for m_key, btn, bg_active, border_active in modes:
        if cur_mode == m_key:
            btn.setStyleSheet(f"background-color: {bg_active}; color: #ffffff; border: 1.5px solid {border_active}; font-weight: bold; border-radius: 4px; padding: 5px; font-size: 11px;")
        else:
            btn.setStyleSheet("background-color: #1e2535; color: #cbd5e1; border: 1px solid #2d3748; border-radius: 4px; padding: 5px; font-size: 11px;")

    # 2. 更新快速加點面板
    update_right_column(win, force=True)

    # 3. 根據當前模式切換可視容器
    if cur_mode == "shop":
        win.tab_widget.setVisible(False)
        win.faction_filter_box.setVisible(False)
        win.class_grid_container.setVisible(False)
        win.lbl_skill_title.setVisible(False)
        win.skill_cards_container.setVisible(False)
        win.symbol_container.setVisible(False)
        win.shop_container.setVisible(True)
        _render_shop_content(win)
        return
    elif cur_mode == "symbol":
        win.tab_widget.setVisible(False)
        win.faction_filter_box.setVisible(False)
        win.class_grid_container.setVisible(False)
        win.lbl_skill_title.setVisible(False)
        win.skill_cards_container.setVisible(False)
        win.shop_container.setVisible(False)
        win.symbol_container.setVisible(True)
        _render_symbol_content(win)
        return
    else: # team
        win.tab_widget.setVisible(True)
        win.faction_filter_box.setVisible(True)
        win.class_grid_container.setVisible(True)
        win.lbl_skill_title.setVisible(True)
        win.skill_cards_container.setVisible(True)
        win.shop_container.setVisible(False)
        win.symbol_container.setVisible(False)

    # 清理隊伍容器內的舊元件
    while win.class_grid_layout.count() > 0:
        child = win.class_grid_layout.takeAt(0)
        if child.widget():
            child.widget().deleteLater()

    while win.sc_layout.count() > 0:
        child = win.sc_layout.takeAt(0)
        if child.widget():
            child.widget().deleteLater()

    if 0 <= win.current_tab_slot < len(win.player.team):
        slot_idx = win.current_tab_slot
        member = win.player.team[slot_idx]
        cur_cls_id = member.class_id

        # 更新陣營篩選按鈕樣式
        for fid, btn in win.filter_btns.items():
            if fid == win.class_faction_filter:
                btn.setStyleSheet("background-color: #2b4c7e; color: #ffd700; border: 1.5px solid #ffd700; font-weight: bold; padding: 4px 6px; font-size: 11px;")
            else:
                btn.setStyleSheet("background-color: #1e2535; color: #cbd5e1; border: 1px solid #2d3748; padding: 4px 6px; font-size: 11px;")

        if win.class_faction_filter == "explorer":
            cls_list = list(EXPLORER_CLASSES.values())
        elif win.class_faction_filter == "cygnus":
            cls_list = list(CYGNUS_CLASSES.values())
        elif win.class_faction_filter == "resistance":
            cls_list = list(RESISTANCE_CLASSES.values())
        else:
            cls_list = list(ALL_CLASSES.values())

        cols = 3
        for idx, c_data in enumerate(cls_list):
            row = idx // cols
            col = idx % cols
            is_cur = (cur_cls_id == c_data["id"])
            btn = QPushButton(f"{'★ ' if is_cur else ''}{c_data['name']}")
            if is_cur:
                btn.setStyleSheet("background-color: #2b6cb0; color: #ffd700; border: 1.5px solid #ffd700; font-weight: bold; font-size: 11px; padding: 4px 2px;")
            else:
                btn.setStyleSheet("background-color: #1e2535; color: #cbd5e1; border: 1px solid #2d3748; font-size: 11px; padding: 4px 2px;")
            btn.clicked.connect(lambda _, cid=c_data["id"]: win._switch_class(slot_idx, cid))
            win.class_grid_layout.addWidget(btn, row, col)

        # 渲染出戰技能庫
        c_info = ALL_CLASSES.get(cur_cls_id, {})
        skills = c_info.get("skills", [])
        active_skill_ids = {active_s.skill_id for active_s in member.get_active_skills()}

        role_label = "👑 核心主角" if slot_idx == 0 else f"夥伴 {slot_idx}"
        max_sk = member.max_skill_slots
        hint = " (點擊「🎯 技能配置」開啟跨職技能庫)" if slot_idx == 0 else ""
        win.lbl_skill_title.setText(f"<b>【{role_label}：{c_info.get('name', '')} 技能】 (出戰上限: {max_sk} 招，已選: {len(member.get_active_skills())}/{max_sk}){hint}:</b>")

        prio_map = {
            1: ("[團隊光狂]", "#38b2ac"),
            2: ("[極限爆發]", "#e53e3e"),
            3: ("[控場急救]", "#48bb78"),
            4: ("[多段打擊]", "#ecc94b"),
            5: ("[常規輸出]", "#a0aec0"),
        }

        for s_idx, s in enumerate(skills):
            is_eq = (s.skill_id in active_skill_ids)
            prio = get_skill_priority(s)
            priority_desc, p_color = prio_map.get(prio, ("[戰技]", "#a0aec0"))

            card = QFrame()
            card.setObjectName("card")
            card_border = "#ffd700" if is_eq else "#2d3748"
            card_bg = "#171f2d" if is_eq else "#141721"
            card.setStyleSheet(f"background-color: {card_bg}; border: 1px solid {card_border}; border-radius: 4px; padding: 4px;")

            c_lay = QVBoxLayout(card)
            c_lay.setContentsMargins(6, 4, 6, 4)
            c_lay.setSpacing(2)

            r1 = QHBoxLayout()
            lbl_type = QLabel(f"<b>{priority_desc}</b>")
            lbl_type.setStyleSheet(f"color: {p_color}; font-size: 10px;")
            r1.addWidget(lbl_type)

            lbl_sname = QLabel(f"<b>{s.name}</b>")
            lbl_sname.setStyleSheet("color: #e2e8f0; font-size: 11px;")
            r1.addWidget(lbl_sname)

            tag_badge = QLabel(f"{getattr(s, 'tag_name', '[技能]')}")
            tag_badge.setStyleSheet("color: #63b3ed; font-size: 9px; font-weight: bold;")
            r1.addWidget(tag_badge)

            cd_txt = f"CD {s.cooldown}s" if s.cooldown > 0 else "被動/普攻"
            lbl_cd = QLabel(cd_txt)
            lbl_cd.setStyleSheet("color: #a0aec0; font-size: 10px;")
            r1.addWidget(lbl_cd)
            r1.addStretch()

            btn_toggle = QPushButton("出戰中" if is_eq else "未上陣")
            btn_toggle.setFixedSize(56, 22)
            if is_eq:
                btn_toggle.setStyleSheet("background-color: #2b6cb0; color: #ffffff; border: 1px solid #4299e1; font-size: 10px; font-weight: bold;")
            else:
                btn_toggle.setStyleSheet("background-color: #2d3748; color: #a0aec0; border: 1px solid #4a5568; font-size: 10px;")
            btn_toggle.clicked.connect(lambda _, sk_id=s.skill_id: win._toggle_skill_by_id(slot_idx, sk_id) if hasattr(win, '_toggle_skill_by_id') else win._toggle_skill(slot_idx, s_idx))
            r1.addWidget(btn_toggle)
            c_lay.addLayout(r1)

            lbl_desc = QLabel(getattr(s, "desc", ""))
            lbl_desc.setStyleSheet("color: #cbd5e0; font-size: 10px;")
            lbl_desc.setWordWrap(True)
            c_lay.addWidget(lbl_desc)

            stats_preview = []
            if getattr(s, "dmg_mult", 0) > 0:
                stats_preview.append(f"威力: {int(s.dmg_mult * 100)}%")
            if getattr(s, "hit_count", 1) > 1:
                stats_preview.append(f"連擊: {s.hit_count} 連擊")
            if getattr(s, "lifesteal_bonus", 0) > 0:
                stats_preview.append(f"吸血: {int(s.lifesteal_bonus * 100)}%")
            if getattr(s, "shield_bonus", 0) > 0:
                stats_preview.append(f"護盾: +{s.shield_bonus}")
            if getattr(s, "buff_val", 0) > 0:
                stats_preview.append(f"全隊{getattr(s, 'buff_type', '')}: +{int(s.buff_val * 100)}% ({getattr(s, 'buff_duration', 0)}s)")
            if stats_preview:
                lbl_stat = QLabel(" | ".join(stats_preview))
                lbl_stat.setStyleSheet("color: #ecc94b; font-size: 10px; font-weight: bold;")
                c_lay.addWidget(lbl_stat)

            win.sc_layout.addWidget(card)


