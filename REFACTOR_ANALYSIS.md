# Maple Idle 架構全景掃描與低耦合重構分析報告 (Refactor Analysis)

> **版本**：v1.0.6 (Baseline)  
> **掃描對象**：`src/` 全模組 (84 個內部模組、24 職業、48 項單元與整合測試)  
> **編寫目的**：供後續 Codex / Antigravity 團隊接手進行 Phase 2～Phase 5 之低耦合、模組化與可測試性重構時的最高指導手冊。

---

## 0. 專案現狀總評 (Executive Summary)

經過對全模組之 AST 抽象語法樹靜態掃描與依賴圖分析：
- **良好特質**：
  - **純 Domain 層完全未滲透 Qt**：`combat_*.py`、`player_*.py`、`monster*.py`、`skills.py`、`classes.py` 均未引入 `PySide6` 或 `QtCore/QtWidgets`，領域邏輯已具備良好的 Headless 執行基礎。
  - **測試套件覆蓋完整**：48 項單元與整合測試目前 100% 綠燈 PASS，為重構提供了可靠的 Safety Net。
- **核心架構痛點 (需在後續重構階段解耦)**：
  1. **巨型上帝物件 (God Objects)**：`Player` (61 個方法、20+ 聚合屬性) 與 `CombatManager` (23 個方法、531 行) 承擔了過多領域職責。
  2. **循環引用與局部延遲加載 (Circular & Local Imports)**：檢測出 2 條核心循環引用鏈，全專案散落 39 處在函數內部使用 `import` 規避循環加載。
  3. **音效子系統與領域計算耦合**：`sound_mgr` 單例在 `combat_damage.py`、`combat_loot.py`、`combat_system.py` 中被硬性調用（共 29 處引用）。
  4. **UI 層直接更動經濟與戰鬥狀態**：`pyside_ui.py` 與部分對話框存在直接修改 `player.gold += ...`、`player.abby_scrolls[...] += ...` 及 `combat_mgr.repeat_current_zone` 等行為，缺乏 Service 層封裝。

---

## 1. 模組依賴圖掃描 (Dependency Graph)

全專案 84 個 Python 模組、123 條相依關聯邊。整體分層如下：

```text
[Presentation / UI]
  pyside_main.py
  ├── pyside_ui.py
  ├── ui_arena.py
  ├── ui_panels/ (top_bar, center_column, left_column, right_column, right_column_shop, right_column_symbols)
  └── ui_dialogs/ (companion, skill_deck, inventory_grid, item_compare, auto_cube, special_systems, ...)
        │
        ▼ (依賴)
[Domain Orchestration / God Objects]
  combat_system.py (CombatManager) ──┐
  player_data.py (Player, TeamMember) │
        │                             │
        ▼                             ▼
[Domain Features & Calculations]
  ├── combat_damage.py (傷害計算、無視防禦、暴擊結算)
  ├── combat_stats.py (戰鬥屬性統計)
  ├── combat_loot.py (掉落金幣、經驗、裝備、萌獸)
  ├── combat_zones.py (關卡與首領資料)
  ├── monster.py & monster_ai.py & monster_skills.py (怪物實體與技能)
  ├── classes.py & classes_data/* (24 職業、母職業群技能庫)
  ├── skills.py (技能實體與冷卻狀態)
  ├── legion_system.py (17 職戰地後援加成計算)
  ├── player_gear.py & item_system.py & item_potential.py & item_sets.py (裝備與星力)
  ├── player_symbols.py (ARC / AUT 符文)
  ├── inner_ability.py (傳說內在潛能)
  ├── pet_system.py (月光寵物與自補)
  └── familiar_system.py (萌獸潛能與回血光環)
        │
        ▼ (儲存 / 基礎設施)
[Infrastructure & Audio]
  ├── player_save.py (JSON 存檔序列化/反序列化)
  └── sound.py (SoundManager 音效播放單例)
```

---

## 2. 循環引用清查 (Circular Dependencies)

靜態分析器在專案頂層檢測出 **2 組嚴重循環依賴**，均透過「函數內局部 `import`」暫時掩蓋：

### 循環 1：`item_system ↔ item_gachapon`
- **成因路徑**：
  - `item_system.py` 頂層依賴裝備生成與轉蛋產出。
  - `item_gachapon.py` 在執行 `draw_gachapon()` 時，內部呼叫 `import item_system` 來取得裝備實體化與洗詞條方法。
