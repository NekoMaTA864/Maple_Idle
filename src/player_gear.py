"""
新楓之谷：放置遠征隊 - 裝備穿脫、強化、洗潛與背包管理模組 (player_gear.py)
"""

import random
from settings import INVENTORY_CAPACITY
from item_system import (
    SLOT_NAMES, CATEGORY_TO_SLOTS, SLOT_TO_CATEGORY,
    CUBE_COSTS, POTENTIAL_RANK_INFO, calc_item_combat_score,
    get_slot_potential_pool, ABBY_SCROLLS, WSE_SLOTS, ARMOR_SLOTS, ACCESSORY_SLOTS
)


def ensure_player_slots(player):
    """確保玩家具有 25 格欄位的星力、主/附加潛能與艾比卷軸結構"""
    if not hasattr(player, "slot_enhancements") or player.slot_enhancements is None:
        player.slot_enhancements = {}
    if not hasattr(player, "slot_potentials") or player.slot_potentials is None:
        player.slot_potentials = {}
    if not hasattr(player, "slot_scrolls") or player.slot_scrolls is None:
        player.slot_scrolls = {}

    if not hasattr(player, "abby_scrolls") or player.abby_scrolls is None:
        player.abby_scrolls = {}
    if not hasattr(player, "cube_inventory") or player.cube_inventory is None:
        player.cube_inventory = {}

    for s in SLOT_NAMES.keys():
        if s not in player.slot_enhancements:
            player.slot_enhancements[s] = 0
        if s not in player.slot_potentials:
            main_pool = get_slot_potential_pool(s, "rare", is_bonus=False)
            bonus_pool = get_slot_potential_pool(s, "rare", is_bonus=True)
            player.slot_potentials[s] = {
                "main": {
                    "rank": "rare",
                    "lines": random.sample(main_pool, min(2, len(main_pool)))
                },
                "bonus": {
                    "rank": "rare",
                    "lines": random.sample(bonus_pool, min(2, len(bonus_pool)))
                }
            }
        if s not in player.slot_scrolls:
            player.slot_scrolls[s] = {
                "count": 0,
                "max_count": 10,
                "history": [],
                "stats": {}
            }


def toggle_item_lock(item) -> bool:
    """切換裝備綠鎖狀態 (True: 已上鎖, False: 未上鎖)"""
    item.locked = not getattr(item, "locked", False)
    return item.locked


