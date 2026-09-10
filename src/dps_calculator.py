"""
《新楓之谷：放置遠征隊》獨立 DPS 高速演算計算器 (dps_calculator.py)

功能特性：
1. 高速純數值模擬：直接調用 CombatManager 核心戰鬥邏輯（略過 UI/QPainter 與 60FPS 限制），5 分鐘戰鬥約 0.8~1.2 秒完成。
2. 完整統計輸出：全隊總傷害、小隊 DPS、各隊員輸出與佔比、平砍/技能比例、暴擊率、技能傷害剖析、治療與護盾量。
3. 支援多目標測試：1~5 隻木樁群怪環境，驗證單體 vs AOE 群怪收益。
4. 24 職業天梯排行榜：快速對 24 種正統新楓之谷職業進行單人基準 DPS 跑分排行。
5. 支援讀取遊戲存檔：可直接代入玩家目前的裝備、潛能、星力、符號與隊伍配置進行實戰測評。
"""

import sys
import os
import time
import argparse
import unicodedata
import random

# 確保在 Windows 各種終端環境下輸出編碼安全
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
if hasattr(sys.stderr, "reconfigure"):
    try:
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# 將 src 目錄加入 Python 路徑
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

from classes import ALL_CLASSES, get_class_info
from player_data import Player, TeamMember
from combat_system import CombatManager
from player_save import load_player_from_file
from inner_ability import InnerAbilityLine
from familiar_system import Familiar, FamiliarLine


class SilentSound:
    """純文字/無頭模擬專用靜音音效管理器"""
    def play(self, *args, **kwargs):
        pass


class MockGearItem:
    """模擬標準裝備插槽物件"""
    def __init__(self, stats):
        self._stats = stats
        self.set_id = None

    def get_effective_stats(self, *args, **kwargs):
        return dict(self._stats)


def apply_endgame_gear_standard(player):
    """
    為玩家裝配一套客觀、標準且通用的新楓之谷畢業神裝模板 (Standard Endgame Preset):
    - 等級補正至 Lv.260 (原初神域巔峰)
    - 基礎屬性補正 (對標全套 22 星神裝)
    - WSE 核心部位: 總無視防禦 90% (削弱 300% 頂級王至 30%，保留 70% 完整打擊)
    - BOSS 傷: +250% (滅龍/創世/漆黑套裝加成)
    - 暴傷: +65% (手套傳說雙暴傷)
    - 萌獸: 👑 傳說三終真·皮卡啾 (3排終傷 +20%，獨立相乘 +72.8%)
    - 寵物: 🐾 3 隻頂級月光小寵物 (飾品+165攻, 月光祝福+30攻)
    - 內潛: 首排 BOSS傷 +20%、二排暴擊率 +18%、三排無冷 +10%
    """
    player.level = max(260, player.level)
    player.stat_atk = max(1500, player.stat_atk)
    player.stat_crit = max(60, player.stat_crit)

    # 裝配全套標準畢業裝備 (WSE + 手套 + 飾品)
    player.equipped["weapon"] = MockGearItem({
        "attack": 1800, "def_ignore": 0.40, "boss_dmg": 0.80, "crit_dmg": 0.15, "crit_chance": 0.10
    })
    player.equipped["sub_weapon"] = MockGearItem({
        "attack": 1200, "def_ignore": 0.35, "boss_dmg": 0.70, "crit_chance": 0.10
    })
    player.equipped["emblem"] = MockGearItem({
        "attack": 1000, "def_ignore": 0.15, "boss_dmg": 0.60, "damage_mult": 0.20
    })
    player.equipped["gloves"] = MockGearItem({
        "attack": 600, "crit_dmg": 0.30, "crit_chance": 0.10
    })
    player.equipped["ring1"] = MockGearItem({
        "attack": 400, "boss_dmg": 0.20, "crit_dmg": 0.10
    })
    player.equipped["pendant1"] = MockGearItem({
        "attack": 400, "boss_dmg": 0.20, "crit_dmg": 0.10
    })

    # 傳說內在能力
    player.inner_ability.tier = "legendary"
    player.inner_ability.lines = [
        InnerAbilityLine("boss_damage", "legendary", 0.20),
        InnerAbilityLine("crit_chance", "unique", 0.18),
        InnerAbilityLine("cooldown_skip", "unique", 0.10)
    ]

    # 3 隻滿卷月光小寵物
    for p in player.pet_manager.pets:
        p.is_active = False
    player.pet_manager.set_pet_active("pet_luna_titania", True)
    player.pet_manager.set_pet_active("pet_luna_bella", True)
    player.pet_manager.set_pet_active("pet_luna_pico", True)
    for p in player.pet_manager.get_active_pets():
        p.equip_atk = 55

    # 傳奇三終真·皮卡啾
    player.familiar_manager.familiars = [
        Familiar("fam_3fd", "神之真·三終皮卡啾", "legendary", [
            FamiliarLine("final_damage", "legendary", 0.20),
            FamiliarLine("final_damage", "legendary", 0.20),
            FamiliarLine("final_damage", "legendary", 0.20)
        ], is_summoned=True)
    ]


