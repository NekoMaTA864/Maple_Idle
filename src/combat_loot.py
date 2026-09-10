"""
《新楓之谷：放置遠征隊》戰鬥擊殺掉落與樓層晉級模組 (combat_loot.py)
"""
from settings import COLOR_GOLD
from item_system import generate_loot, create_seed_ring
from combat_zones import ZONES


def handle_monster_killed(combat_mgr, sound_mgr):
    """怪物全滅，支援多怪波次、精英怪掉落、掉寶率、樓層開寶箱與晉級"""
    if combat_mgr.is_training_dummy and combat_mgr.training_dummy_config:
        # 木樁測試：擊破後立即重生新木樁繼續無限打靶，累計完整測試時長的 DPS，不重置統計數據
        combat_mgr._spawn_training_dummy()
        return

    if getattr(combat_mgr, "is_gold_dungeon", False):
        combat_mgr.combat_stats.reset()
        p_lvl = max(1, combat_mgr.player.level)
        if p_lvl < 100:
            gold_award = int(300_000 + (p_lvl / 100.0) * 500_000)
        elif p_lvl < 200:
            gold_award = int(1_200_000 + ((p_lvl - 100) / 100.0) * 1_300_000)
        else:
            gold_award = int(3_500_000 + min(1.0, (p_lvl - 200) / 100.0) * 2_500_000)

        combat_mgr.player.add_gold(gold_award)
        sound_mgr.play("coin")
        combat_mgr.add_popup(f"[黃金寶庫 +${gold_award:,}]", "monster_0", (255, 215, 0))
        combat_mgr.add_log(f"[黃金寶庫] 成功擊破黃金寶箱怪！獲得楓幣 ${gold_award:,}！（金庫不提供經驗值）", COLOR_GOLD)
        combat_mgr._spawn_gold_dungeon_monster()
        return
    total_exp = sum(m.exp_reward for m in combat_mgr.monsters)
    base_gold = sum(m.gold_reward for m in combat_mgr.monsters)
    # 寵物磁吸加成與內潛楓幣獲得量
    loot_pet_mult = getattr(combat_mgr.player.pet_manager, "get_loot_multiplier", lambda: 1.0)() if hasattr(combat_mgr.player, "pet_manager") else 1.0
    meso_bonus = getattr(combat_mgr.player, "get_inner_ability_stat", lambda k: 0.0)("meso_rate")
    total_gold = int(base_gold * loot_pet_mult * (1.0 + meso_bonus))

    has_elite = any(getattr(m, "is_elite", False) for m in combat_mgr.monsters)
    is_boss = any(m.is_boss for m in combat_mgr.monsters)

    leveled_up = combat_mgr.player.add_exp(total_exp)
    combat_mgr.player.add_gold(total_gold)

    if has_elite:
        combat_mgr.add_log(f"[精英討伐] 成功殲滅菁英怪物波次！獲得 {total_exp} EXP (+80%)、{total_gold} 金幣 (+60%)！", (255, 215, 60))
    else:
        combat_mgr.add_log(f"[討伐] 成功殲滅怪物波次，獲得 {total_exp} EXP、{total_gold} 金幣！", COLOR_GOLD)

    if leveled_up:
        sound_mgr.play("levelup")
        combat_mgr.add_log(f"[升級] 遠征隊升級至 Lv.{combat_mgr.player.level}！獲得 4 點核心自由點數！", (60, 240, 130))

    # 掉落神裝 (適度調降掉落頻率，延長遊戲進度：首領 85%，菁英怪 25%，普通怪 7% + 裝備/內潛掉寶率)
    player_drop_bonus = (
        combat_mgr.player.get_gear_stat_sum("drop_rate")
        + combat_mgr.player.get_set_stat_sum("drop_rate")
        + getattr(combat_mgr.player, "get_inner_ability_stat", lambda k: 0.0)("drop_rate")
    )
    base_chance = 0.85 if is_boss else (0.25 if has_elite else 0.07)
    drop_chance = min(1.0, base_chance * (1.0 + player_drop_bonus))

    if combat_mgr.rng.random() < drop_chance:
        ref_m = combat_mgr.monsters[0] if combat_mgr.monsters else combat_mgr.monster
        ref_lvl = ref_m.lvl if ref_m else 1
        source_type = "boss" if is_boss else ("elite" if has_elite else "normal")
        loot = generate_loot(
            ref_lvl,
            is_boss=is_boss,
            player_level=combat_mgr.player.level,
            source_type=source_type,
        )
        if combat_mgr.player.add_to_inventory(loot):
            sound_mgr.play("loot")
            combat_mgr.add_log(f"[神裝] 獲得珍貴掉落：{loot.full_name} (需求 Lv.{loot.level_req})！", loot.color)
        else:
            combat_mgr.add_log(f"[背包] 背包已滿，未能拾取 {loot.full_name}。", (220, 120, 120))

    # 首領專屬稀有掉落 (艾比神級卷軸 X/V/B 與 潛能方塊)
    if is_boss:
        ref_m = combat_mgr.monsters[0] if combat_mgr.monsters else combat_mgr.monster
        b_lvl = ref_m.lvl if ref_m else 1
        if b_lvl >= 160 and combat_mgr.rng.random() < 0.40:
            s_roll = combat_mgr.rng.choice(["V", "B", "X"])
            s_name = "黑卷B" if s_roll == "B" else f"{s_roll}卷"
            combat_mgr.player.abby_scrolls[s_roll] = combat_mgr.player.abby_scrolls.get(s_roll, 0) + 1
            combat_mgr.add_log(f"[首領秘寶] 討伐首領大捷！斬獲神級【艾比{s_name} x1】！已存入庫存！", (255, 215, 0))
            sound_mgr.play("loot")
        elif b_lvl >= 100 and combat_mgr.rng.random() < 0.35:
            s_roll = combat_mgr.rng.choice(["X", "R"])
            combat_mgr.player.abby_scrolls[s_roll] = combat_mgr.player.abby_scrolls.get(s_roll, 0) + 1
            combat_mgr.add_log(f"[首領秘寶] 討伐首領大捷！獲得稀有【艾比{s_roll}卷 x1】！已存入庫存！", (200, 220, 255))
            sound_mgr.play("loot")
        elif combat_mgr.rng.random() < 0.30:
            s_roll = combat_mgr.rng.choice(["R", "electric"])
            s_name = "極電卷" if s_roll == "electric" else "宿命R卷"
            combat_mgr.player.abby_scrolls[s_roll] = combat_mgr.player.abby_scrolls.get(s_roll, 0) + 1
            combat_mgr.add_log(f"[首領掉落] 討伐首領獲得【艾比{s_name} x1】！", (180, 230, 255))

        if combat_mgr.rng.random() < 0.30:
            c_roll = combat_mgr.rng.choice(["bright", "bonus_bright", "bonus_occult"])
            c_names = {"bright": "閃耀方塊", "bonus_bright": "閃耀附加方塊", "bonus_occult": "可疑附加方塊"}
            combat_mgr.player.cube_inventory[c_roll] = combat_mgr.player.cube_inventory.get(c_roll, 0) + 1
            combat_mgr.add_log(f"[首領掉落] 獲得珍貴【{c_names[c_roll]} x1】！", (160, 240, 180))

        # 首領專屬稀有掉落：起源之塔特殊種子戒指 (規範之戒、持續之戒、武器泡泡之戒)
        # 依據首領等級開放：Lv.80+ 擊破首領時有機率斬獲種子戒指
        if b_lvl >= 80 and combat_mgr.rng.random() < (0.22 if b_lvl >= 160 else 0.12):
            seed_name = combat_mgr.rng.choice(["規範之戒", "持續之戒", "武器泡泡之戒"])
            seed_ring = create_seed_ring(seed_name)
            if combat_mgr.player.add_to_inventory(seed_ring):
                sound_mgr.play("loot")
                combat_mgr.add_log(f"[首領神兵] 討伐首領大捷！幸運斬獲起源之塔特殊神戒【{seed_ring.full_name}】！已存入行囊！", (255, 120, 180))
            else:
                combat_mgr.add_log(f"[背包] 背包已滿，未能拾取首領掉落的【{seed_ring.base_name}】。", (220, 120, 120))

        # 首領擊破獎勵：名譽點數 (內潛洗練)、萌獸卡包與寵物超級藥水補給
        if hasattr(combat_mgr.player, "inner_ability"):
            honor_gain = int(800 + combat_mgr.current_zone_idx * 200)
            combat_mgr.player.inner_ability.honor_exp += honor_gain
            combat_mgr.add_log(f"[遠征榮耀] 討伐首領立功！斬獲【名譽點數 +{honor_gain:,}】！", (120, 240, 180))
            combat_mgr.add_popup(f"[名譽 +{honor_gain:,}]", "monster_0", (120, 240, 180))

        if hasattr(combat_mgr.player, "familiar_manager") and combat_mgr.rng.random() < 0.45:
            combat_mgr.player.familiar_manager.familiar_cards += 1
            combat_mgr.add_log("[萌獸秘寶] 首領掉落了珍稀的【萌獸洗潛卡包 x1】！", (255, 210, 60))

        if hasattr(combat_mgr.player, "pet_manager"):
            combat_mgr.player.pet_manager.potions += 3
            combat_mgr.add_log("[寵物物資] 獲得寵物急救備用【超級藥水 x3】！", (100, 255, 120))

    # 關卡低階萌獸掉落 (普通/特殊萌獸，可用於吞噬升階主戰萌獸)
    if hasattr(combat_mgr.player, "familiar_manager"):
        fam_base_chance = 0.50 if is_boss else (0.25 if has_elite else 0.08)
        fam_chance = min(1.0, fam_base_chance * (1.0 + player_drop_bonus))
        if combat_mgr.rng.random() < fam_chance:
            from familiar_system import drop_stage_familiar, FAMILIAR_TIER_NAMES
            new_fam = drop_stage_familiar(is_boss=is_boss, has_elite=has_elite)
            combat_mgr.player.familiar_manager.add_familiar(new_fam)
            sound_mgr.play("loot")
            t_name = FAMILIAR_TIER_NAMES.get(new_fam.tier, new_fam.tier)
            combat_mgr.add_log(f"[萌獸捕獲] 斬獲野生萌獸【{new_fam.name} ({t_name})】！已存入萌獸卡冊，可用於吞噬升階！", (180, 240, 200))
            combat_mgr.add_popup(f"[{new_fam.name}]", "monster_0", (180, 240, 200))


    # 掉落符號碎片 (Symbol Fragments)
    zone = combat_mgr.get_current_zone()
    sym_key = zone.get("symbol_drop")
    if sym_key:
        frag_chance = 0.95 if is_boss else (0.55 if has_elite else 0.28)
        if combat_mgr.rng.random() < frag_chance:
            frag_count = (combat_mgr.rng.randint(2, 4) if is_boss else (2 if has_elite else 1))
            combat_mgr.player.add_symbol_fragment(sym_key, frag_count)
            sym_name = combat_mgr.player.get_symbol_name(sym_key)
            combat_mgr.add_popup(f"[{sym_name} 碎片 +{frag_count}]", "monster_0", (180, 220, 255))
            combat_mgr.add_log(f"[符號碎片] 獲得【{sym_name} 碎片 x{frag_count}】！", (180, 220, 255))

    # 層數制結算與首領通關 (支援鎖定地圖循環農怪)
    if is_boss:
        if combat_mgr.repeat_current_zone:
            # 循環刷怪模式開啟：留在原地重置為第 1 層
            combat_mgr.current_floor = 1
            combat_mgr.player.on_floor_cleared()
            if combat_mgr.current_zone_idx + 1 < len(ZONES):
                combat_mgr.unlocked_zones = max(combat_mgr.unlocked_zones, combat_mgr.current_zone_idx + 2)
            combat_mgr.add_log(f"[循環刷怪] 成功擊破首領！【原地循環模式】保持在【{zone['name']}】重置至第 1/10 層！", (255, 215, 0))
        elif combat_mgr.current_zone_idx + 1 < len(ZONES):
            # 普通推進模式
            combat_mgr.unlocked_zones = max(combat_mgr.unlocked_zones, combat_mgr.current_zone_idx + 2)
            combat_mgr.current_zone_idx += 1
            combat_mgr.current_floor = 1
            combat_mgr.player.on_floor_cleared()
            next_zone = combat_mgr.get_current_zone()
            combat_mgr.add_log(f"[通關大捷] 成功討伐區域首領！遠征隊全員復活滿血，晉級【{next_zone['name']}】第 1/10 層！", (255, 215, 0))
        else:
            # 最終太古魔神擊破
            combat_mgr.current_floor = 1
            combat_mgr.player.on_floor_cleared()
            b_name = combat_mgr.monster.name if combat_mgr.monster else "太古神"
            combat_mgr.add_log(f"[太古榮耀] 終極首領【{b_name}】已被遠征隊徹底擊潰！全員獲封新楓之谷格蘭帝斯救世主！", (255, 215, 0))
        combat_mgr.is_boss_active = False
    else:
        # 普通層數突破 (1..9 層)
        combat_mgr.current_floor += 1
        combat_mgr.player.on_floor_cleared()
        combat_mgr.add_log(f"[層數突破] 遠征隊挺進至第 {combat_mgr.current_floor}/10 層！全員傷勢已全額治癒刷新！", (80, 240, 140))

    combat_mgr.spawn_next_monster()

