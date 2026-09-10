# Maple Idle Python 主線重構與 GitHub 發布計畫

> 目的：保留現有 Python + PySide6 桌面版作為主線，不進行完整 Web 重寫；將既有專案整理為低耦合、可測試、可由 Codex / Antigravity 長期維護的架構，並建立適合頻繁更新給朋友使用的 Portable Python + GitHub Releases 發布流程。

---

## 0. 核心決策

### 0.1 主線技術

正式主線維持：

- Python
- PySide6
- 既有向量繪圖 / VFX
- 既有戰鬥、裝備、技能、地圖、Boss、養成系統
- Portable / Embedded Python Runtime
- BAT 或簡易 Launcher 啟動
- GitHub 作為原始碼、Issue、版本與 Release 的中心

目前 Web 版保留為：

- UI / UX prototype
- 未來若要瀏覽器版時的設計參考
- 不再優先補齊與 Python 版同等功能

不進行以下工程：

- 全量 Python → TypeScript rewrite
- PySide6 → React 全面替換
- QPainter → Canvas 全面替換
- 為了部署便利而重做整個遊戲核心

---

## 1. 專案目標

本階段優先目標：

1. 降低模組耦合。
2. 明確定義 dependency direction。
3. 拆解過度集中的 Player / CombatManager 職責。
4. 將戰鬥輸出改為 Event-driven。
5. 將 UI、遊戲邏輯、資料、存檔、音效、VFX 分層。
6. 保持既有玩法與數值結果不變。
7. 建立 regression tests / golden tests。
8. 建立穩定 GitHub workflow。
9. 建立 Portable Runtime + Incremental Update 發布流程。
10. 讓沒有開發基礎的玩家只需：
   - 第一次解壓完整包。
   - 之後按「更新」。
   - 按「開始遊戲」。

---

# 2. 目標架構

建議逐步收斂成以下結構：

```text
Maple_Idle/
├─ maple_idle/
│  ├─ core/
│  │  ├─ combat/
│  │  │  ├─ models.py
│  │  │  ├─ engine.py
│  │  │  ├─ damage.py
│  │  │  ├─ targeting.py
│  │  │  ├─ effects.py
│  │  │  └─ events.py
│  │  │
│  │  ├─ character/
│  │  │  ├─ models.py
│  │  │  ├─ stats.py
│  │  │  └─ progression.py
│  │  │
│  │  ├─ equipment/
│  │  ├─ skills/
│  │  ├─ monster/
│  │  ├─ symbols/
│  │  ├─ economy/
│  │  └─ common/
│  │
│  ├─ services/
│  │  ├─ battle_service.py
│  │  ├─ equipment_service.py
│  │  ├─ progression_service.py
│  │  ├─ inventory_service.py
│  │  └─ save_service.py
│  │
│  ├─ data/
│  │  ├─ classes/
│  │  ├─ skills/
│  │  ├─ zones/
│  │  ├─ items/
│  │  ├─ bosses/
│  │  └─ balance/
│  │
│  ├─ presentation/
│  │  └─ qt/
│  │     ├─ main_window.py
│  │     ├─ arena/
│  │     ├─ panels/
│  │     ├─ dialogs/
│  │     └─ view_models/
│  │
│  ├─ infrastructure/
│  │  ├─ persistence/
│  │  │  ├─ json_save.py
│  │  │  └─ migrations.py
│  │  ├─ audio/
│  │  ├─ logging/
│  │  └─ platform/
│  │
│  └─ tools/
│     ├─ dps_calculator/
│     └─ vfx_sandbox/
│
├─ tests/
│  ├─ unit/
│  ├─ integration/
│  ├─ regression/
│  └─ golden/
│
├─ runtime/
│  └─ python/
│
├─ launcher/
│  ├─ start.bat
│  ├─ update.bat
│  └─ updater.py
│
├─ saves/
├─ settings/
├─ logs/
├─ VERSION
├─ requirements-lock.txt
└─ README.md
```

此結構是目標，不要求一次搬完。

---

# 3. Dependency Direction

必須固定：

```text
Presentation / Qt
        ↓
Application Services
        ↓
Domain Core
        ↓
Pure Models / Rules
```

Infrastructure 只能由上層透過介面或 service 使用：

```text
JSON / Filesystem / Sound / Qt / OS
                ↓
         Infrastructure
```

