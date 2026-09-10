"""
《新楓之谷：放置遠征隊》冒險地區設定資料 (combat_zones.py)
包含 23 個冒險區域設定（維多利亞島、神秘冥界 ARC 與格蘭蒂斯 AUT 地區）
"""

ZONES = [
    {
        "id": "henesys_forest",
        "name": "弓箭手村森林",
        "level_range": (1, 15),
        "desc": "冒險者啟程的溫馨森林，遍布綠水靈與可愛菇菇。",
        "max_floors": 10,
        "monsters": [
            {"name": "嫩寶", "lvl": 2, "hp": 260, "atk": 16, "def": 6, "spd": 2.8},
            {"name": "藍菇菇", "lvl": 7, "hp": 480, "atk": 25, "def": 11, "spd": 2.9},
            {"name": "綠水靈", "lvl": 12, "hp": 750, "atk": 36, "def": 16, "spd": 2.7},
        ],
        "boss": {"name": "菇菇寶貝", "lvl": 15, "hp": 3200, "atk": 68, "def": 24, "spd": 3.0, "skill_kit": ["earthquake_slam", "void_barrier"]}
    },
    {
        "id": "perion_highlands",
        "name": "勇士部落荒野",
        "level_range": (15, 30),
        "desc": "狂風呼嘯的高原赤岩地帶，棲息著狂暴野豬與木面妖。",
        "max_floors": 10,
        "monsters": [
            {"name": "黑肥肥", "lvl": 18, "hp": 1350, "atk": 54, "def": 28, "spd": 2.7},
            {"name": "木面怪", "lvl": 23, "hp": 2100, "atk": 75, "def": 38, "spd": 2.8},
            {"name": "黑石頭人", "lvl": 28, "hp": 3100, "atk": 105, "def": 50, "spd": 2.9},
        ],
        "boss": {"name": "巨型樹妖", "lvl": 30, "hp": 9600, "atk": 155, "def": 62, "spd": 2.8, "skill_kit": ["earthquake_slam", "hell_fire"]}
    },
    {
        "id": "ellinia_forest",
        "name": "魔法森林密林",
        "level_range": (30, 45),
        "desc": "巨樹遮天的神祕古老森林，魔法微光中湧動著靈動魔物。",
        "max_floors": 10,
        "monsters": [
            {"name": "風獨眼獸", "lvl": 33, "hp": 4200, "atk": 125, "def": 62, "spd": 2.6},
            {"name": "巫婆", "lvl": 38, "hp": 5800, "atk": 160, "def": 78, "spd": 2.7},
            {"name": "猴子魔靈", "lvl": 43, "hp": 7900, "atk": 195, "def": 95, "spd": 2.6},
        ],
        "boss": {"name": "綠水靈王", "lvl": 45, "hp": 18500, "atk": 255, "def": 110, "spd": 2.7, "skill_kit": ["earthquake_slam", "chaos_laser"]}
    },
    {
        "id": "ludibrium_clock",
        "name": "玩具城時空裂隙",
        "level_range": (45, 60),
        "desc": "積木搭建的夢幻玩具之城，深層隱藏著扭曲的時鐘裂痕。",
        "max_floors": 10,
        "monsters": [
            {"name": "發條鴨", "lvl": 48, "hp": 10200, "atk": 230, "def": 115, "spd": 2.5},
            {"name": "妖精帕菲", "lvl": 53, "hp": 13800, "atk": 285, "def": 135, "spd": 2.6},
            {"name": "幽靈發條熊", "lvl": 58, "hp": 17800, "atk": 350, "def": 160, "spd": 2.5},
        ],
        "boss": {"name": "鐘樓帕普拉圖斯", "lvl": 60, "hp": 38000, "atk": 440, "def": 180, "spd": 2.6, "skill_kit": ["earthquake_slam", "void_barrier"]}
    },
    {
        "id": "elnath_snowfield",
        "name": "冰原雪域雪山",
        "level_range": (60, 75),
        "desc": "終年積雪的極寒險峰，兇殘雪怪與冰龍潛伏於暴風雪中。",
        "max_floors": 10,
        "monsters": [
            {"name": "白狼", "lvl": 63, "hp": 21500, "atk": 410, "def": 185, "spd": 2.4},
            {"name": "企鵝王", "lvl": 68, "hp": 27000, "atk": 490, "def": 220, "spd": 2.5},
            {"name": "寒冰巨龍", "lvl": 73, "hp": 34000, "atk": 580, "def": 260, "spd": 2.4},
        ],
        "boss": {"name": "殘暴雪吉拉", "lvl": 75, "hp": 65000, "atk": 720, "def": 290, "spd": 2.5, "skill_kit": ["earthquake_slam", "frost_nova"]}
    },
    {
        "id": "leafre_dragon",
        "name": "神木村龍森林",
        "level_range": (75, 90),
        "desc": "古老巨樹庇護的龍族秘境，巨龍振翅咆哮震撼峽谷。",
        "max_floors": 10,
        "monsters": [
            {"name": "萊西", "lvl": 78, "hp": 42000, "atk": 670, "def": 295, "spd": 2.3},
            {"name": "侏儒怪", "lvl": 83, "hp": 52000, "atk": 780, "def": 340, "spd": 2.4},
            {"name": "雙角赤龍", "lvl": 88, "hp": 66000, "atk": 910, "def": 395, "spd": 2.3},
        ],
        "boss": {"name": "闇黑龍王", "lvl": 90, "hp": 125000, "atk": 1180, "def": 450, "spd": 2.4, "skill_kit": ["earthquake_slam", "hell_fire"]}
    },
    {
        "id": "temple_of_time",
        "name": "時間神殿祭壇",
        "level_range": (90, 120),
        "desc": "通往時間盡頭的神聖長廊，深處坐鎮著粉萌而強大的混沌支配者皮卡啾。",
        "max_floors": 10,
        "monsters": [
            {"name": "回憶祭司", "lvl": 95, "hp": 80000, "atk": 1050, "def": 440, "spd": 2.2},
            {"name": "忘卻神官", "lvl": 105, "hp": 105000, "atk": 1280, "def": 520, "spd": 2.3},
            {"name": "杜庫守護神", "lvl": 115, "hp": 138000, "atk": 1550, "def": 610, "spd": 2.2},
        ],
        "boss": {"name": "皮卡啾", "lvl": 120, "hp": 280000, "atk": 2100, "def": 750, "spd": 2.4, "skill_kit": ["earthquake_slam", "dark_curse"]}
    },
    {
        "id": "fallen_world_tree",
        "name": "墮落世界樹",
        "level_range": (120, 160),
        "desc": "被魔族侵蝕枯萎的巨大世界樹頂端，黑翼領袖戴米安在此揮舞魔劍掌控生死。",
        "max_floors": 10,
        "monsters": [
            {"name": "污染樹妖", "lvl": 125, "hp": 190000, "atk": 1850, "def": 780, "spd": 2.2},
            {"name": "魔族盾兵", "lvl": 138, "hp": 260000, "atk": 2200, "def": 920, "spd": 2.3},
            {"name": "腐化翼魔", "lvl": 150, "hp": 350000, "atk": 2650, "def": 1080, "spd": 2.1},
        ],
        "boss": {"name": "墮落魔劍 戴米安", "lvl": 160, "hp": 680000, "atk": 3400, "def": 1250, "spd": 2.3, "skill_kit": ["earthquake_slam", "chaos_laser", "dark_curse"]}
    },
    {
        "id": "scrapyard",
        "name": "機械墳場",
        "level_range": (160, 200),
        "desc": "被遺棄的重型機械工廠廢墟，中央核心由冷酷的人造人史烏坐鎮控制。",
        "max_floors": 10,
        "monsters": [
            {"name": "巡邏機器人", "lvl": 168, "hp": 460000, "atk": 3100, "def": 1220, "spd": 2.2},
            {"name": "重裝防禦機甲", "lvl": 180, "hp": 600000, "atk": 3650, "def": 1400, "spd": 2.1},
            {"name": "改造雷射守衛", "lvl": 192, "hp": 780000, "atk": 4300, "def": 1620, "spd": 2.2},
        ],
        "boss": {"name": "核心魔偶 史烏", "lvl": 200, "hp": 1550000, "atk": 5200, "def": 1850, "spd": 2.4, "skill_kit": ["earthquake_slam", "chaos_laser", "void_barrier"]}
    },
    # =========================================================================
    # ARC 奧術之河 (Arcane River, Lv. 200 ~ 260) - 考驗 ARC 秘法符文力！
    # =========================================================================
    {
        "id": "vanishing_journey",
        "name": "消亡旅途",
        "level_range": (200, 210),
        "arc_req": 60,
        "symbol_drop": "vanishing",
        "desc": "流淌著艾爾達之光的虛無之河，無數回憶在此消逝化為純淨能量。",
        "max_floors": 10,
        "monsters": [
            {"name": "安息的艾爾達", "lvl": 202, "hp": 1100000, "atk": 4900, "def": 1750, "spd": 2.1},
            {"name": "岩石艾爾達", "lvl": 205, "hp": 1380000, "atk": 5400, "def": 1920, "spd": 2.2},
            {"name": "火焰艾爾達", "lvl": 208, "hp": 1720000, "atk": 6000, "def": 2100, "spd": 2.0},
        ],
        "boss": {"name": "艾爾達巨像", "lvl": 210, "hp": 3600000, "atk": 7400, "def": 2450, "spd": 2.3, "skill_kit": ["earthquake_slam", "chaos_laser", "void_barrier"]}
    },
    {
        "id": "chu_chu_island",
        "name": "啾啾島",
        "level_range": (210, 220),
        "arc_req": 130,
        "symbol_drop": "chuchu",
        "desc": "巨獸穆托沉睡的奇幻美食之島，生物皆由奇異的食材融合而成。",
        "max_floors": 10,
        "monsters": [
            {"name": "果實綠水靈", "lvl": 212, "hp": 2100000, "atk": 6600, "def": 2300, "spd": 2.1},
            {"name": "羊駝鳥", "lvl": 215, "hp": 2550000, "atk": 7300, "def": 2520, "spd": 2.0},
            {"name": "香蕉猴妖", "lvl": 218, "hp": 3100000, "atk": 8100, "def": 2780, "spd": 2.1},
        ],
        "boss": {"name": "熟成穆托", "lvl": 220, "hp": 6500000, "atk": 9800, "def": 3200, "spd": 2.3, "skill_kit": ["earthquake_slam", "chaos_laser", "dark_curse"]}
    },
    {
        "id": "lachelein",
        "name": "夢之都 拉克蘭",
        "level_range": (220, 230),
        "arc_req": 210,
        "symbol_drop": "lachelein",
        "desc": "惡夢與狂歡永不落幕的華麗鐘樓城市，蝴蝶翩躚掩蓋著露希妲的虛妄夢境。",
        "max_floors": 10,
        "monsters": [
            {"name": "提燈舞者", "lvl": 222, "hp": 3800000, "atk": 9000, "def": 3050, "spd": 2.0},
            {"name": "紙袋假面客", "lvl": 225, "hp": 4600000, "atk": 10000, "def": 3350, "spd": 2.1},
            {"name": "夢魘巡邏者", "lvl": 228, "hp": 5500000, "atk": 11200, "def": 3680, "spd": 1.9},
        ],
        "boss": {"name": "惡夢支配者 露希妲", "lvl": 230, "hp": 12500000, "atk": 13800, "def": 4200, "spd": 2.2, "skill_kit": ["earthquake_slam", "chaos_laser", "dark_curse"]}
    },
    {
        "id": "arcana",
        "name": "神秘森林 阿爾卡娜",
        "level_range": (230, 235),
        "arc_req": 360,
        "symbol_drop": "arcana",
        "desc": "微風呢喃、小精靈嬉戲的奇幻森林深處，遭邪惡荊棘侵蝕而失去純淨之歌。",
        "max_floors": 10,
        "monsters": [
            {"name": "水滴精靈", "lvl": 231, "hp": 6600000, "atk": 12400, "def": 4050, "spd": 2.0},
            {"name": "太陽精靈", "lvl": 233, "hp": 7800000, "atk": 13700, "def": 4400, "spd": 1.9},
            {"name": "劇毒藤蔓妖", "lvl": 234, "hp": 9200000, "atk": 15200, "def": 4800, "spd": 2.0},
        ],
        "boss": {"name": "調和精靈", "lvl": 235, "hp": 21000000, "atk": 18500, "def": 5400, "spd": 2.2, "skill_kit": ["earthquake_slam", "frost_nova", "dark_curse"]}
    },
    {
        "id": "morass",
        "name": "記憶之沼 魔菈斯",
        "level_range": (235, 240),
        "arc_req": 520,
        "symbol_drop": "morass",
        "desc": "吞噬無數歷史的珊瑚色泥沼，重現著克里提亞斯王國覆滅前的悲哀記憶。",
        "max_floors": 10,
        "monsters": [
            {"name": "記憶守衛兵", "lvl": 236, "hp": 10800000, "atk": 16800, "def": 5250, "spd": 1.9},
            {"name": "赤紅變異獸", "lvl": 238, "hp": 12600000, "atk": 18500, "def": 5700, "spd": 2.0},
            {"name": "深淵暗影", "lvl": 239, "hp": 14800000, "atk": 20400, "def": 6200, "spd": 1.8},
        ],
        "boss": {"name": "赤血女皇", "lvl": 240, "hp": 34000000, "atk": 24800, "def": 7000, "spd": 2.1, "skill_kit": ["earthquake_slam", "hell_fire", "dark_curse"]}
    },
    {
        "id": "esfera",
        "name": "始源之海 艾斯佩拉",
        "level_range": (240, 250),
        "arc_req": 600,
        "symbol_drop": "esfera",
        "desc": "艾爾達之河匯入的純白始源大海，軍團長威爾在此編織光與暗的鏡之世界。",
        "max_floors": 10,
        "monsters": [
            {"name": "始源之水", "lvl": 242, "hp": 17500000, "atk": 22600, "def": 6750, "spd": 1.9},
            {"name": "光輝結晶怪", "lvl": 245, "hp": 20800000, "atk": 25200, "def": 7350, "spd": 1.8},
            {"name": "深海鏡魔", "lvl": 248, "hp": 24500000, "atk": 28000, "def": 8000, "spd": 1.9},
        ],
        "boss": {"name": "光與暗之眼 威爾", "lvl": 250, "hp": 55000000, "atk": 33500, "def": 9200, "spd": 2.1, "skill_kit": ["earthquake_slam", "chaos_laser", "dark_curse"]}
    },
    {
        "id": "limina",
        "name": "終焉之眼 利曼",
        "level_range": (250, 260),
        "arc_req": 880,
        "symbol_drop": "esfera",
        "desc": "巨人之心深處的虛無黑洞裂縫，終極魔神【黑魔法師】端坐於毀滅神域。",
        "max_floors": 10,
        "monsters": [
            {"name": "創世之影", "lvl": 252, "hp": 29000000, "atk": 31500, "def": 8800, "spd": 1.8},
            {"name": "虛無騎士", "lvl": 255, "hp": 34500000, "atk": 35500, "def": 9700, "spd": 1.9},
            {"name": "破滅眼魔", "lvl": 258, "hp": 41000000, "atk": 40000, "def": 10700, "spd": 1.7},
        ],
        "boss": {"name": "黑魔法師", "lvl": 260, "hp": 98000000, "atk": 48000, "def": 12500, "spd": 2.0, "skill_kit": ["earthquake_slam", "chaos_laser", "dark_curse", "hell_fire"]}
    },
    # =========================================================================
    # AUT 格蘭帝斯 (Grandis, Lv. 260 ~ 300) - 考驗 AUT 原初符文力！
    # 完整 7 大原初地區：塞爾尼恩、阿爾克斯、奧迪溫、桃源境、阿爾特利亞、卡爾西溫、塔拉哈特
    # =========================================================================
    {
        "id": "cernium",
        "name": "神之都市 塞爾尼恩",
        "level_range": (260, 270),
        "aut_req": 70,
        "symbol_drop": "cernium",
        "desc": "太古聖劍與神聖圖書館守護的異界神之都，太陽侍從瑟倫拔出弒神之刃。",
        "max_floors": 10,
        "monsters": [
            {"name": "烈焰步兵", "lvl": 262, "hp": 52000000, "atk": 46000, "def": 12200, "spd": 1.8},
            {"name": "聖地祭司", "lvl": 265, "hp": 63000000, "atk": 52000, "def": 13600, "spd": 1.7},
            {"name": "狂日守護魔", "lvl": 268, "hp": 76000000, "atk": 59000, "def": 15200, "spd": 1.8},
        ],
        "boss": {"name": "選定者 瑟倫", "lvl": 270, "hp": 180000000, "atk": 72000, "def": 18000, "spd": 1.9, "skill_kit": ["earthquake_slam", "chaos_laser", "hell_fire", "dark_curse"]}
    },
    {
        "id": "hotel_arcus",
        "name": "荒漠旅館 阿爾克斯",
        "level_range": (270, 275),
        "aut_req": 130,
        "symbol_drop": "arcus",
        "desc": "格蘭帝斯無垠黃沙荒漠中的鐵道補給旅館，隱藏著古代神殘骸與生化防禦兵器。",
        "max_floors": 10,
        "monsters": [
            {"name": "荒漠沙鼠兵", "lvl": 271, "hp": 85000000, "atk": 63000, "def": 16000, "spd": 1.7},
            {"name": "生化改裝犬", "lvl": 273, "hp": 102000000, "atk": 71000, "def": 17800, "spd": 1.8},
            {"name": "列車防禦核心", "lvl": 275, "hp": 122000000, "atk": 80000, "def": 19800, "spd": 1.6},
        ],
        "boss": {"name": "守護兵 警戒者", "lvl": 275, "hp": 280000000, "atk": 96000, "def": 23000, "spd": 1.8, "skill_kit": ["earthquake_slam", "chaos_laser", "void_barrier", "dark_curse"]}
    },
    {
        "id": "odium",
        "name": "機械之城 奧迪溫",
        "level_range": (275, 280),
        "aut_req": 200,
        "symbol_drop": "odium",
        "desc": "雲海之巔的沉睡機械科研堡壘，太古兵器【監視者 卡洛斯】巡邏著禁忌領域。",
        "max_floors": 10,
        "monsters": [
            {"name": "巡邏核心兵", "lvl": 276, "hp": 138000000, "atk": 88000, "def": 21500, "spd": 1.7},
            {"name": "重裝防禦機甲", "lvl": 278, "hp": 162000000, "atk": 97000, "def": 23800, "spd": 1.6},
            {"name": "高階哨戒魔像", "lvl": 280, "hp": 190000000, "atk": 107000, "def": 26200, "spd": 1.7},
        ],
        "boss": {"name": "監視者 卡洛斯", "lvl": 280, "hp": 420000000, "atk": 128000, "def": 30000, "spd": 1.8, "skill_kit": ["earthquake_slam", "chaos_laser", "void_barrier", "dark_curse"]}
    },
    {
        "id": "shangri_la",
        "name": "仙界 桃源境",
        "level_range": (275, 282),
        "aut_req": 260,
        "symbol_drop": "shangrila",
        "desc": "四季常青、水墨繚繞的超然仙界捲軸內部，封印著太古凶獸之首咖凌。",
        "max_floors": 10,
        "monsters": [
            {"name": "冬雪水墨鶴", "lvl": 278, "hp": 165000000, "atk": 98000, "def": 24000, "spd": 1.7},
            {"name": "夏雷墨麒麟", "lvl": 280, "hp": 200000000, "atk": 112000, "def": 27200, "spd": 1.6},
            {"name": "四凶眷族獸", "lvl": 282, "hp": 245000000, "atk": 128000, "def": 30800, "spd": 1.7},
        ],
        "boss": {"name": "四凶獸 咖凌", "lvl": 282, "hp": 580000000, "atk": 155000, "def": 36000, "spd": 1.8, "skill_kit": ["earthquake_slam", "chaos_laser", "frost_nova", "dark_curse"]}
    },
    {
        "id": "arteria",
        "name": "空中戰艦 阿爾特利亞",
        "level_range": (280, 285),
        "aut_req": 330,
        "symbol_drop": "arteria",
        "desc": "高等翼族突襲楓之谷的大型巡洋戰艦，雷納德司令官率領機械精銳艦隊狂轟濫炸。",
        "max_floors": 10,
        "monsters": [
            {"name": "空降偵察兵", "lvl": 281, "hp": 220000000, "atk": 120000, "def": 29000, "spd": 1.7},
            {"name": "戰艦重裝巡警", "lvl": 283, "hp": 265000000, "atk": 135000, "def": 32500, "spd": 1.6},
            {"name": "突襲殲滅機甲", "lvl": 285, "hp": 315000000, "atk": 150000, "def": 36000, "spd": 1.7},
        ],
        "boss": {"name": "司令官 雷納德", "lvl": 285, "hp": 760000000, "atk": 178000, "def": 41000, "spd": 1.8, "skill_kit": ["earthquake_slam", "chaos_laser", "hell_fire", "dark_curse"]}
    },
    {
        "id": "carcion",
        "name": "生命搖籃 卡爾西溫",
        "level_range": (285, 290),
        "aut_req": 390,
        "symbol_drop": "carcion",
        "desc": "阿尼瑪一族的生命古樹發源之地，遭到企圖染指古代神之力的奇斯特瘋狂侵略。",
        "max_floors": 10,
        "monsters": [
            {"name": "毒霧古木精", "lvl": 286, "hp": 340000000, "atk": 155000, "def": 37500, "spd": 1.6},
            {"name": "墮落樹靈衛", "lvl": 288, "hp": 405000000, "atk": 175000, "def": 41800, "spd": 1.7},
            {"name": "奇斯特狂信徒", "lvl": 290, "hp": 480000000, "atk": 198000, "def": 46500, "spd": 1.5},
        ],
        "boss": {"name": "墮落古代神 奇斯特", "lvl": 290, "hp": 990000000, "atk": 225000, "def": 50000, "spd": 1.7, "skill_kit": ["earthquake_slam", "chaos_laser", "hell_fire", "frost_nova", "dark_curse"]}
    },
    {
        "id": "talahart",
        "name": "靈魂之鄉 塔拉哈特",
        "level_range": (290, 300),
        "aut_req": 460,
        "symbol_drop": "talahart",
        "desc": "原初星光璀璨的靈魂歸宿神殿，太古靈魂之主【塔拉哈特 太古神影】鎮守最高境界。",
        "max_floors": 10,
        "monsters": [
            {"name": "星宿幽魂", "lvl": 292, "hp": 520000000, "atk": 210000, "def": 49000, "spd": 1.6},
            {"name": "原初靈魂武士", "lvl": 295, "hp": 610000000, "atk": 235000, "def": 54000, "spd": 1.7},
            {"name": "天界神殿裁決者", "lvl": 298, "hp": 720000000, "atk": 265000, "def": 60000, "spd": 1.5},
        ],
        "boss": {"name": "太古神靈 影獸", "lvl": 300, "hp": 1350000000, "atk": 295000, "def": 68000, "spd": 1.6, "skill_kit": ["earthquake_slam", "chaos_laser", "hell_fire", "frost_nova", "void_barrier", "dark_curse"]}
    }
]


# =========================================================================
