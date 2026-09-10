"""
新楓之谷：放置遠征隊 - 左欄面板模組 (left_column.py)
包含 5x5 正統裝備欄位、官方完整套裝效果展示區與 60 格行囊全覽按鈕
"""

from PySide6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QPushButton,
    QScrollArea, QWidget, QProgressBar
)
from PySide6.QtCore import Qt
from settings import INVENTORY_CAPACITY
from item_system import SLOT_NAMES


def build_left_column(win) -> QFrame:
    """建構左欄 UI"""
    col = QFrame()
    col.setStyleSheet("background-color: #141824; border: 1px solid #2a3447; border-radius: 6px;")
    layout = QVBoxLayout(col)
    layout.setContentsMargins(8, 8, 8, 8)
    layout.setSpacing(6)

    # 1. 楓之谷官方 5x5 精準格局裝備面板 (中央全列主副武徽章，共 25 個標準欄位)
    layout.addWidget(QLabel("<b style='color: #f6ad55; font-size: 12px;'>【新楓之谷裝備欄】 (全隊共享加成):</b>"))

    GRID_MAP = [
        [("ring1", "戒指1"), ("face", "臉飾"), ("weapon", "主武器"), ("hat", "帽子"), ("cape", "披風")],
        [("ring2", "戒指2"), ("eye", "眼飾"), ("sub_weapon1", "副武1(攻)"), ("top", "上衣"), ("gloves", "手套")],
        [("ring3", "戒指3"), ("earrings", "耳環"), ("sub_weapon2", "副武2(防)"), ("bottom", "褲子"), ("shoes", "鞋子")],
        [("ring4", "戒指4"), ("pendant1", "項鍊1"), ("sub_weapon3", "副武3(速)"), ("shoulder", "肩膀"), ("badge_chest", "胸章")],
        [("belt", "腰帶"), ("pendant2", "項鍊2"), ("badge", "徽章"), ("pocket", "口袋"), ("emblem", "能源核心")],
    ]

    grid_frame = QFrame()
    grid_frame.setStyleSheet("background-color: #10131d; border: 1px solid #232a3b; border-radius: 4px; padding: 2px;")
    grid_layout = QGridLayout(grid_frame)
    grid_layout.setSpacing(4)
    grid_layout.setContentsMargins(4, 4, 4, 4)

    win.equip_slot_buttons = {}

    for row_idx, row_slots in enumerate(GRID_MAP):
        for col_idx, slot_item in enumerate(row_slots):
            slot_id, slot_short = slot_item
            btn = QPushButton(slot_short)
            btn.setFixedSize(56, 46)
            btn.setStyleSheet("background-color: #171b26; border: 1px dashed #2d3748; color: #718096; font-size: 10px; border-radius: 4px;")
            btn.clicked.connect(lambda _, s=slot_id: win._on_equip_slot_clicked(s))
            grid_layout.addWidget(btn, row_idx, col_idx)
            win.equip_slot_buttons[slot_id] = btn

    layout.addWidget(grid_frame)

    # 1.2 裝備快捷操作列 (一鍵換裝)
    btn_auto_eq = QPushButton("⚡ 一鍵換裝")
    btn_auto_eq.setToolTip("自動搜尋背包與身上裝備，為 25 格各部位穿戴最高戰力神裝！")
    btn_auto_eq.setStyleSheet("background-color: #2b6cb0; color: #ebf8ff; border: 1px solid #4299e1; font-weight: bold; padding: 4px 6px; border-radius: 4px;")
    btn_auto_eq.clicked.connect(win._auto_equip_all)
    action_row = QHBoxLayout()
    action_row.addWidget(btn_auto_eq, 2)
    win.btn_set_bonus = QPushButton("🛡 套裝效果")
    win.btn_set_bonus.setToolTip("開啟彈窗查看目前穿戴套裝與下一階效果")
    win.btn_set_bonus.clicked.connect(win._open_set_bonus_dialog)
    win.btn_set_bonus.setStyleSheet("background-color: #4a3b1a; color: #ecc94b; border: 1px solid #b7791f; font-weight: bold; padding: 4px 6px; border-radius: 4px;")
    action_row.addWidget(win.btn_set_bonus, 1)
    layout.addLayout(action_row)

    # 1.3 固定戰鬥分析區，套裝詳情改由彈窗按需查看
    layout.addWidget(QLabel("<b style='color: #63b3ed; font-size: 12px;'>【戰鬥分析】</b>"))
    win.combat_stats_scroll = QScrollArea()
    win.combat_stats_scroll.setWidgetResizable(True)
    win.combat_stats_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
    win.combat_stats_scroll.setStyleSheet("background-color: #0d1117; border: 1px solid #21262d; border-radius: 4px;")
    stats_frame = QWidget()
    stats_layout = QVBoxLayout(stats_frame)
    stats_layout.setContentsMargins(6, 6, 6, 6)
    win.lbl_combat_stats = QLabel("戰鬥分析")
    win.lbl_combat_stats.setStyleSheet("color: #63b3ed; font-size: 11px; font-weight: bold;")
    stats_layout.addWidget(win.lbl_combat_stats)
    win.combat_stat_rows = []
    for idx in range(7):
        row = QFrame()
        row.setStyleSheet("background-color: #111722; border-bottom: 1px solid #2a3447; padding: 2px;")
        row_layout = QVBoxLayout(row)
        row_layout.setContentsMargins(4, 3, 4, 3)
        row_layout.setSpacing(1)
        name_prefix = "👑 主角" if idx == 0 else f"夥伴{idx}"
        name_label = QLabel(f"[{name_prefix}]")
        name_label.setStyleSheet("color: #ecc94b; font-size: 10px; font-weight: bold;")
        output_label = QLabel("輸出 0 (0%) · DPS 0")
        output_label.setStyleSheet("color: #e2e8f0; font-size: 9px;")
        output_bar = QProgressBar()
        output_bar.setRange(0, 100)
        output_bar.setValue(0)
        output_bar.setTextVisible(False)
        output_bar.setFixedHeight(6)
        output_bar.setStyleSheet("QProgressBar { background: #202938; border: none; } QProgressBar::chunk { background: #ed8936; }")
        support_label = QLabel("治療 0 (0%) · 護盾 0 (0%) · 承傷 0")
        support_label.setStyleSheet("color: #a0aec0; font-size: 9px;")
        support_bar = QProgressBar()
        support_bar.setRange(0, 100)
        support_bar.setValue(0)
        support_bar.setTextVisible(False)
        support_bar.setFixedHeight(5)
        support_bar.setStyleSheet("QProgressBar { background: #202938; border: none; } QProgressBar::chunk { background: #48bb78; }")
        row_layout.addWidget(name_label)
        row_layout.addWidget(output_label)
        row_layout.addWidget(output_bar)
        row_layout.addWidget(support_label)
        row_layout.addWidget(support_bar)
        stats_layout.addWidget(row)
        win.combat_stat_rows.append({
            "name": name_label,
            "output": output_label,
            "output_bar": output_bar,
            "support": support_label,
            "support_bar": support_bar,
        })
    stats_layout.addStretch()
    win.combat_stats_scroll.setWidget(stats_frame)
    layout.addWidget(win.combat_stats_scroll, stretch=1)

    # 2. 底部精巧行囊背包面板 (收納為快捷列，提供 60 格全覽彈窗與一鍵售劣)
    inv_bar = QFrame()
    inv_bar.setStyleSheet("background-color: #121722; border: 1px solid #283347; border-radius: 6px; padding: 4px;")
    inv_bar_layout = QVBoxLayout(inv_bar)
    inv_bar_layout.setContentsMargins(6, 6, 6, 6)
    inv_bar_layout.setSpacing(5)

    inv_top_row = QHBoxLayout()
    win.lbl_inv_title = QLabel(f"<b>🎒 冒險行囊 (0/{INVENTORY_CAPACITY} 格)</b>")
    win.lbl_inv_title.setStyleSheet("color: #e2e8f0; font-size: 11px;")
    inv_top_row.addWidget(win.lbl_inv_title)
    inv_top_row.addStretch()
    inv_bar_layout.addLayout(inv_top_row)

    inv_btn_row = QHBoxLayout()
    inv_btn_row.setSpacing(6)

    win.btn_open_inventory = QPushButton("🎒 打開背包 (60格全覽)")
    win.btn_open_inventory.setToolTip("以 60 格整齊網格彈窗瀏覽全部背包裝備，支援檢視、穿戴、強化、洗潛與綠鎖！")
    win.btn_open_inventory.setStyleSheet("background-color: #2b4c7e; color: #ffd700; border: 1.5px solid #ffd700; font-weight: bold; padding: 6px 8px; border-radius: 4px; font-size: 11px;")
    win.btn_open_inventory.clicked.connect(win._open_inventory_dialog)
    inv_btn_row.addWidget(win.btn_open_inventory, stretch=2)

    win.btn_sell_inf = QPushButton("💰 一鍵售劣")
    win.btn_sell_inf.setToolTip("自動檢索背包，出售數值低於目前身上穿戴的淘汰裝備 (自動保護綠鎖裝備)")
    win.btn_sell_inf.setStyleSheet("background-color: #744210; color: #feebc8; border: 1px solid #d69e2e; font-weight: bold; padding: 6px 8px; border-radius: 4px; font-size: 11px;")
    win.btn_sell_inf.clicked.connect(win._sell_inferior_gear)
    inv_btn_row.addWidget(win.btn_sell_inf, stretch=1)

    inv_bar_layout.addLayout(inv_btn_row)
    layout.addWidget(inv_bar)

    return col


