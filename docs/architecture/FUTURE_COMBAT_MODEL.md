# Future Combat Model

## Goal

未來戰鬥方向採：

1 Full Player Character
+ 3 Companions
+ optional Summon/Special Slot

## Player

- 唯一完整角色
- 有 HP / DEF / gear / skills / class mechanic
- 死亡代表戰鬥失敗
- Active skill pool 6，裝備 4
- Class mechanics / passives 2

## Companion

- 不使用完整 Player model
- 不配置完整裝備
- 不承擔主角級 HP/DEF/state
- 主要提供：
  - Passive
  - Assist Skill ×2
  - Ultimate ×1
- 可具有 cooldown / resource，但應保持簡化

## Summon

- Temporary combat entity
- 由 Player skill 或 Companion skill 建立
- 不應被建模成完整 Player

## Enemy

- Normal
- Elite
- Boss

## Refactor Constraint

Current refactor must not harden assumptions that every party member is a full Player-equivalent combatant.

現階段：
- 不重寫現有 Party 系統
- 不立即實作 Companion
- 不為新玩法修改 gameplay
- 只確保新的 abstraction 不阻礙未來此方向