def create_simulation_player(
    level=200, class_ids=None, load_save=False,
    inner_legendary=False, pets_luna=False, familiar_3fd=False,
    endgame=False
):
    """建立用於模擬計算的 Player 對象"""
    player = Player()

    if load_save:
        res = load_player_from_file(player)
        if res is not None:
            print(f"[系統] 已成功載入遊戲存檔！隊伍等級: Lv.{player.level}，金幣: {player.gold:,}")
        else:
            print("[警告] 未找到存檔 savegame.json，使用預設配置。")

    if level and not load_save:
        player.level = max(1, min(300, int(level)))

    if class_ids:
        # 自選職業組合
        valid_cids = [cid.strip() for cid in class_ids if cid.strip() in ALL_CLASSES]
        if valid_cids:
            player.team = [
                TeamMember(idx, cid, player)
                for idx, cid in enumerate(valid_cids[:5])
            ]

    # 若指定標準畢業套裝，直接裝配標準巔峰神裝
    if endgame:
        apply_endgame_gear_standard(player)
        print("[模擬強化] 已裝配【🌟 標準畢業巔峰神裝】：Lv.260、90%無視、250%BOSS傷、三終萌獸、P寵滿卷！")
    else:
        # 套用自選個別強化配置
        if inner_legendary:
            player.inner_ability.tier = "legendary"
            player.inner_ability.lines = [
                InnerAbilityLine("boss_damage", "legendary", 0.20),
                InnerAbilityLine("crit_chance", "unique", 0.18),
                InnerAbilityLine("cooldown_skip", "unique", 0.10)
            ]
            print("[模擬強化] 已裝配【傳說內潛】：BOSS傷+20%、暴擊率+18%、無冷+10%！")

        if pets_luna:
            for p in player.pet_manager.pets:
                p.is_active = False
            player.pet_manager.set_pet_active("pet_luna_titania", True)
            player.pet_manager.set_pet_active("pet_luna_bella", True)
            player.pet_manager.set_pet_active("pet_luna_pico", True)
            for p in player.pet_manager.get_active_pets():
                p.equip_atk = 30
            print("[模擬強化] 已裝配【3隻月光小寵物 (P寵)】：飾品攻擊力 +90、月光祝福 +30！")

        if familiar_3fd:
            fam_3fd = Familiar("fam_3fd", "神之真·三終皮卡啾", "legendary", [
                FamiliarLine("final_damage", "legendary", 0.20),
                FamiliarLine("final_damage", "legendary", 0.20),
                FamiliarLine("final_damage", "legendary", 0.20)
            ], is_summoned=True)
            player.familiar_manager.familiars = [fam_3fd]
            print("[模擬強化] 已召喚【👑 傳奇三終萌獸】：三排終傷 +20% (獨立相乘 +72.8%)！")

    # 確保全技能已啟用
    for m in player.team:
        m.enable_all_skills()

    return player


