# Refactor Progress

> Technical refactor and portable release pipeline completed through Milestone
> 5. GitHub Release v1.0.6 is prepared for manual publication.

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

## Final Status

- Milestone 1 completed.
- Milestone 2 completed.
- Milestone 3 completed.
- Milestone 4 completed.
- Milestone 5 completed.
- Technical refactor completed.
- Portable release pipeline completed.
- Safe updater completed.
- 129/129 tests PASS.
- Full / Update packaging ready.
- Save schema v1 ready.
- Silent DPS ready.
- GitHub Release v1.0.6 prepared for publication.
- After the first manual GitHub Release and real-world updater smoke test,
  remaining work is normal feature development only.
