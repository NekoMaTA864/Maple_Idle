"""
新楓之谷：放置遠征隊 - 官方正統裝備核心系統 (item_system.py)
採用模組化架構，作為核心 Facade 介面統一對外提供：
1. 裝備目錄與規格資料 (item_catalog.py)
2. 正統套裝定義與套裝加成 (item_sets.py)
3. 潛能系統與台服艾比卷軸強化 (item_potential.py)
4. 黃金轉蛋機抽獎邏輯 (item_gachapon.py)
5. 核心裝備資料結構 (Item) 與掉落生成 (generate_loot)
6. 特殊種子戒指 (規範之戒、持續之戒、武器泡泡等) 規格支援
"""

import math
import random
import uuid

# 匯入並統一 Re-export 子模組所有常數與資料結構，維持 100% 向下相容
from item_catalog import (
    RARITIES, RARITY_INFO, SLOT_NAMES, CATEGORY_TO_SLOTS, SLOT_TO_CATEGORY,
    AFFIX_POOL, SPECIAL_SEED_RINGS, BASE_NAMES, ITEM_REQUIRED_LEVEL, ITEM_INHERENT_RARITY
)
from item_sets import (
    SET_DEFINITIONS, ITEM_SET_MAPPING
)
from item_potential import (
    POTENTIAL_RANKS, POTENTIAL_RANK_INFO, CUBE_COSTS,
    WSE_SLOTS, ACCESSORY_SLOTS, ARMOR_SLOTS,
    get_slot_potential_pool, POTENTIAL_POOLS, ABBY_SCROLLS
)
from item_gachapon import (
    draw_gachapon
)
from settings import (
    COLOR_COMMON, COLOR_UNCOMMON, COLOR_RARE, COLOR_EPIC, COLOR_LEGENDARY
)


def create_seed_ring(ring_name: str) -> "Item":
    """
    建立起源之塔特殊種子戒指 (如：規範之戒、持續之戒、武器泡泡之戒)：
    - 具備 is_seed_ring 特殊標記
    - 綁定專屬技能種子識別 (seed_skill) 與技能等級 (skill_level)
    - 專供 BOSS 討伐掉落與黃金轉蛋大獎獲取
    """
    info = SPECIAL_SEED_RINGS.get(ring_name, SPECIAL_SEED_RINGS["規範之戒"])
    item = Item(
        slot="ring",
        rarity=info.get("rarity", "epic"),
        level_req=info.get("level_req", 110),
        base_name=info.get("name", ring_name),
        stats=dict(info.get("stats", {"attack": 4, "defense": 2, "hp": 100})),
        potential_rank="epic"
    )
    item.is_seed_ring = True
    item.seed_skill = info.get("seed_skill", "restraint")
    item.skill_level = info.get("skill_level", 4)
    item.description = info.get("description", "")
    return item


