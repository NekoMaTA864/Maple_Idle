"""
新楓之谷：放置遠征隊 - 玩家資料與 5 人遠征隊系統核心門面 (player_data.py)
職責已解耦拆分至子模組：
- player_stats.py: 屬性、套裝加成運算
- player_gear.py: 裝備穿脫、星力強化、潛能洗練
- player_save.py: 存讀檔序列化與持久化
- player_offline.py: 離線掛機結算
- player_symbols.py: ARC / AUT 符號與碎片管理
"""

from settings import INVENTORY_CAPACITY
from item_system import Item, SLOT_NAMES
from classes import ALL_CLASSES, get_class_info
from player_symbols import (
    ARC_SYMBOLS_DATA, AUT_SYMBOLS_DATA,
    calculate_total_arc, calculate_total_aut, calculate_symbol_stat_sum,
    get_symbol_display_name, get_symbol_upgrade_req
)
import player_stats
import player_gear
import player_save
from inner_ability import InnerAbility
from pet_system import PetManager
from familiar_system import FamiliarManager


class TeamMember:
    """遠征隊成員 (席位 0 為主角，席位 1~6 為隨行護衛夥伴)"""
    def __init__(self, slot_idx, class_id, player=None):
        self.slot_idx = slot_idx
        self.class_id = class_id
        self.player = player
        self.class_info = get_class_info(class_id)
        self.skills = [s.clone() for s in self.class_info["skills"]]

        # 技能槽位配置 (主角預設 6 招，Lv.100 解鎖至 12 招；夥伴每人至多 2 招)
        self.equipped_skills = []
        avail = self.get_available_skills()
        self.equipped_skills = avail[:self.max_skill_slots]
        self.equipped_skill_indices = list(range(len(self.equipped_skills)))

        self.attack_timer = 0.0
        self.cast_delay_timer = slot_idx * 0.08  # 席位錯峰施法間隔
        self._shield = 0.0
        self._hp = 120.0

        # 職業專屬機制與增益狀態
        self.mechanic_stacks = 0
        self.mechanic_timer = 0.0
        self.is_buffed = False
        self.buff_timer = 0.0

        if self.is_protagonist:
            if player:
                self._hp = float(self.get_max_hp(player))
            else:
                self._hp = 120.0

    @property
    def is_protagonist(self):
        """是否為核心玩家主角 (席位 0)"""
        return self.slot_idx == 0

    @property
    def max_skill_slots(self):
        """技能槽位數量：主角預設 6 招，Lv.100 擴充至 12 招；夥伴固定 2 招"""
        if self.is_protagonist:
            lvl = self.player.level if self.player else 1
            return 12 if lvl >= 100 else 6
        return 2

    @property
    def name(self):
        return self.class_info["name"]

    @property
    def faction(self):
        return self.class_info["faction"]

    @property
    def branch(self):
        return self.class_info["branch"]

    @property
    def is_alive(self):
        """存活判定：作戰系統只計算主角血防，夥伴全體不死 (隨主角生死同步)"""
        if self.is_protagonist:
            return self._hp > 0
        if self.player and self.player.team:
            return self.player.team[0].is_alive
        return True

    @property
    def current_hp(self):
        """血量數值：夥伴共享/依託於主角生命池"""
        if self.is_protagonist:
            return self._hp
        if self.player and self.player.team:
            return self.player.team[0].current_hp
        return 120.0

    @current_hp.setter
    def current_hp(self, val):
        if self.is_protagonist:
            self._hp = float(val)
        elif self.player and self.player.team:
            self.player.team[0].current_hp = val

    @property
    def shield(self):
        """護盾值：全隊護盾統一匯入主角護盾池"""
        if self.is_protagonist:
            return self._shield
        if self.player and self.player.team:
            return self.player.team[0].shield
        return 0.0

    @shield.setter
    def shield(self, val):
        if self.is_protagonist:
            self._shield = float(val)
        elif self.player and self.player.team:
            self.player.team[0].shield = val

    def get_available_skills(self):
        """獲取該成員可選配的技能庫：主角享用母職業群龐大技能庫 (24招)，夥伴為本職技能"""
        if self.is_protagonist:
            from classes import get_mother_group_skills
            return get_mother_group_skills(self.class_id)
        else:
            return [s.clone() for s in self.class_info["skills"]]

    def get_active_skills(self):
        """獲取當前已裝備出戰的主動技能清單"""
        limit = self.max_skill_slots
        if hasattr(self, "equipped_skills") and self.equipped_skills:
            return self.equipped_skills[:limit]
        avail = self.get_available_skills()
        self.equipped_skills = avail[:limit]
        return self.equipped_skills[:limit]

    def set_equipped_skills(self, skill_list):
        """更新裝備的技能清單"""
        limit = self.max_skill_slots
        self.equipped_skills = [s.clone() for s in skill_list[:limit]]
        self.equipped_skill_indices = list(range(len(self.equipped_skills)))

    def equip_skill(self, skill):
        """裝備技能"""
        if not hasattr(self, "equipped_skills"):
            self.equipped_skills = []
        for s in self.equipped_skills:
            if s.skill_id == skill.skill_id:
                return False, "技能已在裝備槽中"
        if len(self.equipped_skills) >= self.max_skill_slots:
            return False, f"技能槽位已滿 (當前上限: {self.max_skill_slots} 招)"
        self.equipped_skills.append(skill.clone())
        self.equipped_skill_indices = list(range(len(self.equipped_skills)))
        return True, "裝備成功"

    def unequip_skill(self, skill_id):
        """卸下技能"""
        if not hasattr(self, "equipped_skills"):
            return False, "無裝備技能"
        if len(self.equipped_skills) <= 1:
            return False, "至少需保留 1 個出戰技能"
        self.equipped_skills = [s for s in self.equipped_skills if s.skill_id != skill_id]
        self.equipped_skill_indices = list(range(len(self.equipped_skills)))
        return True, "已卸下技能"

    def toggle_skill_by_id(self, skill_id):
        """依 skill_id 切換技能裝備狀態"""
        cur_ids = [s.skill_id for s in self.get_active_skills()]
        if skill_id in cur_ids:
            return self.unequip_skill(skill_id)
        else:
            avail = self.get_available_skills()
            target_skill = next((s for s in avail if s.skill_id == skill_id), None)
            if not target_skill:
                all_s = self.class_info.get("skills", [])
                target_skill = next((s for s in all_s if s.skill_id == skill_id), None)
            if target_skill:
                return self.equip_skill(target_skill)
            return False, "找不到對應技能"

    def toggle_skill(self, skill_idx):
        """切換技能槽位啟用狀態 (支援本職索引與母群可用庫索引)"""
        cls_skills = self.class_info.get("skills", [])
        if 0 <= skill_idx < len(cls_skills):
            return self.toggle_skill_by_id(cls_skills[skill_idx].skill_id)
        avail = self.get_available_skills()
        if 0 <= skill_idx < len(avail):
            return self.toggle_skill_by_id(avail[skill_idx].skill_id)
        return False, "無效技能"

    def enable_all_skills(self):
        """一鍵啟用最大上限技能"""
        avail = self.get_available_skills()
        self.set_equipped_skills(avail[:self.max_skill_slots])
        return True, f"已裝備前 {len(self.equipped_skills)} 招技能"

    def set_class(self, new_class_id, player):
        self.class_id = new_class_id
        self.player = player
        self.class_info = get_class_info(new_class_id)
        self.skills = [s.clone() for s in self.class_info["skills"]]
        avail = self.get_available_skills()
        self.equipped_skills = avail[:self.max_skill_slots]
        self.equipped_skill_indices = list(range(len(self.equipped_skills)))
        self.attack_timer = 0.0
        self.cast_delay_timer = self.slot_idx * 0.08
        self.mechanic_stacks = 0
        self.mechanic_timer = 0.0
        self.is_buffed = False
        self.buff_timer = 0.0
        if self.is_protagonist:
            m_hp = self.get_max_hp(player)
            self._hp = min(self._hp, float(m_hp)) if self._hp > 0 else 0.0

    def get_max_hp(self, player):
        """全隊生存屬性統一以主角為核心計算"""
        if not self.is_protagonist and player and player.team:
            return player.team[0].get_max_hp(player)
        return player_stats.calc_member_max_hp(self, player)

    def get_defense(self, player):
        """全隊防禦減傷統一以主角防禦力為核心計算"""
        if not self.is_protagonist and player and player.team:
            return player.team[0].get_defense(player)
        return player_stats.calc_member_defense(self, player)

    def get_attack(self, player):
        return player_stats.calc_member_attack(self, player)

    def get_crit_chance(self, player):
        return player_stats.calc_member_crit_chance(self, player)

    def get_attack_speed(self, player):
        return player_stats.calc_member_attack_speed(self, player)

    def take_damage(self, amount):
        """傷害結算：護盾優先抵扣，剩餘扣減 HP，統一結算於主角核心生命池"""
        if not self.is_protagonist and self.player and self.player.team:
            return self.player.team[0].take_damage(amount)
        shield_absorbed = min(self._shield, amount)
        self._shield -= shield_absorbed
        remaining = amount - shield_absorbed
        self._hp = max(0.0, self._hp - remaining)
        return remaining, shield_absorbed