- **解耦方案**：
  - 將裝備資料模型 (`Item` dataclass) 抽離至純粹的 `core/equipment/models.py`。
  - 轉蛋機率表與生成行為獨立為 `services/gachapon_service.py`，不再反向依賴整個 `item_system`。

### 循環 2：`player_data ↔ player_save`
- **成因路徑**：
  - `player_data.py` 包含 `Player` 與 `TeamMember` 定義，並在存檔方法中需要調用序列化邏輯。
  - `player_save.py` 的反序列化方法 `player_load_dict()` 為了實體化玩家物件，在函式內執行 `from player_data import Player, TeamMember`。
- **解耦方案**：
  - 遵循計畫書第 7 節，將存檔搬移至 `infrastructure/persistence/json_save.py`。
  - `player_data` 僅保留領域模型（純狀態），序列化/反序列化由專責的 `SaveService` 進行組裝與還原，消解雙向引用。

---

## 3. 函數內部局部載入 (Local Imports) 詳盡清單

全專案共計 **39 處** 局部 `import`，主要分佈如下：

| 檔案位置 | 行號與所屬函式 | 引入之模組 | 存在原因與風險 |
|---|---|---|---|
| `src/player_data.py` | L128 in `get_available_skills()` | `import classes` | 規避 classes 與 player_data 間之潛在互相引用 |
| `src/player_data.py` | L310 in `get_legion_stat()` | `import legion_system` | 規避 player_data 與 legion_system 之相互引用 |
| `src/player_save.py` | L24 in `player_to_dict()` | `import player_gear` | 規避 save 與 gear 之循環依賴 |
| `src/player_save.py` | L57, 141 in `player_load_dict()` | `import player_gear, player_data` | **核心循環**：save 反向建構 player 實體 |
| `src/player_save.py` | L181-183 in `player_load_dict()` | `import inner_ability, pet_system, familiar_system` | 延遲載入次要系統反序列化函式 |
| `src/item_gachapon.py` | L23 in `draw_gachapon()` | `import item_system` | **核心循環**：轉蛋呼叫道具工廠 |
| `src/item_gachapon.py` | L81, 106, 184 in `draw_gachapon()` | `import pet_system, familiar_system, player_symbols` | 轉蛋各獎項分支臨時引入模組 |
| `src/combat_loot.py` | L138 in `handle_monster_killed()` | `import familiar_system` | 掉落物結算時臨時加載萌獸掉落卡牌邏輯 |
| `src/pyside_ui.py` | L132, 439, 502, 522 | `import ui_dialogs` | 避免視窗模組與對話框模組循環引用 |
| `src/pyside_ui.py` | L486, 533, 556, 579 | `import item_system` | UI 商城按鈕內部臨時載入道具系統 |
| `src/pyside_ui.py` | L615, 641 | `import pet_system` | UI 寵物商店按鈕內部臨時載入寵物系統 |
| `src/ui_dialogs/*.py` | 多處（auto_cube, inventory, compare） | `import player_gear` | 裝備視窗內部直接調用洗方塊/換裝底層 |

**重構方向**：
在 Phase 2 與 Phase 4 透過抽出共同 `models` 及建立 `services` 統一注入，將所有 39 處局部引入完全拔除，還原至檔案頂部正規 `import`。

---

## 4. Qt 滲透檢查 (Qt Leakage into Domain)

- **審計結論**：**【0 滲透，極度優秀】**
- 經 AST 嚴格掃描，下列 25 個領域計算與資料模型檔案中，**完全沒有任何 `PySide6`、`QtCore`、`QtWidgets`、`QtGui` 的 import 或調用**：
  `combat_damage.py`, `combat_loot.py`, `combat_stats.py`, `combat_system.py`, `combat_zones.py`, `familiar_system.py`, `inner_ability.py`, `item_catalog.py`, `item_gachapon.py`, `item_potential.py`, `item_sets.py`, `item_system.py`, `legion_system.py`, `monster.py`, `monster_ai.py`, `monster_skills.py`, `pet_system.py`, `player_data.py`, `player_gear.py`, `player_offline.py`, `player_save.py`, `player_stats.py`, `player_symbols.py`, `skills.py`。
