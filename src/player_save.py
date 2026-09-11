"""
新楓之谷：放置遠征隊 - 存讀檔與資料持久化模組 (player_save.py)
"""

import os
import json
import shutil
import time
from item_system import Item, SLOT_NAMES
from classes import ALL_CLASSES
from player_symbols import ARC_SYMBOLS_DATA, AUT_SYMBOLS_DATA
from player_offline import settle_offline_progression


SCHEMA_VERSION = 1


def migrate_v0_to_v1(data: dict) -> dict:
    """Add the first explicit schema marker without reshaping legacy saves."""
    migrated = dict(data)
    migrated["schema_version"] = 1
    return migrated


MIGRATIONS = {
    0: migrate_v0_to_v1,
}


def migrate_save_data(data: dict) -> dict:
    """Migrate a legacy save sequentially to the current schema version."""
    if not isinstance(data, dict):
        raise ValueError("Save root must be a JSON object")

    version = data.get("schema_version", 0)
    if not isinstance(version, int) or isinstance(version, bool):
        raise ValueError("Save schema_version must be an integer")
    if version > SCHEMA_VERSION or version < 0:
        raise ValueError(f"Unsupported save schema version: {version}")

    migrated = data
    while version < SCHEMA_VERSION:
        migration = MIGRATIONS.get(version)
        if migration is None:
            raise ValueError(f"No migration path from save schema version: {version}")
        migrated = migration(migrated)
        version = migrated["schema_version"]
    return migrated


def validate_save_data(data: dict) -> None:
    """Validate root fields before applying a save to Player state."""
    if not isinstance(data, dict):
        raise ValueError("Save root must be a JSON object")
    if data.get("schema_version") != SCHEMA_VERSION:
        raise ValueError(f"Unsupported save schema version: {data.get('schema_version')}")

    numeric_fields = ("level", "exp", "gold", "stat_atk", "stat_def", "stat_hp", "stat_crit", "free_points", "last_save_time")
    for field in numeric_fields:
        if field in data and (not isinstance(data[field], (int, float)) or isinstance(data[field], bool)):
            raise ValueError(f"Save field '{field}' must be numeric")

    if "name" in data and not isinstance(data["name"], str):
        raise ValueError("Save field 'name' must be a string")

    collection_types = {
        "team_classes": list,
        "team": list,
        "team_skills": list,
        "equipped": dict,
        "inventory": list,
        "slot_enhancements": dict,
        "slot_potentials": dict,
        "slot_scrolls": dict,
        "abby_scrolls": dict,
        "cube_inventory": dict,
        "arc_symbols": dict,
        "aut_symbols": dict,
        "symbol_fragments": dict,
    }
    for field, expected_type in collection_types.items():
        if field in data and not isinstance(data[field], expected_type):
            raise ValueError(f"Save field '{field}' must be a {expected_type.__name__}")

    for field in ("inner_ability", "pet_manager", "familiar_manager"):
        if field in data and data[field] is not None and not isinstance(data[field], dict):
            raise ValueError(f"Save field '{field}' must be an object or null")


def get_default_save_path() -> str:
    """解析存檔路徑：預設儲存於 src/saves/savegame.json"""
    release_saves_dir = os.environ.get("MAPLE_IDLE_SAVE_DIR")
    if release_saves_dir:
        os.makedirs(release_saves_dir, exist_ok=True)
        return os.path.join(release_saves_dir, "savegame.json")

    cur_dir = os.path.dirname(os.path.abspath(__file__))
    saves_dir = os.path.join(cur_dir, "saves")
    os.makedirs(saves_dir, exist_ok=True)
    return os.path.join(saves_dir, "savegame.json")


def player_to_dict(player) -> dict:
    """將玩家數據序列化為字典 (包含 25 格欄位星力、主/附加潛能與艾比卷軸強化)"""
    from player_gear import ensure_player_slots
    ensure_player_slots(player)
    return {
        "schema_version": SCHEMA_VERSION,
        "name": player.name,
        "level": player.level,
        "exp": player.exp,
        "gold": player.gold,
        "team_classes": [m.class_id for m in player.team],
        "team_skills": [[s.skill_id for s in m.get_active_skills()] for m in player.team],
        "stat_atk": player.stat_atk,
        "stat_def": player.stat_def,
        "stat_hp": player.stat_hp,
        "stat_crit": player.stat_crit,
        "free_points": player.free_points,
        "equipped": {k: v.to_dict() if v else None for k, v in player.equipped.items()},
        "inventory": [it.to_dict() for it in player.inventory],
        "slot_enhancements": player.slot_enhancements,
        "slot_potentials": player.slot_potentials,
        "slot_scrolls": player.slot_scrolls,
        "abby_scrolls": getattr(player, "abby_scrolls", {}),
        "cube_inventory": getattr(player, "cube_inventory", {}),
        "arc_symbols": player.arc_symbols,
        "aut_symbols": player.aut_symbols,
        "symbol_fragments": player.symbol_fragments,
        "inner_ability": player.inner_ability.to_dict() if hasattr(player, "inner_ability") else None,
        "pet_manager": player.pet_manager.to_dict() if hasattr(player, "pet_manager") else None,
        "familiar_manager": player.familiar_manager.to_dict() if hasattr(player, "familiar_manager") else None,
        "last_save_time": time.time()
    }


