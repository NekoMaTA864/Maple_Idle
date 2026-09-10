"""
《新楓之谷：放置遠征隊》首領與怪物技能與動態數值系統 (monster_skills.py)
包含：
- 首領專屬招式 (全屏震地、穿透死光、虛空護盾、黑暗詛咒、殘血狂暴)
- 動態層數數值遞增演算 (Floors 1~9 平滑成長、Floor 10 首領爆發)
- 怪物 AI 技能冷卻與發動決策
"""

import math
import random


class MonsterSkill:
    """怪物/首領技能實體"""
    def __init__(self, skill_id, name, cooldown, target_type="aoe_all",
                 dmg_mult=1.0, debuff_type=None, debuff_duration=5.0,
                 shield_val=0, vfx_kind="explosion", vfx_color=(255, 60, 60),
                 cast_desc=""):
        self.skill_id = skill_id
        self.name = name
        self.cooldown = cooldown
        self.timer = random.uniform(1.5, cooldown * 0.6)  # 開局隨機初始冷卻，避免瞬間秒殺
        self.target_type = target_type                    # 'aoe_all', 'random_multi', 'single_tank', 'self_shield', 'curse_all'
        self.dmg_mult = dmg_mult
        self.debuff_type = debuff_type                    # 'weaken', 'burn', 'bleed', 'chill'
        self.debuff_duration = debuff_duration
        self.shield_val = shield_val
        self.vfx_kind = vfx_kind
        self.vfx_color = vfx_color
        self.cast_desc = cast_desc

    @property
    def is_ready(self):
        return self.timer <= 0.0

    def update(self, dt):
        if self.timer > 0.0:
            self.timer -= dt

    def trigger(self):
        self.timer = self.cooldown

    def clone(self, rng=None):
        s = MonsterSkill(
            self.skill_id, self.name, self.cooldown, self.target_type,
            self.dmg_mult, self.debuff_type, self.debuff_duration,
            self.shield_val, self.vfx_kind, self.vfx_color, self.cast_desc
        )
        rng = random if rng is None else rng
        s.timer = rng.uniform(2.0, self.cooldown * 0.7)
        return s


# =========================================================================
# 經典首領技能池 (Boss Skills Pool)
# =========================================================================
BOSS_SKILLS_CATALOG = {
    "earthquake_slam": MonsterSkill(
        "earthquake_slam", "撼地重擊", cooldown=8.5, target_type="aoe_all",
        dmg_mult=0.75, vfx_kind="explosion", vfx_color=(255, 120, 40),
        cast_desc="引爆毀滅地裂震波！對遠征隊全員造成 AOE 衝擊打擊！"
    ),
    "chaos_laser": MonsterSkill(
        "chaos_laser", "毀滅死光", cooldown=9.0, target_type="random_multi",
        dmg_mult=1.35, vfx_kind="laser_blast", vfx_color=(255, 40, 120),
        cast_desc="凝聚高能混沌死光，貫穿掃射遠征隊多名成員！"
    ),
    "void_barrier": MonsterSkill(
        "void_barrier", "虛空暗影護盾", cooldown=14.0, target_type="self_shield",
        shield_val=350, vfx_kind="support_gate", vfx_color=(160, 60, 255),
        cast_desc="張開深淵暗影護盾！吸收大量傷害並抵禦衝擊！"
    ),
    "dark_curse": MonsterSkill(
        "dark_curse", "虛弱詛咒", cooldown=12.0, target_type="curse_all",
        debuff_type="weaken", debuff_duration=6.0, vfx_kind="distortion_bomb_singularity",
        vfx_color=(120, 40, 200), cast_desc="散播上古虛弱詛咒！全員攻擊力降低 25%，持續 6 秒！"
    ),
    "hell_fire": MonsterSkill(
        "hell_fire", "地獄烈焰", cooldown=10.0, target_type="single_tank",
        dmg_mult=1.2, debuff_type="burn", debuff_duration=5.0, vfx_kind="magnum_punch",
        vfx_color=(255, 80, 20), cast_desc="噴湧地獄黑炎重創前排戰士，並附加深度灼燒！"
    ),
    "frost_nova": MonsterSkill(
        "frost_nova", "極寒冰爆", cooldown=11.0, target_type="aoe_all",
        dmg_mult=0.65, debuff_type="chill", debuff_duration=5.0, vfx_kind="ice",
        vfx_color=(80, 200, 255), cast_desc="釋放刺骨極寒冰霜，凍結大地並大幅減緩全員攻速！"
    ),
}


def get_skills_for_boss(zone_id, boss_name="", skill_kit=None, rng=None):
    """依據區域 skill_kit 或主題為首領配置專屬戰術技能"""
    if skill_kit:
        skills = []
        for sk_id in skill_kit:
            if sk_id in BOSS_SKILLS_CATALOG:
                skills.append(BOSS_SKILLS_CATALOG[sk_id].clone(rng=rng))
        if skills:
            return skills

    skills = []
    # 所有 Boss 均配置基礎 AOE 震地
    skills.append(BOSS_SKILLS_CATALOG["earthquake_slam"].clone(rng=rng))

    if "冰" in zone_id or "雪" in boss_name or "elnath" in zone_id:
        skills.append(BOSS_SKILLS_CATALOG["frost_nova"].clone(rng=rng))
    elif "炎魔" in boss_name or "世界樹" in zone_id or "荒野" in zone_id or "world_tree" in zone_id or "perion" in zone_id:
        skills.append(BOSS_SKILLS_CATALOG["hell_fire"].clone(rng=rng))
    elif "神殿" in zone_id or "黑魔法師" in boss_name or "利曼" in zone_id or "temple" in zone_id or "limen" in zone_id:
        skills.append(BOSS_SKILLS_CATALOG["dark_curse"].clone(rng=rng))
        skills.append(BOSS_SKILLS_CATALOG["chaos_laser"].clone(rng=rng))
    elif "玩具城" in zone_id or "機械" in zone_id or "ludi" in zone_id or "scrapyard" in zone_id:
        skills.append(BOSS_SKILLS_CATALOG["chaos_laser"].clone(rng=rng))
    else:
        # 預設通用技能：虛空護盾
        skills.append(BOSS_SKILLS_CATALOG["void_barrier"].clone(rng=rng))

    return skills


def scale_monster_stats(base_data, floor=1, is_boss=False):
    """
    動態層數數值梯度演算：
    - 普通怪物 (1~9 層)：每層微幅遞增 8% HP, 5% ATK, 4% DEF
    - 區域首領 (第 10 層)：基礎數值強化，並根據層數享有首領加權
    """
    scaled = dict(base_data)
    floor = max(1, min(10, floor))

    if not is_boss:
        # 1~9 層梯隊推進
        floor_mult_hp = 1.0 + (floor - 1) * 0.10
        floor_mult_atk = 1.0 + (floor - 1) * 0.06
        floor_mult_def = 1.0 + (floor - 1) * 0.05
        scaled["hp"] = int(base_data["hp"] * floor_mult_hp)
        scaled["atk"] = max(1, int(base_data["atk"] * floor_mult_atk))
        scaled["def"] = max(1, int(base_data["def"] * floor_mult_def))
    else:
        # 第 10 層區域首領
        boss_hp_mult = 1.25 + (floor * 0.05)
        scaled["hp"] = int(base_data["hp"] * boss_hp_mult)
        scaled["atk"] = max(1, int(base_data["atk"] * 1.15))
        scaled["def"] = max(1, int(base_data["def"] * 1.15))

    return scaled