- 這意味著未來的 **Headless 戰鬥模擬器** 與 **單元測試** 不需要做任何 Qt Mock 即可純粹運行！

---

## 5. 共享可變狀態與單例模式 (Shared Mutable State)

1. **`sound_mgr = SoundManager()` 全域單例**：
   - 定義於 `src/sound.py` 第 136 行。
   - **污染點**：在 `combat_damage.py` (9 處)、`combat_loot.py` (7 處)、`combat_system.py` (10 處)、`monster_ai.py` (3 處) 中被直接調用（如 `sound_mgr.play_attack(...)`、`sound_mgr.play_loot(...)`）。
   - **問題**：導致純數值計算函數（如傷害計算、擊殺結算）隱含了 Pygame Audio 裝置副作用。在無聲卡環境或極速 DPS 壓測中會產生無謂負擔。
   - **解耦方案**：改由 Event-driven 輸出 `SoundPlayEvent(sound_id)`，戰鬥引擎不直接持有 `sound_mgr`。
2. **模組級靜態目錄字典 (Module-Level Static Catalogs)**：
   - `BOSS_SKILLS_CATALOG` (`monster_skills.py`)
   - `BASIC_PET_SHOP_CATALOG`, `LUNA_PET_CATALOG` (`pet_system.py`)
   - 現況良好：均為只讀設定表（Read-only Reference），未發現執行階段動態 append/modify 之髒狀態。

---

## 6. 上帝物件剖析 (God Objects)

### 6.1 `Player` (`src/player_data.py`)
- **規模**：402 行代碼、**61 個成員方法**、`__init__` 初始化多達 20 個異構子系統屬性。
- **過度承載之職責**：
  1. **身分與基礎屬性** (`level`, `exp`, `gold`, `free_points`, `stat_atk`, `stat_crit`, `stat_def`, `stat_hp`)
  2. **編隊陣型** (`team`: 7 位成員，主角 + 6 隨行夥伴管理、互換、出戰槽位計算)
  3. **裝備背包與穿戴** (`inventory`, `equipped`, 套裝檢查、星力計算)
  4. **奧術與真實符文** (`arc_symbols`, `aut_symbols`, `symbol_fragments`, 升級邏輯)
  5. **寵物系統** (`pet_manager`: 自補水、飽食度、寵物裝備)
  6. **萌獸系統** (`familiar_manager`: 3 萌獸出戰、光環定時回血、洗方塊)
  7. **傳說內在潛能** (`inner_ability`: 三排洗詞條、鎖定)
  8. **聯盟戰地** (`get_bench_classes()`, `get_legion_stat()`)
  9. **戰鬥增益光環與休整** (`team_buffs`, `on_floor_cleared()`, `restore_team_full_hp()`)
- **建議拆解路徑 (依計畫書第 4.1 節)**：
  ```text
  CharacterState (純資料容器)
  ├── BaseProgression (等級、經驗、金幣、點數)
  ├── ExpeditionTeam (7 位隊員與出戰狀態)
  ├── EquipmentInventory (裝備穿戴與背包)
  ├── AuxiliaryProgression (符文、萌獸、寵物、內潛、戰地)
  └── CombatRuntimeStats (戰鬥中動態 Buff、護盾與生命)
  ```

### 6.2 `CombatManager` (`src/combat_system.py`)
- **規模**：531 行代碼、**23 個成員方法**、`__init__` 包含 23 個狀態變數。
- **過度承載之職責**：
  1. **戰鬥大迴圈與時間推進** (`update(dt)`, 技能冷卻遞減、怪物攻擊間隔計時)
  2. **關卡與層數調度** (`current_zone_idx`, `current_floor`, `spawn_next_monster()`, 倒數計時休整)
  3. **特殊挑戰副本** (`enter_gold_dungeon()`, `configure_training_dummy()`)
  4. **首領特殊機制** (露希妲全屏瘴氣計時器、狂暴計時器、多階段判定)
  5. **表現層浮字與震動混入** (`floating_popups`, `shake_team`, `shake_monster`, `add_popup()`)
  6. **戰鬥日誌格式化與色彩管理** (`combat_logs`, `add_log()`, 包含顏色 RGB 元組)
  7. **音效直接播放** (直接調用 `sound_mgr.play(...)`)
