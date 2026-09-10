"""
《新楓之谷：放置遠征隊 (MapleStory Idle)》全域設定
採用 1120 x 720 桌面橫向比例、微軟雅黑 UI 清晰字型與暗黑護眼色系
"""

# 桌面三欄全景視窗尺寸 (1120 x 720：黃金比例寬螢幕，三欄並列一覽無遺)
SCREEN_WIDTH = 1120
SCREEN_HEIGHT = 720
FPS = 60
TITLE = "新楓之谷：放置遠征隊 - MapleStory Idle"

# 字體配置 (首選微軟雅黑 UI，清晰銳利不擠字)
FONT_PRIMARY = "microsoftyaheiui"
FONT_FALLBACKS = ["microsoftyahei", "microsoftjhengheiui", "microsoftjhenghei", "simhei", "arial"]

# 護眼暗黑風色彩
COLOR_BG = (14, 16, 24)              # 總體深石板背景
COLOR_PANEL_BG = (22, 26, 38)        # 面板底色
COLOR_PANEL_HOVER = (30, 36, 52)     # 卡片懸停
COLOR_BORDER = (46, 54, 76)          # 邊框線
COLOR_DIVIDER = (36, 42, 60)         # 分隔線

# 戰鬥小隊與角色卡牌色彩
COLOR_CARD_TANK = (24, 36, 48)       # 聖堂守衛卡牌 (深石青)
COLOR_CARD_HERO = (22, 34, 56)       # 主角英雄卡牌 (深海藍)
COLOR_CARD_HEALER = (20, 38, 36)     # 德魯伊卡牌 (深松綠)
COLOR_CARD_ENEMY = (42, 22, 28)      # 敵方卡牌 (暗緋紅)
COLOR_CARD_BOSS = (46, 18, 52)       # 首領卡牌 (深紫金)

# 狀態與進度條色彩
COLOR_HP_RED = (225, 55, 65)         # 生命值血條
COLOR_ACTION_BAR = (245, 195, 45)    # 攻速行動條
COLOR_EXP_BLUE = (45, 175, 240)      # 經驗值條
COLOR_GOLD = (255, 215, 55)          # 金幣
COLOR_BOSS_PURPLE = (220, 60, 240)   # 首領標記
COLOR_HEAL_GREEN = (60, 240, 130)    # 治癒綠光
COLOR_SHIELD_BLUE = (70, 180, 255)   # 護盾青藍

# 裝備品質 5 色階 (暗黑/不朽之旅)
COLOR_COMMON = (205, 210, 220)       # ⚪ 普通 (白)
COLOR_UNCOMMON = (50, 215, 105)      # 🟢 優秀 (綠)
COLOR_RARE = (55, 160, 255)          # 🔵 稀有 (藍)
COLOR_EPIC = (185, 80, 255)          # 🟣 史詩 (紫)
COLOR_LEGENDARY = (255, 155, 30)     # 🟠 傳奇 (橙)

# 文字色彩
COLOR_TEXT_MAIN = (240, 245, 255)
COLOR_TEXT_MUTED = (145, 155, 180)
COLOR_TEXT_DARK = (90, 100, 125)
COLOR_GREEN_STAT = (60, 230, 120)    # 屬性提升綠
COLOR_RED_STAT = (255, 80, 90)       # 屬性下降紅

# 系統常數
INVENTORY_CAPACITY = 60
SAVE_INTERVAL = 5.0
OFFLINE_EFFICIENCY = 0.8
MAX_OFFLINE_HOURS = 24.0
