/**
 * Fluid desk snap — maps any viewport onto a named layout.
 * CSS reads data-layout / data-rail / data-vm plus --desk-* custom properties.
 */

export const LAYOUT_SNAPS = [
  { name: "phone", max: 560 },
  { name: "phablet", max: 800 },
  { name: "tablet", max: 1100 },
  { name: "laptop", max: 1440 },
  { name: "desk", max: 1920 },
  { name: "wide", max: 2560 },
  { name: "ultra", max: Infinity },
];

function clamp(n, lo, hi) {
  return Math.min(hi, Math.max(lo, n));
}

export function snapName(width) {
  const w = Math.max(0, Number(width) || 0);
  return LAYOUT_SNAPS.find((s) => w < s.max)?.name || "ultra";
}

/**
 * @param {number} width
 * @param {number} height
 */
export function snapLayout(width = 1280, height = 800) {
  const w = Math.max(0, Number(width) || 0);
  const h = Math.max(0, Number(height) || 0);
  const name = snapName(w);
  const landscape = w >= h;
  const short = h > 0 && h < 560;

  let rail = "top";
  let vm = "side";
  if (name === "phone" || name === "phablet") vm = landscape && short ? "side" : "bottom";
  else if (name === "tablet" && !landscape) vm = "bottom";

  const vmFr =
    name === "ultra" ? 0.36 : name === "wide" ? 0.4 : name === "desk" ? 0.42 : 0.48;
  const pad = clamp(Math.round(w * 0.012), 10, 22);
  const kpiCols = name === "phone" ? 3 : name === "phablet" || name === "tablet" ? 3 : 6;

  return {
    name,
    rail,
    vm,
    landscape,
    short,
    width: w,
    height: h,
    vars: {
      "--desk-w": `${Math.round(w)}px`,
      "--desk-h": `${Math.round(h)}px`,
      "--rail-w": "100%",
      "--vm-fr": String(vmFr),
      "--pad": `${pad}px`,
      "--kpi-cols": String(kpiCols),
    },
  };
}

export function applyDeskLayout(el, layout) {
  if (!el || !layout) return layout;
  el.dataset.layout = layout.name;
  el.dataset.rail = layout.rail;
  el.dataset.vm = layout.vm;
  el.dataset.orient = layout.landscape ? "landscape" : "portrait";
  for (const [k, v] of Object.entries(layout.vars || {})) {
    el.style.setProperty(k, v);
  }
  return layout;
}

export function bindDeskLayout(el, getSize) {
  if (!el) return () => {};
  const measure =
    getSize ||
    (() => {
      const vv = globalThis.visualViewport;
      return {
        width: Math.round(vv?.width || globalThis.innerWidth || 1280),
        height: Math.round(vv?.height || globalThis.innerHeight || 800),
      };
    });
  let raf = 0;
  const tick = () => {
    raf = 0;
    applyDeskLayout(el, snapLayout(measure().width, measure().height));
  };
  const schedule = () => {
    if (raf) return;
    raf = globalThis.requestAnimationFrame ? requestAnimationFrame(tick) : 0;
    if (!raf) tick();
  };
  tick();
  const docEl = el.ownerDocument?.documentElement;
  let ro;
  if (typeof ResizeObserver !== "undefined" && docEl) {
    ro = new ResizeObserver(schedule);
    ro.observe(docEl);
  }
  globalThis.addEventListener?.("resize", schedule);
  globalThis.addEventListener?.("orientationchange", schedule);
  globalThis.visualViewport?.addEventListener("resize", schedule);
  globalThis.visualViewport?.addEventListener("scroll", schedule);
  return () => {
    ro?.disconnect();
    globalThis.removeEventListener?.("resize", schedule);
    globalThis.removeEventListener?.("orientationchange", schedule);
    globalThis.visualViewport?.removeEventListener("resize", schedule);
    globalThis.visualViewport?.removeEventListener("scroll", schedule);
  };
}
