"""
新楓之谷：放置遠征隊 - 潛能系統與艾比卷軸強化資料模組 (item_potential.py)
負責管理：
1. 潛能階級與顏色標籤 (POTENTIAL_RANKS, POTENTIAL_RANK_INFO)
2. 方塊消耗成本 (CUBE_COSTS)
3. 新楓之谷正統部位潛能池生成函式 (get_slot_potential_pool)
4. 台服艾比卷軸規格資料庫 (ABBY_SCROLLS - 極電/R/X/V/黑卷B)
"""

POTENTIAL_RANKS = ["rare", "epic", "unique", "legendary"]

POTENTIAL_RANK_INFO = {
    "rare": {"name": "特殊", "color": (66, 153, 225), "qcolor": "#4299e1"},
    "epic": {"name": "稀有", "color": (159, 122, 234), "qcolor": "#9f7aea"},
    "unique": {"name": "罕見", "color": (236, 201, 75), "qcolor": "#ecc94b"},
    "legendary": {"name": "傳奇", "color": (72, 187, 120), "qcolor": "#48bb78"},
}

CUBE_COSTS = {
    "mystic": 6000,          # 楓方塊 (洗主潛能至稀有 Epic)
    "bright": 30000,         # 閃耀方塊 (洗主潛能至傳奇 Legendary)
    "bonus_occult": 15000,   # 可疑附加方塊 (洗附加至稀有 Epic)
    "bonus_bright": 50000,   # 閃耀附加方塊 (洗附加至傳奇 Legendary)
}

# 部位分類集合
WSE_SLOTS = {"weapon", "sub_weapon", "sub_weapon1", "sub_weapon2", "sub_weapon3", "emblem", "badge"}
ACCESSORY_SLOTS = {"ring", "ring1", "ring2", "ring3", "ring4", "pendant", "pendant1", "pendant2", "face", "eye", "earrings", "belt", "pocket"}
ARMOR_SLOTS = {"top", "bottom", "shoes", "cape", "shoulder", "badge_chest", "armor"}