class Player:
    """遠征隊總管與帳號核心數據門面 (Facade)"""
    def __init__(self):
        self.name = "新楓之谷遠征隊"
        self.level = 1
        self.exp = 0
        self.gold = 100

        # 四大核心戰鬥能力 (攻擊 / 防禦 / 生命 / 技巧)
        self.stat_atk = 6
        self.stat_def = 6
        self.stat_hp = 6
        self.stat_crit = 6
        self.free_points = 0

        # 穿戴中的裝備 (25 個新楓之谷標準裝備欄位，全隊共享加成)
        self.equipped = {k: None for k in SLOT_NAMES.keys()}
        # 欄位星力、潛能與卷軸強化初始化 (換裝不流失)
        player_gear.ensure_player_slots(self)

        # 秘法符號 (ARC) 與 原初符號 (AUT)
        self.arc_symbols = {k: 0 for k in ARC_SYMBOLS_DATA}
        self.aut_symbols = {k: 0 for k in AUT_SYMBOLS_DATA}
        self.symbol_fragments = {k: 0 for k in list(ARC_SYMBOLS_DATA.keys()) + list(AUT_SYMBOLS_DATA.keys())}

        # 背包清單
        self.inventory = []

        # 內在能力 (內潛)、寵物系統、萌獸系統
        self.inner_ability = InnerAbility()
        self.pet_manager = PetManager()
        self.familiar_manager = FamiliarManager()

        # 全隊光環與戰術增益
        self.team_buffs = {}

        # 初始新手裝備
        self._give_starter_gear()

        # 7 人冒險隊伍 (席位 0 為核心主角，席位 1~6 為兩側隨行護衛夥伴)
        self.team = []
        self.team = [
            TeamMember(0, "hero", self),           # 席位 0: 👑 主角 (英雄)
            TeamMember(1, "dawn_warrior", self),   # 席位 1: ⚔️ 夥伴 1 (聖魂劍士)
            TeamMember(2, "battle_mage", self),    # 席位 2: 🛡️ 夥伴 2 (煉獄巫師)
            TeamMember(3, "bishop", self),         # 席位 3: 🏹 夥伴 3 (主教)
            TeamMember(4, "night_lord", self),     # 席位 4: 🔮 夥伴 4 (夜使者)
            TeamMember(5, "bowmaster", self),      # 席位 5: 🗡️ 夥伴 5 (箭神)
            TeamMember(6, "buccaneer", self),      # 席位 6: 💣 夥伴 6 (拳霸)
        ]

    def get_bench_classes(self):
        """獲取未出戰的其餘後援職業 ID 清單 (總共 24 職，出戰 7 職，後援 17 職)"""
        active_cids = {m.class_id for m in getattr(self, "team", [])}
        return [cid for cid in ALL_CLASSES.keys() if cid not in active_cids]

    def get_legion_stat(self, stat_key):
        """獲取聯盟戰地 17 位後援職業提供的全域被動屬性加成"""
        from legion_system import calc_legion_bonuses
        return calc_legion_bonuses(self.get_bench_classes()).get(stat_key, 0.0)

    # --- 符號系統委派 ---
    def get_total_arc(self):
        return calculate_total_arc(self.arc_symbols)

    def get_total_aut(self):
        return calculate_total_aut(self.aut_symbols)

    def get_symbol_stat_sum(self, stat_name):
        return calculate_symbol_stat_sum(self.arc_symbols, self.aut_symbols, stat_name)

    def get_symbol_name(self, sym_key):
        return get_symbol_display_name(sym_key)

    def add_symbol_fragment(self, sym_key, count=1):
        self.symbol_fragments[sym_key] = self.symbol_fragments.get(sym_key, 0) + count
        if sym_key in self.arc_symbols and self.arc_symbols[sym_key] == 0:
            self.arc_symbols[sym_key] = 1
        elif sym_key in self.aut_symbols and self.aut_symbols[sym_key] == 0:
            self.aut_symbols[sym_key] = 1

    def get_symbol_upgrade_req(self, sym_key):
        cur_lvl = self.arc_symbols.get(sym_key, 0) if sym_key in ARC_SYMBOLS_DATA else self.aut_symbols.get(sym_key, 0)
        return get_symbol_upgrade_req(sym_key, cur_lvl)

    def upgrade_symbol(self, sym_key):
        is_arc = sym_key in ARC_SYMBOLS_DATA
        if not is_arc and sym_key not in AUT_SYMBOLS_DATA:
            return False, "無效符號"

        data = ARC_SYMBOLS_DATA[sym_key] if is_arc else AUT_SYMBOLS_DATA[sym_key]
        cur_lvl = self.arc_symbols[sym_key] if is_arc else self.aut_symbols[sym_key]
        if cur_lvl >= data["max_lvl"]:
            return False, f"【{data['name']}】已達滿級 (Lv.{data['max_lvl']})！"

        req_frags, req_gold, is_max = self.get_symbol_upgrade_req(sym_key)
        cur_frags = self.symbol_fragments.get(sym_key, 0)

        if cur_frags < req_frags:
            return False, f"碎片不足！需要 {req_frags} 個碎片 (當前: {cur_frags})"
        if self.gold < req_gold:
            return False, f"金幣不足！需要 ${req_gold:,} 金幣 (當前: ${self.gold:,})"

        self.symbol_fragments[sym_key] -= req_frags
        self.gold -= req_gold
        new_lvl = max(1, cur_lvl) + 1
        if is_arc:
            self.arc_symbols[sym_key] = new_lvl
        else:
            self.aut_symbols[sym_key] = new_lvl

        for m in self.team:
            m.current_hp = min(m.current_hp, float(m.get_max_hp(self)))

        return True, f"【{data['name']}】升級成功！提升至 Lv.{new_lvl}！"

    # --- 光環與戰術增益 ---
    def apply_team_buff(self, buff_id, buff_type, val, duration, source_name, source_slot_idx=0):
        self.team_buffs[buff_id] = {
            "type": buff_type,
            "val": val,
            "timer": duration,
            "max_timer": duration,
            "source": source_name,
            "source_slot_idx": source_slot_idx
        }

    def get_buff_val(self, buff_type):
        return sum(b["val"] for b in self.team_buffs.values() if b.get("type") == buff_type and b.get("timer", 0) > 0)

    def update_buffs(self, dt):
        expired = []
        for bid, b in self.team_buffs.items():
            b["timer"] -= dt
            if b["timer"] <= 0:
                expired.append(bid)
        for bid in expired:
            del self.team_buffs[bid]

    def on_floor_cleared(self):
        """層數突破時刷新全隊狀態：主角生命全滿、護盾重置、全體冷卻重置"""
        if self.team:
            leader = self.team[0]
            leader.current_hp = float(leader.get_max_hp(self))
            leader.shield = 0.0
        for m in self.team:
            m.attack_timer = 0.0

    def restore_team_full_hp(self):
        """主角核心生命與護盾全滿"""
        if self.team:
            leader = self.team[0]
            leader.current_hp = float(leader.get_max_hp(self))
            leader.shield = 0.0

    def _give_starter_gear(self):
        self.equipped["weapon"] = Item("weapon", "common", 1, "木製短劍", {"attack": 15})
        self.equipped["top"] = Item("top", "common", 1, "初學者便服", {"defense": 6, "hp": 50})
        self.equipped["hat"] = Item("hat", "common", 1, "初學者頭巾", {"defense": 4, "hp": 30})
        self.equipped["bottom"] = Item("bottom", "common", 1, "粗布短褲", {"defense": 4, "hp": 30})
        self.equipped["shoes"] = Item("shoes", "common", 1, "皮革涼鞋", {"defense": 2, "attack_speed": 0.05})

    def set_slot_class(self, slot_idx, class_id):
        if slot_idx < 0 or slot_idx >= len(self.team):
            return False
        if class_id not in ALL_CLASSES:
            return False
        old_cid = self.team[slot_idx].class_id
        if old_cid == class_id:
            return True
        # 若該職業已被其他席位佔用，則自動互換以維持 7 席位不重複
        for other_idx, other_m in enumerate(self.team):
            if other_idx != slot_idx and other_m.class_id == class_id:
                other_m.set_class(old_cid, self)
                break
        self.team[slot_idx].set_class(class_id, self)
        return True

    # --- 自由配點 ---
    def auto_allocate_points(self, mode="all_atk"):
        if self.free_points <= 0:
            return 0, "無剩餘自由點數"

        pts = self.free_points
        allocated = {"atk": 0, "def": 0, "hp": 0, "crit": 0}

        if mode == "all_atk":
            allocated["atk"] = pts
        elif mode == "balanced":
            allocated["atk"] = int(pts * 0.4)
            allocated["def"] = int(pts * 0.2)
            allocated["hp"] = int(pts * 0.2)
            allocated["crit"] = pts - allocated["atk"] - allocated["def"] - allocated["hp"]
        elif mode == "defensive":
            allocated["atk"] = int(pts * 0.3)
            allocated["def"] = int(pts * 0.35)
            allocated["hp"] = pts - allocated["atk"] - allocated["def"]

        self.stat_atk += allocated["atk"]
        self.stat_def += allocated["def"]
        self.stat_hp += allocated["hp"]
        self.stat_crit += allocated["crit"]
        self.free_points = 0

        for m in self.team:
            m.current_hp = min(m.current_hp, float(m.get_max_hp(self)))

        desc = f"攻+{allocated['atk']} 防+{allocated['def']} 體+{allocated['hp']} 技+{allocated['crit']}"
        return pts, f"一鍵配點成功 ({desc})！"

    def add_stat_points(self, stat_key, count=1):
        if self.free_points <= 0 or count <= 0:
            return 0
        actual = min(self.free_points, count)
        if stat_key == "atk":
            self.stat_atk += actual
        elif stat_key == "def":
            self.stat_def += actual
        elif stat_key == "hp":
            self.stat_hp += actual
        elif stat_key == "crit":
            self.stat_crit += actual
        else:
            return 0

        self.free_points -= actual
        for m in self.team:
            m.current_hp = min(m.current_hp, float(m.get_max_hp(self)))
        return actual

    def allocate_point(self, stat_name):
        if self.free_points <= 0:
            return False
        if stat_name in ["atk", "str"]:
            self.stat_atk += 1
        elif stat_name in ["def"]:
            self.stat_def += 1
        elif stat_name in ["hp", "vit"]:
            self.stat_hp += 1
        elif stat_name in ["crit", "agi"]:
            self.stat_crit += 1
        else:
            return False
        self.free_points -= 1
        return True

    # --- 屬性加成計算委派 ---
    def get_gear_stat_sum(self, stat_key):
        return player_stats.calc_gear_stat_sum(
            self.equipped, self.slot_enhancements, stat_key,
            slot_potentials=getattr(self, "slot_potentials", None),
            slot_scrolls=getattr(self, "slot_scrolls", None)
        )

    def get_active_sets(self):
        return player_stats.calc_active_sets(self.equipped)

    def get_set_stat_sum(self, stat_key):
        return player_stats.calc_set_stat_sum(self.equipped, stat_key)

    @property
    def exp_to_next(self):
        # 放置遠征隊加速成長曲線：優化中後期升級節奏，大幅減少卡等時間
        return int(28 * (self.level ** 1.70) + 20 * self.level)

    def add_exp(self, amount):
        self.exp += amount
        leveled_up = False
        while self.exp >= self.exp_to_next:
            self.exp -= self.exp_to_next
            self.level += 1
            self.free_points += 4
            self.restore_team_full_hp()
            leveled_up = True
        return leveled_up

    def add_gold(self, amount):
        self.gold += amount

    @property
    def life_steal(self):
        return player_stats.calc_life_steal(self)

    @property
    def current_hp(self):
        return sum(m.current_hp for m in self.team)

    @property
    def max_hp(self):
        return sum(m.get_max_hp(self) for m in self.team)

    @property
    def current_class(self):
        return self.team[0].class_id

    @property
    def class_info(self):
        return self.team[0].class_info

    @property
    def skills(self):
        return self.team[0].skills

    @property
    def attack(self):
        return self.team[0].get_attack(self)

    @property
    def defense(self):
        return self.team[0].get_defense(self)

    @property
    def attack_speed(self):
        return self.team[0].get_attack_speed(self)

    @property
    def crit_chance(self):
        return self.team[0].get_crit_chance(self)

    # --- 裝備管理與強化委派 (player_gear) ---
    def add_to_inventory(self, item):
        if len(self.inventory) < INVENTORY_CAPACITY:
            self.inventory.append(item)
            return True
        return False

    def equip_item(self, item, target_slot=None):
        return player_gear.equip_item(self, item, target_slot)

    def unequip_item(self, slot):
        return player_gear.unequip_item(self, slot)

    def sell_item(self, item):
        return player_gear.sell_item(self, item)

    def sell_by_rarities(self, rarities):
        return player_gear.sell_by_rarities(self, rarities)

    def get_slot_enhance_cost(self, slot_key):
        return player_gear.get_slot_enhance_cost(self.slot_enhancements, slot_key)

    def get_slot_enhance_success_rate(self, slot_key):
        return player_gear.get_slot_enhance_success_rate(self.slot_enhancements, slot_key)

    def can_enhance_slot(self, slot_key):
        return player_gear.can_enhance_slot(self, slot_key)

    def enhance_slot(self, slot_key):
        return player_gear.enhance_slot(self, slot_key)

    def auto_enhance_slot(self, slot_key, target_star=15, max_attempts=100):
        return player_gear.auto_enhance_slot(self, slot_key, target_star, max_attempts)

    def cube_item(self, item, cube_type="mystic"):
        return player_gear.cube_item(self, item, cube_type)

    def cube_slot(self, slot_key, cube_type="bright", is_bonus=False):
        return player_gear.cube_slot(self, slot_key, cube_type, is_bonus)

    def auto_cube_item(self, item, cube_type="bright", target_rank="unique", target_stat_keyword=None, max_cubes=100):
        return player_gear.auto_cube_item(self, item, cube_type, target_rank, target_stat_keyword, max_cubes)

    def auto_cube_slot(self, slot_key, cube_type="bright", target_rank="unique", target_stat_keyword=None, is_bonus=False, max_cubes=100):
        return player_gear.auto_cube_slot(self, slot_key, cube_type, target_rank, target_stat_keyword, is_bonus, max_cubes)

    def auto_equip_best_gear(self):
        return player_gear.auto_equip_best_gear(self)

    def sell_inferior_gear(self):
        return player_gear.sell_inferior_gear(self)

    # --- 內在能力、寵物與萌獸系統委派 ---
    def get_inner_ability_stat(self, stat_type: str) -> float:
        return self.inner_ability.get_stat_sum(stat_type) if hasattr(self, "inner_ability") else 0.0

    def get_pet_attack(self) -> int:
        if not hasattr(self, "pet_manager"):
            return 0
        return self.pet_manager.get_total_equip_attack() + self.pet_manager.get_luna_set_attack()

    def get_familiar_final_damage_mult(self) -> float:
        return self.familiar_manager.get_final_damage_multiplier() if hasattr(self, "familiar_manager") else 1.0

    def get_familiar_stat(self, pot_type: str) -> float:
        return self.familiar_manager.get_stat_sum(pot_type) if hasattr(self, "familiar_manager") else 0.0

    # --- 存讀檔持久化委派 (player_save) ---
    def to_dict(self):
        return player_save.player_to_dict(self)

    def load_dict(self, d):
        return player_save.player_load_dict(self, d)

    @staticmethod
    def get_default_save_path():
        return player_save.get_default_save_path()

    def save_to_file(self, filepath=None, combat_mgr=None):
        return player_save.save_player_to_file(self, filepath, combat_mgr)

    def load_from_file(self, filepath=None, combat_mgr=None):
        return player_save.load_player_from_file(self, filepath, combat_mgr)


def get_default_save_path():
    """模組級捷徑函式：取得預設存檔路徑"""
    return player_save.get_default_save_path()
