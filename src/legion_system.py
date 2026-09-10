"""
新楓之谷：放置冒險記 - 聯盟戰地 (Legion) 後援支援系統 (legion_system.py)
未登場的職業將自動進入戰地後援陣列，提供強大的全域被動屬性光環。
"""

LEGION_EFFECTS = {
    "hero": {
        "name": "英雄", "desc": "全隊傷害 +3.0%",
        "stats": {"damage_mult": 0.03}
    },
    "dark_knight": {
        "name": "黑騎士", "desc": "全隊生命 +5.0%，吸血率 +2.0%",
        "stats": {"hp_pct": 0.05, "lifesteal": 0.02}
    },
    "paladin": {
        "name": "聖騎士", "desc": "全隊防禦 +6.0%，傷害減免 +3.0%",
        "stats": {"def_pct": 0.06, "dmg_reduction": 0.03}
    },
    "bowmaster": {
        "name": "箭神", "desc": "全隊暴擊率 +3.0%",
        "stats": {"crit_chance": 0.03}
    },
    "marksman": {
        "name": "神射手", "desc": "全隊暴擊傷害 +3.5%",
        "stats": {"crit_dmg": 0.035}
    },
    "pathfinder": {
        "name": "開拓者", "desc": "全隊攻速 +3.0%，暴擊率 +2.0%",
        "stats": {"atk_spd": 0.03, "crit_chance": 0.02}
    },
    "fire_poison_mage": {
        "name": "火毒魔導士", "desc": "全隊BOSS傷害 +3.5%，DOT持續傷害 +5.0%",
        "stats": {"boss_dmg": 0.035, "dot_damage": 0.05}
    },
    "ice_lightning_mage": {
        "name": "冰雷魔導士", "desc": "全隊攻擊力 +15，終極傷害 +2.0%",
        "stats": {"attack": 15, "final_dmg": 0.02}
    },
    "bishop": {
        "name": "主教", "desc": "全隊經驗值獲得 +8.0%，治癒量 +15.0%",
        "stats": {"exp_mult": 0.08, "heal_mult": 0.15}
    },
    "night_lord": {
        "name": "夜使者", "desc": "全隊暴擊傷害 +4.0%",
        "stats": {"crit_dmg": 0.04}
    },
    "shadower": {
        "name": "暗影神偷", "desc": "全隊楓幣獲得 +10.0%，暴擊率 +2.0%",
        "stats": {"gold_mult": 0.10, "crit_chance": 0.02}
    },
    "dual_blade": {
        "name": "影武者", "desc": "全隊終極傷害 +3.0%",
        "stats": {"final_dmg": 0.03}
    },
    "buccaneer": {
        "name": "拳霸", "desc": "全隊攻擊力 +20，BOSS傷害 +2.0%",
        "stats": {"attack": 20, "boss_dmg": 0.02}
    },
    "corsair": {
        "name": "槍神", "desc": "全隊多段打擊傷害 +5.0%，攻擊力 +15",
        "stats": {"attack": 15, "multi_hit": 0.05}
    },
    "cannoneer": {
        "name": "重砲指揮官", "desc": "全隊全屬性 +15，攻擊力 +15",
        "stats": {"all_stat": 15, "attack": 15}
    },
    "dawn_warrior": {
        "name": "聖魂劍士", "desc": "全隊無視防禦 +4.0%",
        "stats": {"def_ignore": 0.04}
    },
    "flame_wizard": {
        "name": "烈焰巫師", "desc": "全隊攻擊力 +15，傷害 +2.5%",
        "stats": {"attack": 15, "damage_mult": 0.025}
    },
    "wind_archer": {
        "name": "破風使者", "desc": "全隊暴擊率 +3.0%，攻擊速度 +3.0%",
        "stats": {"crit_chance": 0.03, "atk_spd": 0.03}
    },
    "night_walker": {
        "name": "暗夜行者", "desc": "全隊暴擊傷害 +3.5%，攻擊力 +10",
        "stats": {"crit_dmg": 0.035, "attack": 10}
    },
    "thunder_breaker": {
        "name": "閃雷悍將", "desc": "全隊終極傷害 +2.5%",
        "stats": {"final_dmg": 0.025}
    },
    "wild_hunter": {
        "name": "狂豹獵人", "desc": "全隊傷害 +3.0%，攻擊力 +10",
        "stats": {"damage_mult": 0.03, "attack": 10}
    },
    "blaster": {
        "name": "爆拳槍神", "desc": "全隊無視防禦 +4.0%",
        "stats": {"def_ignore": 0.04}
    },
    "mechanic": {
        "name": "機甲戰神", "desc": "全隊增益持續時間 +15.0%",
        "stats": {"buff_duration": 0.15}
    },
    "battle_mage": {
        "name": "煉獄巫師", "desc": "全隊光環增益效果 +15.0%，攻擊力 +10",
        "stats": {"attack": 10, "aura_bonus": 0.15}
    },
}


def calc_legion_bonuses(bench_classes):
    """
    計算目前後援陣列所有職業提供的戰地被動屬性總和
    :param bench_classes: 未上場的職業 ID 清單
    :return: 屬性加總字典
    """
    totals = {
        "attack": 0,
        "damage_mult": 0.0,
        "boss_dmg": 0.0,
        "final_dmg": 0.0,
        "crit_chance": 0.0,
        "crit_dmg": 0.0,
        "def_ignore": 0.0,
        "hp_pct": 0.0,
        "def_pct": 0.0,
        "atk_spd": 0.0,
        "gold_mult": 0.0,
        "exp_mult": 0.0,
        "lifesteal": 0.0,
    }

    for cid in bench_classes:
        eff = LEGION_EFFECTS.get(cid)
        if eff and "stats" in eff:
            for k, val in eff["stats"].items():
                if k in totals:
                    totals[k] += val
                else:
                    totals[k] = val
    return totals