禁止 Core 直接知道：

- PySide6
- QWidget
- QPainter
- QTimer
- pygame.mixer
- Windows 路徑
- JSON 檔案位置
- BAT
- GitHub
- UI 元件

---

# 4. 低耦合重構重點

## 4.1 Player 不再持續膨脹

避免未來變成：

```python
player.gear
player.symbols
player.pet
player.familiar
player.legion
player.inner_ability
player.gems
player.totems
player.hexa
player.artifact
...
```

建議拆為：

```text
CharacterState
├─ Identity
├─ BaseStats
├─ Progression
├─ EquipmentState
├─ SkillLoadout
└─ RuntimeCombatState
```

其餘系統由 service / aggregate 管理。

原則：

- Model 儲存資料。
- Service 執行行為。
- UI 不直接修改深層 model。
- Combat 不直接持有整個 UI-facing Player object。

---

## 4.2 CombatManager 拆責任

若目前 CombatManager 同時負責：

- 技能判定
- target selection
- damage
- healing
- shield
- cooldown
- monster AI
- loot
- stats
- VFX
- sound
- UI callback

則逐步拆成：

```text
BattleEngine
├─ SkillResolver
├─ DamageResolver
├─ TargetingResolver
├─ StatusEffectResolver
├─ MonsterAI
├─ LootResolver
└─ BattleEventEmitter
```

CombatManager 最終只做 orchestration。

---

# 5. Event-driven Battle Output

這是本次重構的核心項目之一。

不要讓 Combat Engine 直接：

- 畫 VFX
- 顯示浮字
- 播音效
- 寫 UI
- 修改 QWidget

建議：

```python
events = battle_engine.step(dt)
```

回傳：

```python
DamageEvent(...)
CriticalHitEvent(...)
HealEvent(...)
ShieldEvent(...)
SkillCastEvent(...)
BuffAppliedEvent(...)
MonsterKilledEvent(...)
BossPhaseChangedEvent(...)
LootDroppedEvent(...)
BattleEndedEvent(...)
```

然後：

```text
BattleEngine
     │
     ├─ Qt UI       → 畫動畫與浮字
     ├─ Audio       → 播音效
     ├─ DPS Tool    → 記錄數據
     ├─ Logger      → 寫 log
     └─ Tests       → assert events
```

優點：

- Battle 可 headless 執行。
- DPS simulator 不需要 UI。
- 單元測試簡單。
- VFX 修改不影響遊戲規則。
- 未來若要換 UI，不需重寫 Combat Core。

---

# 6. Data 與 Balance

遊戲資料應盡量 data-driven。

例如：

```text
data/classes/
data/skills/
data/zones/
data/items/
data/bosses/
```

長期目標：

- 避免大量 class-specific hardcode 散落於 combat code。
- 技能倍率 / CD / hits / tags / effect definition 集中。
- 地圖數值集中。
- 裝備與 set effect 集中。
- balance constants 集中。

可保留 Python 定義，不強制 JSON 化。

若 Python dataclass / dict 已足夠乾淨，可維持 Python 作為 canonical source。

---

# 7. Save System

## 7.1 Save Schema Version

存檔必須加入 schema version：

```json
{
  "schema_version": 3,
  "game_version": "1.1.0",
  "player": {},
  "inventory": {},
  "progression": {}
}
```

---

## 7.2 Migration

新增：

```text
infrastructure/persistence/migrations.py
```

範例：

```python
def migrate_v1_to_v2(data):
    ...

def migrate_v2_to_v3(data):
    ...
```

載入流程：

```text
load JSON
   ↓
detect schema_version
   ↓
run migrations
   ↓
validate
   ↓
construct models
```

---

## 7.3 不可覆蓋玩家資料

任何 updater / release package 都禁止覆蓋：

```text
saves/
settings/
screenshots/
logs/
```

其中 `logs/` 可清理，但 updater 不應直接 replace。

---

# 8. 測試策略

## 8.1 Unit Tests

涵蓋：

- stats calculation
- damage
- crit
- defense
- ARC / AUT
- starforce
- potentials
- equipment effects
- cooldown
- targeting
- healing
- shields
- boss mechanics

---

## 8.2 Regression Tests

每次重構前固定現有結果。

不要在低耦合重構階段順手改 balance。

重構原則：

