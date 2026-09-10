# -*- coding: utf-8 -*-
"""
新楓之谷 6 大秘法符號 (ARC) 與 4 大原初符號 (AUT) 系統模組 (player_symbols.py)
"""

ARC_SYMBOLS_DATA = {
    "vanishing": {"name": "消亡旅途秘法符號", "max_lvl": 20, "base_arc": 30, "arc_per_lvl": 10, "stat_atk": 30, "stat_hp": 300},
    "chuchu": {"name": "啾啾島秘法符號", "max_lvl": 20, "base_arc": 30, "arc_per_lvl": 10, "stat_atk": 30, "stat_hp": 300},
    "lachelein": {"name": "夢之都拉克蘭秘法符號", "max_lvl": 20, "base_arc": 30, "arc_per_lvl": 10, "stat_atk": 30, "stat_hp": 300},
    "arcana": {"name": "神秘森林阿爾卡娜秘法符號", "max_lvl": 20, "base_arc": 30, "arc_per_lvl": 10, "stat_atk": 30, "stat_hp": 300},
    "morass": {"name": "記憶之沼魔菈斯秘法符號", "max_lvl": 20, "base_arc": 30, "arc_per_lvl": 10, "stat_atk": 30, "stat_hp": 300},
    "esfera": {"name": "始源之海艾斯佩拉秘法符號", "max_lvl": 20, "base_arc": 30, "arc_per_lvl": 10, "stat_atk": 30, "stat_hp": 300},
}

AUT_SYMBOLS_DATA = {
    "cernium": {"name": "塞爾尼恩原初符號", "max_lvl": 11, "base_aut": 10, "aut_per_lvl": 10, "stat_atk": 80, "stat_hp": 800},
    "arcus": {"name": "阿爾克斯原初符號", "max_lvl": 11, "base_aut": 10, "aut_per_lvl": 10, "stat_atk": 80, "stat_hp": 800},
    "odium": {"name": "奧迪溫原初符號", "max_lvl": 11, "base_aut": 10, "aut_per_lvl": 10, "stat_atk": 80, "stat_hp": 800},
    "shangrila": {"name": "桃源境原初符號", "max_lvl": 11, "base_aut": 10, "aut_per_lvl": 10, "stat_atk": 80, "stat_hp": 800},
    "arteria": {"name": "阿爾特利亞原初符號", "max_lvl": 11, "base_aut": 10, "aut_per_lvl": 10, "stat_atk": 80, "stat_hp": 800},
    "carcion": {"name": "卡爾西溫原初符號", "max_lvl": 11, "base_aut": 10, "aut_per_lvl": 10, "stat_atk": 80, "stat_hp": 800},
    "talahart": {"name": "塔拉哈特原初符號", "max_lvl": 11, "base_aut": 10, "aut_per_lvl": 10, "stat_atk": 80, "stat_hp": 800},
}


def calculate_total_arc(arc_symbols: dict) -> int:
    """計算遠征隊目前累計的總 ARC (秘法符文力)"""
    total = 0
    for k, lvl in arc_symbols.items():
        if lvl > 0 and k in ARC_SYMBOLS_DATA:
            data = ARC_SYMBOLS_DATA[k]
            total += data["base_arc"] + (lvl - 1) * data["arc_per_lvl"]
    return total


def calculate_total_aut(aut_symbols: dict) -> int:
    """計算遠征隊目前累計的總 AUT (原初符文力)"""
    total = 0
    for k, lvl in aut_symbols.items():
        if lvl > 0 and k in AUT_SYMBOLS_DATA:
            data = AUT_SYMBOLS_DATA[k]
            total += data["base_aut"] + (lvl - 1) * data["aut_per_lvl"]
    return total


def calculate_symbol_stat_sum(arc_symbols: dict, aut_symbols: dict, stat_name: str) -> int:
    """獲取符號提供的全隊屬性總和 (attack / hp / defense)"""
    total = 0
    for k, lvl in arc_symbols.items():
        if lvl > 0 and k in ARC_SYMBOLS_DATA:
            data = ARC_SYMBOLS_DATA[k]
            if stat_name == "attack":
                total += lvl * data["stat_atk"]
            elif stat_name == "hp":
                total += lvl * data["stat_hp"]
            elif stat_name == "defense":
                total += lvl * (data["stat_atk"] // 2)

    for k, lvl in aut_symbols.items():
        if lvl > 0 and k in AUT_SYMBOLS_DATA:
            data = AUT_SYMBOLS_DATA[k]
            if stat_name == "attack":
                total += lvl * data["stat_atk"]
            elif stat_name == "hp":
                total += lvl * data["stat_hp"]
            elif stat_name == "defense":
                total += lvl * (data["stat_atk"] // 2)
    return total


def get_symbol_display_name(sym_key: str) -> str:
    if sym_key in ARC_SYMBOLS_DATA:
        return ARC_SYMBOLS_DATA[sym_key]["name"]
    elif sym_key in AUT_SYMBOLS_DATA:
        return AUT_SYMBOLS_DATA[sym_key]["name"]
    return sym_key


def get_symbol_upgrade_req(sym_key: str, cur_lvl: int):
    """取得升級指定符號所需的碎片數與金幣 (req_frags, req_gold, is_max)"""
    is_arc = sym_key in ARC_SYMBOLS_DATA
    data = ARC_SYMBOLS_DATA[sym_key] if is_arc else AUT_SYMBOLS_DATA.get(sym_key)
    if not data:
        return 0, 0, True
    max_lvl = data["max_lvl"]
    if cur_lvl >= max_lvl:
        return 0, 0, True

    req_lvl = max(1, cur_lvl)
    if is_arc:
        req_frags = req_lvl * 4 + 8
        req_gold = req_lvl * 25000 + 50000
    else:
        req_frags = req_lvl * 6 + 12
        req_gold = req_lvl * 120000 + 200000
    return req_frags, req_gold, False

