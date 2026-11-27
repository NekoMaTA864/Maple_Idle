import { brushes, sample, swingGeometry } from './brushes.mjs';

// Each play() consumes one simulation tick. Geometry always comes from the live cards.
export function createEffects(field, rng = Math.random) {
  const stage = field.querySelector('.vfx-stage');
  const top = field.querySelector('.top-band');
  const bottom = field.querySelector('.bottom-band');
  const timers = new Set();
  const highlights = new Map();
  let swingSide = 1, sweepReverse = false;

  function after(ms, fn) {
    const id = setTimeout(() => { timers.delete(id); fn(); }, ms);
    timers.add(id);
  }

  function clear() {
    for (const id of timers) clearTimeout(id);
    timers.clear();
    swingSide = 1;
    sweepReverse = false;
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
    reduced ||= matchMedia('(prefers-reduced-motion: reduce)').matches;
    const fast = speed === 4;
    const short = fast ? 220 : 420;
    const ttl = fast ? 430 : 820;
    const rect = field.getBoundingClientRect();
    if (!rect.width || !rect.height) return;
    stage.setAttribute('viewBox', `0 0 ${rect.width} ${rect.height}`);
    const bounds = { width: rect.width, top: top.offsetTop + top.offsetHeight, bottom: bottom.offsetTop };
    const center = id => {
      const r = document.getElementById(id).getBoundingClientRect();
      return r.left + r.width / 2 - rect.left;
    };
    const core = { x: center('hero-core'), y: rect.height - 12 };
    const shield = { x: core.x, y: rect.height - 44 };
    const enemy = (id, dx = 0) => ({ x: center(id) + dx, y: 16 });
    function group(kind, source, target, duration = ttl) {
      const g = document.createElementNS(stage.namespaceURI, 'g');
      Object.assign(g.dataset, { kind, source, target });
      stage.append(g);
      if (duration) after(duration, () => g.remove());
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
      return el;
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
    const heal = events.find(e => e.kind === 'buff' && e.source === 'heal');
    // Keep a previous beat's recovery glyph paired with its label if an impact follows.
    function positionHeal(beside) {
      const label = bottom.querySelector('[data-owner="heal"]');
      const halo = stage.querySelector('[data-kind="heal"]');
      if (!label || !halo) return;
      const x = Math.min(core.x + (beside ? 104 : 0), rect.width - Math.max(26, label.offsetWidth / 2));
      label.style.left = x + 'px';
      halo.setAttribute('transform', `translate(${x - core.x} 0)`);
    }
    let wedge;
    if (threat) {
      for (const e of incoming) highlight('#' + e.source, 'enemy-source', ttl);
      // Only the current incoming stroke needs the full center lane.
      stage.querySelector('[data-kind="incoming"]')?.remove();
      wedge = group('incoming', threat.source, 'hero-core', fast ? 290 : 640);
      brushes(wedge, fast).drawEnemyDownwardWedge(enemy(threat.source, -8), { ...shield, x: shield.x - 6 }, opts);
      const lost = incoming.reduce((sum, e) => sum + e.lost, 0);
      const blocked = incoming.some(e => e.absorbed);
      const impact = () => {
        highlight('#hero-core', blocked ? 'core-block' : 'core-hurt', ttl);
        if (blocked) {
          stage.querySelector('[data-kind="shield"]')?.remove();
          brushes(group('shield', threat.source, 'hero-core', fast ? 340 : 670), fast).drawShieldContact(shield);
        }
        badge(bottom, 'hero-core', core.x, blocked ? `盾擋 ${lost} 傷` : `▼ 受擊 −${lost}`, blocked ? 'block' : 'hurt', 2);
        positionHeal(true);
      };
      if (reduced) impact(); else after(fast ? 70 : 160, impact);
    }
    if (heal) {
      stage.querySelector('[data-kind="heal"]')?.remove();
      brushes(group('heal', 'hero-core', 'hero-core'), fast).drawHealHalo(core.x, shield.y - 15, reduced);
      highlight('#hero-core', 'core-heal', ttl);
      badge(bottom, 'heal', core.x, `＋回復 ${heal.amount}`, 'heal');
      positionHeal(threat || bottom.querySelector('[data-owner="hero-core"]') || stage.querySelector('[data-kind="incoming"]'));
    }

    const targetY = bounds.top + 19;
    const sweep = hits.filter(e => e.source === 'sweep');
    if (sweep.length) {
      const reverse = !reduced && sweepReverse;
      if (!reduced) sweepReverse = !sweepReverse;
      const targets = reverse ? sweep.toReversed() : sweep;
      const xs = sweep.map(e => center(e.target));
      const arc = group('sweep', 'hero-core', 'field', short);
      arc.dataset.slots = sweep.map(e => e.target).join(' ');
      brushes(arc, fast).sweep(Math.max(12, Math.min(...xs)-18), Math.min(rect.width-12, Math.max(...xs)+18),
        targetY+8, sample(-4,4,reduced,rng), reverse, reduced);
      targets.forEach((e,i) => {
        const light = () => {
          if (!arc.isConnected) return;
          highlight('#'+e.target, 'hit-target', short);
          badge(top, e.target, center(e.target), `▲ −${e.amount}`, 'hit');
        };
        if (reduced || !i) light(); else after(i * (fast ? 18 : 40), light);
      });
    }
    const rank = e => breaks.has(e.target) && e.source === 'break' ? 3 : e.source === 'guard' ? 2 : 1;
    for (const e of hits.filter(e => e.source !== 'sweep')) {
      const priority = rank(e);
      const counter = e.source === 'guard', interrupt = priority === 3;
      const draw = () => {
        const target = document.getElementById(e.target);
        if (!target || (counter && target.classList.contains('fallen'))) return;
        const label = top.querySelector(`[data-owner="${e.target}"]`);
        if (Number(label?.dataset.priority) > priority || hits.some(h => h.target === e.target && rank(h) > priority)) return;
        // Evict older strokes even if a slow beat queued the current counter.
        const obsolete = priority > 1 ? `[data-target="${e.target}"],[data-slots~="${e.target}"]` : `[data-target="${e.target}"][data-kind="basic"]`;
        for (const old of stage.querySelectorAll(obsolete)) old.remove();
        if (interrupt) {
          for (const old of stage.querySelectorAll(`[data-kind="incoming"][data-source="${e.target}"]`)) {
            if (old !== wedge) old.remove();
          }
        }
        const to = { x:center(e.target) + (counter ? 13 : 0), y:targetY };
        const from = { x:core.x + (counter || threat ? 16 : 0), y:counter ? shield.y-4 : bounds.bottom-17 };
        const kind = counter ? 'counter' : e.source || 'basic';
        if (!counter || e.target === threat?.source) {
          const brush = brushes(group(kind, 'hero-core', e.target, priority > 1 ? ttl : short), fast);
          if (kind === 'orbit') brush.orbitHit(to.x, to.y);
          else if (kind === 'break') brush.seal(from, to, interrupt, reduced);
          else {
            const geo = swingGeometry(kind, from, to, bounds, swingSide, reduced, rng);
            brush.swing(kind, geo, e.shieldBonus, reduced);
            if (!reduced && !counter) swingSide *= -1;
          }
        }
        highlight('#' + e.target, interrupt ? 'interrupted' : counter ? 'counter-target' : 'hit-target', ttl);
        badge(top, e.target, center(e.target), interrupt ? `▲ 打斷 −${e.amount}` : counter ? `▲ 反擊 −${e.amount}` : `▲ −${e.amount}`,
          interrupt ? 'interrupt' : counter ? 'counter' : 'hit', priority);
      };
      if (counter && wedge && e.target === threat.source) {
        const delay = fast ? 150 : reduced ? 80 : 480;
        after(delay - 30, () => wedge.setAttribute('opacity', '0.3'));
        after(delay, draw);
      } else draw();
    }
  }
  let orbitTrack;
  function syncOrbit(active, speed, reduced) {
    reduced ||= matchMedia('(prefers-reduced-motion: reduce)').matches;
    const mode = speed + '/' + reduced;
    if (active && orbitTrack?.isConnected && orbitTrack.dataset.mode === mode) return;
    orbitTrack?.remove();
    orbitTrack = null;
    if (!active) return;
    const r = field.getBoundingClientRect();
    stage.setAttribute('viewBox', `0 0 ${r.width} ${r.height}`);
    orbitTrack = document.createElementNS(stage.namespaceURI, 'g');
    Object.assign(orbitTrack.dataset, { kind:'orbit-track', mode });
    stage.append(orbitTrack);
    brushes(orbitTrack, speed === 4).orbit(r.width/2, r.height*.37, r.width*.18, reduced, speed);
  }
  new ResizeObserver(clear).observe(field);
  return { clear, play, refreshCards, syncOrbit };
}
