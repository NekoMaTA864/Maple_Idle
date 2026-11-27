// Drawing methods from agy’s 聖騎士攻防動效/motion.js.
const SVG_NS = "http://www.w3.org/2000/svg";
function createSvgEl(tag, attrs = {}) {
  const el = document.createElementNS(SVG_NS, tag);
  for (const [k, v] of Object.entries(attrs)) el.setAttribute(k, String(v));
  return el;
}

export function brushes(svg, fast) {
  const trailMs = fast ? 115 : 290;
  const popMs = fast ? 110 : 185;
  return {
    // 我方上行：窄弧（向上彎弧＋終點箭尖）
    drawHeroUpwardArc(from, to, opts = {}) {
      const color = opts.color || "#e6c382";
      const curve = opts.curve !== undefined ? opts.curve : (to.x >= from.x ? 18 : -18);
      const midX = (from.x + to.x) / 2 + curve;
      const midY = (from.y + to.y) / 2;
      const startY = from.y - 22;
      const endY = to.y + (opts.endOffset !== undefined ? opts.endOffset : 24);
      const d = `M ${from.x.toFixed(1)} ${startY.toFixed(1)} Q ${midX.toFixed(1)} ${midY.toFixed(1)} ${to.x.toFixed(1)} ${endY.toFixed(1)}`;
      const len = Math.hypot(to.x - from.x, startY - endY) * 1.25;

      const g = createSvgEl("g");
      const mainPath = createSvgEl("path", {
        d,
        stroke: color,
        "stroke-width": opts.counter ? "2.1" : "2.5",
        class: `fx-stroke ${opts.staticMode ? "" : "fx-anim-draw"}`,
        "stroke-dasharray": opts.staticMode ? "5 4" : "",
      });
      mainPath.style.setProperty("--len", len.toFixed(0));
      mainPath.style.setProperty("--dur", `${trailMs}ms`);
      mainPath.style.setProperty("--delay", `${opts.delay || 0}ms`);
      g.appendChild(mainPath);

      // 外側細伴弧強調「窄弧」輪廓
      const d2 = `M ${(from.x + 3).toFixed(1)} ${(startY - 2).toFixed(1)} Q ${(midX + (curve >= 0 ? 5 : -5)).toFixed(1)} ${midY.toFixed(1)} ${(to.x + 2).toFixed(1)} ${(endY + 3).toFixed(1)}`;
      const subPath = createSvgEl("path", {
        d: d2,
        stroke: color,
        "stroke-width": "1.0",
        opacity: "0.48",
        class: `fx-stroke ${opts.staticMode ? "" : "fx-anim-draw"}`,
      });
      subPath.style.setProperty("--len", len.toFixed(0));
      subPath.style.setProperty("--dur", `${trailMs}ms`);
      subPath.style.setProperty("--delay", `${(opts.delay || 0) + 25}ms`);
      g.appendChild(subPath);

      // 終點上行窄弧箭尖（讓靜態與灰階下方向零歧義）
      const tip = createSvgEl("path", {
        d: `M ${(to.x - 6).toFixed(1)} ${(endY + 8).toFixed(1)} Q ${to.x.toFixed(1)} ${(endY - 2).toFixed(1)} ${(to.x + 6).toFixed(1)} ${(endY + 8).toFixed(1)}`,
        stroke: color,
        "stroke-width": "2.2",
        class: `fx-stroke ${opts.staticMode ? "" : "fx-anim-pop"}`,
      });
      tip.style.setProperty("--pop-dur", `${popMs}ms`);
      tip.style.setProperty("--delay", `${(opts.delay || 0) + Math.round(trailMs * 0.65)}ms`);
      g.appendChild(tip);

      svg.appendChild(g);
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

    // 格擋：盾面微弧接觸＋碰撞碎點
    drawShieldContact(pt, opts = {}) {
      const color = opts.color || "#e9cb8d";
      const r = opts.compact ? 22 : 28;
      const g = createSvgEl("g", { class: opts.staticMode ? "" : "fx-anim-pop" });
      g.style.setProperty("--pop-dur", `${popMs}ms`);

      // 厚實微弧盾面
      g.appendChild(createSvgEl("path", {
        d: `M ${(pt.x - r).toFixed(1)} ${(pt.y + 4).toFixed(1)} Q ${pt.x.toFixed(1)} ${(pt.y - 10).toFixed(1)} ${(pt.x + r).toFixed(1)} ${(pt.y + 4).toFixed(1)}`,
        stroke: color,
        "stroke-width": "3.0",
        class: "fx-stroke",
      }));
      g.appendChild(createSvgEl("path", {
        d: `M ${(pt.x - r + 6).toFixed(1)} ${(pt.y + 8).toFixed(1)} Q ${pt.x.toFixed(1)} ${(pt.y - 3).toFixed(1)} ${(pt.x + r - 6).toFixed(1)} ${(pt.y + 8).toFixed(1)}`,
        stroke: color,
        "stroke-width": "1.2",
        opacity: "0.65",
        class: "fx-stroke",
      }));

      // 碰撞碎點（4 道短濺射）
      const sparks = [
        [-10, -4, -18, -11],
        [-4, -7, -7, -15],
        [4, -7, 8, -15],
        [10, -4, 18, -10],
      ];
      sparks.forEach(([x1, y1, x2, y2]) => {
        g.appendChild(createSvgEl("line", {
          x1: (pt.x + x1).toFixed(1),
          y1: (pt.y + y1).toFixed(1),
          x2: (pt.x + x2).toFixed(1),
          y2: (pt.y + y2).toFixed(1),
          stroke: color,
          "stroke-width": "1.6",
          class: "fx-stroke",
        }));
      });

      svg.appendChild(g);
    },

    // 斷勢聖印落點：敵槽下緣短角框交叉符號（置於落點徽章正下方，零遮擋）
    drawInterruptGlyph(pt, opts = {}) {
      const color = opts.color || "#bfd8e0";
      const cy = pt.y + 33;
      const g = createSvgEl("g", { class: opts.staticMode ? "" : "fx-anim-pop" });
      g.style.setProperty("--pop-dur", `${popMs}ms`);
      g.appendChild(createSvgEl("path", {
        d: `M ${pt.x - 10} ${cy - 4}v-5h5m10 0h5v5m0 6v5h-5m-10 0h-5v-5M${pt.x - 5} ${cy - 5}l10 10m0-10-10 10`,
        stroke: color,
        "stroke-width": "1.7",
        class: "fx-stroke",
      }));
      svg.appendChild(g);
    },

    // 回生禱言：武器核心上緣溫和回復十字輪廓（不進中央軌跡區）
    drawHealHalo(pt, opts = {}) {
      const color = opts.color || "#8cc290";
      const cy = pt.y - 44;
      const g = createSvgEl("g", { class: opts.staticMode ? "" : "fx-anim-pop" });
      g.style.setProperty("--pop-dur", `${popMs}ms`);
      g.appendChild(createSvgEl("path", {
        d: `M ${pt.x} ${cy - 10}v20M${pt.x - 10} ${cy}h20`,
        stroke: color,
        "stroke-width": "2.4",
        class: "fx-stroke",
      }));
      g.appendChild(createSvgEl("path", {
        d: `M ${pt.x - 24} ${cy + 14} Q ${pt.x} ${cy + 2} ${pt.x + 24} ${cy + 14}`,
        stroke: color,
        "stroke-width": "1.4",
        opacity: "0.75",
        class: "fx-stroke",
      }));
      svg.appendChild(g);
    },
  };
}