class Item:
    def __init__(self, slot, rarity, level_req, base_name, stats, affixes=None, set_id=None,
                 potential_rank=None, potential_lines=None, locked=False,
                 is_seed_ring=False, seed_skill=None, skill_level=4):
        self.uid = str(uuid.uuid4())[:8]
        self.slot = slot
        self.level_req = ITEM_REQUIRED_LEVEL.get(base_name, level_req)
        self.item_level = self.level_req
        self.base_name = base_name
        self.locked = bool(locked)

        # 特殊種子戒指屬性 (起源之塔)
        self.is_seed_ring = bool(is_seed_ring or base_name in SPECIAL_SEED_RINGS)
        if self.is_seed_ring:
            s_info = SPECIAL_SEED_RINGS.get(base_name, {})
            self.seed_skill = seed_skill or s_info.get("seed_skill")
            self.skill_level = skill_level or s_info.get("skill_level", 4)
            self.description = s_info.get("description", "")
        else:
            self.seed_skill = None
            self.skill_level = 0
            self.description = ""

        # 稀有度由裝備名稱固定決定 (同名裝備稀有度完全一致)
        self.rarity = ITEM_INHERENT_RARITY.get(base_name, rarity or "common")
        self.stats = stats
        self.affixes = affixes or []
        self.enhance_level = 0
        self.sell_price = self._calc_base_price()

        # 套裝歸屬 (自動比對官方對應)
        self.set_id = set_id or ITEM_SET_MAPPING.get(base_name)
        if self.set_id and self.set_id in SET_DEFINITIONS:
            self.set_name = SET_DEFINITIONS[self.set_id]["name"]
        else:
            self.set_name = None

        # 正統新楓之谷潛能系統
        self.potential_rank = potential_rank or "rare"
        if potential_lines is not None:
            self.potential_lines = potential_lines
        else:
            # 預設生成初始潛能 (使用部位潛能池)
            pool = get_slot_potential_pool(self.slot, self.potential_rank)
            cnt = 3 if self.potential_rank in ["unique", "legendary"] else 2
            self.potential_lines = random.sample(pool, min(cnt, len(pool)))

    def _calc_base_price(self):
        r_mult = RARITY_INFO.get(self.rarity, {}).get("mult", 1.0)
        lvl = max(1, self.level_req)
        if lvl < 100:
            base = lvl * 35
        elif lvl <= 140:
            base = 8000 + (lvl - 100) * 250
        elif lvl <= 199:
            base = 20000 + (lvl - 140) * 500
        else:
            base = 80000 + (lvl - 200) * 1000
        return max(100, int(base * r_mult))

    @property
    def starforce_str(self):
        return f"★{self.enhance_level}" if self.enhance_level > 0 else ""

    @property
    def full_name(self):
        """純淨新楓之谷官方裝備名稱，杜絕任何加油添醋的前綴詞"""
        r_name = RARITY_INFO.get(self.rarity, {}).get("name", "普通")
        pot_name = POTENTIAL_RANK_INFO.get(self.potential_rank, {}).get("name", "特殊")
        star = f" ★{self.enhance_level}" if self.enhance_level > 0 else ""
        lock_str = " [🔒]" if self.locked else ""
        seed_tag = " [塔戒]" if self.is_seed_ring else ""
        return f"[{r_name}] {self.base_name}{star}{seed_tag} ({pot_name}潛能){lock_str}"

    @property
    def color(self):
        if self.is_seed_ring:
            return (255, 120, 180)
        return RARITY_INFO.get(self.rarity, {}).get("color", COLOR_COMMON)

    def get_display_name(self, star_level=None):
        """依據傳入之欄位星力 (或預設星力) 獲取純淨名稱與潛能標籤"""
        r_name = RARITY_INFO.get(self.rarity, {}).get("name", "普通")
        pot_name = POTENTIAL_RANK_INFO.get(self.potential_rank, {}).get("name", "特殊")
        star_val = self.enhance_level if star_level is None else star_level
        star = f" ★{star_val}" if star_val > 0 else ""
        lock_str = " [🔒]" if self.locked else ""
        seed_tag = " [塔戒]" if self.is_seed_ring else ""
        return f"[{r_name}] {self.base_name}{star}{seed_tag} ({pot_name}潛能){lock_str}"

    def get_effective_stats(self, star_level=None, slot_potentials=None, slot_scrolls=None):
        """
        計算實際生效總數值：
        - 欄位星力 (每星 +7%)
        - 艾比卷軸強化數值 (slot_scrolls)
        - 欄位主潛能與附加潛能 (slot_potentials)
        - 換裝時星力、卷軸、潛能永久保留於欄位！
        """
        effective_star = self.enhance_level if star_level is None else star_level
        star_mult = 1.0 + effective_star * 0.07

        # 彙整卷軸屬性
        scroll_atk = 0
        scroll_hp = 0
        scroll_def = 0
        scroll_all_stat = 0
        scroll_crit = 0.0
        scroll_def_ign = 0.0

        if slot_scrolls and isinstance(slot_scrolls, dict):
            s_stats = slot_scrolls.get("stats", {})
            scroll_atk = s_stats.get("attack", 0)
            scroll_hp = s_stats.get("hp", 0)
            scroll_def = s_stats.get("defense", 0)
            scroll_all_stat = s_stats.get("all_stat", 0)
            scroll_crit = s_stats.get("crit_chance", 0.0)
            scroll_def_ign = s_stats.get("def_ignore", 0.0)

        # 彙整潛能屬性加成 (優先讀取欄位主潛能與附加潛能)
        pot_atk_pct = 0.0
        pot_all_pct = 0.0
        pot_atk_flat = 0
        pot_hp_flat = 0
        pot_def_flat = 0
        pot_crit = 0.0
        pot_speed = 0.0
        pot_vamp = 0.0
        pot_crit_dmg = 0.0
        pot_def_ign = 0.0
        pot_dmg_mult = 0.0
        pot_boss_dmg = 0.0
        pot_cooldown = 0.0
        pot_drop_rate = 0.0
        pot_meso_rate = 0.0

        lines_to_process = []
        if slot_potentials and isinstance(slot_potentials, dict):
            main_lines = slot_potentials.get("main", {}).get("lines", [])
            bonus_lines = slot_potentials.get("bonus", {}).get("lines", [])
            lines_to_process.extend(main_lines)
            lines_to_process.extend(bonus_lines)
        else:
            lines_to_process = getattr(self, "potential_lines", [])

        for line in lines_to_process:
            st = line.get("stat")
            val = line.get("val", 0)
            if st == "attack_pct":
                pot_atk_pct += val
            elif st == "all_stat_pct":
                pot_all_pct += val
            elif st == "all_stat_flat":
                scroll_all_stat += int(val)
            elif st == "attack_flat":
                pot_atk_flat += int(val)
            elif st == "hp_flat":
                pot_hp_flat += int(val)
            elif st == "defense_flat":
                pot_def_flat += int(val)
            elif st == "crit_chance":
                pot_crit += val
            elif st == "attack_speed":
                pot_speed += val
            elif st == "life_steal":
                pot_vamp += val
            elif st == "crit_dmg":
                pot_crit_dmg += val
            elif st == "def_ignore":
                pot_def_ign += val
            elif st in ["damage_mult", "team_dmg_pct"]:
                pot_dmg_mult += val
            elif st == "boss_dmg":
                pot_boss_dmg += val
            elif st == "cooldown_reduction":
                pot_cooldown += val
            elif st == "drop_rate":
                pot_drop_rate += val
            elif st == "meso_rate":
                pot_meso_rate += val

        eff = {}
        for k, v in self.stats.items():
            if k == "attack":
                base_atk = v + scroll_atk + scroll_all_stat
                eff["attack"] = int(round(base_atk * star_mult * (1.0 + pot_atk_pct + pot_all_pct))) + pot_atk_flat
            elif k == "hp":
                base_hp = v + scroll_hp + scroll_all_stat * 10
                eff["hp"] = int(round(base_hp * star_mult * (1.0 + pot_all_pct))) + pot_hp_flat
            elif k == "defense":
                base_def = v + scroll_def + scroll_all_stat * 2
                eff["defense"] = int(round(base_def * star_mult * (1.0 + pot_all_pct))) + pot_def_flat
            elif k == "crit_chance":
                eff["crit_chance"] = round(v * star_mult + pot_crit + scroll_crit, 4)
            elif k == "attack_speed":
                eff["attack_speed"] = round(v * star_mult + pot_speed, 4)
            elif k == "life_steal":
                eff["life_steal"] = round(v * star_mult + pot_vamp, 4)
            else:
                eff[k] = round(v * star_mult, 4)

        if "attack" not in eff and (pot_atk_flat > 0 or scroll_atk > 0):
            eff["attack"] = pot_atk_flat + scroll_atk
        if "hp" not in eff and (pot_hp_flat > 0 or scroll_hp > 0):
            eff["hp"] = pot_hp_flat + scroll_hp
        if "defense" not in eff and (pot_def_flat > 0 or scroll_def > 0):
            eff["defense"] = pot_def_flat + scroll_def
        if (pot_crit > 0 or scroll_crit > 0) and "crit_chance" not in eff:
            eff["crit_chance"] = round(pot_crit + scroll_crit, 4)
        if pot_crit_dmg > 0:
            eff["crit_dmg"] = round(pot_crit_dmg, 4)
        if (pot_def_ign > 0 or scroll_def_ign > 0):
            eff["def_ignore"] = round(pot_def_ign + scroll_def_ign, 4)
        if pot_dmg_mult > 0:
            eff["damage_mult"] = round(pot_dmg_mult, 4)
        if pot_boss_dmg > 0:
            eff["boss_dmg"] = round(pot_boss_dmg, 4)
        if pot_cooldown > 0:
            eff["cooldown_reduction"] = round(pot_cooldown, 1)
        if pot_drop_rate > 0:
            eff["drop_rate"] = round(pot_drop_rate, 4)
        if pot_meso_rate > 0:
            eff["meso_rate"] = round(pot_meso_rate, 4)

        return eff

    def cube_potential(self, cube_type="mystic"):
        """洗潛能 (Cube Potential)：重骰潛能詞條並有機率提升階級"""
        did_tier_up = False
        if cube_type == "mystic":
            if self.potential_rank == "rare" and random.random() < 0.18:
                self.potential_rank = "epic"
                did_tier_up = True
        elif cube_type == "bright":
            if self.potential_rank == "rare" and random.random() < 0.35:
                self.potential_rank = "epic"
                did_tier_up = True
            elif self.potential_rank == "epic" and random.random() < 0.16:
                self.potential_rank = "unique"
                did_tier_up = True
            elif self.potential_rank == "unique" and random.random() < 0.08:
                self.potential_rank = "legendary"
                did_tier_up = True

        current_pool = get_slot_potential_pool(self.slot, self.potential_rank)
        line_count = 3 if self.potential_rank in ["unique", "legendary"] else 2
        self.potential_lines = random.sample(current_pool, min(line_count, len(current_pool)))
        return did_tier_up, self.potential_rank, self.potential_lines

    def matches_cube_target(self, target_rank="unique", target_stat_keyword=None):
        rank_order = {"rare": 1, "epic": 2, "unique": 3, "legendary": 4}
        cur_order = rank_order.get(self.potential_rank, 1)
        tgt_order = rank_order.get(target_rank, 3)

        if cur_order >= tgt_order:
            if not target_stat_keyword:
                return True
            for line in self.potential_lines:
                if target_stat_keyword in line.get("name", ""):
                    return True
        return False

    def to_dict(self):
        return {
            "uid": self.uid,
            "slot": self.slot,
            "rarity": self.rarity,
            "level_req": self.level_req,
            "base_name": self.base_name,
            "stats": self.stats,
            "affixes": self.affixes,
            "enhance_level": self.enhance_level,
            "sell_price": self.sell_price,
            "set_id": self.set_id,
            "potential_rank": self.potential_rank,
            "potential_lines": self.potential_lines,
            "locked": self.locked,
            "is_seed_ring": getattr(self, "is_seed_ring", False),
            "seed_skill": getattr(self, "seed_skill", None),
            "skill_level": getattr(self, "skill_level", 4),
            "description": getattr(self, "description", ""),
        }

    @staticmethod
    def from_dict(d):
        base_name = d.get("base_name", "木製短劍")
        set_id = d.get("set_id") or ITEM_SET_MAPPING.get(base_name)
        item = Item(
            slot=d["slot"],
            rarity=d.get("rarity", ITEM_INHERENT_RARITY.get(base_name, "common")),
            level_req=d.get("level_req", 10),
            base_name=base_name,
            stats=d["stats"],
            affixes=d.get("affixes", []),
            set_id=set_id,
            potential_rank=d.get("potential_rank", "rare"),
            potential_lines=d.get("potential_lines"),
            locked=d.get("locked", False),
            is_seed_ring=d.get("is_seed_ring", base_name in SPECIAL_SEED_RINGS),
            seed_skill=d.get("seed_skill") or (SPECIAL_SEED_RINGS.get(base_name, {}).get("seed_skill")),
            skill_level=d.get("skill_level", 4)
        )
        item.uid = d.get("uid", item.uid)
        item.enhance_level = d.get("enhance_level", 0)
        item.sell_price = d.get("sell_price", item._calc_base_price())
        item.description = d.get("description", getattr(item, "description", ""))
        return item


