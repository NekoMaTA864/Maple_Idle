"""
《新楓之谷：放置遠征隊》戰鬥核心系統與管理外觀 (combat_system.py)
整合地區、怪物、視覺特效、傷害計算、怪物AI與擊殺掉落模組
"""
import random
import time
from settings import (
    COLOR_TEXT_MAIN, COLOR_TEXT_MUTED, COLOR_HP_RED, COLOR_ACTION_BAR,
    COLOR_GOLD, COLOR_UNCOMMON, COLOR_RARE, COLOR_EPIC, COLOR_LEGENDARY,
    COLOR_HEAL_GREEN, COLOR_BOSS_PURPLE, COLOR_SHIELD_BLUE
)
from monster_skills import get_skills_for_boss, scale_monster_stats
from combat_stats import CombatStats

# 模組化子系統匯入與重匯出 (保證 100% 向下相容性)
from combat_zones import ZONES
from combat_vfx_manager import (
    VisualEffect, _get_vfx_priority, HIGH_PRIORITY_VFX,
    VisualEffectManager
)
from combat_events import PendingHit
from monster import Monster, get_skill_priority
from combat_loot import handle_monster_killed
from monster_ai import process_monster_attack, execute_monster_skill
from combat_damage import execute_pending_hit, apply_member_shield, execute_member_attack

__all__ = [
    "CombatManager", "ZONES", "Monster", "VisualEffect", "_get_vfx_priority",
    "HIGH_PRIORITY_VFX", "VisualEffectManager", "PendingHit", "get_skill_priority"
]


