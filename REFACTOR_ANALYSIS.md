# Maple Idle 實測架構審計與重構基線

> 審計日期：2026-09-10  
> 範圍：目前 `src/`、測試、啟動／CI／存檔與指定規劃文件。本文以實際程式碼為準，不以先前分析中的數字或結論作為事實來源。

## Baseline

- 執行環境：內附 Python 3.12.10、pygame 2.6.1。
- 命令：`runtime\python\python.exe -m unittest discover -s src/tests -p "test_*.py" -v`
- 結果：48 tests，全部通過，1.610 秒。
- Git 工作樹目前不能建立 baseline tag：`git status --short` 回報 `.git/index: index file smaller than expected`。此為 repository metadata 損壞；本輪未修復、未寫入 Git。
- `.gitignore` 已排除 `runtime/`、`saves/`、`src/saves/`、`logs/`、scratch 與發行產物。實際預設存檔位置仍是 `src/saves/savegame.json`，尚未遷到根目錄 `saves/`。

## 實際結構與邊界

- 產品入口是 `src/pyside_main.py`，Qt 主視窗是 `pyside_ui.MainWindow`；QTimer tick 呼叫 `CombatManager.update(dt, sound_mgr)`。
- 領域／遊戲檔案沒有直接 import `PySide6`；Qt imports 位於 `pyside_*`、`ui_*`、`vfx_*` 與工具。這是良好起點，但不表示戰鬥已和表現解耦。
- `combat_damage`、`monster_ai`、`combat_loot` 會直接寫 `CombatManager.vfx_mgr`、座標、screen shake、floating popups、彩色 log，並呼叫傳入的 `sound_mgr`。因此目前是「無 Qt import」，不是「無 presentation side effect」的 Battle Core。
- `CombatArenaWidget` 直接讀取 `combat_mgr.vfx_mgr.effects` 和 `combat_mgr.floating_popups`；這些都是 mutable presentation state。

## Player / PlayerData

`Player` 有 61 個方法、`TeamMember` 有 26 個方法。`Player` 同時保存並操作帳號進度、裝備／背包、25 欄位強化資料、符號、7 人隊伍、buff、寵物、萌獸、內在能力、聯盟、升級、存檔委派；它是實際的 aggregate/facade，仍是 God object。

`TeamMember` 也同時含職業／技能 loadout、攻擊計時、職業 runtime 狀態，並透過主角代理 HP／shield。這個「單一生存池」規則是既有契約，拆分時不能誤改成七個獨立生命池。

先前的 module split 已存在（`player_stats`、`player_gear`、`player_symbols`、`player_save`），但 `Player` 仍擁有 public forwarding methods 和跨系統 mutation；下一步應優先建立明確的操作邊界，而非急著搬檔案或重命名模型。

## Combat 與 DPS

`CombatManager` 有 23 個方法，持有 encounter／zone／floor、monster waves、timer／boss phase、pending hits、CombatStats、VFX、popup、log、screen shake 與休整狀態。它確實是 battle-loop orchestrator，但也持有 presentation state。

`combat_damage` 包含技能選擇、傷害公式、ARC/AUT、暴擊、DoT、heal、shield、buff、multi-hit 排程及 presentation/audio 呼叫；`monster_ai` 同樣混合 AI、傷害、狀態改變和 presentation；`combat_loot` 混合獎勵、進度、物品／寵物／符號 mutation、log/popup/audio。`combat_stats.py` 則是獨立 dataclass 統計模型，是最乾淨的 combat 模組。

`dps_calculator.run_dps_simulation()` 建立同一個 `Player` 與 `CombatManager`，以 `SilentSound` 呼叫同一個 `CombatManager.update()`；因此正式戰鬥規則沒有另寫一套 DPS damage loop。它仍會建立 VFX/popup 等 state，也沒有注入 RNG：combat、loot、monster、item 等散用 module-level `random`。所以「同一核心」成立，「deterministic、純無表現模擬」尚不成立。

## Circular imports 與 local imports

對 76 個非測試、非 scratch Python modules 的 AST 掃描得到 150 條內部 import edges。包含函式內 imports 的 project-level SCC 有兩組：

1. `item_system <-> item_gachapon`：前者頂層 re-export gachapon API；後者在 `draw_gachapon()` 局部 import `Item`／`create_seed_ring`。
2. `player_data <-> player_save`：前者頂層 import save module 作 forwarding；後者在 load 時局部 import `TeamMember`。

共有 39 個 production local imports（排除 `src/scratch/`；包含標準庫、Qt 與專案 imports）。它們不能一概視為 bug：例如 lazy Qt dialog import 可以是啟動成本或 UI package cycle 的合理策略；`uuid`／`random` 的函式內 import 也不是 circular-import workaround。優先處理上述兩個真實 cycles，並逐一為其餘 local import 記錄原因；不要設定「消除所有 local imports」作為目標。

## Shared mutable state、UI mutation、Qt