def generate_loot(zone_level, is_boss=False, player_level=None, source_type=None):
    """
    依照當前地圖等級與怪物階級，生成固定稀有度與正統潛能的新楓之谷神裝：
    - 普通小怪：僅掉落低階至中階裝備 (嚴格禁止掉落漆黑、永恆與特殊種子戒指)
    - Boss (Zone 15+)：才有低機率掉落神話級 (漆黑/神秘冥界/永恆神恩)
    - 所有裝備等級固定為 ITEM_REQUIRED_LEVEL (杜絕浮動等級)
    """
    all_categories = list(BASE_NAMES.keys())
    slot = random.choice(all_categories)
    name_list = BASE_NAMES[slot]

    # 普通小怪排除 legendary 頂裝
    if not is_boss:
        eligible_names = [n for n in name_list if ITEM_INHERENT_RARITY.get(n) != "legendary"]
        if not eligible_names:
            eligible_names = name_list
    else:
        # 僅在深層 Boss (zone_level >= 180) 才開放全部神裝 (包含漆黑與永恆)
        if zone_level < 180:
            eligible_names = [n for n in name_list if ITEM_INHERENT_RARITY.get(n) != "legendary"]
            if not eligible_names:
                eligible_names = name_list
        else:
            eligible_names = name_list

    # 以區域與玩家等級共同定位掉落，讓低等過渡裝仍有機會出現。
    player_level = int(player_level or zone_level)
    target_level = max(int(zone_level), player_level)
    source_type = source_type or ("boss" if is_boss else "normal")
    if source_type == "boss":
        min_drop_req, max_drop_req, target_bias = target_level, target_level + 15, 8
    elif source_type == "elite":
        min_drop_req, max_drop_req, target_bias = target_level - 5, target_level + 10, 5
    else:
        min_drop_req, max_drop_req, target_bias = target_level - 10, target_level + 5, 0
    candidates = [
        n for n in eligible_names
        if min_drop_req <= ITEM_REQUIRED_LEVEL.get(n, 10) <= max_drop_req
    ]
    if not candidates:
        candidates = [
            n for n in eligible_names
            if ITEM_REQUIRED_LEVEL.get(n, 10) <= max_drop_req
        ]
    if not candidates:
        candidates = [min(eligible_names, key=lambda n: ITEM_REQUIRED_LEVEL.get(n, 10))]

    # 以接近目標等級為中心，避免候選越高就越容易超前。
    candidates.sort(key=lambda n: ITEM_REQUIRED_LEVEL.get(n, 10))
    preferred_level = target_level + target_bias
    weights = [
        max(1, 20 - abs(ITEM_REQUIRED_LEVEL.get(n, 10) - preferred_level))
        for n in candidates
    ]
    base_name = random.choices(candidates, weights=weights, k=1)[0]

    # 裝備稀有度完全由名稱決定！同名裝備稀有度完全一致
    rarity = ITEM_INHERENT_RARITY.get(base_name, "common")
    req_level = ITEM_REQUIRED_LEVEL.get(base_name, zone_level)
    r_mult = RARITY_INFO[rarity]["mult"]

    stats = {}
    if slot in ["weapon", "sub_weapon", "emblem"]:
        stats["attack"] = int((14 + req_level * 0.42) * r_mult)
        if random.random() < 0.45:
            stats["crit_chance"] = round(min(0.25, 0.03 + req_level * 0.0003 * r_mult), 3)

    elif slot in ["hat", "top", "bottom", "shoes", "gloves", "cape", "shoulder"]:
        stats["defense"] = int((7 + req_level * 0.22) * r_mult)
        stats["hp"] = int((40 + req_level * 2.2) * r_mult)
        if slot == "shoes" and random.random() < 0.50:
            stats["attack_speed"] = round(min(0.20, 0.02 + req_level * 0.0002 * r_mult), 3)
        if slot == "gloves" and random.random() < 0.50:
            stats["attack"] = int((6 + req_level * 0.16) * r_mult)

    elif slot in ["ring", "pendant", "face", "eye", "earrings", "belt"]:
        stats["defense"] = int((5 + req_level * 0.15) * r_mult)
        stats["hp"] = int((30 + req_level * 1.5) * r_mult)
        stats["attack"] = int((6 + req_level * 0.18) * r_mult)
        if random.random() < 0.45:
            stats["crit_chance"] = round(min(0.20, 0.02 + req_level * 0.0002 * r_mult), 3)
        if random.random() < 0.35:
            stats["life_steal"] = round(min(0.10, 0.015 + req_level * 0.0002 * r_mult), 3)

    elif slot in ["pocket", "badge", "badge_chest", "android", "heart"]:
        stats["attack"] = int((12 + req_level * 0.25) * r_mult)
        stats["defense"] = int((8 + req_level * 0.18) * r_mult)
        stats["hp"] = int((45 + req_level * 2.5) * r_mult)
        stats["crit_chance"] = round(min(0.22, 0.03 + req_level * 0.0002 * r_mult), 3)

    # 抽取附加屬性
    affix_count = RARITY_INFO[rarity]["affix_count"]
    affixes = []
    if affix_count > 0:
        chosen_affixes = random.sample(AFFIX_POOL, min(affix_count, len(AFFIX_POOL)))
        for aff in chosen_affixes:
            stat_key = aff["stat"]
            low, high = aff["bonus_range"]
            lvl_scale = 1.0 + (req_level - 1) * 0.008
            val = round(random.uniform(low, high) * lvl_scale, 3) if isinstance(low, float) else int(round(random.uniform(low, high) * lvl_scale))
            stats[stat_key] = stats.get(stat_key, 0) + val
            affixes.append({"name": aff["name"], "stat": stat_key, "value": val})

    set_id = ITEM_SET_MAPPING.get(base_name)

    # 掉落正統潛能階級判定
    if is_boss:
        pot_roll = random.random()
        if pot_roll < 0.45:
            pot_rank = "epic"
        elif pot_roll < 0.85:
            pot_rank = "unique"
        else:
            pot_rank = "legendary"
    else:
        pot_roll = random.random()
        if pot_roll < 0.70:
            pot_rank = "rare"
        elif pot_roll < 0.95:
            pot_rank = "epic"
        else:
            pot_rank = "unique"

    item = Item(slot, rarity, req_level, base_name, stats, affixes, set_id=set_id, potential_rank=pot_rank)
    return item


