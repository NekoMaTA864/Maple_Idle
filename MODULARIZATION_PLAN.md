# 模組化瘦身計畫書（已全部實施完成 ✅）

> 目的：在專案持續擴充新系統（轉蛋、種子戒指、木樁環境……）的同時，
> 避免核心檔案越滾越大、越難維護。範圍只涵蓋「拆檔案」，不涉及玩法
> 或數值改動。與職業平衡、VFX 相關的計畫請見 `PROJECT_HANDOFF.md`。
>
> 建立日期：2026-09-08
> 完成日期：2026-09-08（已達成 100% 拆分與 25 單元測試全綠通過）

## 現況：瘦身前後對比

| 原始檔案 | 原行數 | 拆分後架構與檔案 | 現行數 | 改善幅度 |
|---|---|---|---|---|
| `src/combat_system.py` | 1,549行 | `combat_system.py` (門面 Facade)<br>`combat_zones.py` (23區資料表)<br>`combat_vfx_manager.py` (VFX/打擊隊列)<br>`monster.py` (怪物/技能優先度)<br>`combat_loot.py` (掉落/晉級)<br>`monster_ai.py` (怪物AI)<br>`combat_damage.py` (傷害/護盾/治療) | **447行**<br>344行<br>102行<br>82行<br>137行<br>151行<br>347行 | 主檔 **-71.1%**<br>所有子模組均 < 350行 |
| `src/ui_dialogs.py` | 1,097行 | `ui_dialogs/` 套件包：<br>`__init__.py`<br>`set_bonus_dialog.py`<br>`training_dummy_dialog.py`<br>`auto_cube_dialog.py`<br>`item_compare_dialog.py`<br>`inventory_grid_dialog.py`<br>`gachapon_result_dialog.py` | <br>18行<br>67行<br>66行<br>156行<br>457行<br>252行<br>150行 | 原巨石檔已移除<br>全模組獨立解耦<br>最大檔僅 457行 |

全庫目前除 `item_system.py` (806行，包含大量裝備公式與品階定義) 外，**已無任何超過 500 行的業務邏輯檔案**！

---

## 1. `combat_system.py` 拆分方案（1549行 → 預估主檔降到 400-500行）

### 現況結構（已用 `grep` 實際核對行號）

```
32-372行    ZONES               純資料表（23個區域配置），340行
373-428行   VisualEffect / _get_vfx_priority
429-471行   VisualEffectManager / PendingHit
472-527行   Monster 類別 / get_skill_priority
553-1549行  CombatManager 類別   ← 本體，將近 1000 行，職責過度集中
```

`CombatManager` 內部方法拆解（實際核對的行號）：

- `_member_attack`（約280行）——**全庫最肥的單一函式**：傷害公式、
  暴擊、ARC/AUT 加成與壓制、多段連擊分段、buff/護盾/治療/凍結套用、
  彈跳文字、戰鬥紀錄，全部塞在一起。
- `_on_monster_killed`（約126行）——擊殺後的掉落結算：一般裝備掉落、
  首領神裝/種子戒指/艾比卷軸/方塊掉落、符號碎片掉落、樓層與區域
  進度推進。
- `_monster_attack_unit` + `_execute_monster_skill`（約140行）——
  怪物/首領的攻擊 AI 與技能施放判斷。
- `spawn_next_monster`（約82行）——怪物/首領生成、木樁環境設定。
- 其餘（`update`、`add_log`、`add_popup`、座標計算等）——真正屬於
  「戰鬥管理器主迴圈」該留下的部分。

### 建議拆法（比照 `player_data.py` 已驗證成功的 Facade 模式）

| 新檔案 | 內容 | 預估行數 |
|---|---|---|
| `combat_zones.py` | `ZONES` 資料表 | ~340 |
| `combat_vfx_manager.py` | `VisualEffect`、`_get_vfx_priority`、`VisualEffectManager`、`PendingHit` | ~100 |
| `monster.py` | `Monster` 類別、`get_skill_priority` | ~80 |
| `combat_damage.py` | `_member_attack`、`_apply_member_shield`（傷害/buff/護盾/治療/凍結核心運算） | ~300 |
| `combat_loot.py` | `_on_monster_killed` 的掉落結算邏輯 | ~130 |
| `monster_ai.py` | `_monster_attack`、`_monster_attack_unit`、`_execute_monster_skill` | ~140 |
| `combat_system.py`（保留） | `CombatManager` 作為門面，`update()`／`spawn_next_monster()`／區域樓層管理，內部方法委派給上述模組 | ~400-450 |

**實作提醒**：
- `CombatManager` 對外的方法簽名（`update(dt, sound_mgr)`、
  `spawn_next_monster()` 等）**一律不變**，`pyside_ui.py` 跟測試檔案
  都直接呼叫 `CombatManager` 的方法，拆分時只搬動內部實作，不要動
  對外介面。
- `_member_attack` 拆出去後，內部會需要存取 `self.player`、
  `self.vfx_mgr`、`self.monsters` 等 `CombatManager` 的狀態，建議做成
  獨立函式並把 `combat_mgr` 或必要的幾個屬性當參數傳入（而不是整個
  搬成另一個類別），維持目前的呼叫慣例。
