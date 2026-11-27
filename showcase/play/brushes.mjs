// Geometry for the Paladin skill effects. The incoming wedge follows agy’s original drawing.
const SVG_NS = "http://www.w3.org/2000/svg";
function createSvgEl(tag, attrs = {}) {
  const el = document.createElementNS(SVG_NS, tag);
  for (const [k, v] of Object.entries(attrs)) el.setAttribute(k, String(v));
  return el;
}

const gold = '#ddbb7c', ice = '#bdd4d9', green = '#8bb391';
const clamp = (v, lo, hi) => Math.max(lo, Math.min(hi, v));
export function sample(lo, hi, reduced, rng = Math.random) {
  return lo + (hi - lo) * (reduced ? .5 : rng());
}

// The normal points to the right of an upward swing, away from the incoming wedge.
export function swingGeometry(kind, from, to, bounds, side, reduced, rng = Math.random) {
  const range = { strike: [34, 54], basic: [18, 32], counter: [28, 44] }[kind];
  const bend = sample(...range, reduced, rng);
  const safe = ({ x, y }) => ({
    x: clamp(x, 15, bounds.width - 15),
    y: clamp(y, bounds.top + 15, bounds.bottom - 15),
  });
  const jitter = pt => safe({ x: pt.x + sample(-5, 5, reduced, rng), y: pt.y + sample(-5, 5, reduced, rng) });
  const a = jitter(from), b = jitter(to);
  if (kind === 'basic') {
    a.x += (b.x - a.x) * .54;
    a.y += (b.y - a.y) * .54;
  }
  const length = Math.hypot(b.x - a.x, b.y - a.y) || 1;
  const sign = kind === 'counter' || reduced ? 1 : side;
  const nx = (a.y - b.y) / length * sign, ny = (b.x - a.x) / length * sign;
  const control = offset => safe({ x: (a.x + b.x) / 2 + nx * offset, y: (a.y + b.y) / 2 + ny * offset });
  return { a, b, c: control(bend), inner: control(bend - (kind === 'strike' ? 15 : 9)), bend };
}

const xy = p => `${p.x.toFixed(2)} ${p.y.toFixed(2)}`;

