# MapleIdle 模組化 VFX 交接與明日視覺複核指南

> 這份文件是給明天接手本專案的 Chat / Work / Codex 主持人使用的交接資料。
> 主持人的任務是先保護既有架構與邊界，再引導使用者完成視覺複核；不要把視覺原型直接擴張成新的戰鬥引擎。

## 1. 目前結論

截至本次交接：

- 正式專案根目錄：`C:\Users\User\Desktop\MapleIdle\Maple_Idle`
- 主線分支：`main`
- 已推送提交：`472bc9acd2f34a90ef65172af8a3183f493c20d9`
- 提交標題：`feat: add modular vertical combat VFX prototype`
- `main` 與 `origin/main` 已同步，工作樹乾淨
- 本次提交包含 8 個檔案：1,601 行新增、66 行刪除
- 本機驗證已通過：155/155 個 unittest、prototype 檔案 `py_compile`、`git diff --check`

這次提交代表「presentation-side 的垂直戰場與 VFX 模組化原型已經進入主線」，不代表所有正式技能的戰鬥語意、數值結算或完整職業技能都已完成。

視覺細節可以明天在另一個環境 pull 後再確認。除非視覺複核發現實際阻塞問題，主持人不應先行重寫架構或擴張正式戰鬥邏輯。

## 2. 明天第一步：拉取與驗證

在另一個環境中，先確認自己位於正確的專案根目錄：

```powershell
cd C:\Users\User\Desktop\MapleIdle\Maple_Idle
git switch main
git pull --ff-only origin main
git log -1 --oneline --decorate
git status --short --branch
```

預期最新提交是：

```text
472bc9a feat: add modular vertical combat VFX prototype
```

優先使用專案已驗證的測試命令：

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s src/tests
```

如果另一個環境沒有 `.venv`，才使用該環境已安裝的 Python：

```powershell
python -m unittest discover -s src/tests
```

Windows 目前的舊環境中，裸 `python` 可能指向 Windows Store alias；遇到這種情況，應建立/啟用虛擬環境，或改用環境中可用的 Python 直譯器，不要因為測試命令問題而改動專案測試架構。

## 3. 專案架構速覽

MapleIdle 是 Python + PySide6 的桌面放置 RPG，主要分層如下：

```text
pyside_main.py
  └─ pyside_ui.py / MainWindow
       ├─ ui_panels/       主畫面面板
       ├─ ui_dialogs/      裝備、技能、夥伴與系統對話框
       └─ ui_arena.py      QPainter 戰鬥畫布

combat_system.py / CombatManager
  ├─ combat_damage.py     傷害、暴擊、多段、護盾、治療
  ├─ monster_ai.py        怪物與首領行為
  ├─ combat_loot.py       掉落、經驗、金幣、樓層推進
  ├─ combat_zones.py      區域與怪物資料
  ├─ combat_output.py     Gameplay / Silent output sink
  └─ combat_vfx_manager.py 視覺效果生命週期與併發上限

vfx_core.py
  ├─ vfx_renderer.py
  └─ vfx/                 各職業既有 QPainter 向量效果

presentation prototype
  ├─ arena_layout.py      垂直戰場座標與 anchor
  ├─ combat_avatar.py     武器/職業符號 Avatar
  ├─ vfx_prototype.py     可重用的 presentation effect 與 presets
  ├─ ui_arena.py          將 prototype 接到正式畫布
  └─ tools/vfx_gallery.py 獨立 Debug Gallery
