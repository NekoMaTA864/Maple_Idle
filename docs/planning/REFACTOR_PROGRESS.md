# Refactor Progress

> Technical refactor and portable release pipeline completed through Milestone
> 5. GitHub Release v1.0.7 is prepared as an updater bootstrap hotfix.

## Current baseline

- Full test suite: 136/136 PASS.
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
- 136/136 tests PASS.
- Full / Update packaging ready.
- Save schema v1 ready.
- Silent DPS ready.
- GitHub Release v1.0.6 published.
- GitHub Release v1.0.7 prepared as an updater bootstrap hotfix.
- Remaining work after publishing and smoke-testing v1.0.7 is normal feature
  development only.

## v1.0.7 updater bootstrap hotfix

- Fix updater HTTP 403 caused by GitHub unauthenticated REST API rate limits.
- Update checks now use the public `releases/latest/download/version.json`
  release-asset path instead of GitHub REST latest-release lookup.
- No gameplay changes.
