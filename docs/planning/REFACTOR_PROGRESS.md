# Refactor Progress

> Technical refactor completed through Milestone 5. The remaining release work
> is a first manual GitHub Release and a real-world updater smoke test.

## Current baseline

- Full test suite: 129/129 PASS.
- Milestone 1 — Combat Safety Net: completed.
- Milestone 2 — UI Mutation Boundary: completed.
- Milestone 3 Architecture Review: completed.
- Milestone 3 Combat Output Boundary: completed.
- Milestone 4 — Façade Stabilization: completed.
- Milestone 5 — Persistence and Portable Release Hardening: completed.

## Milestone 3 accepted design

- Use a synchronous, narrow `CombatOutput` sink.
- Provide `GameplayCombatOutput` for the existing UI/VFX/audio/log behavior.
- Provide `SilentCombatOutput` for DPS and headless execution.
- Do not introduce a `BattleEvent` hierarchy.
- Do not introduce an event queue.
- Do not rewrite `CombatManager`.

The sink remains an immediate adapter: combat calls it at the current call site and in the current order. It is not a deferred event collector.

## Migration sequence

1. **3A — Output-order characterization**: completed.
2. **3B — VFX / audio sink**: completed.
3. **3C — Popup / log / shake ownership**: completed.
4. **3D — Silent DPS**: completed.

## Critical regression risks

- `VisualEffect` currently consumes module-level `random`.
- Popup jitter consumes `CombatManager.rng`.
- A silent output must preserve every required RNG consumption.
- Side effects must remain synchronous.
- Battle tick order, `PendingHit` ordering, and kill -> loot -> spawn ordering must not change.

## Milestone 3 result

- `GameplayCombatOutput` owns VFX, popup, log, and shake presentation state.
- `SilentCombatOutput` runs DPS headlessly without presentation collections while preserving visual and popup RNG consumption.
- Gameplay/Silent domain and RNG parity are covered by characterization tests.
- Legacy `CombatManager` presentation-facing façade remains compatible for the existing UI.

## Release status

- Full and Update portable ZIPs, SHA-256 checksums, `version.json`, and the
  safe foreground updater are implemented and covered by tests.
- Remaining task: manually publish the first GitHub Release, then smoke-test
  `start.bat` and `update.bat` from a clean extracted Full package.