```

核心邊界：

- `CombatManager`、傷害公式、掉落、存檔與 DPS headless 執行屬於 domain/gameplay。
- `ui_arena.py`、`CombatAvatar`、`ArenaLayout`、prototype effects 屬於 presentation。
- Debug Gallery 使用最小的 mock view model，不讀取正式存檔，不建立正式戰鬥狀態。
- 既有 `CombatOutput`、`SilentCombatOutput`、`add_vfx()` 與戰鬥 RNG 順序必須保持相容。

## 4. 本次提交新增的模組

### `src/arena_layout.py`

集中管理垂直戰場座標，不讓 `ui_arena.py` 到處散落比例常數。

目前設計意圖：

- 敵人約在畫布上方 26% 的區域
- 主角約在畫布 62% 的區域
- 技能欄約在畫布 81% 的區域
- 位置依畫布大小自適應
- 保留 companion staging anchor，但正常畫面不顯示 `COMPANION SPACE`

### `src/combat_avatar.py`

純 presentation 的職業/武器型 Avatar，不儲存戰鬥數值。

目前 Avatar：

- `hero`
- `night_lord`
- `cannon`
- `bishop`

共用 anchor：

- `center`
- `attack_origin`
- `tip`
- `ground`

Cannon 額外有：

- `muzzle`

### `src/vfx_prototype.py`

純視覺效果 primitive 與資料驅動 preset：

- `SlashEffect`
- `ProjectileEffect`
- `AreaEffect`
- `LightningEffect`
- `ImpactEffect`

目前 preset：

- `hero_slash`
- `night_lord_shuriken`
- `cannonball_heavy`
- `bishop_holy_area`

這些 effect 不應攜帶 damage、cooldown、hit count、buff、progression 或戰鬥決策資料。視覺上的延遲手裏劍不是正式多段傷害；它只是 presentation timing。

### `src/combat_vfx_manager.py`

新增：

- `add_effect(effect)`：加入 prototype effect，沿用 manager 的生命週期與併發上限
- `clear()`：清除 presentation effects

不要刪除或改寫舊的 `add_vfx()` 行為，因為它仍受既有 CombatOutput 與 RNG characterization tests 保護。

### `src/ui_arena.py`

把新的 layout、Avatar、技能欄、區域效果、travel effect 與 impact effect 接到既有 QPainter 戰鬥畫布。

目前是「單一主角視覺核心」的垂直戰場展示：正式 team state 仍存在於 gameplay model，但畫布 prototype 不建立七個永久角色 renderer。

### `src/tools/vfx_gallery.py` / `src/tools/run_vfx_gallery.py`

Debug Gallery 以 `CombatArenaWidget`、`ArenaLayout`、`VisualEffectManager` 和共用 prototype presets 為基礎，避免做第二套 renderer。

啟動命令：

```powershell
.\.venv\Scripts\python.exe src\tools\run_vfx_gallery.py
```

Gallery 應被視為安全的視覺複核工具，不應讀檔、不應改存檔、不應執行正式掉落或戰鬥結算。

### `src/tests/test_vfx_prototype.py`

目前有 19 個 prototype-focused tests，涵蓋：

- 垂直座標與任意畫布尺寸
- Avatar anchor 綁定
- 四種 preset
- effect lifecycle 與到達目標後的 impact
- manager cleanup
- global gameplay RNG 不被 presentation seed 消耗
- Gallery 不具有正式 CombatManager 狀態

## 5. Anchor 與效果綁定表

| Avatar / preset | 起點 anchor | 目標 anchor | 說明 |
| --- | --- | --- | --- |
| Hero / `hero_slash` | `hero.tip` | `enemy.hit` | 近戰斬擊 |
| Night Lord / `night_lord_shuriken` | `night_lord.attack_origin` | `enemy.hit` | 手裏劍投擲 |
| Cannon / `cannonball_heavy` | `cannon.muzzle` | `enemy.hit` | 炮彈與命中爆炸 |
| Bishop / `bishop_holy_area` | `bishop.tip` | `enemy.ground` | 地面聖域效果 |

如果視覺上出現偏移，優先檢查 anchor 與 `ArenaLayout`，不要直接把座標硬編碼到各個 skill renderer。

## 6. 明日視覺複核流程

主持人應先讓使用者觀察，再討論修改，不要一開場就改程式。

### A. 場景構圖

- 敵人是否明確位於上方？
- 主角是否穩定位於下方？
- 敵人到主角之間是否保留足夠 travel space？
- 技能欄是否靠近主角但沒有壓住 Avatar 或 HP bar？
- 畫布縮放後，四個區域仍是否清楚？

### B. Avatar 與資訊層級

- Hero 是否像劍，而不是低品質人形 sprite？
- Night Lord 是否能辨認手裏劍/盜賊符號？
- Cannon 是否能看出炮口、後座與炮彈方向？
- Bishop 是否有明確的法杖/神聖焦點與地面效果？
- 名稱、HP bar、BOSS/ELITE 標籤是否是輔助資訊，而不是搶過特效？
- 正常 Arena 是否沒有不必要的 debug anchor 或 `COMPANION SPACE` 標記？

### C. 技能效果與節奏

- 起點是否真的從正確 weapon anchor 出發？
- travel 方向是否能支援任意 source-to-target 座標，而不是只假設橫向？
- 命中瞬間是否看得出 flash、ring、burst、fade？
- Area effect 是否落在 enemy ground，而不是浮在角色中心？
- 三枚延遲手裏劍是否看起來是視覺節奏，而不是誤導成正式三段傷害？
- cooldown / READY 顯示是否易讀？

### D. 工程安全檢查

- Gallery 是否只使用 mock state？
- 是否沒有讀取 save、loot、progression 或正式 CombatManager 戰鬥狀態？
- 是否沒有改變 `CombatManager`、`combat_damage`、`SilentCombatOutput` 的行為？
- 是否沒有改變 module-level gameplay RNG 或 popup jitter 的消耗順序？
- effect 是否會正常過期並從 manager 清除？

## 7. 主持人的變更分類規則

使用者提出新要求時，先把要求分類：

### A 類：安全的視覺參數調整

例如：

- 顏色、透明度、尺寸、角度、動畫速度
- Avatar 的 offset 或 anchor 微調
- UI label、技能欄間距、Arena 比例
- impact 的 ring / flash / particle 強度

這類可以在視覺複核後直接提出小範圍修改。

### B 類：presentation contract 調整

例如：

- 新增一個共用 effect primitive
- 新增一個資料驅動 preset
- 擴充 `VisualEffectManager.add_effect()` 的 presentation 生命週期
- 讓 Gallery 與正式 Arena 共用同一個 renderer

這類需要先確認是否仍維持低耦合、可測試、資料驅動與 presentation-only。

### C 類：gameplay / domain 變更

例如：

- 讓特效直接決定傷害、命中、暴擊、冷卻或掉落
- 修改 CombatManager 的 tick order
- 修改 CombatOutput / SilentCombatOutput 的 RNG 行為
- 把 Gallery 接上存檔或正式戰鬥狀態
- 為每個職業或每個技能建立獨立 renderer 子類別
- 引入 ECS、EventBus、AnimationGraph、Timeline DSL 或 BattleEngine

這類必須先停下來，向使用者說明它已超出本次 presentation 模組範圍，取得明確決策後才可繼續。

## 8. 不要做的事

- 不要 `git reset --hard`、刪除未確認檔案或重置使用者的視覺調整。
- 不要在視覺複核前把 prototype 改成正式技能結算系統。
- 不要為了測試方便安裝 pytest；專案目前使用 unittest。
- 不要只提交 `ui_arena.py` 而漏掉它依賴的新模組。
- 不要把本機 `main` 變更推到 `visual-sandbox-company`。
- 不要把 GitHub Pages showcase 的 web layer 與 PySide6 desktop layer 混成同一個 renderer。
- 不要因為 README 仍寫著 48 個測試，就把實際通過的 155 個測試降回舊數字；文件數字應另行更新。

## 9. 遠端分支背景

目前 GitHub 上有另一條工作線：`visual-sandbox-company`。

它的方向是獨立的 `visual_sandbox/` Python prototype 加上 `showcase/` 靜態 GitHub Pages 展示，曾有自己的 showcase commits 與部署。它不是本次 `src/` presentation prototype 的替代品，也不是明天視覺複核時需要同步修改的目標。

明天只先使用：

```text
main @ 472bc9a
```

如果未來要合併兩條工作線，應另開一個架構比較與整合任務，先處理責任邊界、測試策略與重複 renderer 問題，不要在視覺複核中順手合併。

## 10. CI 注意事項

遠端 `main` 在本次提交之前曾有既有的 GitHub Actions `Run Tests` 失敗紀錄；本機使用 Python 3.10.6 的完整 155 tests 是通過的，而遠端 workflow 使用 Python 3.12 與 `requirements.txt`。

因此主持人明天應分開判斷：

1. 本機/另一環境是否能成功 pull、啟動 Gallery、通過 unittest。
2. GitHub Actions 新 run 是否通過，以及失敗是否來自 Python/依賴/CI 環境差異。

不要把舊的 CI 紅燈直接解讀成這次 VFX prototype 必然錯誤；但若新 run 仍失敗，應在正式合併更多功能前建立獨立的 CI 修復事項。

## 11. 可直接轉交給 Chat / Work 的主持人提示詞

以下文字可以直接貼給新的主持人：

```text
你是 MapleIdle 專案的架構與視覺複核主持人。