def get_slot_potential_pool(slot_or_cat: str, rank: str = "rare", is_bonus: bool = False) -> list:
    """
    依據新楓之谷官方部位嚴格限制生成潛能池：
    - 武器/副武器/能源/徽章 (WSE)：獨佔 攻擊力%、BOSS傷害%、無視防禦%、總傷害%
    - 手套 (gloves)：獨佔 暴擊傷害 (傳奇 8%, 罕見 6%)
    - 帽子 (hat)：獨佔 技能冷卻時間減少 (-1秒 / -2秒)
    - 飾品 (accessories)：獨佔 掉寶率 +20%、楓幣獲得量 +20%
    - 附加潛能 (Bonus Potential)：提供微型攻擊力%、全屬性、數值加成
    """
    s = str(slot_or_cat).lower() if slot_or_cat else "weapon"
    is_wse = (s in WSE_SLOTS)
    is_gloves = (s == "gloves")
    is_hat = (s == "hat")
    is_acc = (s in ACCESSORY_SLOTS)

    if not is_bonus:
        # ================= 主潛能 (Main Potential) =================
        if rank == "rare":
            pool = [
                {"name": "最大生命 +200", "stat": "hp_flat", "val": 200, "desc": "HP +200"},
                {"name": "防禦力 +25", "stat": "defense_flat", "val": 25, "desc": "防禦力 +25"},
                {"name": "全屬性 +5", "stat": "all_stat_flat", "val": 5, "desc": "全屬性 +5"},
            ]
            if is_wse:
                pool.extend([
                    {"name": "攻擊力 +3%", "stat": "attack_pct", "val": 0.03, "desc": "攻擊力 +3%"},
                    {"name": "總傷害 +3%", "stat": "damage_mult", "val": 0.03, "desc": "傷害 +3%"},
                    {"name": "暴擊率 +4%", "stat": "crit_chance", "val": 0.04, "desc": "暴擊率 +4%"},
                ])
            else:
                pool.extend([
                    {"name": "防禦力 +3%", "stat": "def_pct", "val": 0.03, "desc": "防禦力 +3%"},
                    {"name": "全屬性 +3", "stat": "all_stat_flat", "val": 3, "desc": "全屬性 +3"},
                ])
            return pool

        elif rank == "epic":
            pool = [
                {"name": "全屬性 +3%", "stat": "all_stat_pct", "val": 0.03, "desc": "全屬性 +3%"},
                {"name": "最大生命 +450", "stat": "hp_flat", "val": 450, "desc": "HP +450"},
                {"name": "防禦力 +50", "stat": "defense_flat", "val": 50, "desc": "防禦力 +50"},
            ]
            if is_wse:
                pool.extend([
                    {"name": "攻擊力 +6%", "stat": "attack_pct", "val": 0.06, "desc": "攻擊力 +6%"},
                    {"name": "總傷害 +6%", "stat": "damage_mult", "val": 0.06, "desc": "傷害 +6%"},
                    {"name": "暴擊率 +6%", "stat": "crit_chance", "val": 0.06, "desc": "暴擊率 +6%"},
                    {"name": "攻擊力 +20", "stat": "attack_flat", "val": 20, "desc": "攻擊力 +20"},
                ])
            elif is_gloves:
                pool.extend([
                    {"name": "暴擊率 +6%", "stat": "crit_chance", "val": 0.06, "desc": "暴擊率 +6%"},
                    {"name": "攻擊力 +15", "stat": "attack_flat", "val": 15, "desc": "攻擊力 +15"},
                    {"name": "攻擊速度 +0.05", "stat": "attack_speed", "val": 0.05, "desc": "攻速 +0.05"},
                ])
            elif is_acc:
                pool.extend([
                    {"name": "普攻吸血 +1.5%", "stat": "life_steal", "val": 0.015, "desc": "吸血 +1.5%"},
                    {"name": "攻擊力 +12", "stat": "attack_flat", "val": 12, "desc": "攻擊力 +12"},
                ])
            else:
                pool.extend([
                    {"name": "防禦力 +6%", "stat": "def_pct", "val": 0.06, "desc": "防禦力 +6%"},
                    {"name": "HP +6%", "stat": "hp_pct", "val": 0.06, "desc": "HP +6%"},
                ])
            return pool

        elif rank == "unique":
            pool = [
                {"name": "全屬性 +6%", "stat": "all_stat_pct", "val": 0.06, "desc": "全屬性 +6%"},
            ]
            if is_wse:
                pool.extend([
                    {"name": "攻擊力 +9%", "stat": "attack_pct", "val": 0.09, "desc": "攻擊力 +9%"},
                    {"name": "BOSS傷害 +30%", "stat": "boss_dmg", "val": 0.30, "desc": "BOSS傷害 +30%"},
                    {"name": "無視防禦 +15%", "stat": "def_ignore", "val": 0.15, "desc": "無視防禦 15%"},
                    {"name": "總傷害 +9%", "stat": "damage_mult", "val": 0.09, "desc": "總傷害 +9%"},
                    {"name": "暴擊率 +9%", "stat": "crit_chance", "val": 0.09, "desc": "暴擊率 +9%"},
                ])
            elif is_gloves:
                pool.extend([
                    {"name": "暴擊傷害 +6%", "stat": "crit_dmg", "val": 0.06, "desc": "暴擊傷害 +6%"},
                    {"name": "暴擊率 +9%", "stat": "crit_chance", "val": 0.09, "desc": "暴擊率 +9%"},
                    {"name": "攻擊速度 +0.08", "stat": "attack_speed", "val": 0.08, "desc": "攻速 +0.08"},
                    {"name": "攻擊力 +25", "stat": "attack_flat", "val": 25, "desc": "攻擊力 +25"},
                ])
            elif is_hat:
                pool.extend([
                    {"name": "技能冷卻時間 -1秒", "stat": "cooldown_reduction", "val": 1.0, "desc": "冷卻 -1秒"},
                    {"name": "HP +8%", "stat": "hp_pct", "val": 0.08, "desc": "HP +8%"},
                    {"name": "防禦力 +8%", "stat": "def_pct", "val": 0.08, "desc": "防禦力 +8%"},
                ])
            elif is_acc:
                pool.extend([
                    {"name": "掉寶率 +15%", "stat": "drop_rate", "val": 0.15, "desc": "掉寶率 +15%"},
                    {"name": "楓幣獲得量 +15%", "stat": "meso_rate", "val": 0.15, "desc": "楓幣獲得 +15%"},
                    {"name": "普攻吸血 +3.0%", "stat": "life_steal", "val": 0.03, "desc": "吸血 +3.0%"},
                    {"name": "攻擊力 +20", "stat": "attack_flat", "val": 20, "desc": "攻擊力 +20"},
                ])
            else:
                pool.extend([
                    {"name": "HP +8%", "stat": "hp_pct", "val": 0.08, "desc": "HP +8%"},
                    {"name": "防禦力 +8%", "stat": "def_pct", "val": 0.08, "desc": "防禦力 +8%"},
                    {"name": "攻擊速度 +0.06", "stat": "attack_speed", "val": 0.06, "desc": "攻速 +0.06"},
                ])
            return pool

        else: # legendary
            if is_wse:
                return [
                    {"name": "攻擊力 +12%", "stat": "attack_pct", "val": 0.12, "desc": "攻擊力 +12%"},
                    {"name": "攻擊力 +9%", "stat": "attack_pct", "val": 0.09, "desc": "攻擊力 +9%"},
                    {"name": "BOSS傷害 +40%", "stat": "boss_dmg", "val": 0.40, "desc": "BOSS傷害 +40%"},
                    {"name": "BOSS傷害 +35%", "stat": "boss_dmg", "val": 0.35, "desc": "BOSS傷害 +35%"},
                    {"name": "無視防禦 +35%", "stat": "def_ignore", "val": 0.35, "desc": "無視防禦 35%"},
                    {"name": "無視防禦 +30%", "stat": "def_ignore", "val": 0.30, "desc": "無視防禦 30%"},
                    {"name": "總傷害 +12%", "stat": "damage_mult", "val": 0.12, "desc": "總傷害 +12%"},
                    {"name": "全屬性 +9%", "stat": "all_stat_pct", "val": 0.09, "desc": "全屬性 +9%"},
                ]
            elif is_gloves:
                # 手套獨佔爆傷 8% (新楓之谷官方頂級詞條)
                return [
                    {"name": "暴擊傷害 +8%", "stat": "crit_dmg", "val": 0.08, "desc": "暴擊傷害 +8%"},
                    {"name": "全屬性 +9%", "stat": "all_stat_pct", "val": 0.09, "desc": "全屬性 +9%"},
                    {"name": "暴擊率 +10%", "stat": "crit_chance", "val": 0.10, "desc": "暴擊率 +10%"},
                    {"name": "攻擊速度 +0.12", "stat": "attack_speed", "val": 0.12, "desc": "攻速 +0.12"},
                    {"name": "攻擊力 +35", "stat": "attack_flat", "val": 35, "desc": "攻擊力 +35"},
                ]
            elif is_hat:
                return [
                    {"name": "技能冷卻時間 -2秒", "stat": "cooldown_reduction", "val": 2.0, "desc": "冷卻 -2秒"},
                    {"name": "技能冷卻時間 -1秒", "stat": "cooldown_reduction", "val": 1.0, "desc": "冷卻 -1秒"},
                    {"name": "全屬性 +9%", "stat": "all_stat_pct", "val": 0.09, "desc": "全屬性 +9%"},
                    {"name": "HP +12%", "stat": "hp_pct", "val": 0.12, "desc": "HP +12%"},
                    {"name": "防禦力 +12%", "stat": "def_pct", "val": 0.12, "desc": "防禦力 +12%"},
                ]
            elif is_acc:
                # 飾品獨佔掉寶 20%、楓幣 20%
                return [
                    {"name": "掉寶率 +20%", "stat": "drop_rate", "val": 0.20, "desc": "掉寶率 +20%"},
                    {"name": "楓幣獲得量 +20%", "stat": "meso_rate", "val": 0.20, "desc": "楓幣獲得 +20%"},
                    {"name": "全屬性 +9%", "stat": "all_stat_pct", "val": 0.09, "desc": "全屬性 +9%"},
                    {"name": "攻擊力 +30", "stat": "attack_flat", "val": 30, "desc": "攻擊力 +30"},
                    {"name": "普攻吸血 +5.0%", "stat": "life_steal", "val": 0.05, "desc": "吸血 +5.0%"},
                ]
            else:
                return [
                    {"name": "全屬性 +12%", "stat": "all_stat_pct", "val": 0.12, "desc": "全屬性 +12%"},
                    {"name": "全屬性 +9%", "stat": "all_stat_pct", "val": 0.09, "desc": "全屬性 +9%"},
                    {"name": "HP +12%", "stat": "hp_pct", "val": 0.12, "desc": "HP +12%"},
                    {"name": "防禦力 +12%", "stat": "def_pct", "val": 0.12, "desc": "防禦力 +12%"},
                    {"name": "攻擊力 +25", "stat": "attack_flat", "val": 25, "desc": "攻擊力 +25"},
                ]
    else:
        # ================= 附加潛能 (Bonus Potential) =================
        if rank == "rare":
            return [
                {"name": "[附加] 攻擊力 +10", "stat": "attack_flat", "val": 10, "desc": "攻擊力 +10"},
                {"name": "[附加] 最大生命 +150", "stat": "hp_flat", "val": 150, "desc": "HP +150"},
                {"name": "[附加] 全屬性 +4", "stat": "all_stat_flat", "val": 4, "desc": "全屬性 +4"},
                {"name": "[附加] 防禦力 +15", "stat": "defense_flat", "val": 15, "desc": "防禦力 +15"},
            ]
        elif rank == "epic":
            if is_wse:
                return [
                    {"name": "[附加] 攻擊力 +4%", "stat": "attack_pct", "val": 0.04, "desc": "攻擊力 +4%"},
                    {"name": "[附加] 攻擊力 +16", "stat": "attack_flat", "val": 16, "desc": "攻擊力 +16"},
                    {"name": "[附加] 暴擊率 +4%", "stat": "crit_chance", "val": 0.04, "desc": "暴擊率 +4%"},
                ]
            elif is_gloves:
                return [
                    {"name": "[附加] 暴擊傷害 +2%", "stat": "crit_dmg", "val": 0.02, "desc": "暴傷 +2%"},
                    {"name": "[附加] 攻擊力 +14", "stat": "attack_flat", "val": 14, "desc": "攻擊力 +14"},
                    {"name": "[附加] 全屬性 +2%", "stat": "all_stat_pct", "val": 0.02, "desc": "全屬性 +2%"},
                ]
            else:
                return [
                    {"name": "[附加] 全屬性 +2%", "stat": "all_stat_pct", "val": 0.02, "desc": "全屬性 +2%"},
                    {"name": "[附加] 攻擊力 +12", "stat": "attack_flat", "val": 12, "desc": "攻擊力 +12"},
                    {"name": "[附加] HP +300", "stat": "hp_flat", "val": 300, "desc": "HP +300"},
                ]
        elif rank == "unique":
            if is_wse:
                return [
                    {"name": "[附加] 攻擊力 +6%", "stat": "attack_pct", "val": 0.06, "desc": "攻擊力 +6%"},
                    {"name": "[附加] BOSS傷害 +12%", "stat": "boss_dmg", "val": 0.12, "desc": "BOSS傷害 +12%"},
                    {"name": "[附加] 無視防禦 +10%", "stat": "def_ignore", "val": 0.10, "desc": "無視防禦 10%"},
                    {"name": "[附加] 攻擊力 +22", "stat": "attack_flat", "val": 22, "desc": "攻擊力 +22"},
                ]
            elif is_gloves:
                return [
                    {"name": "[附加] 暴擊傷害 +3%", "stat": "crit_dmg", "val": 0.03, "desc": "暴傷 +3%"},
                    {"name": "[附加] 攻擊力 +18", "stat": "attack_flat", "val": 18, "desc": "攻擊力 +18"},
                    {"name": "[附加] 全屬性 +4%", "stat": "all_stat_pct", "val": 0.04, "desc": "全屬性 +4%"},
                ]
            else:
                return [
                    {"name": "[附加] 全屬性 +4%", "stat": "all_stat_pct", "val": 0.04, "desc": "全屬性 +4%"},
                    {"name": "[附加] 攻擊力 +16", "stat": "attack_flat", "val": 16, "desc": "攻擊力 +16"},
                    {"name": "[附加] HP +500", "stat": "hp_flat", "val": 500, "desc": "HP +500"},
                ]
        else: # legendary
            if is_wse:
                return [
                    {"name": "[附加] 攻擊力 +8%", "stat": "attack_pct", "val": 0.08, "desc": "攻擊力 +8%"},
                    {"name": "[附加] BOSS傷害 +18%", "stat": "boss_dmg", "val": 0.18, "desc": "BOSS傷害 +18%"},
                    {"name": "[附加] 無視防禦 +15%", "stat": "def_ignore", "val": 0.15, "desc": "無視防禦 15%"},
                    {"name": "[附加] 攻擊力 +30", "stat": "attack_flat", "val": 30, "desc": "攻擊力 +30"},
                ]
            elif is_gloves:
                return [
                    {"name": "[附加] 暴擊傷害 +4%", "stat": "crit_dmg", "val": 0.04, "desc": "暴傷 +4%"},
                    {"name": "[附加] 攻擊力 +25", "stat": "attack_flat", "val": 25, "desc": "攻擊力 +25"},
                    {"name": "[附加] 全屬性 +6%", "stat": "all_stat_pct", "val": 0.06, "desc": "全屬性 +6%"},
                ]
            elif is_acc:
                return [
                    {"name": "[附加] 掉寶率 +10%", "stat": "drop_rate", "val": 0.10, "desc": "掉寶率 +10%"},
                    {"name": "[附加] 楓幣獲得量 +10%", "stat": "meso_rate", "val": 0.10, "desc": "楓幣獲得 +10%"},
                    {"name": "[附加] 攻擊力 +22", "stat": "attack_flat", "val": 22, "desc": "攻擊力 +22"},
                    {"name": "[附加] 全屬性 +6%", "stat": "all_stat_pct", "val": 0.06, "desc": "全屬性 +6%"},
                ]
            else:
                return [
                    {"name": "[附加] 全屬性 +6%", "stat": "all_stat_pct", "val": 0.06, "desc": "全屬性 +6%"},
                    {"name": "[附加] 攻擊力 +20", "stat": "attack_flat", "val": 20, "desc": "攻擊力 +20"},
                    {"name": "[附加] HP +800", "stat": "hp_flat", "val": 800, "desc": "HP +800"},
                ]

