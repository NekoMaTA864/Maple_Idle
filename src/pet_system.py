"""
《新楓之谷：放置遠征隊》寵物系統 (Pet System / pet_system.py)

原版 TMS 機制考究實作：
1. 3 隻寵物出戰槽位：角色最多可同時召喚 3 隻寵物上陣。
2. 自動喝水 (Auto-Potion)：
   - 可設定 HP 警戒線閾值（例如 30%~70%）。
   - 戰鬥中當隊員生命值跌破閾值時，寵物自動使用「超級藥水」補滿生命。
3. 月光小寵物 (P 寵 / Luna Petite 磁鐵寵)：
   - 擁有強大全圖黑洞磁力吸寶能力，掉落金幣與經驗拾取收益提高 25%。
   - 三隻 P 寵集齊觸發「月光祝福」套裝效果：全隊攻擊力 +30、全屬性增加。
   - 需透過轉蛋屋 (黃金轉蛋機) 特等獎池抽取！
4. 寵物裝備與衝卷：
   - 寵物配備專屬飾品/裝備，可在轉蛋屋商店購買。
   - 可消耗寵物飾品攻擊卷軸強化飾品攻擊力（每張卷軸 +3 攻擊力）。
"""

BASIC_PET_SHOP_CATALOG = {
    "pet_husky": {"name": "小哈士奇", "cost": 200000, "auto_hp": 0.45, "equip_name": "哈士奇禦寒背心", "equip_atk": 6},
    "pet_shiba": {"name": "小柴犬", "cost": 200000, "auto_hp": 0.45, "equip_name": "柴犬紅色領巾", "equip_atk": 6},
    "pet_yeti": {"name": "雪吉拉寶寶", "cost": 200000, "auto_hp": 0.50, "equip_name": "雪吉拉小圍巾", "equip_atk": 8},
}

PET_EQUIP_CATALOG = {
    "golden_bell": {"name": "黃金守護鈴鐺", "cost": 150000, "atk": 10, "slots": 10, "desc": "基礎攻擊力 +10，具備 10 次衝卷空間"},
    "angel_wings": {"name": "精靈天使之翼", "cost": 300000, "atk": 18, "slots": 10, "desc": "基礎攻擊力 +18，具備 10 次衝卷空間"},
}

LUNA_PET_CATALOG = {
    "pet_luna_titania": {"name": "月光蒂塔妮亞 (P寵)", "auto_hp": 0.60, "equip_name": "蒂塔妮亞魔精羽冠", "equip_atk": 25},
    "pet_luna_bella": {"name": "月光貝拉 (P寵)", "auto_hp": 0.60, "equip_name": "貝拉夜之迷蝶", "equip_atk": 25},
    "pet_luna_pico": {"name": "月光皮可 (P寵)", "auto_hp": 0.60, "equip_name": "皮可星辰耳環", "equip_atk": 25},
}

LUNA_PET_EQUIP_CATALOG = {
    "luna_titania_crown": {
        "pet_id": "pet_luna_titania",
        "name": "蒂塔妮亞魔精羽冠",
        "cost": 500000,
        "atk": 25,
        "slots": 10,
        "desc": "月光蒂塔妮亞專屬神級飾品！基礎攻擊力 +25，具備 10 次衝卷空間"
    },
    "luna_bella_wings": {
        "pet_id": "pet_luna_bella",
        "name": "貝拉夜之迷蝶",
        "cost": 500000,
        "atk": 25,
        "slots": 10,
        "desc": "月光貝拉專屬神級飾品！基礎攻擊力 +25，具備 10 次衝卷空間"
    },
    "luna_pico_earring": {
        "pet_id": "pet_luna_pico",
        "name": "皮可星辰耳環",
        "cost": 500000,
        "atk": 25,
        "slots": 10,
        "desc": "月光皮可專屬神級飾品！基礎攻擊力 +25，具備 10 次衝卷空間"
    },
}


class Pet:
    """單一寵物"""
    def __init__(
        self,
        pet_id: str,
        name: str,
        pet_type: str = "normal",  # "normal", "luna_petite"
        auto_potion_hp: float = 0.50,
        equip_name: str = "初階寵物項圈",
        equip_atk: int = 0,
        scroll_slots_left: int = 10,
        is_active: bool = False
    ):
        self.pet_id = pet_id
        self.name = name
        self.pet_type = pet_type  # "normal" 或 "luna_petite"
        self.auto_potion_hp = auto_potion_hp
        self.equip_name = equip_name
        self.equip_atk = equip_atk
        self.scroll_slots_left = scroll_slots_left
        self.is_active = is_active

    @property
    def is_luna(self) -> bool:
        return self.pet_type == "luna_petite"

    def equip_gear(self, equip_name: str, bonus_atk: int, extra_slots: int = 10) -> tuple[bool, str]:
        """穿戴或更換寵物專屬裝備"""
        self.equip_name = equip_name
        self.equip_atk += bonus_atk
        self.scroll_slots_left = max(self.scroll_slots_left, extra_slots)
        return True, f"【{self.name}】成功裝備【{equip_name}】！基礎攻擊力 +{bonus_atk}，開放 {extra_slots} 次衝卷！"

    def scroll_equip(self) -> tuple[bool, str]:
        """使用寵物飾品攻擊卷軸進行強化"""
        if self.scroll_slots_left <= 0:
            return False, f"【{self.name}】的寵物裝備衝卷次數已用盡！"
        self.scroll_slots_left -= 1
        gain = 3
        self.equip_atk += gain
        return True, f"【{self.name}】寵物裝備強化成功！攻擊力 +{gain} (當前: +{self.equip_atk}，剩餘次數: {self.scroll_slots_left})"

    def to_dict(self) -> dict:
        return {
            "pet_id": self.pet_id,
            "name": self.name,
            "pet_type": self.pet_type,
            "auto_potion_hp": self.auto_potion_hp,
            "equip_name": self.equip_name,
            "equip_atk": self.equip_atk,
            "scroll_slots_left": self.scroll_slots_left,
            "is_active": self.is_active
        }

    @classmethod
    def from_dict(cls, data: dict):
        return cls(
            pet_id=data.get("pet_id", "pet_husky"),
            name=data.get("name", "小哈士奇"),
            pet_type=data.get("pet_type", "normal"),
            auto_potion_hp=float(data.get("auto_potion_hp", 0.50)),
            equip_name=data.get("equip_name", "初階寵物項圈"),
            equip_atk=int(data.get("equip_atk", 0)),
            scroll_slots_left=int(data.get("scroll_slots_left", 10)),
            is_active=bool(data.get("is_active", False))
        )