> Architecture changes should not change gameplay results.

---

## 8.3 Golden Tests

建立固定 battle cases：

```text
tests/golden/
├─ damage_cases.json
├─ boss_cases.json
├─ equipment_cases.json
├─ skill_cases.json
└─ progression_cases.json
```

範例：

```json
{
  "case": "hero_skill_vs_boss",
  "input": {
    "stats": {},
    "skill": {},
    "enemy": {},
    "rng_seed": 12345
  },
  "expected": {
    "damage": 1234567,
    "hits": 7
  }
}
```

用途：

- Agent 修改後快速驗證。
- 防止數值 drift。
- 未來改引擎時作 reference。

---

# 9. Random / Deterministic Simulation

戰鬥核心不要直接散落：

```python
random.random()
```

改為注入 RNG：

```python
rng = Random(seed)
battle = BattleEngine(rng=rng)
```

測試可以：

```python
Random(12345)
```

正式遊戲可以：

```python
Random()
```

如此才能重現：

- 暴擊
- 潛能
- 星力
- 掉落
- Boss AI
- 技能 proc

---

# 10. GitHub Repository 策略

建議正式建立 Python 主線 Repo：

```text
NekoMaTA864/Maple_Idle
```

若目前 Repo 被 Web prototype 使用：

建議二選一：

### 方案 A：重新定位現 Repo

```text
Maple_Idle
```

改回 Python 主線。

Web prototype 搬：

```text
Maple_Idle_Web
```

### 方案 B：保留現 Repo

```text
Maple_Idle_Web
Maple_Idle_Python
```

較推薦 A，因為 Python 才是正式主線。

---

# 11. Branch Strategy

個人專案不需要複雜 Git Flow。

建議：

```text
main
│
├─ refactor/*
├─ feature/*
├─ fix/*
└─ release/*
```

規則：

- `main` 必須可執行。
- 大型重構走 branch。
- 功能完成並測試後 merge main。
- Release 只從 main 打 tag。

---

# 12. Commit 規範

推薦 Conventional Commits：

```text
feat: add symbol workshop
fix: correct critical damage calculation
refactor: decouple combat engine from Qt
test: add boss phase regression cases
build: update portable runtime
docs: update architecture handoff
```

Agent 每次修改避免一次跨太多 subsystem。

---

# 13. GitHub Actions

建立：

```text
.github/workflows/test.yml
```

至少執行：

```bash
python -m pytest
```

若有 lint：

```bash
ruff check .
```

若有 type check：

```bash
pyright
```

建議 CI：

```text
Push / PR
   ↓
Install dependencies
   ↓
Unit Tests
   ↓
Regression Tests
   ↓
Lint
   ↓
PASS
```

Release build 不需每次 push 都做。

---

# 14. Release Version

使用 Semantic Versioning：

```text
MAJOR.MINOR.PATCH
```

例：

```text
1.0.5
1.0.6
1.1.0
2.0.0
```

定義：

- PATCH：Bug fix / balance 微調。
- MINOR：新增系統 / 地圖 / 職業 / UI 功能。
- MAJOR：存檔或核心架構大幅變動。

---

# 15. Portable Python Distribution

本專案目前優先採用：

> Portable / Embedded Python + BAT

而非每版 PyInstaller。

原因：

- 更新頻率高。
- 使用者只有少數固定朋友。
- Runtime 通常不會頻繁變動。
- 避免每次完整 rebuild。
- 更新包可非常小。

---

# 16. Distribution Layout

建議玩家端：

```text
MapleIdle/
├─ runtime/
│  └─ python/
│
├─ game/
│  ├─ maple_idle/
│  ├─ data/
│  └─ assets/
│
├─ saves/
├─ settings/
├─ logs/
│
├─ start.bat
├─ update.bat
└─ VERSION
```

---

# 17. start.bat

範例：

```bat
@echo off
cd /d "%~dp0"

runtime\python\python.exe game\main.py

if errorlevel 1 (
    echo.
    echo 遊戲發生錯誤，請將 logs 資料夾提供給開發者。
    pause
)
```

實際 entrypoint 依重構後路徑調整。

---

# 18. Runtime 與 Game 分離

第一次完整包：

```text
MapleIdle_Full_1.1.0.zip
```

內容：

```text
runtime/
game/
start.bat
update.bat
VERSION
```