def run_dps_simulation(
    player,
    duration_sec=300.0,
    dummy_level=200,
    dummy_hp=10**13,
    dummy_def=300,
    dummy_targets=1,
    sim_dt=0.05,
    is_boss=True,
    rng=None,
):
    """
    執行純邏輯高速戰鬥模擬
    :param player: Player 對象
    :param duration_sec: 戰鬥模擬秒數 (預設 300 秒)
    :param dummy_level: 木樁等級
    :param dummy_hp: 木樁血量
    :param dummy_def: 木樁防禦力 (楓之谷頂級首領防禦通常為 300%)
    :param dummy_targets: 木樁數量 (1 ~ 5)
    :param sim_dt: 每步時間步長 (預設 0.05 秒，即 20Hz 邏輯更新)
    :param is_boss: 是否為首領木樁 (首領木樁觸發裝備、套裝、內潛與萌獸的 BOSS傷 加成)
    """
    combat_mgr = CombatManager(player, rng=rng)
    combat_mgr.configure_training_dummy(
        dummy_level, dummy_hp, attack=0, defense=dummy_def, count=dummy_targets, is_boss=is_boss
    )

    sound_mgr = SilentSound()
    total_ticks = max(1, int(duration_sec / sim_dt))

    t_start = time.time()
    for _ in range(total_ticks):
        combat_mgr.update(sim_dt, sound_mgr)
    real_time_elapsed = time.time() - t_start

    stats = combat_mgr.combat_stats
    total_damage = stats.total_damage
    team_dps = stats.team_dps

    # 匯總各成員數據
    member_data = []
    for idx, mem in enumerate(player.team):
        m_st = stats.for_member(idx)
        dmg = m_st.damage_dealt
        dps = stats.member_dps(idx)
        share = (dmg / max(1, total_damage)) * 100.0
        total_hits = m_st.hit_lines if m_st.hit_lines > 0 else m_st.attack_count
        crit_rate = min(100.0, (m_st.critical_count / max(1, total_hits)) * 100.0)
        norm_atks = max(0, m_st.attack_count - m_st.skill_cast_count)

        # 整理招牌技能輸出
        sorted_skills = sorted(
            m_st.skill_damage.items(),
            key=lambda x: x[1],
            reverse=True
        )

        skill_breakdown = []
        for sk_name, sk_dmg in sorted_skills:
            sk_share = (sk_dmg / max(1, dmg)) * 100.0
            casts = m_st.skill_casts.get(sk_name, 0)
            avg_hit = sk_dmg / max(1, casts)
            skill_breakdown.append({
                "name": sk_name,
                "damage": sk_dmg,
                "share": sk_share,
                "casts": casts,
                "avg_hit": avg_hit,
            })

        member_data.append({
            "slot_idx": idx,
            "class_id": mem.class_id,
            "name": mem.name,
            "faction": mem.faction,
            "branch": mem.branch,
            "damage": dmg,
            "dps": dps,
            "share": share,
            "attacks": m_st.attack_count,
            "skill_casts": m_st.skill_cast_count,
            "normal_attacks": norm_atks,
            "crit_count": m_st.critical_count,
            "crit_rate": crit_rate,
            "highest_hit": m_st.highest_hit,
            "shield_granted": m_st.shield_granted,
            "shield_absorbed": m_st.shield_absorbed,
            "healing_done": m_st.healing_done,
            "buff_casts": m_st.buff_cast_count,
            "skills": skill_breakdown,
        })

    return {
        "duration": stats.elapsed_seconds,
        "real_time": real_time_elapsed,
        "team_damage": total_damage,
        "team_dps": team_dps,
        "dummy_level": dummy_level,
        "dummy_defense": dummy_def,
        "dummy_targets": dummy_targets,
        "members": member_data,
    }


def print_simulation_report(res):
    """格式化輸出美觀的 ASCII 戰鬥統計報表"""
    raw_d = float(res.get("dummy_defense", 300))
    def_pct = int(round(raw_d if raw_d >= 5.0 else raw_d * 100))
    print("\n" + "=" * 78)
    print(" 🍁 《新楓之谷：放置遠征隊》DPS 高速演算測試報告 🍁")
    print("=" * 78)
    print(f" 戰鬥模擬時間: {res['duration']:.1f} 秒 (算法耗時: {res['real_time']:.3f} 秒)")
    print(f" 木樁配置環境: Lv.{res['dummy_level']} | 正統防禦率: {def_pct}% | 目標數量: {res['dummy_targets']} 隻")
    print(f" 遠征小隊總傷: {res['team_damage']:,} 點傷害")
    print(f" 小隊整體 DPS: {res['team_dps']:,.1f} / 秒")
    print("-" * 78)

    # 成員輸出總覽表
    print(f" {'席位':<4} {'職業 (陣營)':<18} {'總輸出傷害':<14} {'單人 DPS':<12} {'佔比':<8} {'打擊數':<8} {'暴擊率':<8}")
    print("-" * 78)
    for m in res["members"]:
        class_str = f"{m['name']} ({m['faction']})"
        dmg_str = f"{m['damage']:,}"
        dps_str = f"{m['dps']:,.1f}"
        share_str = f"{m['share']:.1f}%"
        atk_str = f"{m['attacks']}"
        crit_str = f"{m['crit_rate']:.1f}%"
        print(f" [{m['slot_idx']+1}]  {class_str:<18} {dmg_str:<14} {dps_str:<12} {share_str:<8} {atk_str:<8} {crit_str:<8}")

    print("-" * 78)
    print(" ⚔️  各隊員主力招式傷害深度剖析 (Top Skills Breakdown):")
    print("-" * 78)

    for m in res["members"]:
        print(f" ▶ [{m['slot_idx']+1}] {m['name']} ({m['class_id']}) - 總輸出: {m['damage']:,} | 頂傷: {m['highest_hit']:,}")
        if m.get("healing_done", 0) > 0 or m.get("shield_granted", 0) > 0:
            supp_parts = []
            if m["healing_done"] > 0:
                supp_parts.append(f"累積治療: {m['healing_done']:,}")
            if m["shield_granted"] > 0:
                supp_parts.append(f"提供護盾: {m['shield_granted']:,}")
            print(f"    💚 輔助支援: {' | '.join(supp_parts)}")

        if not m["skills"]:
            print("    (無技能輸出記錄，全數為普攻)")
        else:
            for sk in m["skills"][:4]:
                bar_len = int(sk["share"] / 5)
                bar = "■" * bar_len + " " * (20 - bar_len)
                print(f"    - {sk['name']:<12} | {bar} | {sk['damage']:>10,} ({sk['share']:>5.1f}%) | {sk['casts']:>3}次 (均傷 {sk['avg_hit']:>7,.0f})")
        print()

    print("=" * 78 + "\n")


