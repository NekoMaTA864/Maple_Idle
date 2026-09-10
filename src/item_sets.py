"""
新楓之谷：放置遠征隊 - 正統套裝資料與套裝加成計算模組 (item_sets.py)
負責管理：
1. 正統套裝定義庫 (SET_DEFINITIONS)
2. 裝備名稱與套裝映射表 (ITEM_SET_MAPPING)

純資料模組，不含邏輯函式；套裝啟用判定與屬性加總計算實際位於
player_stats.py 的 calc_active_sets() / calc_set_stat_sum()。
"""

# =========================================================================
# 官方正統套裝定義 (Canonical Set Definitions & Set Bonuses)
# =========================================================================
SET_DEFINITIONS = {
    "gollux_superior": {
        "id": "gollux_superior",
        "name": "頂級培羅德套裝",
        "color": (255, 185, 50),
        "tiers": {
            2: {"attack": 20, "defense": 100, "desc": "攻擊力 +20, 防禦力 +100"},
            3: {"attack": 30, "hp": 1500, "desc": "攻擊力 +30, HP +1500"},
            4: {"attack": 35, "boss_dmg": 0.30, "def_ignore": 0.30, "desc": "攻擊力 +35, BOSS傷害 +30%, 無視防禦 30%"},
        }
    },
    "pitched_boss": {
        "id": "pitched_boss",
        "name": "漆黑的Boss飾品套裝",
        "color": (230, 80, 255),
        "tiers": {
            2: {"attack": 10, "hp": 250, "boss_dmg": 0.10, "desc": "攻擊力 +10, HP +250, BOSS傷害 +10%"},
            3: {"attack": 10, "hp": 250, "def_ignore": 0.10, "defense": 250, "desc": "攻擊力 +10, HP +250, 無視防禦 10%, 防禦力 +250"},
            4: {"attack": 15, "hp": 375, "crit_dmg": 0.05, "desc": "攻擊力 +15, HP +375, 暴擊傷害 +5%"},
            5: {"attack": 15, "hp": 375, "boss_dmg": 0.10, "desc": "攻擊力 +15, HP +375, BOSS傷害 +10%"},
            6: {"attack": 15, "hp": 375, "damage_mult": 0.10, "desc": "攻擊力 +15, HP +375, 傷害 +10%"},
            7: {"attack": 15, "hp": 375, "crit_dmg": 0.05, "desc": "攻擊力 +15, HP +375, 暴擊傷害 +5%"},
            8: {"attack": 15, "hp": 375, "boss_dmg": 0.10, "desc": "攻擊力 +15, HP +375, BOSS傷害 +10%"},
            9: {"attack": 15, "hp": 375, "damage_mult": 0.10, "desc": "攻擊力 +15, HP +375, 傷害 +10%"},
        }
    },
    "dawn_boss": {
        "id": "dawn_boss",
        "name": "黎明之晨套裝",
        "color": (120, 215, 255),
        "tiers": {
            2: {"attack": 10, "hp": 250, "boss_dmg": 0.10, "desc": "攻擊力 +10, HP +250, BOSS傷害 +10%"},
            3: {"attack": 10, "hp": 250, "defense": 250, "desc": "攻擊力 +10, HP +250, 防禦力 +250"},
            4: {"attack": 10, "hp": 250, "damage_mult": 0.10, "defense": 250, "desc": "攻擊力 +10, HP +250, 傷害 +10%, 防禦力 +250"},
        }
    },
    "absolab": {
        "id": "absolab",
        "name": "航海師套裝",
        "color": (80, 200, 160),
        "tiers": {
            2: {"attack": 20, "defense": 100, "hp": 500, "desc": "攻擊力 +20, 防禦力 +100, HP +500"},
            3: {"attack": 25, "defense": 150, "desc": "攻擊力 +25, 防禦力 +150"},
            4: {"attack": 30, "defense": 200, "damage_mult": 0.10, "desc": "攻擊力 +30, 防禦力 +200, 傷害 +10%"},
            5: {"attack": 30, "boss_dmg": 0.30, "desc": "攻擊力 +30, BOSS傷害 +30%"},
        }
    },
    "arcane_umbra": {
        "id": "arcane_umbra",
        "name": "神秘冥界幽靈套裝",
        "color": (90, 160, 255),
        "tiers": {
            2: {"attack": 30, "defense": 200, "desc": "攻擊力 +30, 防禦力 +200"},
            3: {"attack": 35, "defense": 300, "desc": "攻擊力 +35, 防禦力 +300"},
            4: {"attack": 40, "defense": 400, "def_ignore": 0.10, "desc": "攻擊力 +40, 防禦力 +400, 無視防禦 10%"},
            5: {"attack": 85, "boss_dmg": 0.30, "hp": 2000, "desc": "攻擊力 +85, BOSS傷害 +30%, HP +2000"},
            6: {"attack": 50, "damage_mult": 0.10, "attack_speed": 0.10, "desc": "攻擊力 +50, 傷害 +10%, 攻速提升 +0.10"},
        }
    },
    "fafnir": {
        "id": "fafnir",
        "name": "深淵法夫納套裝",
        "color": (255, 120, 80),
        "tiers": {
            2: {"attack": 20, "defense": 100, "hp": 1000, "desc": "攻擊力 +20, 防禦力 +100, HP +1000"},
            3: {"attack": 50, "hp": 2000, "desc": "攻擊力 +50, HP +2000"},
            4: {"boss_dmg": 0.30, "damage_mult": 0.10, "desc": "BOSS傷害 +30%, 傷害 +10%"},
        }
    },
    "eternal": {
        "id": "eternal",
        "name": "永恆神恩套裝",
        "color": (255, 225, 100),
        "tiers": {
            2: {"attack": 40, "defense": 500, "boss_dmg": 0.10, "desc": "攻擊力 +40, 防禦力 +500, BOSS傷害 +10%"},
            3: {"attack": 40, "defense": 500, "def_ignore": 0.10, "desc": "攻擊力 +40, 防禦力 +500, 無視防禦 10%"},
            4: {"attack": 40, "defense": 500, "boss_dmg": 0.15, "desc": "攻擊力 +40, 防禦力 +500, BOSS傷害 +15%"},
            5: {"attack": 40, "defense": 500, "damage_mult": 0.10, "crit_dmg": 0.05, "desc": "攻擊力 +40, 防禦力 +500, 傷害 +10%, 暴擊傷害 +5%"},
        }
    }
}

