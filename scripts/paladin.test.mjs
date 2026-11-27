import assert from 'node:assert/strict';
import test from 'node:test';
import {
  BOSS_ORDER, DEFAULT_ORDER, PITY, addDrop, finishBattle, newSave, readSave, reforge, reroll, settleOffline,
  startBattle, stats, tick,
} from '../showcase/play/rules.mjs';

import { swingGeometry, sample } from '../showcase/play/brushes.mjs';

const fixed = () => .5;

function fight(save, stage) {
  const battle = startBattle(save, stage);
  while (!tick(battle)) {}
  return battle;
}

test('push goes through 3 stages, automatically attempts the boss once and stops on loss', () => {
  const save = newSave(0);
  save.running = { stage: 0, mode: 'push' };
  for (let stage = 0; stage < 3; stage++) {
    assert.equal(save.running.stage, stage);
    const battle = fight(save, stage);
    assert.equal(battle.result, 'win');
    assert.ok(finishBattle(save, battle, fixed));
    assert.equal(finishBattle(save, battle, fixed), null);
  }
  assert.deepEqual(save.bag.map(item => item.slot), ['weapon', 'shield', 'armor']);
  assert.deepEqual(save.running, { stage: 3, mode: 'boss' });
  assert.equal(save.firstBoss, true);
  const boss = fight(save, 3);
  assert.equal(boss.result, 'loss');
  finishBattle(save, boss, fixed);
  assert.equal(save.running, null);
  save.running = { stage: 2, mode: 'farm' };
  finishBattle(save, fight(save, 2), fixed);
  assert.deepEqual(save.running, { stage: 2, mode: 'farm' });
});

test('priority changes opening damage and boss clear time with the same build', () => {
  const save = newSave(0);
  save.order = [...BOSS_ORDER];
  const shieldFirst = fight(save, 3);
  save.order = ['strike', 'guard', 'break', 'heal'];
  const strikeFirst = fight(save, 3);
  const opener = battle => battle.events.filter(event => event.kind === 'cast').slice(0, 2).map(event => event.source);
  assert.deepEqual(opener(shieldFirst), ['guard', 'strike']);
  assert.deepEqual(opener(strikeFirst), ['strike', 'guard']);
  assert.equal(shieldFirst.result, 'win');
  assert.equal(strikeFirst.result, 'win');
  assert.ok(shieldFirst.time < strikeFirst.time);
  assert.ok(shieldFirst.events.some(event => event.kind === 'ice'));
  assert.ok(shieldFirst.events.some(event => event.kind === 'buff' && event.source === 'heal'));
  assert.ok(shieldFirst.events.find(event => event.kind === 'hit' && event.source === 'strike').title.endsWith('62'));
  assert.ok(strikeFirst.events.find(event => event.kind === 'hit' && event.source === 'strike').title.endsWith('44'));
  save.order = [...DEFAULT_ORDER];
  Object.keys(save.levels).forEach(slot => { save.levels[slot] = 2; });
  assert.equal(fight(save, 3).result, 'win');
});

test('drops vary, switching items inherits the slot upgrade, and pity respects a locked affix', () => {
  const save = newSave(0);
  const first = addDrop(save, 'shield', () => 0);
  const second = addDrop(save, 'shield', () => .99);
  assert.notEqual(first.flame, second.flame);
  for (const item of [first, second]) {
    save.equipped.shield = item.id;
    save.levels.shield = 0;
    const base = stats(save).reduction;
    save.levels.shield = 2;
    assert.equal(stats(save).reduction, base + 2);
  }
  first.locked = 0;
  const locked = { ...first.affixes[0] };
  save.dust = 4;
  assert.equal(reforge(save, first, 'haste', fixed), false);
  for (let i = 0; i < PITY; i++) assert.ok(reroll(save, first, fixed));
  assert.equal(save.pity, PITY);
  assert.equal(reforge(save, first, 'expose', fixed), false);
  assert.ok(reforge(save, first, 'haste', fixed));
  assert.deepEqual(first.affixes[0], locked);
  assert.deepEqual(first.affixes[1], { key: 'haste', value: 1 });
  assert.equal(save.dust, 0);
  assert.equal(save.pity, 0);
});

test('offline accrues only while stationed, caps at 120 minutes and survives reloading without duplication', () => {
  const minute = 60_000;
  let save = newSave(0);
  assert.equal(settleOffline(save, 15 * minute, fixed), null);
  save.resident = true;
  save.best = 1;
  const restored = readSave(JSON.stringify(save));
  assert.deepEqual(settleOffline(restored, 30 * minute, fixed), { minutes: 15, gold: 30, dust: 15, drops: 1 });
  save = readSave(JSON.stringify(restored));
  assert.equal(settleOffline(save, 30 * minute, fixed), null);
  assert.equal(settleOffline(save, 29 * minute, fixed), null);
  assert.equal(save.savedAt, 30 * minute);
  assert.deepEqual(settleOffline(save, 210 * minute, fixed), { minutes: 120, gold: 240, dust: 120, drops: 8 });
  assert.equal(save.bag.length, 9);
});

test('swings bend along the normal, stay within safe bounds, and use exact static midpoints', () => {
  const bounds = { width:390, top:32, bottom:260 };
  for (const [kind, lo, hi] of [['strike',34,54], ['counter',28,44], ['basic',18,32]]) {
    const geometry = (value, reduced = false, side = -1) => swingGeometry(kind,
      {x:195,y:230}, {x:52,y:58}, bounds, side, reduced, () => {
        if (reduced) assert.fail('static rendering sampled RNG');
        return value;
      });
    assert.equal(geometry(0).bend,lo);
    assert.equal(geometry(1).bend,hi);
    const {a,b,c,bend} = geometry(0,true);
    assert.equal(bend,(lo+hi)/2);
    const dx = c.x - (a.x+b.x)/2, dy = c.y - (a.y+b.y)/2;
    assert.ok(Math.abs(dx*(b.x-a.x)+dy*(b.y-a.y)) < 1e-7);
    assert.ok(Math.abs(Math.hypot(dx,dy)-bend) < 1e-7);
    assert.ok(dx > 0);
    if (kind === 'counter') assert.deepEqual(geometry(.1),geometry(.1,false,1));
    for (const extreme of [-90,490]) {
      const g = swingGeometry(kind,{x:195,y:400},{x:extreme,y:-40},bounds,-1,false,()=>1);
      for (const pt of [g.a,g.b,g.c,g.inner]) {
        assert.ok(pt.x >= 15 && pt.x <= 375 && pt.y >= 47 && pt.y <= 245);
      }
    }
  }
  assert.equal(sample(-4,4,true,()=>assert.fail()),0);
});

test('strike impact ring follows the shield bonus at the actual cast', () => {
  const save = newSave(0);
  for (const [order, expected] of [[BOSS_ORDER,true],[DEFAULT_ORDER,false]]) {
    save.order = [...order];
    const hit = fight(save,3).events.find(e => e.kind === 'hit' && e.source === 'strike');
    assert.equal(hit.shieldBonus,expected);
  }
});