def classify_class_role(class_id):
    """判定職業戰術定位 (坦/輔/輸出)"""
    if class_id in ["paladin", "dark_knight", "mechanic"]:
        return "🛡️ 坦克 (Tank)"
    elif class_id in ["bishop", "battle_mage", "flame_wizard", "pathfinder"]:
        return "💚 輔助 (Support)"
    else:
        return "⚔️ 輸出 (DPS)"


def create_random_team_player(level=200):
    """全隨機抽取 7 個不同職業組建遠征小隊 (1 主角 + 6 隨行夥伴)"""
    import random
    cids = random.sample(list(ALL_CLASSES.keys()), 7)
    player = Player()
    player.level = level
    player.team = [TeamMember(idx, cid, player) for idx, cid in enumerate(cids)]
    for m in player.team:
        m.enable_all_skills()
    return player, cids


def run_ladder_ranking(level=260, duration_sec=60.0, dummy_def=300, dummy_targets=1, rounds=3, endgame=True):
    """
    執行 24 職業單人基準 DPS 天梯排行測試 (支援多場次平均數消除暴擊與技能輪轉隨機浮動)
    :param endgame: 是否裝配標準畢業神裝 (預設 True)
    """
    gear_mode_str = "【🌟 標準畢業神裝】" if endgame else "【預設無裝】"
    print(f"\n[天梯排行] 開始進行 24 職業標準化基準測試 (Lv.{level}, 規格: {gear_mode_str}, 時長: {duration_sec}s, 木樁防禦: {dummy_def}%, 目標: {dummy_targets}隻, 每職業測試 {rounds} 場取平均值)...")
    results = []

    t_all_start = time.time()
    for cid, cinfo in ALL_CLASSES.items():
        dps_records = []
        last_res = None
        for _ in range(rounds):
            player = Player()
            player.level = level
            player.team = [TeamMember(0, cid, player)]
            player.team[0].enable_all_skills()
            if endgame:
                apply_endgame_gear_standard(player)

            res = run_dps_simulation(
                player,
                duration_sec=duration_sec,
                dummy_level=level,
                dummy_def=dummy_def,
                dummy_targets=dummy_targets,
                sim_dt=0.05,
                is_boss=dummy_def >= 100
            )
            dps_records.append(res["members"][0]["dps"])
            last_res = res

        m0 = last_res["members"][0]
        avg_dps = sum(dps_records) / max(1, len(dps_records))
        min_dps = min(dps_records)
        max_dps = max(dps_records)
        top_skill = m0["skills"][0]["name"] if m0["skills"] else "普攻"
        top_skill_share = m0["skills"][0]["share"] if m0["skills"] else 100.0

        results.append({
            "class_id": cid,
            "name": cinfo["name"],
            "faction": cinfo["faction"],
            "branch": cinfo["branch"],
            "role": classify_class_role(cid),
            "dps": avg_dps,
            "min_dps": min_dps,
            "max_dps": max_dps,
            "total_damage": m0["damage"],
            "crit_rate": m0["crit_rate"],
            "top_skill": top_skill,
            "top_skill_share": top_skill_share,
            "highest_hit": m0["highest_hit"],
        })

    # 依照平均 DPS 降冪排序
    results.sort(key=lambda x: x["dps"], reverse=True)
    total_calc_time = time.time() - t_all_start

    # 輸出天梯排行榜
    print("\n" + "=" * 90)
    print(f" 🏆 24 職業單人 DPS 天梯榜 (各職業跑 {rounds} 場取平均值 | 總耗時: {total_calc_time:.2f}s) 🏆")
    print("=" * 90)
    print(f" {'名次':<4} {'職業名稱':<10} {'定位':<14} {'陣營-分支':<14} {'平均 DPS':<15} {'浮動區間 (Min~Max)':<22} {'主力技能':<16}")
    print("-" * 90)

    for rank, r in enumerate(results, 1):
        tier = "⭐ S " if rank <= 5 else ("   A " if rank <= 12 else ("   B " if rank <= 18 else "   C "))
        faction_branch = f"{r['faction']}-{r['branch']}"
        skill_str = f"{r['top_skill']} ({r['top_skill_share']:.0f}%)"
        range_str = f"[{r['min_dps']:,.0f} ~ {r['max_dps']:,.0f}]"
        print(f" #{rank:<2} {tier} {r['name']:<8} {r['role']:<14} {faction_branch:<14} {r['dps']:>9,.1f}/s   {range_str:<22} {skill_str}")

    print("=" * 90)
    print(" 💡 備註：")
    print(f" - 本次數據為每職業真實跑滿 {rounds} 場戰鬥之精確算術平均數，有效消除暴擊機率與技能冷卻步調之隨機誤差。")
    print(" - 輔助與坦克型職業（主教、煉獄、聖騎、機甲）著重於全隊光環、減傷護盾與急救群補，在小隊實戰中能使整體團隊輸出與生存能力倍增。")
    print("=" * 90 + "\n")
    return results


