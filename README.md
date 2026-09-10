# 🍁 新楓之谷：放置冒險記 (MapleStory: Idle RPG)

> **正式桌面主線 (Python + PySide6 繁體中文版)**  
> 融合經典冒險家、皇家騎士團、末日反抗軍等 24 大職業，以「單一核心主角 + 6 位隨行護衛夥伴 + 17 職聯盟戰地後援」為架構的正統放置冒險 RPG。

---

## 🌟 核心特色 (Core Features)

### 1. ⚔️ 7 人遠征編隊與單一生存池 (7-Member Expedition)
- **陣型佈局**：以 **席位 0 (主角)** 為戰術核心，左右兩側各安排 3 位隨行護衛夥伴（共 7 位戰鬥單位上陣）。
- **生存共享機制**：隊伍生存嚴格取決於主角的生命值、防禦力與護盾壁壘。隨行夥伴共享主角生存狀態，不分攤傷害、不單獨陣亡；首領 AOE 技能僅依主角屬性單次結算，徹底告別傳統全隊滅團的數值雪崩問題。

### 2. 🔮 5 大母職業群跨職技能庫 (Mother Class Archetypes)
24 大職業完整歸納至 5 大母職業體系：
- 🛡️ **劍士系 (Warrior)**：英雄、黑騎士、聖騎士、聖魂劍士、爆拳槍神 (40 招技能庫)
- 🔮 **法師系 (Magician)**：火毒大魔導士、冰雷大魔導士、主教、烈焰巫師、煉獄巫師 (40 招技能庫)
- 🏹 **弓箭手系 (Bowman)**：箭神、神射手、開拓者、破風使者、狂豹獵人 (40 招技能庫)
- 🗡️ **盜賊系 (Thief)**：夜使者、暗影神偷、影武者、暗夜行者 (32 招技能庫)
- 💣 **海盜系 (Pirate)**：拳霸、槍神、重砲指揮官、閃雷悍將、機甲戰神 (40 招技能庫)

**主角技能槽位躍升**：
- **Lv.1 ~ 99**：開放 **6 個技能槽位**，可自所屬母職業群中自由跨職挑選組合。
- **Lv.100+**：解鎖額外 6 槽，躍升為極致 **12 招出戰技能陣容**！
- **隨行夥伴**：每位隨行夥伴精選配置 **2 招本職王牌招式** 出戰。

### 3. 🎖️ 17 職聯盟戰地後援 (Legion Bench Passive)
- 24 職扣除出戰 7 職後，其餘 **17 個職業自動常駐戰地後援陣列**。
- 提供全隊常駐全域屬性加成（包含攻擊力、首領傷害、無視防禦、暴擊機率、暴擊傷害、最終傷害等）。

### 4. 💎 深度數值與養成系統 (Endgame Progression)
- **裝備與潛能**：武器/防具/飾品/副手/心臟，支援星力強化 (Starforce)、稀有/罕見/傳說/航海/滅龍套裝效果。
- **符文工坊 (ARC / AUT)**：奧術符文與真實符文升級，提供巨額屬性加權與區域減傷抑制補正。
- **萌獸與寵物 (Familiar & Pet)**：3 隻月光小寵物自動補水補魔，傳說三終萌獸提供獨立終傷乘區與定時全隊回血光環。
- **正統防御傷害公式**：無視防禦率 (IED)、等級差壓制、屬性相剋、多段連擊機制。

### 5. 🎨 向量動態特效 (Vector VFX & PySide6 UI)
- 純 Python QPainter 向量繪製，不依賴龐大外源圖片素材，具備流暢刀光劍影、魔法光陣、箭雨席捲與首領全屏奧義。
- 支援金框卡片主角展演、7 席位面板即時切換、技能構築對話框 (`SkillDeckDialog`) 與夥伴陣容對話框 (`CompanionDialog`)。

---

## 🚀 快速啟動 (Getting Started)

### 方式 A：綠色免安裝版 (推薦玩家)
1. 從 [Releases](https://github.com/NekoMaTA864/Maple_Idle/releases) 下載最新 `MapleIdle_Full_vX.X.X.zip`。
2. 解壓縮後直接雙擊執行 **`start.bat`** (或 `啟動遊戲.bat`) 即可暢玩。

### 方式 B：開發者環境運行 (源碼運行)
需 Python 3.10+ 環境：

```bash
# 1. 複製倉庫
git clone https://github.com/NekoMaTA864/Maple_Idle.git
cd Maple_Idle

# 2. 安裝依賴套件
pip install -r requirements.txt

# 3. 啟動遊戲
python src/pyside_main.py

# 或執行標準測試
python -m unittest discover -s src/tests
```

---

## 🛠️ 開發與除錯工具

專案內建豐富的高速分析與測試工具：
- **`dps_calc.bat` / `src/dps_calculator.py`**：
  - 多執行緒高速戰鬥模擬器，支援短線 (60s) 與長線 (180s) 輸出檢測。
  - 支援全套標準畢業神裝 (Lv.260 / 90% 無視 / 傳說三終) 之 24 職業天梯榜評估。
- **`src/tools/run_vfx_sandbox.py`**：技能特效沙盒預覽工具。
- **`src/tests/`**：包含 48 項完整覆蓋的單元與整合測試套件。

---

## 📂 專案結構概覽

```text
Maple_Idle/
├── .github/workflows/       # GitHub Actions CI 自動化測試
├── src/
│   ├── classes_data/       # 24 職業原始設定 (冒險家/皇家/反抗軍)
│   ├── ui_dialogs/         # 技能組構築、隨行夥伴、裝備對話框
│   ├── ui_panels/          # 頂欄、戰鬥主區、左右控制欄
│   ├── tests/              # 48 項單元與整合測試
│   ├── vfx/                # 向量特效繪製核心
│   ├── classes.py          # 5 大母職業群定義
│   ├── combat_system.py    # 戰鬥核心循環與傷害派發
│   ├── legion_system.py    # 17 職戰地後援計算
│   ├── player_data.py      # 玩家與 7 人隊伍數據實體
│   ├── pyside_main.py      # 桌面程式入口
│   └── skills.py           # 技能定義與冷卻管理
├── requirements.txt        # 核心依賴
├── start.bat               # 遊戲標準啟動器
├── dps_calc.bat            # DPS 高速演算器
├── VERSION                 # 語意化版本號 (SemVer)
└── README.md
```

---

## 📜 授權與宣告 (Disclaimer)
本專案為個人程式設計學習與放置遊戲機制研究之非營利開源專案。MapleStory 相關著作權與商標歸原作者及 NEXON 公司所有。