- `sound.sound_mgr` 是 module-level singleton；戰鬥本身沒有 import 它，而是由呼叫端傳入。因此比舊報告描述得好一些，但 audio port 仍和 battle function signatures 與流程耦合。
- module-level catalog data（zones、職業、item／pet tables）主要是設定資料；目前沒有證據顯示它們在 runtime 被寫入。不可與真正的 global mutable runtime state 混為一談。
- `pyside_ui.py` 直接改 `repeat_current_zone`（252、261、270、272、276），並直接扣／加 `gold`、改 `abby_scrolls`、`cube_inventory`、`familiar_cubes`、寵物與寵物裝備（約 546–682）。這是最清楚、最適合 service 化的 UI 穿透 mutation。
- UI 的一般裝備、符號、隊伍操作多數已經呼叫 Player methods；不應誇大成「所有 UI 操作都繞過 domain」。
- 未發現 Qt leak 到 domain/core imports；但 VFX 是 Python presentation code，並非 domain。`combat_vfx_manager.PendingHit` 把 combat queue model 放在 VFX 模組，是語意方向錯置，即使它本身不 import Qt。

## Save / Load 與發行

`player_save.py` 做 JSON I/O、schema reconstruction、舊欄位 fallback、offline progression，以及在帶 `combat_mgr` 時直接還原 zone/floor。它沒有 `schema_version`、顯式 migration registry、validation、atomic write 或 backup。舊存檔相容是以 scattered `dict.get()` fallback 實作，已有行為必須先被 characterization tests 固定。

Portable BAT 方案已可用，但 `requirements.txt` 是 `>=` 範圍，並非 release lock；CI 僅跑 unittest。Full/Update packaging、checksum、updater、rollback、logs 都尚未實作。Web 應從規劃中移除：不保留 prototype 相容責任，也不做 web migration。

## 對既有計畫的判斷與修正

我同意其核心方向：Python + PySide6 唯一正式主線、不要大爆炸重寫、以行為不變／測試／save migration／Portable Releases 為約束，並將 presentation/audio 與 battle rules 分離。

需要修正的部分：

- 目標目錄樹是遠期參考，不能作為初期交付物；先建立邊界與相容 facade，再在有明確收益時搬檔案。
- Phase 2 不應要求消除所有 local imports；只消除被驗證的 cycle 或已造成問題的 import。
- Event-driven combat 前先加 seedable RNG seam 和 golden/characterization cases。否則無法證明 event 化沒有改變暴擊、掉落、boss AI 與 multi-hit 結果。
- 「DPS 與正式 Combat 共用同一核心」已基本成立，應把工作改為移除其 VFX/popup allocation、建立同種子可重播驗證，而非另建第二個 engine。
- Save schema versioning 不應等到最後；它可在不搬資料夾的前提下獨立、小步完成。但先只加 version=1／no-op migration 和 read/write regression，避免同一 slice 同時改路徑、資料模型、release layout。
- 不應在尚無更新器前重排玩家目錄或把 runtime/game 強制搬位；目前 release 工作只能先做可重現 build manifest 與 package smoke test。

## 低風險到高風險執行順序

1. 補 characterization/golden tests：固定 seed、戰鬥輸入／輸出、save fixtures；保留現有 public API。
2. 抽純 `combat_events`／`combat_models`：先搬 `PendingHit` 等不含 Qt 的資料型別，舊 import 保留 re-export，零行為改變。
3. 引入 injected RNG（default 為現行 nondeterministic random），逐步替代 combat／AI／loot 的 module random；用第 1 步 golden 驗證。
4. 將 battle output 收集成 events／sink，先與現有 VFX、popup、log、audio side effects 並行，最後讓 Qt/audio 成為 consumers。DPS 改為不建立 presentation state。
5. 封裝 UI shop 與 repeat-zone mutations 成 application services／commands；UI 只處理回傳結果與呈現。
6. 以 facade 保持 API，逐步縮小 Player／CombatManager；先處理已驗證的兩個 cycles。
7. 加入 explicit save schema、migrations、validation、atomic backup，以及舊 save regression fixtures。
8. 建立 locked dependencies、release build、Full/Update packages、checksum、rollback updater；再調整發行目錄。

## 第一個適合實作的 refactor slice

**Slice：建立純 `combat_events.py`，將 `PendingHit` 移入其中，並由 `combat_vfx_manager` re-export 以保持舊 import 相容。**

範圍限定為：新增 queue payload、修改 `combat_damage`／`combat_system` 的 import，保留 `combat_vfx_manager.PendingHit` alias，補 import compatibility 與 pending-hit behavior tests。不改 attack formula、tick ordering、VFX rendering、audio、UI 或 save。

理由：它只修正「combat queue model 位於 VFX namespace」的依賴方向，觸及面小、可回歸、是後續 event output 的自然落點；比一開始抽整個 BattleEngine、Player aggregate 或 shop service 更低風險。
