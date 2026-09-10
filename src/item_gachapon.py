"""
新楓之谷：放置遠征隊 - 黃金轉蛋機抽獎系統模組 (item_gachapon.py)
負責管理：
1. 黃金轉蛋機抽獎邏輯 (draw_gachapon)
2. 特等大獎池 (包含 漆黑飾品、永恆神裝、創世武器 與 特殊種子戒指：規範/持續/武器泡泡)
3. 卷軸禮盒、方塊補給與秘法符號碎片掉落分配
"""

import random
from item_catalog import ITEM_REQUIRED_LEVEL, ITEM_INHERENT_RARITY, SPECIAL_SEED_RINGS
from item_potential import ABBY_SCROLLS

def draw_gachapon(player, draw_count=1) -> tuple[bool, str, list]:
    """
    黃金轉蛋機 (Golden Gachapon)：
    - 單抽 100,000 金幣 / 十連抽 900,000 金幣 (9折特惠)
    - 獎池包含：
      1. 傳奇神裝 (漆黑Boss飾品、永恆神恩、神秘冥界幽靈、規範/持續/武器泡泡特殊種子戒指)
      2. 艾比卷軸禮盒 (極電、R、X、V、黑卷B)
      3. 方塊道具 (閃耀方塊、附加方塊、楓方塊)
      4. 高額楓幣與符號碎片大獎
    """
    from item_system import Item, create_seed_ring

    cost = 100000 if draw_count == 1 else 900000
    if player.gold < cost:
        return False, f"金幣不足！轉蛋需要 ${cost:,} 金幣", []

    player.gold -= cost
    results = []

    # 頂級稀有大獎池 (傳奇神裝 / 漆黑 / 永恆 / 特殊種子戒指)
    JACKPOT_ITEMS = [
        ("巨大恐懼", "ring"), ("苦痛的根源", "pendant"), ("狂暴印記", "face"),
        ("魔導石眼罩", "eye"), ("指揮官耳環", "earrings"), ("夢幻腰帶", "belt"),
        ("詛咒的魔導書", "pocket"), ("米特拉的憤怒", "badge"), ("滅世黑心臟", "emblem"),
        ("規範之戒", "ring"), ("持續之戒", "ring"), ("武器泡泡之戒", "ring"), ("武器之雷戒指", "ring"),
        ("永恆神恩之冠", "hat"), ("永恆聖威戰袍", "top"), ("永恆守護長褲", "bottom"),
        ("永恆天威手套", "gloves"), ("永恆逐風戰靴", "shoes"), ("永恆晨曦披風", "cape"),
        ("創世真·雙手劍", "weapon"), ("創世黑魔導書", "sub_weapon"),
        ("神秘冥界幽靈雙手劍", "weapon"), ("神秘冥界幽靈騎士帽", "hat"),
    ]

    for _ in range(draw_count):
        roll = random.random()
        if roll < 0.04:
            # 4% 超級大獎：傳奇神裝 / 漆黑 / 永恆 / 特殊種子戒指
            b_name, b_slot = random.choice(JACKPOT_ITEMS)
            is_seed = b_name in SPECIAL_SEED_RINGS

            if is_seed:
                loot_item = create_seed_ring(b_name)
            else:
                loot_item = Item(
                    slot=b_slot,
                    rarity=ITEM_INHERENT_RARITY.get(b_name, "legendary"),
                    level_req=ITEM_REQUIRED_LEVEL.get(b_name, 200),
                    base_name=b_name,
                    stats={"attack": 45, "defense": 25, "hp": 300, "crit_chance": 0.08},
                    potential_rank="legendary"
                )

            type_label = "【特殊種子戒指】" if is_seed else "【傳奇大獎】"
            if player.add_to_inventory(loot_item):
                results.append({
                    "type": "item",
                    "name": f"{type_label}{loot_item.base_name}",
                    "color": "#e53e3e" if is_seed else "#48bb78",
                    "desc": f"獲得起源神物：{loot_item.full_name}！" if is_seed else f"獲得正統神裝：{loot_item.full_name}！",
                    "item": loot_item
                })
            else:
                results.append({
                    "type": "item_lost",
                    "name": f"{type_label}{loot_item.base_name}（背包已滿）",
                    "color": "#e53e3e",
                    "desc": f"背包已滿，{loot_item.full_name} 未能存入！請先清理背包再抽獎。"
                })
        elif roll < 0.08:
            # 4% 夢幻特賞：月光小寵物 (P 寵 / Luna Petite 磁鐵寵)
            from pet_system import LUNA_PET_CATALOG, Pet
            pid = random.choice(list(LUNA_PET_CATALOG.keys()))
            pinfo = LUNA_PET_CATALOG[pid]
            new_pet = Pet(
                pet_id=pid,
                name=pinfo["name"],
                pet_type="luna_petite",
                auto_potion_hp=pinfo["auto_hp"],
                equip_name=pinfo["equip_name"],
                equip_atk=pinfo["equip_atk"],
                is_active=False
            )
            if hasattr(player, "pet_manager"):
                ok, pmsg = player.pet_manager.add_pet(new_pet)
            else:
                pmsg = "已加入寵物庫！"
            results.append({
                "type": "pet",
                "name": f"【月光P寵】{pinfo['name']}",
                "color": "#b794f4",
                "desc": f"獲得正統月光磁吸小寵物：{pinfo['name']}！(黑洞磁吸收益 +10%、套裝攻擊力 +30)"
            })
        elif roll < 0.14:
            # 6% 超絕神選：高階首領萌獸 (罕見/傳說)
            import uuid
            from familiar_system import GACHAPON_HIGH_FAMILIARS, Familiar, FAMILIAR_TIER_NAMES
            f_id, f_name, f_tier = random.choice(GACHAPON_HIGH_FAMILIARS)
            full_fid = f"{f_id}_{uuid.uuid4().hex[:6]}"
            new_fam = Familiar(full_fid, f_name, tier=f_tier, is_summoned=False)
            if hasattr(player, "familiar_manager"):
                player.familiar_manager.add_familiar(new_fam)
            t_name = FAMILIAR_TIER_NAMES.get(f_tier, f_tier)
            results.append({
                "type": "familiar",
                "name": f"【{t_name}萌獸】{f_name}",
                "color": "#ecc94b" if f_tier == "legendary" else "#9f7aea",
                "desc": f"斬獲高級首領萌獸：{f_name} [{t_name}]！具備獨立終傷與神級潛能！"
            })
        elif roll < 0.28:
            # 14% 艾比卷軸包
            s_type = random.choice(["electric", "R", "X", "V", "B", "innocence"])
            s_info = ABBY_SCROLLS[s_type]
            if not hasattr(player, "abby_scrolls") or player.abby_scrolls is None:
                player.abby_scrolls = {}
            player.abby_scrolls[s_type] = player.abby_scrolls.get(s_type, 0) + 1
            results.append({
                "type": "scroll",
                "scroll_type": s_type,
                "name": f"【艾比卷軸】{s_info['name']}",
                "color": "#ecc94b",
                "desc": f"獲得台服神級卷軸：{s_info['name']}！(庫存 +1)"
            })
        elif roll < 0.50:
            # 28% 高級裝備 (黎明 / 培羅德 / 法夫納)
            mid_items = [
                ("黎明守護天使之戒", "ring"), ("黃昏墜飾", "pendant"), ("暮色印記", "face"),
                ("頂級培羅德戒指", "ring"), ("頂級培羅德項鍊", "pendant"), ("頂級培羅德腰帶", "belt"),
                ("法夫納斬首巨劍", "weapon"), ("深淵霸王皇家頭盔", "hat")
            ]
            b_name, b_slot = random.choice(mid_items)
            loot_item = Item(
                slot=b_slot,
                rarity=ITEM_INHERENT_RARITY.get(b_name, "epic"),
                level_req=ITEM_REQUIRED_LEVEL.get(b_name, 150),
                base_name=b_name,
                stats={"attack": 25, "defense": 15, "hp": 150},
                potential_rank="unique"
            )
            if player.add_to_inventory(loot_item):
                results.append({
                    "type": "item",
                    "name": f"【稀有神裝】{loot_item.base_name}",
                    "color": "#9f7aea",
                    "desc": f"獲得高級裝備：{loot_item.full_name}",
                    "item": loot_item
                })
            else:
                results.append({
                    "type": "item_lost",
                    "name": f"【稀有神裝】{loot_item.base_name}（背包已滿）",
                    "color": "#e53e3e",
                    "desc": f"背包已滿，{loot_item.full_name} 未能存入！請先清理背包再抽獎。"
                })
        elif roll < 0.75:
            # 25% 方塊資源獎勵
            cube_choices = [
                ("bright", "閃耀方塊", 2),
                ("bonus_bright", "閃耀附加方塊", 1),
                ("mystic", "楓方塊", 5),
                ("bonus_occult", "可疑附加方塊", 3)
            ]
            ck, cn, cc = random.choice(cube_choices)
            if not hasattr(player, "cube_inventory") or player.cube_inventory is None:
                player.cube_inventory = {}
            player.cube_inventory[ck] = player.cube_inventory.get(ck, 0) + cc
            results.append({
                "type": "resource",
                "name": f"【方塊獎勵】{cn} x{cc}",
                "color": "#4299e1",
                "desc": f"獲得鍛造道具：{cn} x{cc} (已存入方塊庫存)"
            })
        else:
            # 25% 符號碎片包
            from player_symbols import ARC_SYMBOLS_DATA
            frag_amount = random.randint(3, 8)
            sym_key = random.choice(list(player.arc_symbols.keys())) if hasattr(player, "arc_symbols") and player.arc_symbols else "vanishing"
            if not hasattr(player, "symbol_fragments") or player.symbol_fragments is None:
                player.symbol_fragments = {}
            player.symbol_fragments[sym_key] = player.symbol_fragments.get(sym_key, 0) + frag_amount
            sym_display = ARC_SYMBOLS_DATA.get(sym_key, {}).get("name", sym_key).replace("秘法符號", "")
            results.append({
                "type": "symbol",
                "name": f"【符號碎片】{sym_display} +{frag_amount}",
                "color": "#63b3ed",
                "desc": f"獲得【{sym_display}】秘法符號碎片 x{frag_amount}"
            })

    msg = f"🎉 恭喜完成 {draw_count} 連抽！消耗 ${cost:,} 金幣。"
    return True, msg, results