export function brushes(svg, fast) {
  const trailMs = fast ? 115 : 290;
  const popMs = fast ? 110 : 185;
  function shape(tag, attrs, parent = svg) {
    const el = createSvgEl(tag, attrs);
    parent.append(el);
    return el;
  }
  function path(d, color, width, extra = {}) {
    return shape('path', { d, fill: 'none', stroke: color, 'stroke-width': width, 'stroke-linecap': 'round', ...extra });
  }
  function reveal(el, reduced) {
    if (!reduced) el.animate([
      { clipPath: 'inset(100% 0 0 0) fill-box' },
      { clipPath: 'inset(0) fill-box' },
    ], { duration: trailMs, easing: 'ease-out' });
    return el;
  }
  return {
    swing(kind, geo, shieldBonus, reduced) {
      const { a, b, c, inner } = geo;
      const d = `M${xy(a)} Q${xy(c)} ${xy(b)}`;
      svg.dataset.bend = geo.bend;
      if (kind === 'basic') {
        reveal(path(d, '#baa98d', 1.2), reduced);
        return;
      }
      reveal(path(`${d} Q${xy(inner)} ${a.x + 2} ${a.y} Z`, gold, .7, { fill: gold, 'fill-opacity': .78 }), reduced);
      if (kind === 'strike') {
        const { x, y } = b;
        path(`M${x} ${y-9}l2 7 7 2-7 2-2 9-2-9-7-2 7-2Z`, gold, 1.2);
        if (shieldBonus) shape('circle', { cx:x, cy:y, r:12, fill:'none', stroke:gold, 'stroke-width':1 });
      }
    },
    sweep(left, right, y, angle, reverse, reduced) {
      const cx = (left + right) / 2;
      const arc = path(`M${left} ${y} Q${cx} ${y+40} ${right} ${y} Q${cx} ${y+22} ${left} ${y}Z`, gold, 1,
        { fill: gold, 'fill-opacity': .65, transform: `rotate(${angle} ${cx} ${y})` });
      if (!reduced) arc.animate([{clipPath: reverse ? 'inset(0 0 0 100%) fill-box' : 'inset(0 100% 0 0) fill-box'}, {clipPath:'inset(0) fill-box'}],
        { duration: trailMs, easing:'ease-out' });
    },
    orbit(cx, cy, radius, reduced, speed) {
      shape('ellipse', { cx, cy, rx:radius, ry:15, fill:'none', stroke:gold, 'stroke-width':1, 'stroke-dasharray':'5 5', opacity:.68 });
      const anchor = shape('g', { transform: `translate(${cx} ${cy})` });
      const hammer = shape('g', {}, anchor);
      shape('image', { href:'./assets/trainee-hammer.svg', x:-11, y:-11, width:22, height:22 }, hammer);
      if (reduced) hammer.setAttribute('transform', `translate(${radius} 0)`);
      else shape('animateMotion', { path: `M${radius} 0a${radius} 15 0 1 1 ${-2*radius} 0a${radius} 15 0 1 1 ${2*radius} 0`,
        dur: `${1/speed}s`, repeatCount:'indefinite', begin:'indefinite' }, hammer).beginElement();
    },
    orbitHit(x, y) {
      path(`M${x-12} ${y+3}l24 -6m-15 8 11-3`, gold, 1.6);
    },
    seal(from, to, interrupted, reduced) {
      const {x,y} = to;
      reveal(path(`M${xy(from)} L${xy(to)}`, ice, 1.15), reduced);
      path(`M${x} ${y-8}l8 8-8 8-8-8Z`, ice, 1.7);
      if (interrupted) path(`M${x-13} ${y-6}v-6h7m12 0h7v6m0 12v6h-7m-12 0h-7v-6m7-1 8-10m-2 12 6-8`, ice, 2.4);
    },
    // 敵方下行：尖楔（直落尖刺楔形，與我方窄弧完全正交）
    drawEnemyDownwardWedge(from, to, opts = {}) {
      const color = opts.color || "#d8907e";
      const startY = from.y + 20;
      const endY = to.y - 4;
      const dx = to.x - from.x;
      const dy = endY - startY;
      const len = Math.max(20, Math.hypot(dx, dy));
      const ux = dx / len;
      const uy = dy / len;
      const px = -uy;
      const py = ux;

      // 楔形中心骨線＋尖端雙斜面
      const g = createSvgEl("g");
      const shaft = createSvgEl("path", {
        d: `M ${from.x.toFixed(1)} ${startY.toFixed(1)} L ${to.x.toFixed(1)} ${endY.toFixed(1)}`,
        stroke: color,
        "stroke-width": "2.4",
        class: `fx-stroke ${opts.staticMode ? "" : "fx-anim-draw"}`,
        "stroke-dasharray": opts.staticMode ? "6 3" : "",
      });
      shaft.style.setProperty("--len", len.toFixed(0));
      shaft.style.setProperty("--dur", `${trailMs}ms`);
      g.appendChild(shaft);

      // 下行尖楔頭部（實心高對比三角形，黑白下與弧形徹底區分）
      const tipLen = 13;
      const halfW = 5.5;
      const bx = to.x - ux * tipLen;
      const by = endY - uy * tipLen;
      const wedge = createSvgEl("polygon", {
        points: `${to.x.toFixed(1)},${endY.toFixed(1)} ${(bx + px * halfW).toFixed(1)},${(by + py * halfW).toFixed(1)} ${(bx - px * halfW).toFixed(1)},${(by - py * halfW).toFixed(1)}`,
        fill: color,
        class: opts.staticMode ? "" : "fx-anim-pop",
      });
      wedge.style.setProperty("--pop-dur", `${popMs}ms`);
      wedge.style.setProperty("--delay", `${Math.round(trailMs * 0.58)}ms`);
      g.appendChild(wedge);

      svg.appendChild(g);
    },

    drawShieldContact(pt) {
      const {x,y} = pt;
      path(`M${x-40} ${y+2}Q${x} ${y-17} ${x+40} ${y+2}M${x-32} ${y+6}Q${x} ${y-8} ${x+32} ${y+6}`, gold, 2.2);
      for (const [dx, dy, ex, ey] of [[-22,-5,-33,-16],[-8,-9,-13,-22],[4,-9,6,-16],[15,-7,28,-21],[20,-6,25,-9]]) {
        shape('line', {x1:x+dx,y1:y+dy,x2:x+ex,y2:y+ey,stroke:gold,'stroke-width':1.5});
      }
    },
    drawHealHalo(x, y, reduced) {
      path(`M${x-24} ${y+6}Q${x} ${y+18} ${x+24} ${y+6}Q${x} ${y+1} ${x-24} ${y+6}Z`, green, 1.2, {fill:green,'fill-opacity':.14});
      const crosses = path(`M${x-7} ${y-17}v13m-6-6.5h12M${x+9} ${y-7}v9m-4.5-4.5h9`, green, 2);
      if (!reduced) crosses.animate([{transform:'translateY(4px)'},{transform:'translateY(-3px)'}], {duration:fast?170:390,fill:'forwards'});
    },
  };
}