class CombatManager:
    def __init__(self, player, rng=None):
        self.player = player
        # Defaulting to the existing module keeps production RNG distribution and call order.
        self.rng = random if rng is None else rng
        self.current_zone_idx = 0
        self.unlocked_zones = 1

        # 層數制進度 (1 ~ 10 層，第 10 層為區域首領)
        self.current_floor = 1
        self.max_floors = 10

        self.monsters = []
        self.repeat_current_zone = False  # 區域循環農怪/鎖定模式
        self.is_boss_active = False
        self.is_training_dummy = False
        self.training_dummy_config = None
        self.is_gold_dungeon = False

        # 特效管理器與多段延遲隊列
        self.vfx_mgr = VisualEffectManager()
        self.pending_hits = []
        self.combat_stats = CombatStats(len(self.player.team))

        # 震動反饋與浮空飄字
        self.shake_team = [0.0] * len(self.player.team)
        self.shake_monster = 0.0
        self.floating_popups = []

        # 戰鬥即時文字日誌
        self.combat_logs = []
        self.max_logs = 120

        # 隊伍團滅休整倒數
        self.is_resting = False
        self.respawn_timer = 0.0

        # 首領威脅領域環境瘴氣計時器
        self.boss_miasma_timer = 0.0

        self.spawn_next_monster()

    @property
    def monster(self):
        """向前相容屬性：返回當前首要存活目標"""
        alive = [m for m in self.monsters if m.is_alive]
        if alive:
            return alive[0]
        return self.monsters[0] if self.monsters else None

    @monster.setter
    def monster(self, val):
        if val is None:
            self.monsters = []
        elif isinstance(val, list):
            self.monsters = val
        else:
            self.monsters = [val]

    def get_current_zone(self):
        return ZONES[self.current_zone_idx]

    def set_zone(self, idx):
        if 0 <= idx < self.unlocked_zones:
            self.is_training_dummy = False
            self.training_dummy_config = None
            self.is_gold_dungeon = False
            self.current_zone_idx = idx
            self.current_floor = 1
            self.is_boss_active = False
            self.boss_miasma_timer = 0.0
            self.pending_hits.clear()
            self.spawn_next_monster()
            zone = self.get_current_zone()
            self.add_log(f"遠征隊已挺進【{zone['name']}】第 1/10 層！", (100, 220, 255))

    def set_repeat_current_zone(self, enabled, announce=False):
        self.repeat_current_zone = bool(enabled)
        if announce:
            zone = self.get_current_zone()
            if self.repeat_current_zone:
                self.add_log(f"[循環刷怪] 已鎖定【{zone['name']}】！首領擊破後原地重置第 1 層刷碎片！", (100, 220, 255))
            else:
                self.add_log("[推進模式] 已恢復一般進度模式！首領擊破後將自動解鎖並挺進下一區！", (255, 215, 60))

    def enter_gold_dungeon(self):
        self.is_gold_dungeon = True
        self.is_training_dummy = False
        self.training_dummy_config = None
        self.current_floor = 1
        self.is_boss_active = True
        self.pending_hits.clear()
        self.combat_stats.reset()
        self._spawn_gold_dungeon_monster()
        self.add_log(f"[黃金寶庫] 遠征隊已進入【黃金寶庫】！擊破黃金寶箱怪可無限獲取巨額楓幣！", (255, 215, 0))

    def leave_gold_dungeon(self):
        self.is_gold_dungeon = False
        self.is_boss_active = False
        self.pending_hits.clear()
        self.spawn_next_monster()
        zone = self.get_current_zone()
        self.add_log(f"[黃金寶庫] 已退出金庫，回到【{zone['name']}】！", (100, 220, 255))

    def _spawn_gold_dungeon_monster(self):
        p_lvl = max(1, self.player.level)
        hp = max(10000, int(1500 * (p_lvl ** 1.82)))
        data = {
            "name": "黃金寶箱怪",
            "lvl": p_lvl,
            "hp": hp,
            "atk": max(5, int(p_lvl * 4)),
            "def": max(5, int(p_lvl * 3)),
            "spd": 3.2,
        }
        m = Monster(data, is_boss=True)
        self.monsters = [m]

    def configure_training_dummy(self, level, hp, attack, defense, count=1, is_boss=False):
        self.is_training_dummy = True
        self.is_gold_dungeon = False
        num_dummies = max(1, min(5, int(count)))
        raw_def = float(defense)
        # 若 defense >= 5 則為百分比 (例如 20, 100, 300 -> 0.20, 1.0, 3.0)，否則直接作為倍率
        def_rate = raw_def / 100.0 if raw_def >= 5.0 else raw_def
        self.training_dummy_config = {
            "level": int(level), "hp": int(hp),
            "atk": int(attack), "def": int(defense),
            "def_rate": def_rate,
            "spd": 2.5,
            "count": num_dummies,
            "is_dummy": True,
            "is_boss": is_boss,
        }
        self.pending_hits.clear()
        self.current_floor = 1
        self.is_boss_active = is_boss
        self.combat_stats.reset()
        self._spawn_training_dummy()
        def_pct_str = f"{int(round(def_rate * 100))}%"
        count_str = f" (群怪數量: {num_dummies}隻)" if num_dummies > 1 else " (單體靶)"
        boss_str = "【首領屬性】" if is_boss else ""
        self.add_log(f"[木樁] {boss_str}Lv.{level} HP {hp:,} 防禦率 {def_pct_str}{count_str}，開始測試！", (100, 220, 255))

    def _spawn_training_dummy(self):
        data = dict(self.training_dummy_config)
        data["lvl"] = data["level"]
        num_dummies = data.get("count", 1)
        is_boss = data.get("is_boss", False)
        prefix = "首領木樁" if is_boss else "自定義木樁"
        self.monsters = [
            Monster(dict(data, name=f"{prefix}{i+1}" if num_dummies > 1 else prefix), is_boss=is_boss)
            for i in range(num_dummies)
        ]

    def add_log(self, text, color=COLOR_TEXT_MAIN):
        now_str = time.strftime("%H:%M:%S")
        self.combat_logs.append({
            "time": now_str,
            "text": text,
            "color": color
        })
        if len(self.combat_logs) > self.max_logs:
            self.combat_logs.pop(0)

    def spawn_next_monster(self):
        if self.is_gold_dungeon:
            self._spawn_gold_dungeon_monster()
            return
        if self.is_training_dummy and self.training_dummy_config:
            self._spawn_training_dummy()
            return
        self.combat_stats.reset()
        self.boss_miasma_timer = 0.0
        zone = self.get_current_zone()
        if self.current_floor >= self.max_floors:
            # 首領層 (第 10 層)：經典單一巨大首領君臨
            boss_data = scale_monster_stats(zone["boss"], self.current_floor, is_boss=True)
            boss_m = Monster(boss_data, is_boss=True)
            boss_m.skills = get_skills_for_boss(
                zone["id"], boss_m.name, zone.get("boss", {}).get("skill_kit"), rng=self.rng
            )
            boss_m.is_enraged = False
            boss_m.shield = 0
            self.monsters = [boss_m]
            self.is_boss_active = True
            self.add_log(f"[第 10/10 層首領試煉] 經典首領【{boss_m.name} (Lv.{boss_m.lvl})】君臨戰場！", COLOR_BOSS_PURPLE)
        else:
            # 普通層 (第 1~9 層)：隨機生成 1~5 隻怪物群 (含菁英怪試煉)
            self.is_boss_active = False
            wave_roll = self.rng.random()

            if wave_roll < 0.20:
                # 20% 機率：菁英怪試煉波次！(1 隻詞綴菁英怪 + 2 隻普通護衛怪)
                affixes = [
                    ("【強大】", {"atk_mult": 1.25, "hp_mult": 1.4}),
                    ("【堅壁】", {"atk_mult": 1.05, "hp_mult": 1.7}),
                    ("【迅捷】", {"atk_mult": 1.15, "hp_mult": 1.3}),
                ]
                affix_name, affix_stat = self.rng.choice(affixes)
                m_raw = self.rng.choice(zone["monsters"])
                base_data = scale_monster_stats(m_raw, self.current_floor, is_boss=False)

                elite_data = dict(base_data)
                elite_data["name"] = f"{affix_name} {base_data['name']}"
                elite_data["hp"] = int(base_data["hp"] * affix_stat["hp_mult"])
                elite_data["atk"] = int(base_data["atk"] * affix_stat["atk_mult"])
                elite_data["is_elite"] = True
                elite_data["elite_affix"] = affix_name
                elite_m = Monster(elite_data, is_boss=False)

                g1_data = scale_monster_stats(self.rng.choice(zone["monsters"]), self.current_floor, is_boss=False)
                g1_data["hp"] = int(g1_data["hp"] * 0.7)
                g1_m = Monster(g1_data, is_boss=False)

                g2_data = scale_monster_stats(self.rng.choice(zone["monsters"]), self.current_floor, is_boss=False)
                g2_data["hp"] = int(g2_data["hp"] * 0.7)
                g2_m = Monster(g2_data, is_boss=False)

                self.monsters = [g1_m, elite_m, g2_m]
                self.add_log(f"[菁英怪現身] 遭遇【{elite_m.name}】率領小怪群突襲！", (255, 200, 50))
            elif wave_roll < 0.55:
                # 35% 機率：3 隻群怪蜂擁
                m_list = []
                for _ in range(3):
                    m_data = scale_monster_stats(self.rng.choice(zone["monsters"]), self.current_floor, is_boss=False)
                    m_data["hp"] = int(m_data["hp"] * 0.75)
                    m_list.append(Monster(m_data, is_boss=False))
                self.monsters = m_list
            elif wave_roll < 0.80:
                # 25% 機率：4~5 隻大群怪
                count = self.rng.choice([4, 5])
                m_list = []
                for _ in range(count):
                    m_data = scale_monster_stats(self.rng.choice(zone["monsters"]), self.current_floor, is_boss=False)
                    m_data["hp"] = int(m_data["hp"] * 0.55)
                    m_list.append(Monster(m_data, is_boss=False))
                self.monsters = m_list
            else:
                # 20% 機率：1~2 隻強敵對決
                count = self.rng.choice([1, 2])
                m_list = []
                for _ in range(count):
                    m_data = scale_monster_stats(self.rng.choice(zone["monsters"]), self.current_floor, is_boss=False)
                    if count == 1:
                        m_data["hp"] = int(m_data["hp"] * 1.3)
                    m_list.append(Monster(m_data, is_boss=False))
                self.monsters = m_list

        for m in self.player.team:
            m.attack_timer = m.slot_idx * 0.05
            m.cast_delay_timer = m.slot_idx * 0.08  # 席位錯峰開場，避免全隊同一毫秒搶發技能

    def add_popup(self, text, target="monster", color=(255, 255, 255), is_crit=False, is_skill=False):
        """在特定單位上方生成浮動文字"""
        self.floating_popups.append({
            "text": text,
            "target": target,
            "color": color,
            "is_crit": is_crit,
            "is_skill": is_skill,
            "life": 40 if (is_crit or is_skill) else 28,
            "max_life": 40 if (is_crit or is_skill) else 28,
            "offset_y": -8,
            "offset_x": self.rng.uniform(-10, 10)
        })

    def _get_slot_pos(self, slot_idx):
        # 席位 0 居中 (0.50 👑 主角)，夥伴對稱展開在兩側 (左 3 + 中 1 + 右 3)
        slot_map = {
            0: 0.50,  # 👑 核心主角
            1: 0.36,  # ⚔️ 夥伴 1
            2: 0.23,  # 🛡️ 夥伴 2
            3: 0.10,  # 🏹 夥伴 3
            4: 0.64,  # 🔮 夥伴 4
            5: 0.77,  # 🗡️ 夥伴 5
            6: 0.90,  # 💣 夥伴 6
        }
        w = 1140
        ratio = slot_map.get(slot_idx, 0.50)
        return (int(w * ratio), 235)

    def _get_monster_pos(self, monster_idx=0, total_monsters=1):
        """計算怪物在畫布上的座標 (支援 1~5 隻多怪動態橫向排布)"""
        w = 1140
        if total_monsters <= 1:
            return (564, 103)
        elif total_monsters == 2:
            ratios = [0.40, 0.60]
        elif total_monsters == 3:
            ratios = [0.28, 0.50, 0.72]
        elif total_monsters == 4:
            ratios = [0.20, 0.40, 0.60, 0.80]
        else:
            ratios = [0.15, 0.32, 0.50, 0.68, 0.85]

        idx = min(monster_idx, len(ratios) - 1)
        return (int(w * ratios[idx]), 103)

    def update(self, dt, sound_mgr):
        """5 人遠征小隊與怪物即時戰鬥循環"""
        self.combat_stats.tick(dt)
        # 0. 更新全隊 Buff 與特效
        self.player.update_buffs(dt)
        self.vfx_mgr.update(dt)

        # 1. 震動衰減
        for i in range(len(self.shake_team)):
            if self.shake_team[i] > 0:
                self.shake_team[i] = max(0.0, self.shake_team[i] - 30.0 * dt)
        if self.shake_monster > 0:
            self.shake_monster = max(0.0, self.shake_monster - 30.0 * dt)

        # 2. 浮空文字更新
        for p in self.floating_popups:
            p["life"] -= 1
            p["offset_y"] -= 1.3
        self.floating_popups = [p for p in self.floating_popups if p["life"] > 0]

        # 3. 異常狀態與控制更新 (遍歷全體在場怪物)
        for m_i, m in enumerate(self.monsters):
            if not m.is_alive:
                continue
            if m.freeze_timer > 0:
                m.freeze_timer = max(0.0, m.freeze_timer - dt)

            if m.burn_timer > 0:
                m.burn_timer -= dt
                m.burn_tick += dt
                if m.burn_tick >= 0.6:
                    m.burn_tick = 0.0
                    b_dmg = max(1, m.burn_dmg)
                    m.hp = max(0, m.hp - b_dmg)
                    self.add_popup(f"[灼燒 -{b_dmg}]", f"monster_{m_i}", (255, 120, 50))

            if m.bleed_timer > 0:
                m.bleed_timer -= dt
                m.bleed_tick += dt
                if m.bleed_tick >= 0.8:
                    m.bleed_tick = 0.0
                    bl_dmg = max(1, m.bleed_dmg)
                    m.hp = max(0, m.hp - bl_dmg)
                    self.add_popup(f"[流血 -{bl_dmg}]", f"monster_{m_i}", (240, 60, 60))

            if m.chill_timer > 0:
                m.chill_timer -= dt

            # 更新首領技能冷卻
            for s in getattr(m, "skills", []):
                s.update(dt)

            # 首領特殊相位機制 (HP <= 50%)
            if m.is_boss and not getattr(m, "phase_50_triggered", False):
                if m.hp <= m.max_hp * 0.50:
                    m.phase_50_triggered = True
                    # 露希妲/咖凌：冷卻全數刷新
                    if any(k in m.name for k in ["露希妲", "咖凌"]):
                        for bs in getattr(m, "skills", []):
                            bs.timer = 0.0
                        self.add_popup("【相位重置：技能刷新！】", f"monster_{m_i}", (255, 60, 180), is_skill=True)
                        self.add_log(f"💥 首領 [{m.name}] 生命值降至 50%，觸發相位轉變！全技能冷卻瞬間重置！", (255, 60, 180))
                    # 瑟倫：進入日蝕相位，全技能冷卻永久縮短 30%
                    if "瑟倫" in m.name:
                        for bs in getattr(m, "skills", []):
                            bs.cooldown *= 0.70
                            bs.timer = min(bs.timer, bs.cooldown)
                        self.add_popup("【日蝕降臨：急速詠唱！】", f"monster_{m_i}", (255, 140, 40), is_skill=True)
                        self.add_log(f"💥 首領 [{m.name}] 生命值降至 50%，進入【日蝕】姿態！全技能冷卻縮短 30%！", (255, 140, 40))
                    # 咖凌：毀滅死光永久增傷 20%
                    if "咖凌" in m.name:
                        for bs in getattr(m, "skills", []):
                            if bs.skill_id == "chaos_laser":
                                bs.dmg_mult *= 1.20

            # 首領殘血狂暴機制 (HP <= 30%)
            if m.is_boss and not getattr(m, "is_enraged", False):
                if m.hp <= m.max_hp * 0.30:
                    m.is_enraged = True
                    m.atk = int(m.atk * 1.25)
                    m.attack_speed = max(0.6, m.attack_speed * 0.75)
                    for bs in getattr(m, "skills", []):
                        bs.cooldown *= 0.80
                        bs.timer = min(bs.timer, bs.cooldown)
                    self.add_popup("【狂暴覺醒！】", f"monster_{m_i}", (255, 40, 40), is_skill=True)
                    self.add_log(f"💥 警報！首領 [{m.name}] 生命值低於 30%，進入【狂暴覺醒】！攻速大幅提升、技能冷卻縮短！", (255, 50, 50))
                    self.vfx_mgr.add_vfx("distortion_bomb_singularity", 564, 103, color=(255, 30, 30))

        # 3.5 首領威脅領域：環境瘴氣 (Floor 10 首領戰場持續威脅)
        if self.is_boss_active and not self.is_gold_dungeon and not self.is_training_dummy and not self.is_resting:
            if any(m.is_alive and m.is_boss for m in self.monsters):
                self.boss_miasma_timer += dt
                if self.boss_miasma_timer >= 2.5:
                    self.boss_miasma_timer = 0.0
                    zone = self.get_current_zone()
                    arc_req = zone.get("arc_req", 0)
                    player_arc = self.player.get_total_arc()
                    is_arc_15x = (arc_req > 0 and player_arc >= int(arc_req * 1.5))

                    hero = self.player.team[0]
                    if hero.is_alive:
                        if is_arc_15x:
                            miasma_dmg = 1
                        else:
                            m_hp = hero.get_max_hp(self.player)
                            miasma_dmg = max(10, int(m_hp * 0.018))

                        hp_lost, absorbed = hero.take_damage(miasma_dmg)
                        self.combat_stats.record_damage_taken(hero.slot_idx, hp_lost, absorbed)
                        if absorbed > 0:
                            self.add_popup(f"[護盾抵扣 {int(absorbed)}]", f"slot_{hero.slot_idx}", COLOR_SHIELD_BLUE)
                        if hp_lost > 0:
                            self.add_popup(f"[瘴氣 -{int(hp_lost)}]", f"slot_{hero.slot_idx}", (180, 70, 220))

                        if hero.current_hp <= 0:
                            self.combat_stats.record_death(hero.slot_idx)
                            self.add_log(f"[戰況] 核心主角 [{hero.name}] 倒在首領領域瘴氣中！", (255, 100, 100))
                            self.is_resting = True
                            self.respawn_timer = 3.2
                            self.add_log("警告：首領領域瘴氣吞噬了遠征隊！全員重創撤退 (3秒)...", (255, 80, 80))

        # 4. 多段連擊延遲隊列結算
        if self.pending_hits and any(m.is_alive for m in self.monsters):
            rem = []
            for hit in self.pending_hits:
                hit.delay -= dt
                if hit.delay <= 0:
                    self._execute_pending_hit(hit, sound_mgr)
                    if not any(m.is_alive for m in self.monsters):
                        self.pending_hits.clear()
                        return
                else:
                    rem.append(hit)
            self.pending_hits = rem

        # 5. 全隊團滅休整 (若團滅則休整 3 秒後重整挑戰當前層)
        if self.is_resting:
            self.respawn_timer -= dt
            if self.respawn_timer <= 0:
                self.is_resting = False
                self.player.on_floor_cleared()
                self.spawn_next_monster()
                self.add_log(f"遠征隊於第 {self.current_floor}/10 層完成整裝，重振旗鼓再次發起挑戰！", (80, 240, 140))
            return

        # 5.5 寵物自動喝水 (Auto-Potion) 與 萌獸定時全隊恢復光狂 (Familiar Aura)
        if any(tm.is_alive for tm in self.player.team):
            if hasattr(self.player, "pet_manager"):
                pot_used = self.player.pet_manager.check_auto_potion(self.player)
                if pot_used > 0:
                    self.add_popup(f"[寵物自補 x{pot_used}]", "slot_0", (100, 255, 100), is_skill=True)

            if hasattr(self.player, "familiar_manager"):
                aura_heal = self.player.familiar_manager.update_regen_aura(dt, self.player)
                if aura_heal > 0:
                    self.add_popup(f"[萌獸光環 +{aura_heal}]", "slot_0", (80, 240, 140), is_skill=True)

        if not any(m.is_alive for m in self.monsters):
            self.spawn_next_monster()
            return

        # 6. 七大席位成員 (主角 + 6 隨行夥伴) 各自獨立行動與技能佇列依序施放
        for member in self.player.team:
            if not member.is_alive:
                continue

            # 更新技能冷卻 (包含已裝備出戰招式與本職技能庫)
            active_skills = member.get_active_skills()
            for s in active_skills:
                s.update(dt)
            for s in member.skills:
                if s not in active_skills:
                    s.update(dt)

            # 更新個人增益
            if member.is_buffed:
                member.buff_timer -= dt
                if member.buff_timer <= 0:
                    member.is_buffed = False

            # 遞減技能施放後搖間隔
            if getattr(member, "cast_delay_timer", 0.0) > 0:
                member.cast_delay_timer = max(0.0, member.cast_delay_timer - dt)

            # 檢查是否有就緒技能可施放
            ready_skills = [
                s for s in member.get_active_skills()
                if s.unlock_lvl <= self.player.level and s.is_ready
            ]

            if ready_skills:
                # 只要施法間隔冷卻結束 (cast_delay_timer <= 0)
                if member.cast_delay_timer <= 0:
                    # 依優先順位排序：光環增益 > 爆發神罰 > 控場護盾 > 多段連擊 > 常規平砍
                    ready_skills.sort(key=get_skill_priority)
                    best_skill = ready_skills[0]
                    self._member_attack(member, sound_mgr, specific_skill=best_skill)
                    member.cast_delay_timer = 0.38  # 每招之間保留 0.38 秒施法間隔，避免同毫秒齊放
                    member.attack_timer = 0.0
                    if not any(m.is_alive for m in self.monsters):
                        return
            else:
                # 所有技能皆在冷卻中：累積普攻計時器
                member.attack_timer += dt
                eff_spd = member.get_attack_speed(self.player)
                if member.attack_timer >= eff_spd and member.cast_delay_timer <= 0:
                    member.attack_timer = 0.0
                    self._member_attack(member, sound_mgr, force_normal=True)
                    if not any(m.is_alive for m in self.monsters):
                        return

        # 7. 怪物攻擊行動 (各存活怪物依獨立攻速蓄力攻擊)
        for m in [m for m in self.monsters if m.is_alive]:
            if m.freeze_timer <= 0:
                m.attack_timer += dt
                eff_m_spd = m.attack_speed * (1.3 if m.chill_timer > 0 else 1.0)
                if m.attack_timer >= eff_m_spd:
                    m.attack_timer = 0.0
                    self._monster_attack_unit(m, sound_mgr)
                    if not any(tm.is_alive for tm in self.player.team):
                        break


    def _execute_pending_hit(self, hit, sound_mgr):
        return execute_pending_hit(self, hit, sound_mgr)

    def _member_attack(self, member, sound_mgr, specific_skill=None, force_normal=False):
        return execute_member_attack(self, member, sound_mgr, specific_skill=specific_skill, force_normal=force_normal)

    def _apply_member_shield(self, caster, target, skill):
        return apply_member_shield(self, caster, target, skill)

    def _monster_attack(self, sound_mgr):
        alive = [m for m in self.monsters if m.is_alive]
        if alive:
            return self._monster_attack_unit(alive[0], sound_mgr)

    def _monster_attack_unit(self, m, sound_mgr):
        return process_monster_attack(self, m, sound_mgr)

    def _execute_monster_skill(self, skill, alive_members, sound_mgr, boss_monster=None):
        return execute_monster_skill(self, skill, alive_members, sound_mgr, boss_monster=boss_monster)

    def _on_monster_killed(self, sound_mgr):
        return handle_monster_killed(self, sound_mgr)
