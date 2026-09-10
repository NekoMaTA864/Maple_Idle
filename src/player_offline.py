"""
新楓之谷：放置遠征隊 - 離線掛機結算模組 (player_offline.py)
"""

import time
from settings import INVENTORY_CAPACITY, OFFLINE_EFFICIENCY, MAX_OFFLINE_HOURS
from item_system import generate_loot


def settle_offline_progression(player, combat_mgr, saved_time: float) -> dict | None:
    """結算離線掛機收益（經驗值、金幣與裝備掉落）"""
    now = time.time()
    elapsed_seconds = max(0.0, now - saved_time)
    max_seconds = MAX_OFFLINE_HOURS * 3600.0
    actual_seconds = min(elapsed_seconds, max_seconds)

    if actual_seconds < 15.0 or not combat_mgr:
        return None

    zone = combat_mgr.get_current_zone()
    m_list = zone["monsters"]
    avg_m = m_list[len(m_list) // 2]

    # 遠征小隊總秒傷計算
    total_dps = 0.0
    for m in player.team:
        m_atk = m.get_attack(player)
        m_spd = m.get_attack_speed(player)
        net_dmg = max(1.0, m_atk - avg_m["def"] * 0.45)
        total_dps += net_dmg / m_spd

    total_dps = max(1.0, total_dps)
    kill_time = max(1.0, avg_m["hp"] / total_dps)

    kills = int((actual_seconds / kill_time) * OFFLINE_EFFICIENCY)
    if kills <= 0:
        return None

    earned_exp = kills * avg_m["lvl"] * 10
    earned_gold = kills * avg_m["lvl"] * 7
    player.add_exp(earned_exp)
    player.add_gold(earned_gold)

    loots_found = []
    for _ in range(min(2, INVENTORY_CAPACITY - len(player.inventory))):
        loot = generate_loot(zone["level_range"][0])
        if player.add_to_inventory(loot):
            loots_found.append(loot.full_name)

    return {
        "seconds": actual_seconds,
        "kills": kills,
        "exp": earned_exp,
        "gold": earned_gold,
        "loots": loots_found,
    }