def player_load_dict(player, d: dict):
    """從字典還原玩家數據（支援舊存檔無損遷移至 25 格、欄位潛能與艾比卷軸）"""
    from player_gear import ensure_player_slots

    d = migrate_save_data(d)
    validate_save_data(d)

    player.name = d.get("name", player.name)
    player.level = d.get("level", player.level)
    player.exp = d.get("exp", player.exp)
    player.gold = d.get("gold", player.gold)

    player.stat_atk = d.get("stat_atk", d.get("stat_str", 6))
    player.stat_def = d.get("stat_def", max(6, int(d.get("stat_vit", 6) * 0.6)))
    player.stat_hp = d.get("stat_hp", d.get("stat_vit", 6))
    player.stat_crit = d.get("stat_crit", d.get("stat_agi", 6))
    player.free_points = d.get("free_points", player.free_points)

    player.abby_scrolls = d.get("abby_scrolls", {})
    player.cube_inventory = d.get("cube_inventory", {})

    # 讀取符號與碎片 (自動補齊新增的 AUT 原初符號與碎片鍵值)
    saved_arc = d.get("arc_symbols", {})
    player.arc_symbols = {k: saved_arc.get(k, 0) for k in ARC_SYMBOLS_DATA}

    saved_aut = d.get("aut_symbols", {})
    player.aut_symbols = {k: saved_aut.get(k, 0) for k in AUT_SYMBOLS_DATA}

    saved_frags = d.get("symbol_fragments", {})
    all_sym_keys = list(ARC_SYMBOLS_DATA.keys()) + list(AUT_SYMBOLS_DATA.keys())
    player.symbol_fragments = {k: saved_frags.get(k, 0) for k in all_sym_keys}

    # 讀取裝備 (支援 25 個欄位並向前相容舊存檔)
    eq = d.get("equipped", {})
    for slot_k in SLOT_NAMES.keys():
        if eq.get(slot_k):
            player.equipped[slot_k] = Item.from_dict(eq[slot_k])
        else:
            player.equipped[slot_k] = None

    # 舊版欄位平移相容
    if eq.get("sub_weapon") and not player.equipped.get("sub_weapon1"):
        player.equipped["sub_weapon1"] = Item.from_dict(eq["sub_weapon"])
    if eq.get("medal") and not player.equipped.get("badge_chest"):
        player.equipped["badge_chest"] = Item.from_dict(eq["medal"])
    if eq.get("heart") and not player.equipped.get("emblem"):
        player.equipped["emblem"] = Item.from_dict(eq["heart"])
    if eq.get("android") and not player.equipped.get("pocket"):
        player.equipped["pocket"] = Item.from_dict(eq["android"])

    # 讀取欄位星力 (若為舊存檔則自動從穿戴裝備遷移)
    saved_enh = d.get("slot_enhancements", {})
    player.slot_enhancements = {}
    for slot_k in SLOT_NAMES.keys():
        if slot_k in saved_enh:
            player.slot_enhancements[slot_k] = int(saved_enh[slot_k])
        else:
            old_it = player.equipped.get(slot_k)
            player.slot_enhancements[slot_k] = getattr(old_it, "enhance_level", 0) if old_it else 0

    if "sub_weapon" in saved_enh and "sub_weapon1" not in saved_enh:
        player.slot_enhancements["sub_weapon1"] = int(saved_enh["sub_weapon"])
    if "medal" in saved_enh and "badge_chest" not in saved_enh:
        player.slot_enhancements["badge_chest"] = int(saved_enh["medal"])
    if "heart" in saved_enh and "emblem" not in saved_enh:
        player.slot_enhancements["emblem"] = int(saved_enh["heart"])

    # 讀取欄位潛能 (若為舊存檔自動從裝備生成遷移)
    player.slot_potentials = d.get("slot_potentials", {})
    # 讀取欄位艾比卷軸
    player.slot_scrolls = d.get("slot_scrolls", {})

    ensure_player_slots(player)

    # 舊存檔相容
    if eq.get("armor") and not player.equipped.get("top"):
        player.equipped["top"] = Item.from_dict(eq["armor"])
    if eq.get("accessory") and not player.equipped.get("ring1"):
        player.equipped["ring1"] = Item.from_dict(eq["accessory"])

    # 讀取背包
    inv = d.get("inventory", [])
    player.inventory = [Item.from_dict(it) for it in inv]

    # 讀取冒險隊 7 人席位 (席位 0 為核心主角，席位 1~6 為兩側隨行護衛夥伴，相容舊存檔 5 人)
    saved_team = d.get("team_classes") or d.get("team")
    defaults = [
        "hero", "dawn_warrior", "battle_mage", "bishop", "night_lord", "bowmaster", "buccaneer"
    ]
    # The supplied Player already owns TeamMember instances. Reuse their type
    # when expanding legacy five-member saves so persistence stays independent
    # of the player_data module.
    team_member_type = type(player.team[0])
    while len(player.team) < 7:
        idx = len(player.team)
        player.team.append(team_member_type(idx, defaults[idx], player))

    if saved_team and isinstance(saved_team, list):
        for idx in range(7):
            item = saved_team[idx] if idx < len(saved_team) else None
            cid = item.get("class_id") if isinstance(item, dict) else item
            cid = cid if cid in ALL_CLASSES else defaults[idx]
            player.team[idx].set_class(cid, player)
    else:
        for idx in range(7):
            player.team[idx].set_class(defaults[idx], player)

    # 讀取技能搭配 (主角 6~12 招，夥伴各 2 招)
    saved_skills = d.get("team_skills")
    if saved_skills and isinstance(saved_skills, list):
        for idx in range(min(7, len(saved_skills))):
            s_list = saved_skills[idx]
            member = player.team[idx]
            avail = member.get_available_skills()
            avail_map = {s.skill_id: s for s in avail}
            matched = []
            if isinstance(s_list, list):
                for item in s_list:
                    if isinstance(item, str) and item in avail_map:
                        matched.append(avail_map[item].clone())
                    elif isinstance(item, int) and 0 <= item < len(avail):
                        matched.append(avail[item].clone())
            if matched:
                member.set_equipped_skills(matched)
            else:
                member.set_equipped_skills(avail[:member.max_skill_slots])
    else:
        for m in player.team:
            avail = m.get_available_skills()
            m.set_equipped_skills(avail[:m.max_skill_slots])

    # 讀取內在能力、寵物系統與萌獸系統
    from inner_ability import InnerAbility
    from pet_system import PetManager
    from familiar_system import FamiliarManager

    if "inner_ability" in d and d["inner_ability"]:
        player.inner_ability = InnerAbility.from_dict(d["inner_ability"])
    else:
        player.inner_ability = InnerAbility()

    if "pet_manager" in d and d["pet_manager"]:
        player.pet_manager = PetManager.from_dict(d["pet_manager"])
    else:
        player.pet_manager = PetManager()

    if "familiar_manager" in d and d["familiar_manager"]:
        player.familiar_manager = FamiliarManager.from_dict(d["familiar_manager"])
    else:
        player.familiar_manager = FamiliarManager()

    player.restore_team_full_hp()