class PetManager:
    """玩家寵物管理庫 (包含 3 隻出戰槽、自動喝水調度、P 寵共鳴)"""
    def __init__(self):
        self.potions = 50  # 超級藥水庫存
        self.pets = [
            # 初始預設三隻經典基本寵物，預設全部出戰
            Pet("pet_puppy", "棕色小狗", "normal", auto_potion_hp=0.45, equip_name="小狗項圈", equip_atk=6, is_active=True),
            Pet("pet_kitty", "小白貓咪", "normal", auto_potion_hp=0.45, equip_name="小貓鈴鐺", equip_atk=6, is_active=True),
            Pet("pet_penguin", "粉紅企鵝", "normal", auto_potion_hp=0.45, equip_name="企鵝領結", equip_atk=6, is_active=True),
        ]

    def add_pet(self, pet: Pet) -> tuple[bool, str]:
        """新增寵物 (若已擁有則強化現有寵物)"""
        existing = next((p for p in self.pets if p.pet_id == pet.pet_id), None)
        if existing:
            existing.equip_atk += 5
            existing.scroll_slots_left += 5
            return True, f"已擁有【{existing.name}】！飾品攻擊力額外強化 +5，增加 5 次衝卷空間！"
        self.pets.append(pet)
        return True, f"獲得新寵物【{pet.name}】！已加入寵物陣容。"

    def get_active_pets(self) -> list[Pet]:
        active = [p for p in self.pets if p.is_active]
        return active[:3]

    def set_pet_active(self, pet_id: str, active: bool) -> tuple[bool, str]:
        pet = next((p for p in self.pets if p.pet_id == pet_id), None)
        if not pet and pet_id in LUNA_PET_CATALOG:
            # 相容性保護：若請求月光寵物且不存在，自動註冊
            c_info = LUNA_PET_CATALOG[pet_id]
            pet = Pet(pet_id, c_info["name"], "luna_petite", auto_potion_hp=c_info["auto_hp"], equip_name=c_info["equip_name"], equip_atk=c_info["equip_atk"], is_active=False)
            self.pets.append(pet)
        if not pet:
            return False, "找不到指定寵物"
        if active:
            current_active = self.get_active_pets()
            if len(current_active) >= 3 and pet not in current_active:
                return False, "最多只能同時出戰 3 隻寵物！請先卸下其他出戰寵物。"
            pet.is_active = True
            return True, f"【{pet.name}】已加入出戰隊伍！"
        else:
            pet.is_active = False
            return True, f"【{pet.name}】已收回休息。"

    def get_total_equip_attack(self) -> int:
        """加總當前出戰 3 隻寵物的飾品攻擊力"""
        return sum(p.equip_atk for p in self.get_active_pets())

    def get_luna_petite_count(self) -> int:
        return sum(1 for p in self.get_active_pets() if p.is_luna)

    def get_luna_set_attack(self) -> int:
        """三隻 P 寵同場出戰觸發『月光祝福』套裝攻擊力 +30"""
        return 30 if self.get_luna_petite_count() >= 3 else 0

    def get_loot_multiplier(self) -> float:
        """P 寵黑洞磁吸金幣加成 (每隻 P 寵 +10%，三隻 P 寵 +30%)"""
        return 1.0 + self.get_luna_petite_count() * 0.10

    def check_auto_potion(self, player) -> int:
        """
        戰鬥迴圈每秒/受擊時調用：
        若出戰寵物中有自動喝水功能，且隊員血量低於閾值，自動扣除藥水回復
        :return: 回復次數
        """
        active = self.get_active_pets()
        if not active or self.potions <= 0:
            return 0

        # 取出戰寵物中最靈敏的喝水閾值
        threshold = max(p.auto_potion_hp for p in active)

        used = 0
        for m in player.team:
            if not m.is_alive:
                continue
            max_hp = m.get_max_hp(player)
            if m.current_hp / max(1.0, float(max_hp)) < threshold:
                if self.potions > 0:
                    self.potions -= 1
                    # 超級藥水直接回復 100% 生命值
                    heal_amount = max_hp - m.current_hp
                    m.current_hp = float(max_hp)
                    used += 1
        return used

    def to_dict(self) -> dict:
        return {
            "potions": self.potions,
            "pets": [p.to_dict() for p in self.pets]
        }

    @classmethod
    def from_dict(cls, data: dict):
        obj = cls()
        if not data:
            return obj
        obj.potions = int(data.get("potions", 50))
        pets_data = data.get("pets", [])
        if pets_data:
            obj.pets = [Pet.from_dict(pd) for pd in pets_data]
        return obj