def apply_scroll_to_slot(player, slot_key: str, scroll_type: str = "V") -> tuple[bool, str]:
    """
    使用台服艾比卷軸強化欄位 (極電/R/X/V/B)：
    - 依據部位 (WSE / 防具 / 飾品) 提供不同加成數值
    - 欄位最高可砸 10 張艾比卷軸
    - 強化永久鎖定於欄位，換裝無損繼承！
    """
    ensure_player_slots(player)
    if slot_key not in player.slot_scrolls:
        return False, "無效裝備欄位"
    sc_data = player.slot_scrolls[slot_key]
    cur_cnt = sc_data.get("count", 0)
    max_cnt = sc_data.get("max_count", 10)
    scroll_info = ABBY_SCROLLS.get(scroll_type)
    if not scroll_info:
        return False, "無效的卷軸類型"

    slot_name = SLOT_NAMES.get(slot_key, slot_key)
    cost = scroll_info.get("cost", 50000)

    # 特殊處理：回真卷軸 (Innocence Scroll) - 重置衝卷次數與累積屬性
    if scroll_type == "innocence" or scroll_info.get("is_innocence"):
        if cur_cnt == 0:
            return False, f"【{slot_name}】尚未施加任何艾比卷軸強化，無須使用回真卷軸！"
        used_inventory = False
        if hasattr(player, "abby_scrolls") and player.abby_scrolls.get(scroll_type, 0) > 0:
            player.abby_scrolls[scroll_type] -= 1
            used_inventory = True
        else:
            if player.gold < cost:
                return False, f"金幣不足！使用【{scroll_info['name']}】需要 ${cost:,} 楓幣 (或持有卷軸)"
            player.gold -= cost

        sc_data["count"] = 0
        sc_data["history"] = []
        sc_data["stats"] = {}

        for m in player.team:
            m.current_hp = min(m.current_hp, float(m.get_max_hp(player)))

        consume_str = "消耗卷軸庫存 x1" if used_inventory else f"花費 ${cost:,} 楓幣"
        return True, f"🔄 【{slot_name}】已成功使用【回真卷軸】！[{consume_str}]\n衝卷次數已重置為 0/10 次，所有卷軸加成已清空，可重新打造完美屬性！"

    if cur_cnt >= max_cnt:
        return False, f"該欄位卷軸次數已滿 ({max_cnt}/{max_cnt})！"

    cost = scroll_info.get("cost", 50000)
    used_inventory = False
    if hasattr(player, "abby_scrolls") and player.abby_scrolls.get(scroll_type, 0) > 0:
        player.abby_scrolls[scroll_type] -= 1
        used_inventory = True
    else:
        if player.gold < cost:
            return False, f"金幣不足！強化【{scroll_info['name']}】需要 ${cost:,} 金幣 (或持有卷軸)"
        player.gold -= cost

    # 決定部位分類
    s_lower = slot_key.lower()
    if s_lower in WSE_SLOTS:
        stat_gain = scroll_info["weapon"]
    elif s_lower in ARMOR_SLOTS:
        stat_gain = scroll_info["armor"]
    else:
        stat_gain = scroll_info["acc"]

    # 累加數值到 slot_scrolls["stats"]
    slot_stats = sc_data.setdefault("stats", {})
    for k, v in stat_gain.items():
        if k != "desc":
            slot_stats[k] = slot_stats.get(k, 0) + v

    sc_data["count"] = cur_cnt + 1
    sc_data.setdefault("history", []).append(scroll_type)

    for m in player.team:
        m.current_hp = min(m.current_hp, float(m.get_max_hp(player)))

    slot_name = SLOT_NAMES.get(slot_key, slot_key)
    consume_str = "消耗卷軸庫存 x1" if used_inventory else f"花費 ${cost:,} 楓幣"
    msg = f"📜 【{slot_name}】成功注入【{scroll_info['name']}】({sc_data['count']}/10)！[{consume_str}]\n獲得加成：{stat_gain['desc']}"
    return True, msg


def cube_slot(player, slot_key: str, cube_type: str = "mystic", is_bonus: bool = False) -> tuple[bool, str]:
    """
    洗欄位潛能 (Cube Slot)：
    - is_bonus=False: 洗主潛能 (楓方塊 mystic / 閃耀方塊 bright)
    - is_bonus=True: 洗附加潛能 (可疑附加方塊 bonus_occult / 閃耀附加方塊 bonus_bright)
    - 潛能嚴格遵循官方部位限制，且永久綁定欄位！換裝不洗白！
    """
    ensure_player_slots(player)
    if slot_key not in player.slot_potentials:
        return False, "無效裝備欄位"

    cost = CUBE_COSTS.get(cube_type, 6000)
    cube_names = {
        "mystic": "楓方塊",
        "bright": "閃耀方塊",
        "bonus_occult": "可疑附加方塊",
        "bonus_bright": "閃耀附加方塊"
    }
    cube_name = cube_names.get(cube_type, "方塊")
    if hasattr(player, "cube_inventory") and player.cube_inventory.get(cube_type, 0) > 0:
        player.cube_inventory[cube_type] -= 1
    else:
        if player.gold < cost:
            return False, f"金幣不足！使用【{cube_name}】需要 ${cost:,} 金幣 (或持有該方塊)"
        player.gold -= cost
    target_dict = player.slot_potentials[slot_key]["bonus" if is_bonus else "main"]
    old_rank = target_dict.get("rank", "rare")

    # 跳階機率判定
    did_tier_up = False
    if cube_type in ["mystic", "bonus_occult"]:
        if old_rank == "rare" and random.random() < 0.18:
            target_dict["rank"] = "epic"
            did_tier_up = True
    elif cube_type in ["bright", "bonus_bright"]:
        if old_rank == "rare" and random.random() < 0.35:
            target_dict["rank"] = "epic"
            did_tier_up = True
        elif old_rank == "epic" and random.random() < 0.16:
            target_dict["rank"] = "unique"
            did_tier_up = True
        elif old_rank == "unique" and random.random() < 0.08:
            target_dict["rank"] = "legendary"
            did_tier_up = True

    new_rank = target_dict["rank"]
    pool = get_slot_potential_pool(slot_key, new_rank, is_bonus=is_bonus)
    line_cnt = 3 if new_rank in ["unique", "legendary"] else 2
    target_dict["lines"] = random.sample(pool, min(line_cnt, len(pool)))

    for m in player.team:
        m.current_hp = min(m.current_hp, float(m.get_max_hp(player)))

    slot_name = SLOT_NAMES.get(slot_key, slot_key)
    old_r_name = POTENTIAL_RANK_INFO.get(old_rank, {}).get("name", old_rank)
    new_r_name = POTENTIAL_RANK_INFO.get(new_rank, {}).get("name", new_rank)
    pot_type_str = "附加潛能" if is_bonus else "主潛能"
    lines_str = "、".join([l.get("name", "") for l in target_dict["lines"]])

    if did_tier_up:
        msg = f"✨ 【{slot_name}】{pot_type_str}階級突破！提升至 [{new_r_name}]！\n新詞條：{lines_str}"
    else:
        msg = f"【{slot_name}】{pot_type_str}洗練完成！[{new_r_name}]\n新詞條：{lines_str}"
    return True, msg