# 相容舊版全域潛能池
POTENTIAL_POOLS = {
    "rare": get_slot_potential_pool("weapon", "rare"),
    "epic": get_slot_potential_pool("weapon", "epic"),
    "unique": get_slot_potential_pool("weapon", "unique"),
    "legendary": get_slot_potential_pool("weapon", "legendary"),
}

# =========================================================================
# 台服艾比卷軸強化體系 (TMS Abby Scrolls System)
# 各部位數值獨立計算：武器 (高攻擊力) vs 防具 (攻擊+生命) vs 飾品 (攻擊+屬性)
# =========================================================================
ABBY_SCROLLS = {
    "electric": {
        "id": "electric", "name": "極電卷軸", "color": (100, 200, 255), "rarity": "rare", "cost": 20000, "sell_price": 30000,
        "weapon": {"attack": 5, "all_stat": 3, "desc": "攻擊力 +5, 全屬性 +3"},
        "armor": {"attack": 3, "hp": 50, "all_stat": 2, "desc": "攻擊力 +3, HP +50, 全屬性 +2"},
        "acc": {"attack": 4, "all_stat": 3, "desc": "攻擊力 +4, 全屬性 +3"},
    },
    "R": {
        "id": "R", "name": "宿命R卷軸", "color": (255, 120, 180), "rarity": "rare", "cost": 50000, "sell_price": 80000,
        "weapon": {"attack": 7, "all_stat": 4, "desc": "攻擊力 +7, 全屬性 +4"},
        "armor": {"attack": 4, "hp": 100, "all_stat": 3, "desc": "攻擊力 +4, HP +100, 全屬性 +3"},
        "acc": {"attack": 5, "all_stat": 4, "desc": "攻擊力 +5, 全屬性 +4"},
    },
    "X": {
        "id": "X", "name": "X卷軸", "color": (255, 180, 50), "rarity": "epic", "cost": 120000,
        "weapon": {"attack": 10, "all_stat": 6, "desc": "攻擊力 +10, 全屬性 +6"},
        "armor": {"attack": 7, "hp": 180, "all_stat": 5, "desc": "攻擊力 +7, HP +180, 全屬性 +5"},
        "acc": {"attack": 8, "all_stat": 5, "desc": "攻擊力 +8, 全屬性 +5"},
    },
    "V": {
        "id": "V", "name": "V卷軸", "color": (180, 100, 255), "rarity": "unique", "cost": 250000,
        "weapon": {"attack": 12, "all_stat": 8, "desc": "攻擊力 +12, 全屬性 +8"},
        "armor": {"attack": 9, "hp": 250, "all_stat": 7, "desc": "攻擊力 +9, HP +250, 全屬性 +7"},
        "acc": {"attack": 10, "all_stat": 7, "desc": "攻擊力 +10, 全屬性 +7"},
    },
    "B": {
        "id": "B", "name": "黑卷(B卷)", "color": (255, 80, 80), "rarity": "legendary", "cost": 600000,
        "weapon": {"attack": 15, "all_stat": 10, "def_ignore": 0.03, "desc": "攻擊力 +15, 全屬性 +10, 無視防禦 +3%"},
        "armor": {"attack": 11, "hp": 350, "all_stat": 9, "desc": "攻擊力 +11, HP +350, 全屬性 +9"},
        "acc": {"attack": 12, "all_stat": 9, "crit_chance": 0.02, "desc": "攻擊力 +12, 全屬性 +9, 暴擊率 +2%"},
    },
    "innocence": {
        "id": "innocence", "name": "回真卷軸", "color": (140, 200, 255), "rarity": "rare", "cost": 100000,
        "is_innocence": True,
        "desc": "重置欄位的艾比卷軸強化次數與加成數值 (回歸 0/10 次)",
        "weapon": {"desc": "重置艾比卷軸衝卷次數 (回歸 0/10 次)"},
        "armor": {"desc": "重置艾比卷軸衝卷次數 (回歸 0/10 次)"},
        "acc": {"desc": "重置艾比卷軸衝卷次數 (回歸 0/10 次)"},
    }
}