POTENTIAL_THEME_COLORS = {
    "rare": {"name": "特殊", "color": "#3182ce", "bg": "#0e2442"},      # 藍-特殊
    "epic": {"name": "稀有", "color": "#9f7aea", "bg": "#271945"},      # 紫-稀有
    "unique": {"name": "罕見", "color": "#ed8936", "bg": "#3d1f0e"},    # 澄-罕見
    "legendary": {"name": "傳說", "color": "#48bb78", "bg": "#113520"}, # 綠-傳說
}


def update_left_column(win, force=False):
    """更新左欄裝備欄位與套裝狀態"""
    left_state = (
        tuple((
            k,
            id(win.player.equipped.get(k)),
            win.player.slot_enhancements.get(k, 0),
            win.player.slot_potentials.get(k, {}).get("main", {}).get("rank"),
            win.player.slot_potentials.get(k, {}).get("bonus", {}).get("rank"),
            win.player.slot_scrolls.get(k, {}).get("count", 0)
        ) for k in win.equip_slot_buttons),
        win.selected_forge_slot,
        win.player.gold,
        len(win.player.inventory),
        tuple((idx, stats.damage_dealt, stats.damage_taken, stats.healing_done, stats.shield_absorbed) for idx, stats in win.combat_mgr.combat_stats.members.items()),
    )
    if not force and left_state == getattr(win, "_last_left_state", None):
        return
    win._last_left_state = left_state

    # 1. 25 個標準裝備欄位按鈕：保持裝備名稱與星數，上半部呈現主潛顏色、下半部呈現附加潛能顏色
    for slot_k, btn in win.equip_slot_buttons.items():
        item = win.player.equipped.get(slot_k)
        slot_star = win.player.slot_enhancements.get(slot_k, 0)
        s_name = SLOT_NAMES.get(slot_k, slot_k)
        s_pots = win.player.slot_potentials.get(slot_k, {})
        main_rank = s_pots.get("main", {}).get("rank", "rare")
        bonus_rank = s_pots.get("bonus", {}).get("rank", "rare")

        m_theme = POTENTIAL_THEME_COLORS.get(main_rank, POTENTIAL_THEME_COLORS["rare"])
        b_theme = POTENTIAL_THEME_COLORS.get(bonus_rank, POTENTIAL_THEME_COLORS["rare"])

        m_col, m_bg = m_theme["color"], m_theme["bg"]
        b_col, b_bg = b_theme["color"], b_theme["bg"]
        m_name, b_name = m_theme["name"], b_theme["name"]

        star_prefix = f"★{slot_star} " if slot_star > 0 else ""
        if item:
            btn_text = f"{star_prefix}{item.base_name[:4]}"
            text_color = "#ffffff"
            font_weight = "bold"
        else:
            btn_text = f"{star_prefix}{s_name}"
            text_color = "#a0aec0"
            font_weight = "normal"

        btn.setText(btn_text)

        # 雙層線性漸層背景 (上半主潛色調 + 下半附加潛色調 + 對應上下邊框色)
        btn.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 {m_bg}, stop:0.48 {m_bg}, 
                    stop:0.49 #1a202c, stop:0.51 #1a202c,
                    stop:0.52 {b_bg}, stop:1 {b_bg});
                border-top: 2px solid {m_col};
                border-bottom: 2px solid {b_col};
                border-left: 1.5px solid {m_col};
                border-right: 1.5px solid {b_col};
                border-radius: 4px;
                color: {text_color};
                font-weight: {font_weight};
                font-size: 10px;
                padding: 2px;
            }}
            QPushButton:hover {{
                border: 2px solid #ffffff;
            }}
        """)

        # Tooltip 詳細資訊 (裝備/空欄、星力、主/附加潛能詞條、卷軸強化)
        main_lines = s_pots.get("main", {}).get("lines", [])
        bonus_lines = s_pots.get("bonus", {}).get("lines", [])
        main_lines_str = "、".join([line.get("desc", line.get("name", "")) for line in main_lines]) if main_lines else "無"
        bonus_lines_str = "、".join([line.get("desc", line.get("name", "")) for line in bonus_lines]) if bonus_lines else "無"
        sc_data = win.player.slot_scrolls.get(slot_k, {})
        sc_cnt = sc_data.get("count", 0)
        sc_max = sc_data.get("max_count", 10)

        if item:
            eff = item.get_effective_stats(star_level=slot_star, slot_potentials=s_pots, slot_scrolls=sc_data)
            stats_str = " | ".join([f"{k}:{v}" for k, v in eff.items()])
            btn.setToolTip(
                f"【{item.get_display_name(star_level=slot_star)}】\n"
                f"部位: {s_name} (欄位星力: ★{slot_star})\n"
                f"需求等級: Lv.{item.item_level}\n"
                f"🔮 主潛能 [{m_name}]: {main_lines_str}\n"
                f"✨ 附加潛能 [{b_name}]: {bonus_lines_str}\n"
                f"📜 艾比卷軸: {sc_cnt}/{sc_max} 次\n"
                f"屬性總計: {stats_str}\n"
                f"(點擊開啟詳細強化、洗潛、換裝與回真面板)"
            )
        else:
            btn.setToolTip(
                f"【{s_name}】(尚未穿戴神裝)\n"
                f"欄位星力: ★{slot_star}\n"
                f"🔮 主潛能 [{m_name}]: {main_lines_str}\n"
                f"✨ 附加潛能 [{b_name}]: {bonus_lines_str}\n"
                f"📜 艾比卷軸: {sc_cnt}/{sc_max} 次\n"
                f"(星力、潛能與卷軸為欄位永久加成，穿戴裝備後自動全額生效)"
            )

    # 2. 更新固定戰鬥分析摘要
    combat_stats = win.combat_mgr.combat_stats
    total_damage = max(1, combat_stats.total_damage)
    total_healing_value = sum(stats.healing_done for stats in combat_stats.members.values())
    total_healing = max(1, total_healing_value)
    total_shield_value = sum(stats.shield_granted for stats in combat_stats.members.values())
    total_shield = max(1, total_shield_value)
    win.lbl_combat_stats.setText(
        f"全隊 DPS {combat_stats.team_dps:,.1f} · 總傷害 {combat_stats.total_damage:,} · "
        f"戰鬥 {combat_stats.elapsed_seconds:.1f}s"
    )
    for idx, member in enumerate(win.player.team):
        if idx >= len(win.combat_stat_rows):
            break
        stats = combat_stats.for_member(idx)
        row = win.combat_stat_rows[idx]
        damage_pct = int(stats.damage_dealt * 100 / total_damage) if combat_stats.total_damage else 0
        healing_pct = int(stats.healing_done * 100 / total_healing) if total_healing_value else 0
        shield_pct = int(stats.shield_granted * 100 / total_shield) if total_shield_value else 0
        title_prefix = "👑 主角" if idx == 0 else f"夥伴{idx}"
        row["name"].setText(f"[{title_prefix}] {member.name}")
        row["output"].setText(
            f"輸出 {stats.damage_dealt:,} ({damage_pct}%) · DPS {combat_stats.member_dps(idx):,.1f} · "
            f"暴擊 {stats.critical_count}"
        )
        row["output_bar"].setValue(damage_pct)
        row["support"].setText(
            f"治療 {stats.healing_done:,} ({healing_pct}%) · 護盾 {stats.shield_granted:,} ({shield_pct}%) · "
            f"承傷 {stats.damage_taken:,}"
        )
        row["support_bar"].setValue(max(healing_pct, shield_pct))

    # 3. 更新背包摘要文字
    total_inv = len(win.player.inventory)
    win.lbl_inv_title.setText(f"<b>🎒 冒險行囊 ({total_inv}/{INVENTORY_CAPACITY} 格)</b>")


def rebuild_inventory_ui(win):
    """更新冒險行囊容量與狀態"""
    if hasattr(win, "lbl_inv_title") and hasattr(win, "player"):
        win.lbl_inv_title.setText(f"<b>🎒 冒險行囊 ({len(win.player.inventory)}/{INVENTORY_CAPACITY} 格)</b>")
    update_left_column(win, force=True)