def str_width(s):
    """計算字串包含全形中文字元在終端機的顯示寬度"""
    w = 0
    for ch in s:
        if unicodedata.east_asian_width(ch) in ('F', 'W'):
            w += 2
        else:
            w += 1
    return w


def pad_str(s, width, align="left"):
    """根據字串在終端機的顯示寬度進行對齊填充"""
    w = str_width(s)
    pad = max(0, width - w)
    if align == "right":
        return " " * pad + s
    elif align == "center":
        left = pad // 2
        right = pad - left
        return " " * left + s + " " * right
    else:
        return s + " " * pad


def run_comprehensive_matrix_ranking(level=260, short_sec=60.0, long_sec=180.0, rounds=2, endgame=True, **kwargs):
    """
    執行 24 職業全維度實戰雙軸矩陣評測：
    - 短線作戰 (60秒): 小怪割草 (3怪/20%防)、中級首領 (1怪/100%防)、頂級首領 (1怪/300%防)
    - 長線作戰 (180秒): 小怪割草 (3怪/20%防)、中級首領 (1怪/100%防)、頂級首領 (1怪/300%防)
    - 獨立輸出兩組表格 (不計綜合分數，依頂級首領輸出排序)
    - 總結 6 大環境 Top 5 前 5 名純名稱名冊 (傷害數值保留在上方表格)
    """
    gear_mode_str = "【🌟 標準畢業巔峰神裝 (90%無視/250%B傷/三終萌獸/P寵滿卷)】" if endgame else "【預設無裝】"
    print("\n" + "=" * 116)
    print(" 📊 24 職業全維度實戰雙軸矩陣評測 (短線 60s / 長線 180s 各 3 環境對比)")
    print(f" 裝備規格基準: {gear_mode_str} | 每環境各跑 {rounds} 場取平均")
    print("=" * 116)

    scenarios = [
        ("mob_farm",  "🌾 小怪割草 (3怪 / 20%防)", 3, 20, False),
        ("mid_boss",  "⚔️ 中級首領 (1怪 / 100%防)", 1, 100, True),
        ("end_boss",  "👑 頂級首領 (1怪 / 300%防)", 1, 300, True),
    ]

    t_start = time.time()

    short_results = {}
    long_results = {}

    total_classes = len(ALL_CLASSES)
    print(f"[進度] 正在模擬 24 職業之短線 ({short_sec:.0f}s) 與長線 ({long_sec:.0f}s) 實戰數據 (共計 {total_classes * len(scenarios) * 2 * rounds} 場戰鬥)...")

    for cid, cinfo in ALL_CLASSES.items():
        role = classify_class_role(cid)
        cname = cinfo["name"]

        short_results[cid] = {
            "class_id": cid, "name": cname, "role": role,
            "scores": {}
        }
        long_results[cid] = {
            "class_id": cid, "name": cname, "role": role,
            "scores": {}
        }

        for s_key, s_name, s_targets, s_def, s_is_boss in scenarios:
            # 1. 短線 (60s)
            short_runs = []
            for _ in range(rounds):
                p = Player()
                p.level = level
                p.team = [TeamMember(0, cid, p)]
                p.team[0].enable_all_skills()
                if endgame:
                    apply_endgame_gear_standard(p)
                res = run_dps_simulation(p, duration_sec=short_sec, dummy_level=level, dummy_def=s_def, dummy_targets=s_targets, sim_dt=0.05, is_boss=s_is_boss)
                short_runs.append(res["members"][0]["dps"])
            short_results[cid]["scores"][s_key] = sum(short_runs) / max(1, len(short_runs))

            # 2. 長線 (180s)
            long_runs = []
            for _ in range(rounds):
                p = Player()
                p.level = level
                p.team = [TeamMember(0, cid, p)]
                p.team[0].enable_all_skills()
                if endgame:
                    apply_endgame_gear_standard(p)
                res = run_dps_simulation(p, duration_sec=long_sec, dummy_level=level, dummy_def=s_def, dummy_targets=s_targets, sim_dt=0.05, is_boss=s_is_boss)
                long_runs.append(res["members"][0]["dps"])
            long_results[cid]["scores"][s_key] = sum(long_runs) / max(1, len(long_runs))

    total_time = time.time() - t_start

    # 排序：依照頂級首領 (end_boss) 降序排列 (不使用綜合分數)
    short_list = list(short_results.values())
    short_list.sort(key=lambda x: x["scores"]["end_boss"], reverse=True)

    long_list = list(long_results.values())
    long_list.sort(key=lambda x: x["scores"]["end_boss"], reverse=True)

    # 統計短線各環境前 5 名
    short_top5 = {}
    for s_key, _, _, _, _ in scenarios:
        s_sorted = sorted(short_list, key=lambda x: x["scores"][s_key], reverse=True)
        short_top5[s_key] = {item["class_id"]: r for r, item in enumerate(s_sorted[:5], 1)}

    # 統計長線各環境前 5 名
    long_top5 = {}
    for s_key, _, _, _, _ in scenarios:
        l_sorted = sorted(long_list, key=lambda x: x["scores"][s_key], reverse=True)
        long_top5[s_key] = {item["class_id"]: r for r, item in enumerate(l_sorted[:5], 1)}

    def format_cell(score, rank_in_sc):
        score_str = f"{score / 10000:>6.1f} 萬/s"
        if rank_in_sc:
            return f"{score_str} ★{rank_in_sc}"
        else:
            return f"{score_str}    "

    # ========================== 表格 1：短線作戰 (60s) ==========================
    print("\n" + "=" * 116)
    print(f" ⏱️ 【短線作戰 ({short_sec:.0f}秒)】24 職業實戰環境 DPS 交叉矩陣 (依頂級首領排序，前5名標註 ★1~★5)")
    print("=" * 116)
    col_rank = pad_str("名次", 6)
    col_name = pad_str("職業名稱", 12)
    col_role = pad_str("定位", 14)
    col_mob = pad_str("🌾 小怪割草 (3怪/20%防)", 26)
    col_mid = pad_str("⚔️ 中級首領 (1怪/100%防)", 26)
    col_end = pad_str("👑 頂級首領 (1怪/300%防)", 26)
    print(f" {col_rank} {col_name} {col_role} {col_mob} {col_mid} {col_end}")
    print("-" * 116)

    for rank, r in enumerate(short_list, 1):
        s = r["scores"]
        c_rank = pad_str(f"#{rank}", 6)
        c_name = pad_str(r["name"], 12)
        c_role = pad_str(r["role"], 14)
        c_mob = pad_str(format_cell(s["mob_farm"], short_top5["mob_farm"].get(r["class_id"])), 26)
        c_mid = pad_str(format_cell(s["mid_boss"], short_top5["mid_boss"].get(r["class_id"])), 26)
        c_end = pad_str(format_cell(s["end_boss"], short_top5["end_boss"].get(r["class_id"])), 26)
        print(f" {c_rank} {c_name} {c_role} {c_mob} {c_mid} {c_end}")
    print("=" * 116)

    # ========================== 表格 2：長線作戰 (180s) ==========================
    print("\n" + "=" * 116)
    print(f" ⏱️ 【長線作戰 ({long_sec:.0f}秒)】24 職業實戰環境 DPS 交叉矩陣 (依頂級首領排序，前5名標註 ★1~★5)")
    print("=" * 116)
    print(f" {col_rank} {col_name} {col_role} {col_mob} {col_mid} {col_end}")
    print("-" * 116)

    for rank, r in enumerate(long_list, 1):
        s = r["scores"]
        c_rank = pad_str(f"#{rank}", 6)
        c_name = pad_str(r["name"], 12)
        c_role = pad_str(r["role"], 14)
        c_mob = pad_str(format_cell(s["mob_farm"], long_top5["mob_farm"].get(r["class_id"])), 26)
        c_mid = pad_str(format_cell(s["mid_boss"], long_top5["mid_boss"].get(r["class_id"])), 26)
        c_end = pad_str(format_cell(s["end_boss"], long_top5["end_boss"].get(r["class_id"])), 26)
        print(f" {c_rank} {c_name} {c_role} {c_mob} {c_mid} {c_end}")
    print("=" * 116)

    # ========================== 6 大環境 Top 5 前五名名冊 ==========================
    print("\n" + "=" * 116)
    print(f" 🏆 6 大實戰環境 Top 5 榜首名單 (總耗時: {total_time:.2f}s | 傷害數值請查閱上方對應表格)：")
    print("-" * 116)

    # 短線 60s
    for s_key, s_name, _, _, _ in scenarios:
        s_sorted = sorted(short_list, key=lambda x: x["scores"][s_key], reverse=True)[:5]
        names = [f"#{r} {item['name']}" for r, item in enumerate(s_sorted, 1)]
        label = f"【短線 {short_sec:.0f}s - {s_name}】"
        print(f" {pad_str(label, 38)} :  {'   '.join(names)}")

    print("-" * 116)

    # 長線 180s
    for s_key, s_name, _, _, _ in scenarios:
        s_sorted = sorted(long_list, key=lambda x: x["scores"][s_key], reverse=True)[:5]
        names = [f"#{r} {item['name']}" for r, item in enumerate(s_sorted, 1)]
        label = f"【長線 {long_sec:.0f}s - {s_name}】"
        print(f" {pad_str(label, 38)} :  {'   '.join(names)}")

    print("=" * 116 + "\n")
    return {"short": short_list, "long": long_list}