def auto_cube_slot(player, slot_key: str, cube_type: str = "bright", target_rank: str = "unique", target_stat_keyword: str = None, is_bonus: bool = False, max_cubes: int = 100) -> tuple[bool, str]:
    """一鍵洗欄位潛能 (Auto Cube Slot)"""
    ensure_player_slots(player)
    if slot_key not in player.slot_potentials:
        return False, "無效裝備欄位"

    target_dict = player.slot_potentials[slot_key]["bonus" if is_bonus else "main"]
    rank_order = {"rare": 1, "epic": 2, "unique": 3, "legendary": 4}
    tgt_order = rank_order.get(target_rank, 3)

    def is_matched():
        cur_order = rank_order.get(target_dict.get("rank", "rare"), 1)
        if cur_order >= tgt_order:
            if not target_stat_keyword:
                return True
            for l in target_dict.get("lines", []):
                if target_stat_keyword in l.get("name", "") or target_stat_keyword in l.get("desc", ""):
                    return True
        return False

    if is_matched():
        return False, f"該欄位當前已滿足目標條件！"

    cost = CUBE_COSTS.get(cube_type, 30000)
    attempts = 0
    gold_spent = 0

    while attempts < max_cubes:
        if player.gold < cost:
            break
        attempts += 1
        gold_spent += cost
        success, msg = cube_slot(player, slot_key, cube_type=cube_type, is_bonus=is_bonus)
        if not success or is_matched():
            break

    slot_name = SLOT_NAMES.get(slot_key, slot_key)
    cur_r_name = POTENTIAL_RANK_INFO.get(target_dict.get("rank", "rare"), {}).get("name", "")
    lines_str = "、".join([l.get("name", "") for l in target_dict.get("lines", [])])

    if is_matched():
        return True, f"🎉 【{slot_name}】一鍵洗潛達成目標！[{cur_r_name}]\n共洗了 {attempts} 次，消耗 ${gold_spent:,} 金幣\n詞條：{lines_str}"
    elif player.gold < cost:
        return False, f"⚠️ 金幣不足中斷！【{slot_name}】當前 [{cur_r_name}]\n共嘗試 {attempts} 次，消耗 ${gold_spent:,} 金幣\n詞條：{lines_str}"
    else:
        limit_str = f"{max_cubes}次" if max_cubes < 999999 else "安全上限"
        return False, f"⚠️ 已達{limit_str}！【{slot_name}】當前 [{cur_r_name}]\n消耗 ${gold_spent:,} 金幣\n詞條：{lines_str}"


