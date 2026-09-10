"""
新楓之谷：放置遠征隊 - 角色屬性與套裝加成計算模組 (player_stats.py)
負責計算單一隊員與全隊之戰鬥能力數值、裝備屬性加總與官方套裝效果
"""

from item_system import SET_DEFINITIONS


def calc_gear_stat_sum(equipped: dict, slot_enhancements: dict, stat_key: str, slot_potentials: dict = None, slot_scrolls: dict = None) -> float:
    """加總所有穿戴裝備（含欄位星力、欄位主/附加潛能、艾比卷軸）之特定屬性"""
    total = 0.0
    for slot_k, item in equipped.items():
        if item:
            star = slot_enhancements.get(slot_k, 0)
            s_pots = slot_potentials.get(slot_k) if slot_potentials else None
            s_scrolls = slot_scrolls.get(slot_k) if slot_scrolls else None
            stats = item.get_effective_stats(star, slot_potentials=s_pots, slot_scrolls=s_scrolls)
            total += stats.get(stat_key, 0.0)
    return total


def calc_active_sets(equipped: dict) -> list:
    """計算當前已穿戴裝備觸發的楓之谷官方套裝效果"""
    counts = {}
    for item in equipped.values():
        if item and item.set_id and item.set_id in SET_DEFINITIONS:
            counts[item.set_id] = counts.get(item.set_id, 0) + 1

    active_list = []
    for set_id, count in counts.items():
        s_def = SET_DEFINITIONS[set_id]
        active_tiers = []
        combined_stats = {
            "attack": 0,
            "defense": 0,
            "hp": 0,
            "crit_chance": 0.0,
            "damage_mult": 0.0,
            "attack_speed": 0.0,
            "def_ignore": 0.0,
            "crit_dmg": 0.0,
        }
        descriptions = []
        for tier_req, tier_data in sorted(s_def["tiers"].items()):
            if count >= tier_req:
                active_tiers.append(tier_req)
                descriptions.append(f"{tier_req}件: {tier_data['desc']}")
                for k, v in tier_data.items():
                    if k != "desc":
                        combined_stats[k] = combined_stats.get(k, 0) + v

        if active_tiers:
            active_list.append({
                "set_id": set_id,
                "name": s_def["name"],
                "color": s_def["color"],
                "count": count,
                "active_tiers": active_tiers,
                "stats": combined_stats,
                "descriptions": descriptions,
            })
    return active_list


def calc_set_stat_sum(equipped: dict, stat_key: str) -> float:
    """加總所有已激活套裝的特定屬性"""
    active = calc_active_sets(equipped)
    return sum(s["stats"].get(stat_key, 0.0) for s in active)


def calc_member_max_hp(member, player) -> int:
    """計算隊員最大生命值 (受裝備、符號、內潛與戰地後援加成)"""
    gear_hp = player.get_gear_stat_sum("hp")
    set_hp = player.get_set_stat_sum("hp")
    sym_hp = player.get_symbol_stat_sum("hp")
    legion_hp_pct = getattr(player, "get_legion_stat", lambda k: 0.0)("hp_pct")
    base = 90 + player.stat_hp * 22 + gear_hp + set_hp + sym_hp
    return int(base * member.class_info["hp_mult"] * (1.0 + legion_hp_pct))


