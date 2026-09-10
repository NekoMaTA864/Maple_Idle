"""
新楓之谷：放置遠征隊 - 中欄戰鬥與區域面板模組 (center_column.py)
"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QProgressBar, QComboBox, QSizePolicy
)
from combat_system import ZONES
from ui_arena import CombatArenaWidget


def build_center_column(win) -> QFrame:
    """建構中欄戰場與隊伍狀態 UI"""
    col = QFrame()
    col.setStyleSheet("background-color: #141824; border: 1px solid #2a3447; border-radius: 6px;")
    layout = QVBoxLayout(col)
    layout.setContentsMargins(10, 10, 10, 10)
    layout.setSpacing(6)

    # 1. 冒險區域與層數橫幅
    header_layout = QHBoxLayout()
    win.lbl_zone = QLabel("【弓箭手村森林】 第 1/10 層")
    win.lbl_zone.setMinimumWidth(0)
    win.lbl_zone.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Preferred)
    win.lbl_zone.setStyleSheet("color: #f6ad55; font-size: 14px; font-weight: bold;")
    header_layout.addWidget(win.lbl_zone)
    header_layout.addStretch()

    win.btn_prev_zone = QPushButton("<")
    win.btn_prev_zone.setFixedSize(28, 24)
    win.btn_prev_zone.setToolTip("切換至前一冒險區域")
    win.btn_prev_zone.clicked.connect(win._prev_zone)
    header_layout.addWidget(win.btn_prev_zone)

    win.combo_zone = QComboBox()
    win.combo_zone.setMinimumWidth(150)
    win.combo_zone.setMaximumWidth(220)
    win.combo_zone.setStyleSheet("background-color: #1a202c; color: #f6ad55; border: 1px solid #4a5568; font-size: 11px; padding: 2px;")
    win.combo_zone.currentIndexChanged.connect(win._on_combo_zone_changed)
    header_layout.addWidget(win.combo_zone)

    win.btn_next_zone = QPushButton(">")
    win.btn_next_zone.setFixedSize(28, 24)
    win.btn_next_zone.setToolTip("切換至下一冒險區域")
    win.btn_next_zone.clicked.connect(win._next_zone)
    header_layout.addWidget(win.btn_next_zone)

    win.btn_repeat_zone = QPushButton("🔄 推進模式")
    win.btn_repeat_zone.setCheckable(True)
    win.btn_repeat_zone.setToolTip("切換循環刷怪：開啟後擊破第 10 層首領後重置回第 1 層原地刷怪刷碎片；關閉則自動推進下一區")
    win.btn_repeat_zone.setStyleSheet("background-color: #1a202c; color: #a0aec0; border: 1px solid #4a5568; font-size: 11px; padding: 2px 8px; border-radius: 4px;")
    win.btn_repeat_zone.toggled.connect(win._on_toggle_repeat_zone)
    header_layout.addWidget(win.btn_repeat_zone)

    win.btn_training_dummy = QPushButton("木樁")
    win.btn_training_dummy.setToolTip("設定可重複重置的木樁，用來比較隊伍 DPS")
    win.btn_training_dummy.clicked.connect(win._open_training_dummy_dialog)
    header_layout.addWidget(win.btn_training_dummy)

    win.btn_gold_dungeon = QPushButton("💰 金庫")
    win.btn_gold_dungeon.setCheckable(True)
    win.btn_gold_dungeon.setToolTip("切換進入【黃金寶庫】金幣副本：無限刷取楓幣寶箱怪，不給經驗值，大量產出楓幣！")
    win.btn_gold_dungeon.setStyleSheet("background-color: #744210; color: #fbd38d; border: 1px solid #d69e2e; font-size: 11px; padding: 2px 6px; border-radius: 4px; font-weight: bold;")
    win.btn_gold_dungeon.toggled.connect(win._on_toggle_gold_dungeon)
    header_layout.addWidget(win.btn_gold_dungeon)

    layout.addLayout(header_layout)

    # 2. 怪物資訊卡 (精巧緊湊佈局，大幅壓縮 Y 軸高度至 56px)
    win.monster_frame = QFrame()
    win.monster_frame.setObjectName("card")
    win.monster_frame.setFixedHeight(56)
    mf_layout = QVBoxLayout(win.monster_frame)
    mf_layout.setContentsMargins(8, 4, 8, 4)
    mf_layout.setSpacing(2)

    m_top = QHBoxLayout()
    win.lbl_monster_name = QLabel("[怪物] 綠水靈 (Lv.1)")
    win.lbl_monster_name.setStyleSheet("color: #fc8181; font-weight: bold; font-size: 12px;")
    m_top.addWidget(win.lbl_monster_name)
    m_top.addStretch()

    win.lbl_monster_status = QLabel("")
    win.lbl_monster_status.setStyleSheet("color: #cbd5e0; font-size: 11px;")
    m_top.addWidget(win.lbl_monster_status)
    mf_layout.addLayout(m_top)

    win.bar_monster_hp = QProgressBar()
    win.bar_monster_hp.setFixedHeight(12)
    win.bar_monster_hp.setStyleSheet("QProgressBar::chunk { background-color: #e53e3e; }")
    mf_layout.addWidget(win.bar_monster_hp)

    win.bar_monster_spd = QProgressBar()
    win.bar_monster_spd.setFixedHeight(3)
    win.bar_monster_spd.setTextVisible(False)
    win.bar_monster_spd.setStyleSheet("QProgressBar::chunk { background-color: #d69e2e; }")
    mf_layout.addWidget(win.bar_monster_spd)

    layout.addWidget(win.monster_frame, 0)

    # 3. QPainter 戰鬥動態畫布 (垂直擴展佔滿中欄核心，支援震屏、白閃、全螢幕大招光幕、立體金邊暴擊跳字)
    win.arena_widget = CombatArenaWidget(win.combat_mgr, win)
    layout.addWidget(win.arena_widget, stretch=1)

    # 4. 隊伍狀態：上方核心主角狀態卡 (帶技能配置與夥伴編隊按鈕) + 下方 6 位隨行夥伴橫排
    # 4.1 👑 核心主角專屬狀態大卡
    hero_frame = QFrame()
    hero_frame.setObjectName("card")
    hero_frame.setStyleSheet("QFrame#card { background-color: #171f2d; border: 1.5px solid #d69e2e; border-radius: 6px; }")
    hero_layout = QVBoxLayout(hero_frame)
    hero_layout.setContentsMargins(10, 6, 10, 6)
    hero_layout.setSpacing(3)

    hero_top = QHBoxLayout()
    lbl_hero_name = QLabel("👑 核心主角：[英雄]")
    lbl_hero_name.setStyleSheet("color: #f6e05e; font-weight: bold; font-size: 13px;")
    hero_top.addWidget(lbl_hero_name)

    lbl_hero_stat = QLabel("攻:0 防:0")
    lbl_hero_stat.setStyleSheet("color: #cbd5e0; font-size: 11px;")
    hero_top.addWidget(lbl_hero_stat)
    hero_top.addStretch()

    btn_skill_deck = QPushButton("🎯 技能配置")
    btn_skill_deck.setToolTip("自選配置主角 6~12 個主動出戰技能 (母職業群技能庫)")
    btn_skill_deck.setStyleSheet("background-color: #2b6cb0; color: #bee3f8; border: 1px solid #63b3ed; font-size: 11px; padding: 2px 8px; border-radius: 4px; font-weight: bold;")
    btn_skill_deck.clicked.connect(lambda: win._open_skill_deck_dialog() if hasattr(win, '_open_skill_deck_dialog') else None)
    hero_top.addWidget(btn_skill_deck)

    btn_companions = QPushButton("👥 夥伴編隊")
    btn_companions.setToolTip("編配 6 位隨行夥伴並檢視 17 職戰地後援加成")
    btn_companions.setStyleSheet("background-color: #2c7a7b; color: #b2f5ea; border: 1px solid #4fd1c5; font-size: 11px; padding: 2px 8px; border-radius: 4px; font-weight: bold;")
    btn_companions.clicked.connect(lambda: win._open_companion_dialog() if hasattr(win, '_open_companion_dialog') else None)
    hero_top.addWidget(btn_companions)
    hero_layout.addLayout(hero_top)

    # 主角血條
    bar_hero_hp = QProgressBar()
    bar_hero_hp.setFixedHeight(12)
    bar_hero_hp.setStyleSheet("QProgressBar::chunk { background-color: #38a169; }")
    hero_layout.addWidget(bar_hero_hp)

    # 主角護盾條
    bar_hero_shield = QProgressBar()
    bar_hero_shield.setFixedHeight(3)
    bar_hero_shield.setTextVisible(False)
    bar_hero_shield.setStyleSheet("QProgressBar { background-color: rgba(30, 41, 59, 140); border: none; } QProgressBar::chunk { background-color: #38bdf8; }")
    hero_layout.addWidget(bar_hero_shield)

    # 攻速與狀態
    h_bot = QHBoxLayout()
    bar_hero_spd = QProgressBar()
    bar_hero_spd.setFixedHeight(3)
    bar_hero_spd.setTextVisible(False)
    bar_hero_spd.setStyleSheet("QProgressBar::chunk { background-color: #d69e2e; }")
    h_bot.addWidget(bar_hero_spd, 1)

    lbl_hero_status = QLabel("待命")
    lbl_hero_status.setStyleSheet("color: #68d391; font-size: 10px; font-weight: bold;")
    h_bot.addWidget(lbl_hero_status)
    hero_layout.addLayout(h_bot)

    layout.addWidget(hero_frame)

    win.team_card_widgets = [{
        "frame": hero_frame,
        "name": lbl_hero_name,
        "bar_hp": bar_hero_hp,
        "bar_shield": bar_hero_shield,
        "bar_spd": bar_hero_spd,
        "stat": lbl_hero_stat,
        "status": lbl_hero_status,
        "buffs": QLabel()
    }]

    # 4.2 ⚔️ 6 位隨行夥伴 (緊湊橫排 6 格)
    comp_layout = QHBoxLayout()
    comp_layout.setSpacing(4)
    slot_colors = ["#3182ce", "#805ad5", "#38a169", "#dd6b20", "#d69e2e", "#ed64a6"]

    for comp_i in range(1, 7):
        c_frame = QFrame()
        c_frame.setObjectName("card")
        c_frame.setStyleSheet("background-color: #151922; border: 1px solid #2a3447; border-radius: 5px;")
        c_frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        c_l = QVBoxLayout(c_frame)
        c_l.setContentsMargins(4, 3, 4, 3)
        c_l.setSpacing(2)

        lbl_c_name = QLabel(f"[{comp_i}] 夥伴")
        lbl_c_name.setAlignment(Qt.AlignCenter)
        lbl_c_name.setStyleSheet(f"color: {slot_colors[(comp_i-1) % len(slot_colors)]}; font-weight: bold; font-size: 10px;")
        c_l.addWidget(lbl_c_name)

        lbl_c_skills = QLabel("-")
        lbl_c_skills.setAlignment(Qt.AlignCenter)
        lbl_c_skills.setStyleSheet("color: #cbd5e0; font-size: 9px;")
        c_l.addWidget(lbl_c_skills)

        bar_c_spd = QProgressBar()
        bar_c_spd.setFixedHeight(2)
        bar_c_spd.setTextVisible(False)
        bar_c_spd.setStyleSheet("QProgressBar::chunk { background-color: #d69e2e; }")
        c_l.addWidget(bar_c_spd)

        lbl_c_status = QLabel("協戰中")
        lbl_c_status.setAlignment(Qt.AlignCenter)
        lbl_c_status.setStyleSheet("color: #718096; font-size: 9px;")
        c_l.addWidget(lbl_c_status)

        comp_layout.addWidget(c_frame, 1)
        win.team_card_widgets.append({
            "frame": c_frame,
            "name": lbl_c_name,
            "bar_hp": None,
            "bar_shield": None,
            "bar_spd": bar_c_spd,
            "stat": lbl_c_skills,
            "status": lbl_c_status,
            "buffs": QLabel()
        })

    layout.addLayout(comp_layout)
    return col


def update_center_column(win, force=False):
    """更新中欄戰場、怪物與隊伍狀態"""
    zone = win.combat_mgr.get_current_zone()
    m = win.combat_mgr.monster

    # 區域橫幅與下拉清單
    zone_state = (win.combat_mgr.current_zone_idx, win.combat_mgr.unlocked_zones, win.combat_mgr.current_floor, win.combat_mgr.is_boss_active)
    if force or zone_state != win._last_zone_state:
        win._last_zone_state = zone_state
        level_min, level_max = zone.get("level_range", (1, 1))
        level_text = f"推薦 Lv.{level_min}-{level_max}"
        player_level = getattr(win.player, "level", 1)
        if player_level < level_min:
            level_hint = "低於推薦等級"
            level_color = "#fc8181"
        elif player_level > level_max:
            level_hint = "已超過推薦等級"
            level_color = "#a0aec0"
        else:
            level_hint = "適合挑戰"
            level_color = "#68d391"
        zone_tip = (
            f"區域等級：Lv.{level_min}-{level_max}\n"
            f"目前遠征隊：Lv.{player_level}\n"
            f"狀態：{level_hint}\n"
            f"普通怪約 Lv.{min(level_max, level_min + 10)}-{level_max}\n"
            f"區域首領：Lv.{zone.get('boss', {}).get('lvl', level_max)}"
        )
        if win.combat_mgr.is_boss_active:
            boss_name = m.name if m else zone['boss']['name']
            boss_level = m.lvl if m else zone.get("boss", {}).get("lvl", level_max)
            win.lbl_zone.setText(
                f"[第 10/10 層首領試煉] {boss_name} Lv.{boss_level} ｜ {level_text}"
            )
            win.lbl_zone.setStyleSheet(f"color: {level_color}; font-size: 14px; font-weight: bold;")
        else:
            win.lbl_zone.setText(
                f"【{zone['name']}】 第 {win.combat_mgr.current_floor}/10 層 ｜ {level_text}"
            )
            win.lbl_zone.setStyleSheet(f"color: {level_color}; font-size: 14px; font-weight: bold;")
        win.lbl_zone.setToolTip(zone_tip)

        win.btn_prev_zone.setEnabled(win.combat_mgr.current_zone_idx > 0)
        win.btn_next_zone.setEnabled(win.combat_mgr.current_zone_idx + 1 < win.combat_mgr.unlocked_zones)

        cur_idx = win.combat_mgr.current_zone_idx
        unlocked = win.combat_mgr.unlocked_zones

        if win.combo_zone.count() != unlocked:
            win.combo_zone.blockSignals(True)
            win.combo_zone.clear()
            for i in range(unlocked):
                z = ZONES[i]
                prefix = f"[{i+1}/{len(ZONES)}]"
                req = ""
                if z.get("arc_req"):
                    req = f" (ARC {z['arc_req']})"
                elif z.get("aut_req"):
                    req = f" (AUT {z['aut_req']})"
                z_min, z_max = z.get("level_range", (1, 1))
                win.combo_zone.addItem(f"{prefix} {z['name']} (Lv.{z_min}-{z_max}){req}")
            win.combo_zone.setCurrentIndex(cur_idx)
            win.combo_zone.blockSignals(False)
        elif win.combo_zone.currentIndex() != cur_idx:
            win.combo_zone.blockSignals(True)
            win.combo_zone.setCurrentIndex(cur_idx)
            win.combo_zone.blockSignals(False)

    update_repeat_button_ui(win)

    # 怪物與波次狀態
    alive_monsters = [x for x in win.combat_mgr.monsters if x.is_alive]
    total_hp = sum(x.hp for x in win.combat_mgr.monsters)
    total_max_hp = sum(x.max_hp for x in win.combat_mgr.monsters)

    if win.combat_mgr.is_boss_active and m:
        win.lbl_monster_name.setText(f"[BOSS] {m.name} (Lv.{m.lvl})")
    elif len(win.combat_mgr.monsters) > 1:
        elite_tag = "【菁英試煉】" if any(getattr(x, 'is_elite', False) for x in win.combat_mgr.monsters) else ""
        win.lbl_monster_name.setText(f"[群怪波次] {elite_tag}在場小怪 ({len(alive_monsters)}/{len(win.combat_mgr.monsters)} 隻)")
    elif m:
        b_tag = "[菁英]" if getattr(m, 'is_elite', False) else "[怪物]"
        win.lbl_monster_name.setText(f"{b_tag} {m.name} (Lv.{m.lvl})")

    if m:
        status_tags = []
        if getattr(m, 'freeze_timer', 0) > 0:
            status_tags.append(f"[凍結 {m.freeze_timer:.1f}s]")
        if m.chill_timer > 0:
            status_tags.append("[減速]")
        if m.burn_timer > 0:
            status_tags.append("[灼燒]")
        if m.bleed_timer > 0:
            status_tags.append("[流血]")

        st_text = " ".join(status_tags) if status_tags else f"攻:{m.atk} 防:{m.defense}"
        win.lbl_monster_status.setText(st_text)

        win.bar_monster_hp.setMaximum(total_max_hp if total_max_hp > 0 else m.max_hp)
        win.bar_monster_hp.setValue(total_hp if total_max_hp > 0 else m.hp)
        win.bar_monster_hp.setFormat(f"{total_hp}/{total_max_hp}" if total_max_hp > 0 else f"{m.hp}/{m.max_hp}")

        win.bar_monster_spd.setMaximum(int(m.attack_speed * 100))
        win.bar_monster_spd.setValue(int(m.attack_timer * 100))

    # 7 位遠征隊員 (主角 + 6 位隨行夥伴)
    slot_colors = ["#3182ce", "#805ad5", "#38a169", "#dd6b20", "#d69e2e", "#ed64a6"]

    for idx, member in enumerate(win.player.team):
        if idx >= len(win.team_card_widgets):
            break
        c_widgets = win.team_card_widgets[idx]
        m_atk = member.get_attack(win.player)
        m_def = member.get_defense(win.player)
        atk_spd = member.get_attack_speed(win.player)
        ready_skill = next((s for s in member.get_active_skills() if s.is_ready and s.unlock_lvl <= win.player.level), None)

        if idx == 0:
            # 核心主角卡片
            c_widgets["name"].setText(f"👑 核心主角：[{member.name}] Lv.{win.player.level}")
            crit_rate = member.get_crit_chance(win.player) * 100
            c_widgets["stat"].setText(f"攻:{m_atk} 防:{m_def} 爆:{crit_rate:.0f}%")

            max_hp = member.get_max_hp(win.player)
            if c_widgets.get("bar_hp"):
                c_widgets["bar_hp"].setMaximum(max(1, max_hp))
                c_widgets["bar_hp"].setValue(int(member.current_hp))
                c_widgets["bar_hp"].setFormat(f"HP {int(member.current_hp)}/{max_hp}" if member.is_alive else "[戰敗待刷新]")

            sh_val = int(member.shield)
            if c_widgets.get("bar_shield"):
                c_widgets["bar_shield"].setMaximum(max(1, max_hp))
                c_widgets["bar_shield"].setValue(min(max_hp, sh_val))
                c_widgets["bar_shield"].setToolTip(f"【吸收護盾】{sh_val} / {max_hp}" if sh_val > 0 else "")

            if c_widgets.get("bar_spd"):
                c_widgets["bar_spd"].setMaximum(max(1, int(atk_spd * 100)))
                c_widgets["bar_spd"].setValue(int(member.attack_timer * 100))

            if not member.is_alive:
                c_widgets["status"].setText("隊伍戰敗")
                c_widgets["status"].setStyleSheet("color: #e53e3e; font-size: 10px; font-weight: bold;")
            elif ready_skill:
                c_widgets["status"].setText(f"準備: {ready_skill.name}")
                c_widgets["status"].setStyleSheet("color: #48bb78; font-size: 10px; font-weight: bold;")
            elif member.is_buffed:
                c_widgets["status"].setText("爆發中")
                c_widgets["status"].setStyleSheet("color: #ecc94b; font-size: 10px; font-weight: bold;")
            else:
                c_widgets["status"].setText("普攻蓄力")
                c_widgets["status"].setStyleSheet("color: #68d391; font-size: 10px;")
        else:
            # 隨行夥伴卡片 (不單獨承受傷害，共享主角血防生存)
            s_col = slot_colors[(idx - 1) % len(slot_colors)]
            c_widgets["name"].setText(f"<b style='color: {s_col};'>[{idx}]</b> {member.name}")

            active_skills = member.get_active_skills()
            sk_names = "/".join(s.name[:4] for s in active_skills) if active_skills else "普攻"
            c_widgets["stat"].setText(f"{sk_names}")

            if c_widgets.get("bar_spd"):
                c_widgets["bar_spd"].setMaximum(max(1, int(atk_spd * 100)))
                c_widgets["bar_spd"].setValue(int(member.attack_timer * 100))

            if not win.player.team[0].is_alive:
                c_widgets["status"].setText("待命")
                c_widgets["status"].setStyleSheet("color: #718096; font-size: 9px;")
            elif ready_skill:
                c_widgets["status"].setText(f"{ready_skill.name[:4]}")
                c_widgets["status"].setStyleSheet("color: #48bb78; font-size: 9px; font-weight: bold;")
            else:
                c_widgets["status"].setText("協戰")
                c_widgets["status"].setStyleSheet("color: #a0aec0; font-size: 9px;")


def update_repeat_button_ui(win):
    """同步循環刷怪按鈕狀態"""
    if not hasattr(win, 'btn_repeat_zone'):
        return
    is_repeat = getattr(win.combat_mgr, 'repeat_current_zone', False)
    win.btn_repeat_zone.blockSignals(True)
    win.btn_repeat_zone.setChecked(is_repeat)
    if is_repeat:
        win.btn_repeat_zone.setText("🔄 循環刷怪中")
        win.btn_repeat_zone.setStyleSheet("background-color: #2b6cb0; color: #ffffff; border: 1px solid #63b3ed; font-size: 11px; font-weight: bold; padding: 2px 8px; border-radius: 4px;")
    else:
        win.btn_repeat_zone.setText("🔄 推進模式")
        win.btn_repeat_zone.setStyleSheet("background-color: #1a202c; color: #a0aec0; border: 1px solid #4a5568; font-size: 11px; padding: 2px 8px; border-radius: 4px;")
    win.btn_repeat_zone.blockSignals(False)