def cube_item(player, item, cube_type: str = "mystic") -> tuple[bool, str]:
    """單次洗潛能 (支援穿戴時自動綁定欄位洗潛，未穿戴時洗裝備自身)"""
    if not item:
        return False, "無效裝備"
    # 若該裝備已穿戴，自動洗其所在欄位
    for slot_k, eq_it in player.equipped.items():
        if eq_it == item:
            return cube_slot(player, slot_k, cube_type=cube_type, is_bonus=False)

    cost = CUBE_COSTS.get(cube_type, 6000)
    cube_name = "楓方塊" if cube_type == "mystic" else "閃耀方塊"
    if player.gold < cost:
        return False, f"金幣不足！使用【{cube_name}】需要 ${cost:,} 金幣"

    player.gold -= cost
    old_rank = item.potential_rank
    tier_up, new_rank, new_lines = item.cube_potential(cube_type)

    for m in player.team:
        m.current_hp = min(m.current_hp, float(m.get_max_hp(player)))

    old_rank_str = POTENTIAL_RANK_INFO.get(old_rank, {}).get("name", old_rank)
    new_rank_str = POTENTIAL_RANK_INFO.get(new_rank, {}).get("name", new_rank)
    lines_str = "、".join([line.get("name", "") for line in new_lines])

    if tier_up:
        msg = f"✨ 潛能階級突破！【{item.base_name}】提升至 [{new_rank_str}]！\n詞條：{lines_str}"
    else:
        msg = f"洗潛完成！【{item.base_name}】[{new_rank_str}潛能]\n詞條：{lines_str}"
    return True, msg


def auto_cube_item(player, item, cube_type: str = "bright", target_rank: str = "unique", target_stat_keyword: str = None, max_cubes: int = 100) -> tuple[bool, str]:
    """一鍵洗潛 (Auto Cube)"""
    if not item:
        return False, "無效裝備"
    for slot_k, eq_it in player.equipped.items():
        if eq_it == item:
            return auto_cube_slot(player, slot_k, cube_type=cube_type, target_rank=target_rank, target_stat_keyword=target_stat_keyword, is_bonus=False, max_cubes=max_cubes)

    if item.matches_cube_target(target_rank, target_stat_keyword):
        target_desc = f"目標階級 [{POTENTIAL_RANK_INFO.get(target_rank, {}).get('name', target_rank)}]"
        if target_stat_keyword:
            target_desc += f" 且含有「{target_stat_keyword}」"
        return False, f"該裝備目前已滿足 {target_desc}！"

    cost_per_roll = CUBE_COSTS.get(cube_type, 30000)
    attempts = 0
    gold_spent = 0

    while attempts < max_cubes:
        if player.gold < cost_per_roll:
            break
        attempts += 1
        gold_spent += cost_per_roll
        player.gold -= cost_per_roll

        did_tier_up, cur_rank, cur_lines = item.cube_potential(cube_type)
        if item.matches_cube_target(target_rank, target_stat_keyword):
            break

    for m in player.team:
        m.current_hp = min(m.current_hp, float(m.get_max_hp(player)))

    cur_rank_name = POTENTIAL_RANK_INFO.get(item.potential_rank, {}).get("name", item.potential_rank)
    lines_str = "、".join([l.get("name", "") for l in item.potential_lines])

    matched = item.matches_cube_target(target_rank, target_stat_keyword)
    if matched:
        msg = f"🎉 【{item.base_name}】一鍵洗潛達成目標！\n階級：[{cur_rank_name}] | 共洗了 {attempts} 次，消耗 ${gold_spent:,} 金幣\n新詞條：{lines_str}"
        return True, msg
    elif player.gold < cost_per_roll:
        msg = f"⚠️ 金幣耗盡中斷！【{item.base_name}】當前 [{cur_rank_name}]\n共洗了 {attempts} 次，消耗 ${gold_spent:,} 金幣\n詞條：{lines_str}"
        return False, msg
    else:
        limit_str = f"{max_cubes}次" if max_cubes < 999999 else "安全上限"
        msg = f"⚠️ 已達{limit_str}！【{item.base_name}】當前 [{cur_rank_name}]\n消耗 ${gold_spent:,} 金幣\n詞條：{lines_str}"
        return False, msg


def get_slot_enhance_cost(slot_enhancements: dict, slot_key: str) -> int:
    lvl = slot_enhancements.get(slot_key, 0)
    base = 80
    return int(base * (1.25 ** min(15, lvl)) * (1.14 ** max(0, lvl - 15)) + lvl * 120)


def get_slot_enhance_success_rate(slot_enhancements: dict, slot_key: str) -> float:
    lvl = slot_enhancements.get(slot_key, 0)
    if lvl < 5:
        return 0.95
    elif lvl < 10:
        return 0.80
    elif lvl < 15:
        return 0.60
    elif lvl < 20:
        return 0.35
    elif lvl < 23:
        return 0.20
    else:
        return 0.10


def can_enhance_slot(player, slot_key: str) -> bool:
    lvl = player.slot_enhancements.get(slot_key, 0)
    return lvl < 25 and player.gold >= get_slot_enhance_cost(player.slot_enhancements, slot_key)