def interactive_menu():
    """終端互動選單模式"""
    while True:
        print("\n" + "=" * 54)
        print("     🍁 新楓之谷：放置遠征隊 - DPS 演算計算器 🍁")
        print("=" * 54)
        print(" 1. 模擬目前存檔隊伍 (讀取最新存檔 5 人組合，5分鐘木樁)")
        print(" 2. 模擬 24 職業單人 DPS 天梯排行榜 (多場次平均 / 全維度矩陣)")
        print(" 3. 自定義陣容與木樁環境 (自選職業、木樁數量 1~5 隻)")
        print(" 4. 全隨機 5 人組隊實測 (隨機自 24 職業湊出 5 人進場測試)")
        print(" 5. 退出計算器")
        print("=" * 54)

        choice = input("請選擇操作功能 [1-5]: ").strip()
        if choice == "1":
            p = create_simulation_player(load_save=True)
            res = run_dps_simulation(p, duration_sec=300.0, dummy_targets=1)
            print_simulation_report(res)
        elif choice == "2":
            print("\n[天梯模式選擇]")
            print(" 1. 雙軸實戰矩陣 (短線60s + 長線180s 各3環境對比，預設標準畢業神裝)")
            print(" 2. 單一木樁基準天梯 (3 場平均，預設木樁防禦 300%，標準畢業神裝)")
            sub_choice = input("請選擇天梯類型 [1-2, 預設 1]: ").strip()
            if sub_choice == "2":
                rounds_in = input("請輸入每職業測試場次 (取平均值) [預設 3]: ").strip()
                n_rounds = int(rounds_in) if rounds_in.isdigit() and int(rounds_in) > 0 else 3
                def_in = input("請輸入木樁防禦率% [預設 300]: ").strip()
                n_def = int(def_in) if def_in.isdigit() else 300
                run_ladder_ranking(level=260, duration_sec=60.0, dummy_def=n_def, dummy_targets=1, rounds=n_rounds, endgame=True)
            else:
                rounds_in = input("請輸入每環境測試輪數 (取平均) [預設 2]: ").strip()
                n_rounds = int(rounds_in) if rounds_in.isdigit() and int(rounds_in) > 0 else 2
                run_comprehensive_matrix_ranking(level=260, short_sec=60.0, long_sec=180.0, rounds=n_rounds, endgame=True)
        elif choice == "3":
            print("\n可選職業清單 ID:")
            c_list = list(ALL_CLASSES.keys())
            for i in range(0, len(c_list), 4):
                line = "  ".join(f"{c:>18}: {ALL_CLASSES[c]['name']}" for c in c_list[i:i+4])
                print(line)

            classes_input = input("\n請輸入 1~5 個職業 ID (以逗號分隔，留空使用預設): ").strip()
            cids = [c.strip() for c in classes_input.split(",")] if classes_input else None

            endgame_input = input("是否裝配【標準畢業神裝】測試巔峰傷害？[Y/N, 預設 Y]: ").strip().upper()
            is_endgame = endgame_input != "N"

            targets_input = input("請輸入木樁群怪數量 [1~5, 預設 1]: ").strip()
            targets = int(targets_input) if targets_input.isdigit() else 1

            time_input = input("請輸入戰鬥秒數 [預設 300]: ").strip()
            sec = float(time_input) if time_input.isdigit() else 300.0

            def_input = input("請輸入木樁防禦率% [20: 小怪, 100: 中級王, 300: 頂級首領, 預設 300]: ").strip()
            defense = int(def_input) if def_input.isdigit() else 300
            is_boss_flag = defense >= 100

            p = create_simulation_player(level=260 if is_endgame else 200, class_ids=cids, endgame=is_endgame)
            res = run_dps_simulation(p, duration_sec=sec, dummy_def=defense, dummy_targets=targets, is_boss=is_boss_flag)
            print_simulation_report(res)
        elif choice == "4":
            while True:
                p, picked_cids = create_random_team_player(level=260)
                apply_endgame_gear_standard(p)
                print("\n🎲 隨機抽籤湊出 7 人遠征隊 (1 主角 + 6 隨行夥伴，已套用標準畢業神裝)：")
                roles_count = {"tank": 0, "support": 0, "dps": 0}
                for i, cid in enumerate(picked_cids):
                    cname = ALL_CLASSES[cid]["name"]
                    role = classify_class_role(cid)
                    if "坦克" in role: roles_count["tank"] += 1
                    elif "輔助" in role: roles_count["support"] += 1
                    else: roles_count["dps"] += 1
                    print(f"  席位 {i+1}: 【{cname}】({cid}) - {role}")

                eval_str = f"坦克 x{roles_count['tank']} | 輔助 x{roles_count['support']} | 輸出 x{roles_count['dps']}"
                if roles_count['tank'] >= 1 and roles_count['support'] >= 1:
                    verdict = "【黃金平衡】坦補齊備，生存無憂且火力強盛！"
                elif roles_count['support'] >= 2:
                    verdict = "【神聖庇護】多重輔助護盾治療，持久戰極穩！"
                elif roles_count['tank'] == 0 and roles_count['support'] == 0:
                    verdict = "【純粹暴力】極限全輸出！木樁狂暴但高壓首領極度危險！"
                else:
                    verdict = "【偏鋒陣容】極具特色的混編小隊！"
                print(f"\n小隊體系評估: {eval_str} -> {verdict}")

                res = run_dps_simulation(p, duration_sec=120.0, dummy_def=300, dummy_targets=1, is_boss=True)
                print_simulation_report(res)

                again = input("是否再次隨機組隊？[R: 重新隨機 / 任意鍵返回主選單]: ").strip().upper()
                if again != "R":
                    break
        elif choice == "5":
            print("感謝使用，再會！")
            break
        else:
            print("無效選項，請重新輸入。")