- `ZONES` 拆出去後記得檢查 `from combat_system import ZONES` 之類的
  外部引用（目前主要是 `monster_skills.py` 與測試檔案），改成
  `from combat_zones import ZONES`，或在 `combat_system.py` 頂部
  `from combat_zones import ZONES` 再重新 export 一次以維持相容。

**驗收標準**：拆完每一個模組後跑一次
`runtime\python\python.exe -m unittest discover -s src/tests -p "test_*.py"`，
確認 `Ran 25 tests ... OK`；全部拆完後用 `啟動遊戲.bat` 實際玩一輪
（換裝、放技能、擊殺王、看掉落）確認行為沒有變化。

---

## 2. `ui_dialogs.py` 拆分方案（1097行 → 預估主檔降到 20-30行的純轉出層）

### 現況結構（已用 `grep` 實際核對行號）

```
23-79行     SetBonusDialog        （56行）
79-136行    TrainingDummyDialog   （57行）
136-283行   AutoCubeDialog        （147行）
283-718行   ItemCompareDialog     （435行，全庫最大的彈窗類別）
718-959行   InventoryGridDialog   （241行）
959-1097行  GachaponResultDialog  （138行）
```

六個彈窗類別各自獨立、互不依賴，是最適合「一類別一檔案」的教科書案例
（拆分模式完全比照 `vfx/explorers/` 已經驗證過的做法）。

### 建議拆法

在 `src/` 底下新增 `ui_dialogs/` 資料夾：

```
src/ui_dialogs/
  __init__.py
  set_bonus_dialog.py        SetBonusDialog
  training_dummy_dialog.py   TrainingDummyDialog
  auto_cube_dialog.py        AutoCubeDialog
  item_compare_dialog.py     ItemCompareDialog     ← 最大宗，優先拆
  inventory_grid_dialog.py   InventoryGridDialog
  gachapon_result_dialog.py  GachaponResultDialog
```

`src/ui_dialogs.py`（保留原檔名，維持所有外部呼叫不用改 import 路徑）
改成純轉出層：

```python
from ui_dialogs.set_bonus_dialog import SetBonusDialog
from ui_dialogs.training_dummy_dialog import TrainingDummyDialog
from ui_dialogs.auto_cube_dialog import AutoCubeDialog
from ui_dialogs.item_compare_dialog import ItemCompareDialog
from ui_dialogs.inventory_grid_dialog import InventoryGridDialog
from ui_dialogs.gachapon_result_dialog import GachaponResultDialog
```

**注意**：`src/ui_dialogs.py`（檔案）與 `src/ui_dialogs/`（資料夾）不能
同時存在同名，Python 會衝突。做法是：新增資料夾時**先把資料夾取名為
`ui_dialogs_impl/` 或直接把現有 `ui_dialogs.py` 整個移進去變成資料夾
結構**（即把 `ui_dialogs.py` 刪除，改建立 `ui_dialogs/` 資料夾與其中
的 `__init__.py` 扮演原本 `ui_dialogs.py` 的角色，`__init__.py` 內容
就是上面那 6 行 import）。這樣外部 `from ui_dialogs import XxxDialog`
完全不用改。

**目前已知的呼叫點**（拆分後這些地方應該完全不用改動）：
- `src/pyside_ui.py`（4 處）
- `src/tests/test_5player_party_and_boss.py`
- `src/tests/test_gear_pacing_and_slots.py`
- `src/tests/test_refactor_integrity.py`
- `src/scratch/capture_verification.py`（非正式測試，可忽略但不影響）

**驗收標準**：同上，跑完 25 項單元測試 + 實際開遊戲點開換裝/強化/
轉蛋彈窗確認顯示與互動正常。

---

## 3. 低優先項目（暫不建議現在處理，先列在這裡備查）

- **`src/vfx_sandbox.py`（827行）**：這是開發者用的技能特效展示/除錯
  工具，不是玩家會用到的正式遊戲路徑。雖然行數不小，但獨立於主遊戲
  邏輯之外，拆分帶來的維護效益低於 `combat_system.py` / `ui_dialogs.py`，
  建議排在更後面，或等它繼續變大再處理。
- **`src/player_gear.py`（606行）**、**`src/item_catalog.py`（562行）**：
  606 行的 `player_gear.py` 內容應該是裝備穿脫/星力/洗潛/回真卷軸邏輯，
  562 行的 `item_catalog.py` 主要是純資料表（品階/詞條池/種子戒指
  規格），兩者都還在合理範圍內，暫不需要拆，之後如果繼續長大（例如
  加入寶石系統的裝備互動）可以再評估。

---

## 4. 建議施工順序

1. 先拆 `ui_dialogs.py`——六個彈窗類別完全獨立、零交叉依賴，風險
   最低，適合當作驗證拆分流程的第一步。
2. 再拆 `combat_system.py`——依上面第 1 節的順序，**建議從
   `combat_zones.py`（純資料，零邏輯風險）開始**，再來是
   `combat_vfx_manager.py` 與 `monster.py`（邊界清楚），最後才處理
   `_member_attack` 這個核心大函式（風險最高，建議留到最後、且拆完
   要格外仔細跑一次完整測試 + 手動遊戲驗證）。
3. 每完成一個檔案的拆分就跑一次 25 項單元測試，確認全綠再進行下一個，
   不要一次拆多個檔案再一起驗證，方便定位問題。