def enhance_slot(player, slot_key: str) -> tuple[bool, str]:
    if slot_key not in player.slot_enhancements:
        return False, "無效裝備欄位"
    lvl = player.slot_enhancements[slot_key]
    if lvl >= 25:
        return False, "該欄位已達最高星力等級 (★25)！"
    cost = get_slot_enhance_cost(player.slot_enhancements, slot_key)
    if player.gold < cost:
        return False, f"金幣不足！需要 ${cost:,} 金幣"

    player.gold -= cost
    rate = get_slot_enhance_success_rate(player.slot_enhancements, slot_key)
    slot_name = SLOT_NAMES.get(slot_key, slot_key)
    if random.random() <= rate:
        player.slot_enhancements[slot_key] = lvl + 1
        for m in player.team:
            m.current_hp = min(m.current_hp, float(m.get_max_hp(player)))
        return True, f"【{slot_name}】欄位星力強化成功！提升至 ★{lvl + 1}！"
    else:
        return False, f"【{slot_name}】星力強化失敗！維持 ★{lvl}"


def auto_enhance_slot(player, slot_key: str, target_star: int = 15, max_attempts: int = 100) -> tuple[bool, str]:
    """一鍵升星 (Auto Star Force)"""
    if slot_key not in player.slot_enhancements:
        return False, "無效裝備欄位"

    target_star = min(25, max(1, target_star))
    cur_lvl = player.slot_enhancements[slot_key]
    slot_name = SLOT_NAMES.get(slot_key, slot_key)

    if cur_lvl >= target_star:
        return False, f"【{slot_name}】欄位已達 ★{cur_lvl}，已滿足目標 ★{target_star}！"

    attempts = 0
    success_count = 0
    fail_count = 0
    gold_spent = 0

    while player.slot_enhancements[slot_key] < target_star and attempts < max_attempts:
        cost = get_slot_enhance_cost(player.slot_enhancements, slot_key)
        if player.gold < cost:
            break

        attempts += 1
        gold_spent += cost
        player.gold -= cost
        rate = get_slot_enhance_success_rate(player.slot_enhancements, slot_key)

        if random.random() <= rate:
            player.slot_enhancements[slot_key] += 1
            success_count += 1
        else:
            fail_count += 1

    for m in player.team:
        m.current_hp = min(m.current_hp, float(m.get_max_hp(player)))

    final_lvl = player.slot_enhancements[slot_key]
    reached_target = final_lvl >= target_star

    if reached_target:
        msg = f"【{slot_name}】一鍵升星成功！達成 ★{final_lvl}！共強化 {attempts} 次 (成功 {success_count} / 失敗 {fail_count})，消耗 ${gold_spent:,} 金幣。"
        return True, msg
    elif player.gold < get_slot_enhance_cost(player.slot_enhancements, slot_key):
        msg = f"【{slot_name}】金幣不足中斷！當前 ★{final_lvl} (目標 ★{target_star})，共嘗試 {attempts} 次 (成功 {success_count})，消耗 ${gold_spent:,} 金幣。"
        return False, msg
    else:
        return False, msg


def equip_item(player, item, target_slot: str = None) -> tuple[bool, str]:
    """穿戴裝備 (嚴格檢查遠征隊等級需求)"""
    if item not in player.inventory:
        return False, "物品不在行囊中"

    if player.level < getattr(item, "level_req", 1):
        return False, f"等級不足！遠征隊需達 Lv.{item.level_req} 才能穿戴【{item.full_name}】(當前: Lv.{player.level})"

    category = item.slot
    valid_slots = CATEGORY_TO_SLOTS.get(category, [category])
    if target_slot and target_slot in valid_slots:
        dest_slot = target_slot
    else:
        empty_slot = next((s for s in valid_slots if player.equipped.get(s) is None), None)
        dest_slot = empty_slot if empty_slot else valid_slots[0]

    old_item = player.equipped.get(dest_slot)
    player.inventory.remove(item)
    player.equipped[dest_slot] = item
    if old_item:
        player.inventory.append(old_item)

    for m in player.team:
        m.current_hp = min(m.current_hp, float(m.get_max_hp(player)))
    slot_cn = SLOT_NAMES.get(dest_slot, dest_slot)
    return True, f"已將【{item.full_name}】裝備至【{slot_cn}】"