def main():
    parser = argparse.ArgumentParser(description="新楓之谷：放置遠征隊 DPS 演算計算器")
    parser.add_argument("-t", "--time", type=float, default=300.0, help="戰鬥模擬秒數 (預設 300 秒)")
    parser.add_argument("-n", "--targets", type=int, default=1, help="木樁目標數量 1~5 (預設 1)")
    parser.add_argument("-d", "--defense", type=int, default=300, help="木樁防禦率% (例如 20: 小怪, 100: 中級首領, 300: 頂級首領，預設 300)")
    parser.add_argument("-l", "--level", type=int, default=260, help="玩家等級 (預設 260)")
    parser.add_argument("-c", "--classes", type=str, default="", help="自選 1~5 個職業 ID (逗號分隔)")
    parser.add_argument("-a", "--all", action="store_true", help="執行 24 職業單人 DPS 天梯排行榜")
    parser.add_argument("-m", "--matrix", action="store_true", help="執行 24 職業全維度實戰環境 (小怪/中級王/頂級單體王) 交叉天梯")
    parser.add_argument("-r", "--random", action="store_true", help="隨機抽籤組建 5 人小隊進行實測")
    parser.add_argument("--rounds", type=int, default=5, help="天梯/矩陣測試輪數 (預設 5)")
    parser.add_argument("-s", "--save", action="store_true", help="讀取遊戲存檔 savegame.json")
    parser.add_argument("-i", "--interactive", action="store_true", help="進入終端互動選單模式")
    parser.add_argument("--no-endgame", action="store_true", help="關閉標準畢業神裝，改用裸裝測試")
    parser.add_argument("--inner-legendary", action="store_true", help="模擬啟用完美傳說內潛 (Boss+20%, 暴擊+18%, 無冷+10%)")
    parser.add_argument("--pets-luna", action="store_true", help="模擬啟用 3 隻頂級月光小寵物 (飾品+90攻, 月光祝福+30攻)")
    parser.add_argument("--familiar-3fd", action="store_true", help="模擬啟用 👑 傳奇三終真·皮卡啾 (3排終傷+20%，獨立相乘+72.8%)")

    args = parser.parse_args()
    is_endgame = not args.no_endgame

    # 若無指定特別參數且為終端交互執行，預設進入互動模式
    if args.interactive or (len(sys.argv) == 1 and sys.stdin.isatty()):
        interactive_menu()
        return

    if args.matrix:
        matrix_rounds = args.rounds if args.rounds != 5 else 2
        run_comprehensive_matrix_ranking(level=args.level, short_sec=60.0, long_sec=180.0, rounds=matrix_rounds, endgame=is_endgame)
        return

    if args.all:
        run_ladder_ranking(level=args.level, duration_sec=min(180.0, args.time), dummy_def=args.defense, dummy_targets=args.targets, rounds=args.rounds, endgame=is_endgame)
        return

    if args.random:
        p, picked_cids = create_random_team_player(level=args.level)
        if is_endgame:
            apply_endgame_gear_standard(p)
        print(f"\n🎲 隨機 7 人遠征隊 (1 主角 + 6 夥伴) 抽籤完成：{', '.join(picked_cids)}")
        res = run_dps_simulation(p, duration_sec=args.time, dummy_level=args.level, dummy_def=args.defense, dummy_targets=args.targets, is_boss=args.defense >= 100)
        print_simulation_report(res)
        return

    cids = [c.strip() for c in args.classes.split(",")] if args.classes else None
    player = create_simulation_player(
        level=args.level, class_ids=cids, load_save=args.save,
        inner_legendary=args.inner_legendary, pets_luna=args.pets_luna, familiar_3fd=args.familiar_3fd,
        endgame=is_endgame
    )
    res = run_dps_simulation(
        player,
        duration_sec=args.time,
        dummy_level=args.level,
        dummy_def=args.defense,
        dummy_targets=args.targets
    )
    print_simulation_report(res)


if __name__ == "__main__":
    main()