之後 Release 可以只提供：

```text
MapleIdle_Update_1.1.1.zip
```

只含：

```text
game/
VERSION
```

Runtime 只有 dependency 或 Python major/minor 版本改變時才更新。

---

# 19. GitHub Releases

Release 建議：

```text
v1.1.0
├─ MapleIdle_Full_1.1.0.zip
├─ MapleIdle_Update_1.1.0.zip
├─ version.json
└─ CHANGELOG.md
```

`version.json`：

```json
{
  "version": "1.1.0",
  "minimum_runtime": "1.0.0",
  "update_asset": "MapleIdle_Update_1.1.0.zip",
  "full_asset": "MapleIdle_Full_1.1.0.zip"
}
```

---

# 20. Updater

`updater.py` 負責：

```text
local VERSION
    ↓
GitHub latest release
    ↓
version compare
    ↓
download update zip
    ↓
backup
    ↓
replace game/
    ↓
keep saves/
    ↓
update VERSION
```

Updater 不應：

- 刪 saves。
- 修改玩家設定。
- 直接更新自己正在執行的檔案。
- 靜默吞掉 update error。

---

# 21. Safe Update Strategy

推薦：

```text
download
   ↓
temp/
   ↓
verify
   ↓
backup current game/
   ↓
replace
   ↓
launch test
```

失敗則：

```text
rollback backup
```

至少保留上一版：

```text
.backup/game_previous/
```

---

# 22. Dependency Lock

Portable Runtime 必須搭配固定 dependency。

建立：

```text
requirements-lock.txt
```

不要只用：

```text
PySide6>=...
```

正式 release 應固定版本：

```text
PySide6==x.y.z
pygame==x.y.z
...
```

Runtime version 與 dependency lock 綁定。

---

# 23. Release Build Script

新增：

```text
scripts/build_release.py
```

負責：

1. 執行 tests。
2. 清理 `__pycache__`。
3. 建立 `game/`。
4. 複製 assets。
5. 寫入 VERSION。
6. 產生 update zip。
7. 選擇性產生 full zip。
8. 計算 checksum。

可輸出：

```text
dist/
├─ MapleIdle_Full_1.1.0.zip
├─ MapleIdle_Update_1.1.0.zip
└─ SHA256SUMS.txt
```

---

# 24. Logging

正式玩家版必須保留 log。

例如：

```text
logs/latest.log
logs/crash_2026-09-10_183000.log
```

至少記錄：

- game version
- runtime version
- Python version
- exception
- traceback
- save schema version

如此朋友遇到問題只需傳 log。

---

# 25. Agent 執行守則

Codex / Antigravity 執行此重構時必須遵守：

## MUST

- 修改前先閱讀 ARCHITECTURE / HANDOFF / TEST。
- 每階段先跑 baseline tests。
- 小步提交。
- 保持 main 可執行。
- 重構期間保持遊戲結果一致。
- 新功能必須有測試。
- 新 subsystem 優先放入新架構。
- 避免 circular import。
- 避免 UI → deep model direct mutation。
- 避免 Core import Qt。
- 新 random logic 可 seed。
- Save schema 變更一定補 migration。

## MUST NOT

- 一次大爆炸重寫全專案。
- 重構時順便大改平衡。
- 新增巨大 God Object。
- 在 UI code 寫 damage formula。
- Combat Engine 直接呼叫 QWidget。
- 在 domain code 寫硬編碼絕對路徑。
- 自動覆蓋 saves。
- 每次 release 都重新打完整 runtime。
- 為了「漂亮」隨意重命名大量 public API 而不補 migration / compatibility layer。

---

# 26. 實施階段

## Phase 0 — Baseline

目標：

- 現有程式完整可跑。
- 現有 tests 全綠。
- 建立 Git tag。

工作：

```text
tag: legacy-baseline
```

產出：

- baseline test result
- dependency list
- architecture snapshot

---

## Phase 1 — Repository Cleanup

工作：

- 建 GitHub Python 主線。
- 清 `.gitignore`。
- 加 README。
- 加 ARCHITECTURE.md。
- 加 DEVELOPMENT.md。
- 加 TESTING.md。
- 加 CI。

驗收：

- GitHub Actions tests PASS。

---

## Phase 2 — Pure Core Boundary

優先整理：