def compare_stats(current_item, new_item):
    """對比兩件裝備的屬性差值，回傳 {stat_name: diff_value}"""
    curr_eff = current_item.get_effective_stats() if current_item else {}
    new_eff = new_item.get_effective_stats() if new_item else {}

    all_keys = set(curr_eff.keys()).union(set(new_eff.keys()))
    diff = {}
    for k in all_keys:
        v_curr = curr_eff.get(k, 0)
        v_new = new_eff.get(k, 0)
        diff[k] = v_new - v_curr
    return diff


def calc_item_combat_score(item, slot_star=0):
    """計算裝備的綜合戰力評分 (Combat Power)，用於一鍵換裝最佳化與篩選劣質裝備"""
    if not item:
        return 0.0
    stats = item.get_effective_stats(slot_star)
    r_mult = RARITY_INFO.get(item.rarity, {}).get("stat_mult", 1.0)
    score = (
        stats.get("attack", 0) * 4.5 +
        stats.get("defense", 0) * 1.8 +
        stats.get("hp", 0) * 0.16 +
        stats.get("crit_chance", 0.0) * 400.0 +
        stats.get("attack_speed", 0.0) * 250.0 +
        stats.get("life_steal", 0.0) * 300.0 +
        r_mult * 25.0 +
        (30.0 if item.set_id else 0.0)
    )
    return round(score, 1)
