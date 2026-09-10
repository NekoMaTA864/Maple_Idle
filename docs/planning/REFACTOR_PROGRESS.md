# Refactor Progress Checkpoint

> Checkpoint: before Milestone 3 Combat Output Boundary implementation.

## Current baseline

- Full test suite: 84/84 PASS.
- Milestone 1 — Combat Safety Net: completed.
- Milestone 2 — UI Mutation Boundary: completed.
- Milestone 3 Architecture Review: completed.
- Milestone 3 implementation: **not started**.

## Milestone 3 accepted design

- Use a synchronous, narrow `CombatOutput` sink.
- Provide `GameplayCombatOutput` for the existing UI/VFX/audio/log behavior.
- Provide `SilentCombatOutput` for DPS and headless execution.
- Do not introduce a `BattleEvent` hierarchy.
- Do not introduce an event queue.
- Do not rewrite `CombatManager`.

The sink remains an immediate adapter: combat calls it at the current call site and in the current order. It is not a deferred event collector.

## Migration sequence

1. **3A — Output-order characterization**
2. **3B — VFX / audio sink**
3. **3C — Popup / log / shake ownership**
4. **3D — Silent DPS**

## Critical regression risks

- `VisualEffect` currently consumes module-level `random`.
- Popup jitter consumes `CombatManager.rng`.
- A silent output must preserve every required RNG consumption.
- Side effects must remain synchronous.
- Battle tick order, `PendingHit` ordering, and kill -> loot -> spawn ordering must not change.

## Next action

Start **Slice 3A — Output-order characterization**.

Do not start Slice 3B until the 3A characterization tests are complete and passing.
