# Class Skill System v0.1

> Status: gameplay design direction only. This document does not authorize a
> production implementation, a generic skill framework, or a Player/Combat
> architecture rewrite.

## Purpose

Define a small, identity-first class and companion model that can be pressure
tested with six representative classes before extending it to the remaining
eighteen classes. The goal is readable idle combat with recognizable TMS-facing
class identity, not symmetrical skill counts or live-server DPS replication.

## Battle Composition

Each battle has:

- **1 Full Player**
- **3 Companions**
- an optional **Summon / Special Slot**

The Player is the only full combatant. It owns HP, DEF, gear, class mechanics,
and the class skill loadout. A Companion must **not** implement the complete
Player interface or duplicate the Player's gear, HP/DEF, or six-skill combat
loop.

The initial balance direction is Player value of roughly **60–70%** and the
three Companions together at roughly **30–40%**. This is a starting target for
playtesting, not a fixed formula or a promise that every encounter has exactly
that split.

## Player Class Kit

Each class has:

- **2 Core Mechanics**
- an **Active Skill Pool of 6**
- **4 equipped Active Skills** selected from that pool

Core Mechanics do not consume equipped skill slots. The six Active Skills do
not need to fit a fixed role template, but may cover a main attack, resource
tool, burst, AoE/field/summon, utility, and signature action. Class identity is
more important than a perfectly symmetric list.

## Companion Kit

For each class-facing Companion kit, define:

- **1 Passive**
- **1 Assist**
- **1 Ultimate**

Companions are intentionally smaller kits. They do not use a complete Player
equipment system, HP/DEF model, or six-active rotation.

## Auto Battle

Every skill definition must be able to express at least:

- `cooldown`
- `priority`
- `condition`
- `resource_cost`
- `resource_gain`
- `target`
- `effects`

The default auto-battle rule is: choose a usable skill by its condition and
priority. High-operation classes such as Blaster and Thunder Breaker must turn
manual APM demands into automatic combo/resource mechanics. Maple Idle must not
require high-APM manual input to preserve those classes' identities.

## Skill Data Direction

The minimum common skill fields are:

```text
id
name
class_id
kind
cooldown
priority
hits
multiplier
target_count
tags
resource_cost
resource_gain
condition
effects
vfx_key
notes
```

This is a practical shared data shape, not a commitment to a complex generic
framework, DSL, or event language. Class-specific mechanics may remain
explicit, small Python logic when data alone would make their behavior obscure.

## Skill Selection Priority

When deciding whether a TMS-recognizable skill belongs in Maple Idle, use this
order:

1. Class identity
2. TMS-recognizable skill or visual
3. Gameplay differentiation
4. Interaction with Core Mechanics
5. Useful combat role
6. Current live-server DPS contribution

Live-server DPM alone is never sufficient reason to include a skill.

## Identity Guardrails

- **Hero** must not become an Aran-style combo-counter class. Its TMS-facing
  core is Fighting Spirit / Aura and Aura Blade or Aura Orb behavior.
- **Fire/Poison** keeps DoT, Poison, and Detonation.
- **Flame Wizard** must not become a second Fire/Poison.
- **Buccaneer** keeps Sea Serpent.
- **Cannoneer** keeps giant cannon, Monkey, and Buckshot / dense-number
  identity.
- **Thunder Breaker** keeps sea-and-lightning chaining.
- **Blaster** keeps Bullet, Cylinder, and combo rhythm.
- **Battle Mage** keeps melee staff, dark magic, and Aura.
- **Wild Hunter** keeps crossbow and Jaguar cooperation.
- **Mechanic** keeps mech, missiles, and deployable robots.

## Prototype Class Pressure Test

The first six class designs are deliberately chosen to pressure the model in
different ways:

| Class | Model pressure it should test |
| --- | --- |
| Hero | Fighting Spirit / Aura identity without a manual combo counter |
| Bishop | support, recovery, buffs, and a companion-friendly combat role |
| Night Lord | burst windows, mark/projectile identity, and priority decisions |
| Cannoneer | dense projectile output, Monkey, and field/summon readability |
| Blaster | automated Bullet/Cylinder combo rhythm and resource abstraction |
| Battle Mage | melee caster range, Aura ownership, and dark-magic effects |

Do not finalize the remaining eighteen classes until all six can naturally use
the model without requiring a fake full-Player Companion, a special-purpose
skill framework, or an identity-breaking simplification.

## Per-Class Design Template

Every class design uses this template. v0.1 records the template and pressure
test set; it intentionally does not yet select final numbers, cooldowns, or
live skill lists.

### Identity

- Short statement of what a player should immediately recognize.

### Core Mechanic 1

- **Trigger / resource:**
- **Gameplay effect:**
- **Visual:**

### Core Mechanic 2

- **Trigger / resource:**
- **Gameplay effect:**
- **Visual:**

### Player Active Pool ×6

| Slot | Skill | Role / interaction | Auto-battle condition |
| --- | --- | --- | --- |
| 1 | | | |
| 2 | | | |
| 3 | | | |
| 4 | | | |
| 5 | | | |
| 6 | | | |

### Recommended Equipped ×4

-

### Companion

- **Passive:**
- **Assist:**
- **Ultimate:**

### Tags

-

### Do-not-break Identity

-

### Open Balance Questions

-

## Prototype Design Records

The following six records must be completed using the template above before
class-system implementation begins:

1. Hero
2. Bishop
3. Night Lord
4. Cannoneer
5. Blaster
6. Battle Mage

Their purpose is to answer the open questions below through concrete class
design, rather than choosing abstract architecture prematurely.

## Open Questions

Do not lock these decisions before the six prototype designs have exposed the
real trade-offs:

1. Is Companion Ultimate cooldown-based, conditional, or powered by a shared
   Team Gauge?
2. Are all four Player equipped skills automatic, or should one future slot be
   reserved for a manual Ultimate?
3. Is the Summon / Special Slot shared by every class, or shown only by certain
   builds?
4. How much class-resource complexity remains readable in idle combat?
5. Is a Companion Passive permanently active?
6. How should Companion progression work without copying the Player equipment
   system?

## Implementation Guardrails

- Do not make Companion a complete Player-equivalent type.
- Do not require every class to have the same six-role template.
- Do not introduce a generic skill DSL, event framework, or a new architecture
  merely to represent this v0.1 design.
- Do not use current live-server DPS ranking as the primary skill-selection
  rule.
- Resolve the open questions through the six concrete prototype designs first.