def save_player_to_file(player, filepath: str = None, combat_mgr = None) -> bool:
    """將玩家進度寫入磁碟 JSON 檔案"""
    if filepath is None or filepath == "savegame.json":
        filepath = get_default_save_path()

    try:
        data = player_to_dict(player)
        if combat_mgr:
            data["unlocked_zones"] = combat_mgr.unlocked_zones
            data["current_zone_idx"] = combat_mgr.current_zone_idx
            data["current_floor"] = combat_mgr.current_floor
        temp_path = f"{filepath}.tmp"
        try:
            with open(temp_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                f.flush()
                os.fsync(f.fileno())

            if os.path.exists(filepath):
                shutil.copy2(filepath, f"{filepath}.bak")
            os.replace(temp_path, filepath)
            temp_path = None
        finally:
            if temp_path and os.path.exists(temp_path):
                os.unlink(temp_path)
        return True
    except Exception as e:
        print(f"[Player] 存檔失敗: {e}")
        return False


def load_player_from_file(player, filepath: str = None, combat_mgr = None) -> dict | None:
    """從磁碟讀取存檔，並自動觸發離線掛機結算"""
    if filepath is None or filepath == "savegame.json":
        default_path = get_default_save_path()
        if os.path.exists(default_path):
            filepath = default_path
        elif os.path.exists("savegame.json"):
            filepath = "savegame.json"
        else:
            root_save = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "savegame.json")
            if os.path.exists(root_save):
                filepath = root_save
            else:
                return None

    if not os.path.exists(filepath):
        return None

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)

        data = migrate_save_data(data)
        validate_save_data(data)
        player_load_dict(player, data)
        saved_time = float(data.get("last_save_time", time.time()))

        if combat_mgr:
            combat_mgr.unlocked_zones = data.get("unlocked_zones", 1)
            combat_mgr.current_zone_idx = min(
                combat_mgr.unlocked_zones - 1,
                data.get("current_zone_idx", 0)
            )
            combat_mgr.current_floor = max(1, min(10, data.get("current_floor", 1)))
            combat_mgr.spawn_next_monster()

        return settle_offline_progression(player, combat_mgr, saved_time)
    except Exception as e:
        print(f"[Player] 讀取存檔失敗: {e}")
        return None