def unequip_item(player, slot: str) -> tuple[bool, str]:
    """卸下裝備"""
    if slot not in player.equipped or not player.equipped[slot]:
        return False, "該部位未穿戴裝備"
    if len(player.inventory) >= INVENTORY_CAPACITY:
        return False, "行囊空間已滿，無法卸下裝備"
    item = player.equipped[slot]
    player.equipped[slot] = None
    player.inventory.append(item)
    slot_cn = SLOT_NAMES.get(slot, slot)
    return True, f"已從【{slot_cn}】卸下【{item.full_name}】"


def sell_item(player, item) -> int:
    """單件出售物品 (綠鎖保護)"""
    if getattr(item, "locked", False):
        return 0
    if item in player.inventory:
        player.inventory.remove(item)
        player.gold += item.sell_price
        return item.sell_price
    return 0


def sell_by_rarities(player, rarities: list) -> tuple[int, int]:
    """批次出售指定稀有度的裝備 (略過綠鎖保護的裝備)"""
    to_sell = [it for it in player.inventory if it.rarity in rarities and not getattr(it, "locked", False)]
    total_gold = 0
    for it in to_sell:
        player.inventory.remove(it)
        total_gold += it.sell_price
    player.gold += total_gold
    return len(to_sell), total_gold


def auto_equip_best_gear(player) -> list:
    """一鍵換裝：自動搜尋背包與身上裝備，為 25 格各部位配置最高戰力裝備 (嚴格遵循等級限制)"""
    changed = []

    for cat, slots in CATEGORY_TO_SLOTS.items():
        if cat in ["armor", "accessory"]:
            continue

        candidates = []
        for item in list(player.inventory):
            item_cat = SLOT_TO_CATEGORY.get(item.slot, item.slot)
            if item_cat == cat and player.level >= getattr(item, "level_req", 1):
                candidates.append(item)

        for s in slots:
            cur_item = player.equipped.get(s)
            if cur_item and player.level >= getattr(cur_item, "level_req", 1):
                candidates.append(cur_item)

        if not candidates:
            continue

        candidates.sort(key=lambda it: calc_item_combat_score(it, 0), reverse=True)
        sorted_slots = sorted(slots, key=lambda s: player.slot_enhancements.get(s, 0), reverse=True)

        for i, s in enumerate(sorted_slots):
            if i < len(candidates):
                best_item = candidates[i]
                cur_item = player.equipped.get(s)
                if cur_item != best_item:
                    if best_item in player.inventory:
                        player.inventory.remove(best_item)
                    if cur_item:
                        player.inventory.append(cur_item)
                    player.equipped[s] = best_item
                    changed.append((s, best_item))

    for m in player.team:
        m.current_hp = min(m.current_hp, float(m.get_max_hp(player)))

    return changed


def sell_inferior_gear(player) -> tuple[int, int]:
    """一鍵出售劣質裝備：自動出售背包中戰力低於目前身上所穿戴之淘汰裝備 (絕對不售綠鎖鎖定裝備)"""
    to_sell = []
    inv_by_cat = {}
    for item in list(player.inventory):
        if getattr(item, "locked", False):
            continue
        cat = SLOT_TO_CATEGORY.get(item.slot, item.slot)
        inv_by_cat.setdefault(cat, []).append(item)

    for cat, inv_items in inv_by_cat.items():
        slots = CATEGORY_TO_SLOTS.get(cat, [cat])
        empty_slots = [s for s in slots if player.equipped.get(s) is None]
        equipped_items = [player.equipped[s] for s in slots if player.equipped.get(s) is not None]

        inv_items.sort(key=lambda it: calc_item_combat_score(it, 0), reverse=True)
        keep_count = len(empty_slots)
        potential_fillers = inv_items[:keep_count]
        remaining_inv = inv_items[keep_count:]

        all_kept = equipped_items + potential_fillers
        if not all_kept:
            continue

        baseline_score = min(calc_item_combat_score(it, 0) for it in all_kept)

        for item in remaining_inv:
            score = calc_item_combat_score(item, 0)
            if score <= baseline_score:
                to_sell.append(item)

    total_gold = 0
    for item in to_sell:
        if item in player.inventory:
            player.inventory.remove(item)
            player.gold += item.sell_price
            total_gold += item.sell_price

    return len(to_sell), total_gold