請先閱讀：
1. docs/planning/MODULAR_VFX_HANDOFF.md
2. docs/architecture/ARCHITECTURE.md
3. docs/planning/REFACTOR_PROGRESS.md

目前主線是 main @ 472bc9a：
feat: add modular vertical combat VFX prototype

本次已完成的是 presentation-side 模組化：ArenaLayout、CombatAvatar、
vfx_prototype effects/presets、VisualEffectManager 的 presentation API、
垂直 CombatArenaWidget 整合、Debug Gallery 與 19 個 focused tests。
完整 unittest 目前已通過 155/155。

你的工作順序：
1. 先確認目前目錄、分支、HEAD 與 git status。
2. 確認 pull 到 main @ 472bc9a。
3. 執行 .venv\\Scripts\\python.exe -m unittest discover -s src/tests。
4. 啟動 .venv\\Scripts\\python.exe src\\tools\\run_vfx_gallery.py。
5. 先引導使用者觀察構圖、Avatar 辨識度、anchor、travel、impact、技能欄與清理生命週期。
6. 把發現分成「視覺參數」、「presentation contract」、「gameplay/domain」三類。
7. A 類可提出小修改；B 類先檢查低耦合與測試；C 類必須停下來請使用者決策。

請嚴格保持以下邊界：
- 不改 CombatManager、傷害公式、掉落、存檔或正式戰鬥 tick order。
- 不改 SilentCombatOutput 或既有 RNG 消耗順序。
- 不把 Gallery 接上正式存檔或正式戰鬥狀態。
- 不引入 ECS、EventBus、AnimationGraph、Timeline DSL、BattleEngine，
  也不要建立每職業/每技能的 renderer 子類別。
- 不 reset、discard、commit 或 push，除非使用者明確要求。

每次回報都請說清楚：
- 目前觀察到的事實
- 這是視覺問題還是架構問題
- 是否需要修改程式
- 修改會觸及哪些檔案與邊界
- 下一個最小、可驗證的步驟
```

## 12. 交接結束條件

明天視覺複核完成後，主持人應把狀態標成以下其中一個：

- `READY FOR SECOND VISUAL REVIEW`：結構與視覺方向可繼續，暫不需改程式。
- `NEEDS PRESENTATION CALIBRATION`：只需要小幅調整色彩、比例、anchor 或 timing。
- `BLOCKED BY DOMAIN DECISION`：需求已觸及正式戰鬥/數值/存檔邊界，必須由使用者決定是否擴 scope。

在沒有明確視覺結論前，最安全的下一步是記錄觀察與優先級，而不是增加更多技能語意或新的架構層。
