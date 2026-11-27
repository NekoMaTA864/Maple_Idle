import { brushes } from './brushes.mjs';

// Each play() consumes one simulation tick. Geometry always comes from the live cards.
export function createEffects(field) {
  const stage = field.querySelector('.vfx-stage');
  const top = field.querySelector('.top-band');
  const bottom = field.querySelector('.bottom-band');
  const timers = new Set();
  const highlights = new Map();

  function after(ms, fn) {
    const id = setTimeout(() => { timers.delete(id); fn(); }, ms);
    timers.add(id);
  }

  function clear() {
    for (const id of timers) clearTimeout(id);
    timers.clear();
    for (const { selector, cls } of highlights.values()) document.querySelector(selector)?.classList.remove(cls);
    highlights.clear();
    for (const layer of [stage, top, bottom]) layer.replaceChildren();
  }

  function refreshCards() {
    for (const { selector, cls } of highlights.values()) document.querySelector(selector)?.classList.add(cls);
    for (const card of document.querySelectorAll('.enemy .slot-state')) {
      const classes = card.parentElement.classList;
      card.textContent = classes.contains('fallen') ? '已擊破' : classes.contains('interrupted') ? '已打斷' :
        classes.contains('charging') ? '重擊蓄力' : classes.contains('counter-target') ? '遭反擊' :
        classes.contains('enemy-source') ? '攻擊出手' : classes.contains('hit-target') ? '受擊' : '待機';
    }
  }

  function highlight(selector, cls, ms) {
    const key = selector + ':' + cls;
    const mark = { selector, cls };
    highlights.set(key, mark);
    document.querySelector(selector)?.classList.add(cls);
    after(ms, () => {
      if (highlights.get(key) !== mark) return;
      highlights.delete(key);
      document.querySelector(selector)?.classList.remove(cls);
    });
  }

  function play(events, speed, reduced) {
    const fast = speed === 4;
    const ttl = fast ? 430 : 820;
    const rect = field.getBoundingClientRect();
    if (!rect.width || !rect.height) return;
    stage.setAttribute('viewBox', `0 0 ${rect.width} ${rect.height}`);
    const center = id => {
      const r = document.getElementById(id).getBoundingClientRect();
      return r.left + r.width / 2 - rect.left;
    };
    const core = { x: center('hero-core'), y: rect.height - 12 };
    const shield = { x: core.x, y: rect.height - 44 };
    const enemy = (id, dx = 0) => ({ x: center(id) + dx, y: 12 });
    function group(kind, source, target) {
      const g = document.createElementNS(stage.namespaceURI, 'g');
      Object.assign(g.dataset, { kind, source, target });
      stage.append(g);
      after(ttl, () => g.remove());
      return g;
    }
    function badge(band, owner, x, text, tone, priority = 1) {
      const old = band.querySelector(`[data-owner="${owner}"]`);
      if (Number(old?.dataset.priority) > priority) return;
      old?.remove();
      const el = document.createElement('div');
      el.className = `callout show tone-${tone}${reduced ? '' : ' animate-pop'}`;
      Object.assign(el.dataset, { owner, priority });
      el.style.setProperty('--pop-dur', fast ? '110ms' : '185ms');
      el.textContent = text;
      band.append(el);
      const half = el.offsetWidth / 2;
      el.style.left = Math.max(half, Math.min(rect.width - half, x)) + 'px';
      after(ttl, () => el.remove());
    }
    const opts = { staticMode: reduced };
    const incoming = events.filter(e => e.raw != null);
    const threat = [...incoming].sort((a, b) => Number(b.heavy) - Number(a.heavy) || b.raw - a.raw)[0];
    const hits = events.filter(e => e.kind === 'hit');
    const breaks = new Set(events.filter(e => e.kind === 'ice').map(e => e.target));
    for (const e of events.filter(e => e.kind === 'cast')) highlight(`[data-skill="${e.source}"]`, 'source-active', ttl);

    for (const e of events.filter(e => e.kind === 'charge')) {
      badge(top, e.target, center(e.target), '蓄力警戒', 'hurt');
    }
    let wedge;
    if (threat) {
      for (const e of incoming) highlight('#' + e.source, 'enemy-source', ttl);
      wedge = group('incoming', threat.source, 'hero-core');
      brushes(wedge, fast).drawEnemyDownwardWedge(enemy(threat.source, -8), { ...shield, x: shield.x - 6 }, opts);
      const lost = incoming.reduce((sum, e) => sum + e.lost, 0);
      const blocked = incoming.some(e => e.absorbed);
      const impact = () => {
        highlight('#hero-core', blocked ? 'core-block' : 'core-hurt', ttl);
        if (blocked) brushes(group('shield', threat.source, 'hero-core'), fast).drawShieldContact(shield, opts);
        const recentHeal = bottom.querySelector('[data-owner="heal"]');
        if (recentHeal) recentHeal.style.left = Math.min(core.x + 104, rect.width - recentHeal.offsetWidth / 2) + 'px';
        badge(bottom, 'hero-core', core.x, blocked ? `盾擋 ${lost} 傷` : `▼ 受擊 −${lost}`, blocked ? 'block' : 'hurt', 2);
      };
      if (reduced) impact(); else after(fast ? 75 : 180, impact);
    }

    for (const e of hits) {
      const counter = e.source === 'guard';
      const interrupt = e.source === 'break' && breaks.has(e.target);
      const area = e.source === 'orbit' || e.source === 'sweep';
      const index = area ? hits.filter(h => h.source === e.source).indexOf(e) : 0;
      // Secondary counters retain their endpoint without adding another crossing.
      const fullTrail = !counter || e.target === threat?.source;
      const draw = () => {
        if (fullTrail) {
          const kind = counter ? 'counter' : interrupt ? 'interrupt' : 'outgoing';
          const brush = brushes(group(kind, 'hero-core', e.target), fast);
          const dx = counter || threat ? 16 : interrupt ? 8 : area ? (index - 1) * 10 : 0;
          brush.drawHeroUpwardArc({ ...core, x: core.x + dx }, enemy(e.target, counter ? 14 : 0), {
            ...opts, counter, curve: counter ? 26 : interrupt ? 16 : area ? [-24, -10, 24, 28][index] : undefined,
            endOffset: interrupt ? 44 : 24,
            color: interrupt ? '#bfd8e0' : counter ? '#e9cb8d' : area ? '#dfba75' : '#e6c382',
          });
          if (interrupt) brush.drawInterruptGlyph(enemy(e.target), opts);
        }
        highlight('#' + e.target, interrupt ? 'interrupted' : counter ? 'counter-target' : 'hit-target', ttl);
        badge(top, e.target, center(e.target), interrupt ? `▲ 打斷 −${e.amount}` : counter ? `▲ 反擊 −${e.amount}` : `▲ −${e.amount}`,
          interrupt ? 'interrupt' : counter ? 'counter' : 'hit', interrupt ? 3 : counter ? 2 : 1);
      };
      if (counter && wedge && fullTrail) {
        const delay = fast ? 150 : reduced ? 80 : 500;
        after(delay - 30, () => wedge.setAttribute('opacity', '0.3'));
        after(delay, draw);
      } else draw();
    }
    const heal = events.find(e => e.kind === 'buff' && e.source === 'heal');
    if (heal) {
      brushes(group('heal', 'hero-core', 'hero-core'), fast).drawHealHalo(core, opts);
      highlight('#hero-core', 'core-heal', ttl);
      // Healing has its own slot beside the core when damage lands on the same beat.
      const besideImpact = threat || bottom.querySelector('[data-owner="hero-core"]');
      badge(bottom, 'heal', core.x + (besideImpact ? 104 : 0), `＋回復 ${heal.amount}`, 'heal');
    }
  }
  new ResizeObserver(clear).observe(field);
  return { clear, play, refreshCards };
}