```text
combat_damage
combat_stats
player_stats
equipment calculation
skills
zones
```

要求：

- 無 Qt import。
- 無 UI callback。
- 可 headless test。

---

## Phase 3 — Event-driven Combat

導入：

```text
BattleEvent
```

逐步移除：

```text
Combat → UI direct calls
```

驗收：

- Battle 可完全 headless 跑完整 encounter。
- VFX / Sound 改為 event consumers。

---

## Phase 4 — Player / CombatManager 拆解

拆責任，但保持外部 API 相容。

可先用 façade：

```python
class CombatManager:
    def __init__(...):
        self.engine = BattleEngine(...)
```

舊 UI 先繼續呼叫 CombatManager。

內部逐步搬走。

---

## Phase 5 — Save Versioning

加入：

```text
schema_version
migration
validation
backup
```

驗收：

- 舊 save 可讀。
- 新 save 可存。
- migration 有 tests。

---

## Phase 6 — Portable Distribution

建立：

```text
runtime/
game/
launcher/
```

完成：

```text
start.bat
```

驗收：

- 全新 Windows 機器不安裝 Python也能啟動。

---

## Phase 7 — GitHub Release Builder

建立：

```text
build_release.py
```

輸出：

```text
Full.zip
Update.zip
```

---

## Phase 8 — Updater

完成：

```text
update.bat
updater.py
```

驗收：

- v1.0.0 → v1.0.1 可增量更新。
- saves 不變。
- update failure 可 rollback。

---

## Phase 9 — 繼續功能開發

完成以上架構後，才恢復：

- Gem
- Totem
- Hexa
- 新職業
- 新 Boss
- 新地圖
- 新裝備
- 新 UI

新功能直接遵循新 dependency boundary。

---

# 27. Definition of Done

此重構完成的標準：

1. `core/` 完全不依賴 Qt。
2. Battle 可 headless 跑。
3. DPS simulator 與 UI 共用同一 Combat Engine。
4. UI 僅透過 service / events 操作核心。
5. Save 有 schema version。
6. 舊 save 有 migration。
7. CI 自動跑 tests。
8. main 永遠可執行。
9. 玩家只需 `start.bat`。
10. 玩家可用 `update.bat` 更新。
11. Update 不覆蓋 saves/settings。
12. Runtime 與 Game 分離。
13. GitHub Release 有 Full / Update package。
14. 大多數新功能不需跨 5+ unrelated modules 修改。
15. Agent 可只讀特定 subsystem 即安全開發。

---

# 28. 最終架構原則

本專案不是為了追求 Enterprise Architecture。

目標是：

> 對一個長期個人遊戲專案而言，做到足夠低耦合、可測試、可擴充、可由 AI Agent 安全維護。

判斷重構是否有價值的標準不是「資料夾是否漂亮」，而是：

> 新增一個功能時，需要知道多少不相關系統？

理想情況：

```text
feature
  ↓
domain module
  ↓
service
  ↓
UI
  ↓
tests
```

而不是：

```text
feature
  ↓
Player
CombatManager
UI
Save
VFX
Audio
Global State
```

---

# 29. 建議 Agent 第一個任務

將本文件交給 Codex / Antigravity 後，第一個 Prompt 建議：

```text
請先不要修改任何功能。

閱讀整個 Maple Idle Python 專案與本重構計畫，
建立目前實際 dependency graph，特別分析：

1. Player
2. CombatManager
3. combat_damage / combat_stats
4. PySide UI
5. VFX
6. Save
7. DPS simulator

列出：
- circular dependencies
- Qt leaked into domain
- shared mutable state
- God objects
- local imports used to avoid cycles
- UI directly mutating game state

接著提出 Phase 0～Phase 3 的最小風險遷移順序。

先只產生分析文件，不修改 production code。
```

完成分析後，再要求 Agent 從最安全的 pure calculation module 開始搬遷。

---

# 30. 開發原則摘要

```text
Python / PySide6 = Main Game
Web             = Prototype / Reference

Game Rules      ≠ UI
Game State      ≠ Widget State
Combat          ≠ VFX
Save            ≠ Model
Runtime         ≠ Game Code
Release         ≠ Save Data

GitHub          = Source + CI + Releases
Portable Python = Distribution
BAT             = User Entry Point
Updater         = Incremental Delivery
Tests           = Refactor Safety Net
```