# 物品名稱對應套裝 ID (100% 純正官方名稱)
ITEM_SET_MAPPING = {
    # 頂級培羅德套裝
    "頂級培羅德戒指": "gollux_superior",
    "頂級培羅德項鍊": "gollux_superior",
    "頂級培羅德耳環": "gollux_superior",
    "頂級培羅德腰帶": "gollux_superior",
    "頂級培羅德肩飾": "gollux_superior",

    # 漆黑的Boss飾品套裝
    "巨大恐懼": "pitched_boss",
    "苦痛的根源": "pitched_boss",
    "狂暴印記": "pitched_boss",
    "魔導石眼罩": "pitched_boss",
    "指揮官耳環": "pitched_boss",
    "夢幻腰帶": "pitched_boss",
    "詛咒的魔導書": "pitched_boss",
    "米特拉的憤怒": "pitched_boss",
    "滅世黑心臟": "pitched_boss",
    "漆黑天際肩飾": "pitched_boss",

    # 黎明之晨套裝
    "黎明守護天使之戒": "dawn_boss",
    "黃昏墜飾": "dawn_boss",
    "暮色印記": "dawn_boss",
    "埃斯黛拉耳環": "dawn_boss",
    "黎明守護肩飾": "dawn_boss",

    # 神秘冥界幽靈套裝
    "神秘冥界幽靈雙手劍": "arcane_umbra",
    "神秘冥界幽靈騎士帽": "arcane_umbra",
    "神秘冥界幽靈戰袍": "arcane_umbra",
    "神秘冥界幽靈護腿": "arcane_umbra",
    "神秘冥界幽靈戰靴": "arcane_umbra",
    "神秘冥界幽靈手套": "arcane_umbra",
    "神秘冥界幽靈披風": "arcane_umbra",
    "神秘冥界幽靈肩甲": "arcane_umbra",

    # 航海師套裝
    "航海師斬首之劍": "absolab",
    "航海師騎士帽": "absolab",
    "航海師戰服": "absolab",
    "航海師戰靴": "absolab",
    "航海師手套": "absolab",
    "航海師鬥篷": "absolab",
    "航海師肩甲": "absolab",

    # 深淵法夫納套裝
    "法夫納斬首巨劍": "fafnir",
    "深淵霸王皇家頭盔": "fafnir",
    "深淵鷹眼戰士鎧甲": "fafnir",
    "深淵騙徒戰士長褲": "fafnir",

    # 永恆神恩套裝
    "永恆神恩之冠": "eternal",
    "永恆聖威戰袍": "eternal",
    "永恆守護長褲": "eternal",
    "永恆逐風戰靴": "eternal",
    "永恆天威手套": "eternal",
    "永恆晨曦披風": "eternal",
}