- **建議拆解路徑 (依計畫書第 4.2 & 5 節)**：
  ```text
  BattleEngine (純無頭戰鬥邏輯，回傳 List[BattleEvent])
  ├── Step 1: Cooldown & Timer Ticking
  ├── Step 2: Skill & Attack Resolution (SkillResolver, DamageResolver)
  ├── Step 3: Monster AI & Boss Mechanics
  └── Step 4: Output Events (DamageEvent, HealEvent, PopupEvent, AudioEvent, LogEvent)
  ```

---

## 7. UI 直接修改狀態點位 (UI Direct State Mutation)

靜態檢測在 `pyside_ui.py` 中發現 **18 處** UI 控制器直接穿透修改底層資料結構的行為：

### 類別 A：戰鬥開關直接指派 (5 處)
- `src/pyside_ui.py:252, 261, 270, 272, 276`
  - `self.combat_mgr.repeat_current_zone = True / False / checked`
  - **解法**：應提供 `combat_mgr.set_auto_repeat(bool)`。

### 類別 B：商城直接更動金幣與字典數量 (13 處)
- `src/pyside_ui.py:546, 572, 592, 607, 624, 659, 679`
  - `self.player.gold += cost` (扣款或退款直接對 `gold` 整數做 `+=` / `-=` 運算)
- `src/pyside_ui.py:548-549, 570`
  - `self.player.abby_scrolls[scroll_type] = ...` (直接操作背包字典)
- `src/pyside_ui.py:594-595`
  - `self.player.cube_inventory[cube_type] = ...`
- `src/pyside_ui.py:608`
  - `self.player.familiar_manager.familiar_cubes += count`
- **解法**：建立 `EconomyService` 或 `ShopService`，提供 `shop_service.buy_item(player, item_id, count)`，由服務層統一校驗金幣、扣款與發放道具，UI 僅接收回傳結果。

---

## 8. 接手重構之階段執行路線圖 (Roadmap for Codex)

遵循《重構與發布計畫書》第 25～26 節之 **MUST / MUST NOT** 準則，建議後續重構嚴格按以下最小風險順序實施：

```text
[當前已完成] Phase 0 & 1:
  ✔ 覆蓋建立 GitHub Python 主線倉庫 (NekoMaTA864/Maple_Idle)
  ✔ 完整 .gitignore、VERSION (1.0.6)、start.bat、README.md
  ✔ 配置 GitHub Actions CI (.github/workflows/test.yml)
  ✔ 48 項單元測試 100% 通過，打上 tag: python-baseline
  ✔ 產出 REFACTOR_ANALYSIS.md

[後續建議接續] Phase 2: Pure Core Boundary (最安全，零業務變更)
  1. 建立 core/common/、core/character/、core/equipment/ 等純 models 目錄。
  2. 將 item_system ↔ item_gachapon 依賴的資料結構抽出，消除第 1 個循環依賴。
  3. 拔除 combat_damage.py 與 combat_loot.py 中對 sound_mgr 的直接引用（改以可選回調或無操作回退）。
  4. 消除所有 domain 內部函式的 39 處局部 import，回歸檔案頂部規範導入。

[後續建議接續] Phase 3: Event-driven Combat Output (戰鬥表現解耦)
  1. 定義 dataclass BattleEvent 系列 (DamageEvent, SkillCastEvent, PopupEvent 等)。
  2. CombatManager.update() 產生 events，UI 監聽 events 進行 QPainter VFX 播放與跳字。
  3. 達成 BattleEngine 100% 無聲卡、無 UI、純 Headless 快速模擬。

[後續建議接續] Phase 4: Player / CombatManager Facade 拆解
  1. 建立 Application Services (ProgressionService, EquipmentService, EconomyService)。
  2. 封裝 UI 直接修改 gold / abby_scrolls / repeat_zone 的所有點位。
  3. Player 與 CombatManager 原有 API 保留為 Facade，內部代理至 Services，確保向後相容。

[後續建議接續] Phase 5: Save Schema Versioning & Migration
  1. 存檔加入 "schema_version": 1。
  2. 建立 infrastructure/persistence/migrations.py。
  3. 驗證新舊存檔升級與相容測試。
```
