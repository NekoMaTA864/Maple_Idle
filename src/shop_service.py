"""Small application boundary for shop resource mutations."""

from item_potential import CUBE_COSTS
from item_potential import ABBY_SCROLLS
from pet_system import (
    BASIC_PET_SHOP_CATALOG,
    LUNA_PET_EQUIP_CATALOG,
    PET_EQUIP_CATALOG,
    Pet,
)


def buy_scroll(player, scroll_type, count=1):
    info = ABBY_SCROLLS.get(scroll_type)
    if not info:
        return None
    if scroll_type not in ["electric", "R", "innocence"]:
        return False, f"提示：【{info.get('name', scroll_type)}】為超越神物，無法直接購買，請透過黃金轉蛋或首領掉落獲取！"
    cost = info.get("cost", 20000) * count
    if player.gold < cost:
        return False, f"金幣不足！購買 {count} 張【{info['name']}】需要 ${cost:,} 楓幣"
    player.gold -= cost
    if not hasattr(player, "abby_scrolls") or player.abby_scrolls is None:
        player.abby_scrolls = {}
    player.abby_scrolls[scroll_type] = player.abby_scrolls.get(scroll_type, 0) + count
    return True, f"🛒 商店購買成功：獲得【{info['name']}】x{count}！"


def sell_scroll(player, scroll_type, count=1):
    info = ABBY_SCROLLS.get(scroll_type)
    if not info:
        return None
    sell_price = {"electric": 30000, "R": 80000}.get(scroll_type, 0)
    current_stock = player.abby_scrolls.get(scroll_type, 0)
    if current_stock < count or sell_price <= 0:
        return False, "提示：庫存不足或該卷軸無法出售回收！"
    player.abby_scrolls[scroll_type] -= count
    earned = sell_price * count
    player.gold += earned
    return True, f"💰 成功出售【{info['name']}】x{count}！獲得 ${earned:,} 楓幣！"


def buy_cube(player, cube_type, count=1):
    names = {
        "mystic": "楓方塊", "bright": "閃耀方塊",
        "bonus_occult": "可疑附加方塊", "bonus_bright": "閃耀附加方塊",
    }
    name = names.get(cube_type, "方塊")
    cost = CUBE_COSTS.get(cube_type, 6000) * count
    if player.gold < cost:
        return False, f"金幣不足！購買 {count} 顆【{name}】需要 ${cost:,} 楓幣"
    player.gold -= cost
    if not hasattr(player, "cube_inventory") or player.cube_inventory is None:
        player.cube_inventory = {}
    player.cube_inventory[cube_type] = player.cube_inventory.get(cube_type, 0) + count
    return True, f"🛒 商店購買成功：獲得【{name}】x{count}！"


def buy_familiar_cube(player, count=1):
    cost = 50000 * count
    if player.gold < cost:
        return False, f"金幣不足！購買 {count} 顆【神奇萌獸方塊】需要 ${cost:,} 楓幣"
    player.gold -= cost
    player.familiar_manager.familiar_cubes += count
    return True, f"🛒 商店購買成功：獲得【神奇萌獸方塊】x{count}！(現有: {player.familiar_manager.familiar_cubes} 顆)"


def buy_basic_pet(player, pet_key):
    info = BASIC_PET_SHOP_CATALOG.get(pet_key)
    if not info:
        return None
    cost = info["cost"]
    if player.gold < cost:
        return False, f"金幣不足！購買【{info['name']}】需要 ${cost:,} 楓幣"
    player.gold -= cost
    pet = Pet(
        pet_id=pet_key, name=info["name"], pet_type="normal",
        auto_potion_hp=info["auto_hp"], equip_name=info["equip_name"],
        equip_atk=info["equip_atk"], is_active=False,
    )
    _, message = player.pet_manager.add_pet(pet)
    return True, f"🐾 寵物購買成功：{message}"


def buy_pet_equip(player, equip_key):
    info = PET_EQUIP_CATALOG.get(equip_key) or LUNA_PET_EQUIP_CATALOG.get(equip_key)
    if not info:
        return None
    cost = info["cost"]
    if player.gold < cost:
        return False, f"金幣不足！購買【{info['name']}】需要 ${cost:,} 楓幣"
    pets = player.pet_manager.pets
    if not pets:
        return None
    target_pet = None
    target_pet_id = info.get("pet_id")
    if target_pet_id:
        target_pet = next((pet for pet in pets if pet.pet_id == target_pet_id), None)
    if not target_pet:
        target_pet = next((pet for pet in pets if pet.is_active and pet.equip_name != info["name"]), pets[0])
    player.gold -= cost
    _, message = target_pet.equip_gear(info["name"], info["atk"], info["slots"])
    return True, f"🎀 寵物裝備購買成功：{message}"


def buy_pet_scroll(player):
    cost = 50000
    if player.gold < cost:
        return False, f"金幣不足！強化寵物飾品需要 ${cost:,} 楓幣"
    active_pets = player.pet_manager.get_active_pets()
    target_pet = next((pet for pet in active_pets if pet.scroll_slots_left > 0), None)
    if not target_pet:
        target_pet = next((pet for pet in player.pet_manager.pets if pet.scroll_slots_left > 0), None)
    if not target_pet:
        return False, "目前所有寵物裝備的衝卷次數皆已耗盡！"
    player.gold -= cost
    _, message = target_pet.scroll_equip()
    return True, f"📜 寵物卷軸強化成功：{message}"