def calc_member_attack(member, player) -> int:
    """計算隊員當前攻擊力（含套裝增傷、裝備潛能增傷、內潛、寵物裝備、萌獸、自身增益、全隊光環與戰地後援加成）"""
    gear_atk = player.get_gear_stat_sum("attack")
    set_atk = player.get_set_atk_sum() if hasattr(player, "get_set_atk_sum") else player.get_set_stat_sum("attack")
    set_dmg_mult = player.get_set_stat_sum("damage_mult")
    gear_dmg_mult = player.get_gear_stat_sum("damage_mult")
    sym_atk = player.get_symbol_stat_sum("attack")
    inner_atk = getattr(player, "get_inner_ability_stat", lambda k: 0.0)("attack")
    pet_atk = getattr(player, "get_pet_attack", lambda: 0)()
    legion_atk = getattr(player, "get_legion_stat", lambda k: 0.0)("attack")
    legion_dmg_mult = getattr(player, "get_legion_stat", lambda k: 0.0)("damage_mult")
    legion_final_dmg = getattr(player, "get_legion_stat", lambda k: 0.0)("final_dmg")

    base = 12 + player.stat_atk * 3.6 + gear_atk + set_atk + sym_atk + inner_atk + pet_atk + legion_atk

    # 被動技能等級+1 (全隊被動傷害+10%) 與 萌獸攻擊%
    inner_passive = getattr(player, "get_inner_ability_stat", lambda k: 0.0)("passive_level") * 0.10
    fam_atk_pct = getattr(player, "get_familiar_stat", lambda k: 0.0)("attack_pct")
    mult = member.class_info["atk_mult"] * (1.0 + set_dmg_mult + gear_dmg_mult + inner_passive + fam_atk_pct + legion_dmg_mult)
    if legion_final_dmg > 0:
        mult *= (1.0 + legion_final_dmg)

    if member.is_buffed:
        mult *= 1.25
    # 全隊光環增益 (支援普通光環與 5 轉聯盟光環)
    team_atk_buff = player.get_buff_val("attack_mult") + player.get_buff_val("union")
    if team_atk_buff > 0:
        mult *= (1.0 + team_atk_buff)
    return int(base * mult)


def calc_member_defense(member, player) -> int:
    """計算隊員防禦力 (受裝備、符號、內潛與戰地後援防禦%加成)"""
    gear_def = player.get_gear_stat_sum("defense")
    set_def = player.get_set_stat_sum("defense")
    sym_def = player.get_symbol_stat_sum("defense")
    legion_def_pct = getattr(player, "get_legion_stat", lambda k: 0.0)("def_pct")
    base = 4 + player.stat_def * 1.8 + gear_def + set_def + sym_def
    mult = member.class_info["def_mult"] * (1.0 + legion_def_pct)
    team_def_buff = player.get_buff_val("defense_mult") + player.get_buff_val("union") * 0.8
    if team_def_buff > 0:
        mult *= (1.0 + team_def_buff)
    return int(base * mult)


def calc_member_crit_chance(member, player) -> float:
    """計算隊員暴擊率（上限 85%）"""
    gear_crit = player.get_gear_stat_sum("crit_chance")
    set_crit = player.get_set_stat_sum("crit_chance")
    inner_crit = getattr(player, "get_inner_ability_stat", lambda k: 0.0)("crit_chance")
    team_crit_buff = player.get_buff_val("crit_bonus")
    legion_crit = getattr(player, "get_legion_stat", lambda k: 0.0)("crit_chance")
    base = 0.05 + player.stat_crit * 0.005 + gear_crit + set_crit + inner_crit + member.class_info["crit_bonus"] + team_crit_buff + legion_crit
    return min(0.85, base)


def calc_member_attack_speed(member, player) -> float:
    """計算隊員攻擊間隔秒數（下限 0.40s）"""
    gear_spd = player.get_gear_stat_sum("attack_speed")
    set_spd = player.get_set_stat_sum("attack_speed")
    inner_spd = getattr(player, "get_inner_ability_stat", lambda k: 0.0)("attack_speed")
    legion_spd = getattr(player, "get_legion_stat", lambda k: 0.0)("atk_spd")
    base_spd = member.class_info.get("base_speed", 2.2)
    reduction = min(0.70, player.stat_crit * 0.015 + gear_spd + set_spd + inner_spd + legion_spd)
    if member.is_buffed:
        reduction += 0.35
    team_spd_buff = player.get_buff_val("speed_bonus") + player.get_buff_val("union")
    reduction += team_spd_buff
    return max(0.40, base_spd - reduction)


def calc_life_steal(player) -> float:
    """計算生命吸血率（上限 40%）"""
    gear_vamp = player.get_gear_stat_sum("life_steal")
    union_vamp = player.get_buff_val("union") * 0.6
    legion_vamp = getattr(player, "get_legion_stat", lambda k: 0.0)("lifesteal")
    return min(0.40, gear_vamp + union_vamp + legion_vamp)


