const reduced = () => matchMedia("(prefers-reduced-motion: reduce)").matches;

const DEPTH_COPY = {
  1: "Depth 1 — Signal",
  2: "Depth 2 — Measure",
  3: "Depth 3 — Decide",
  4: "Depth 4 — Full"
};

export function initMotion(state) {
  const hero = document.querySelector(".hero-plate");
  const toast = document.getElementById("depth-toast");
  const plot = document.getElementById("sky-plot");

  document.querySelectorAll(".surface").forEach((el) => {
    el.classList.add("is-pending");
  });

  const io = new IntersectionObserver((entries) => {
    for (const e of entries) {
      if (!e.isIntersecting) continue;
      e.target.classList.remove("is-pending");
      e.target.classList.add("is-in");
      io.unobserve(e.target);
    }
  }, { threshold: 0.12 });
  document.querySelectorAll(".surface").forEach((el) => io.observe(el));

  state.plotVisible = true;
  const plotIo = new IntersectionObserver((entries) => {
    state.plotVisible = entries.some((e) => e.isIntersecting);
  }, { threshold: 0.05 });
  if (plot) plotIo.observe(plot.closest(".plot-wrap") || plot);

  let ticking = false;
  const onScroll = () => {
    if (reduced() || !hero) return;
    if (ticking) return;
    ticking = true;
    requestAnimationFrame(() => {
      ticking = false;
      const y = window.scrollY || 0;
      hero.style.transform = `translate3d(0, ${Math.min(y * 0.12, 48)}px, 0)`;
    });
  };
  window.addEventListener("scroll", onScroll, { passive: true });
  state._scroll = onScroll;

  let toastTimer = 0;
  state.showDepthToast = (n) => {
    if (!toast) return;
    toast.hidden = false;
    toast.textContent = DEPTH_COPY[n] || `Depth ${n}`;
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => { toast.hidden = true; }, reduced() ? 0 : 1600);
  };

  state.sweep = 0;
  let raf = 0;
  const loop = (t) => {
    raf = requestAnimationFrame(loop);
    if (reduced()) return;
    if (document.hidden) return;
    if (!state.plotVisible) return;
    state.sweep = (t / 40) % 360;
    if (typeof state.drawPlot === "function") state.drawPlot();
  };
  raf = requestAnimationFrame(loop);
  state._raf = () => cancelAnimationFrame(raf);

  state.compassNeedle = 0;
  state.easeCompass = (target) => {
    if (reduced()) {
      state.compassNeedle = target;
      return;
    }
    const cur = state.compassNeedle;
    let d = ((target - cur + 540) % 360) - 180;
    state.compassNeedle = (cur + d * 0.18 + 360) % 360;
  };
}

export function listMotionListeners() {
  return [
    { kind: "scroll", id: "M01", el: ".hero-plate" },
    { kind: "IntersectionObserver", id: "M02", el: ".surface" },
    { kind: "requestAnimationFrame", id: "M03", el: "#sky-plot sweep" },
    { kind: "canvas", id: "M04", el: "lock pip" },
    { kind: "canvas", id: "M05", el: "#compass" },
    { kind: "text", id: "M06", el: "#az #el #range #mag" },
    { kind: "toast", id: "M07", el: "#depth-toast" },
    { kind: "class", id: "M08", el: "#gate" },
    { kind: "class", id: "M09", el: "#next-pass" },
    { kind: "canvas", id: "M10", el: "#ar-hud" },
    { kind: "canvas", id: "M11", el: "#ground-track" },
    { kind: "text", id: "M12", el: "#face" }
  ];
}
