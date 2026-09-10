"""
新楓之谷職業系統 (classes.py)
定義三大陣營共 24 種正統新楓之谷職業，每個職業配置 8 個官方招牌技能 (共 192 招技能)：
支援 8 選 4 自由出戰搭配！
"""

from skills import Skill
from classes_data.explorers import EXPLORER_CLASSES
from classes_data.cygnus import CYGNUS_CLASSES
from classes_data.resistance import RESISTANCE_CLASSES

ALL_CLASSES = {**EXPLORER_CLASSES, **CYGNUS_CLASSES, **RESISTANCE_CLASSES}

# 五大正統母職業群體系 (將皇家騎士團與末日反抗軍全數歸入五大職系)
MOTHER_CLASS_GROUPS = {
    "warrior": {
        "name": "劍士職業群",
        "classes": ["hero", "dark_knight", "paladin", "dawn_warrior", "blaster"]
    },
    "magician": {
        "name": "法師職業群",
        "classes": ["fire_poison_mage", "ice_lightning_mage", "bishop", "flame_wizard", "battle_mage"]
    },
    "bowman": {
        "name": "弓箭手職業群",
        "classes": ["bowmaster", "marksman", "pathfinder", "wind_archer", "wild_hunter"]
    },
    "thief": {
        "name": "盜賊職業群",
        "classes": ["night_lord", "shadower", "dual_blade", "night_walker"]
    },
    "pirate": {
        "name": "海盜職業群",
        "classes": ["buccaneer", "corsair", "cannoneer", "thunder_breaker", "mechanic"]
    }
}


def get_class_info(class_id):
    """安全獲取職業資料"""
    return ALL_CLASSES.get(class_id, ALL_CLASSES["hero"])


def get_mother_group_for_class(class_id):
    """取得指定職業所屬的母職業群"""
    for g_id, g_info in MOTHER_CLASS_GROUPS.items():
        if class_id in g_info["classes"]:
            return g_info
    return {"name": "獨立職業群", "classes": [class_id]}


def get_mother_group_skills(class_id):
    """獲取該職業所屬母職業群的所有技能清單 (24 招龐大技能庫)"""
    group = get_mother_group_for_class(class_id)
    skills = []
    seen_ids = set()
    for cid in group["classes"]:
        cinfo = ALL_CLASSES.get(cid)
        if cinfo:
            for s in cinfo["skills"]:
                if s.skill_id not in seen_ids:
                    seen_ids.add(s.skill_id)
                    s_copy = s.clone()
                    s_copy.origin_class_name = cinfo["name"]
                    s_copy.origin_class_id = cid
                    skills.append(s_copy)
    return skills

