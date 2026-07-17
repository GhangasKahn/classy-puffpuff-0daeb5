import { useEffect, useRef } from "react";
import { REDUCED } from "../lib/reveal";

/* SIGNATURE MOMENT — "The Sky, Live."
   A canvas smoke field whose drift follows the REAL current wind
   (direction + speed) and whose density follows the REAL PM2.5,
   both fetched from the same models the instrument uses.
   The cursor parts the smoke — the one thing the sky never does for you.
   Reduced motion: a static haze gradient, no particles. */
export default function SmokeField({ windDir, windSpd, pm25 }) {
  const canvasRef = useRef(null);
  const dataRef = useRef({ windDir, windSpd, pm25 });
  dataRef.current = { windDir, windSpd, pm25 };

  useEffect(() => {
    if (REDUCED) return;
    const canvas = canvasRef.current;
    const ctx = canvas.getContext("2d");
    let w, h, raf;
    const mouse = { x: -9999, y: -9999 };
    const dpr = Math.min(window.devicePixelRatio || 1, 2);

    const resize = () => {
      w = canvas.clientWidth; h = canvas.clientHeight;
      canvas.width = w * dpr; canvas.height = h * dpr;
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    };
    resize();

    const N = Math.min(220, Math.floor((w * h) / 6500));
    const parts = Array.from({ length: N }, () => ({
      x: Math.random() * w,
      y: Math.random() * h,
      r: 24 + Math.random() * 90,
      a: 0.02 + Math.random() * 0.05,
      drift: 0.4 + Math.random() * 0.8,
      wob: Math.random() * Math.PI * 2,
    }));

    const onMove = (e) => {
      const rect = canvas.getBoundingClientRect();
      mouse.x = e.clientX - rect.left;
      mouse.y = e.clientY - rect.top;
    };
    const onLeave = () => { mouse.x = -9999; mouse.y = -9999; };
    window.addEventListener("resize", resize);
    canvas.parentElement.addEventListener("pointermove", onMove);
    canvas.parentElement.addEventListener("pointerleave", onLeave);

    let t = 0;
    const tick = () => {
      t += 0.004;
      const { windDir: wd, windSpd: ws, pm25: pm } = dataRef.current;
      // downwind = direction the air is GOING (wind blows FROM wd)
      const rad = (((wd ?? 240) + 180) % 360 - 90) * (Math.PI / 180);
      const speed = 0.15 + Math.min((ws ?? 10) / 30, 1.4) * 0.7;
      const density = Math.min(Math.max((pm ?? 8) / 60, 0.25), 1);
      const vx = Math.cos(rad) * speed;
      const vy = Math.sin(rad) * speed;

      ctx.clearRect(0, 0, w, h);
      for (const p of parts) {
        p.wob += 0.006 * p.drift;
        p.x += vx * p.drift + Math.sin(p.wob) * 0.18;
        p.y += vy * p.drift + Math.cos(p.wob * 0.8) * 0.12;

        // the cursor parts the smoke
        const dx = p.x - mouse.x, dy = p.y - mouse.y;
        const d2 = dx * dx + dy * dy;
        if (d2 < 32000) {
          const f = (1 - d2 / 32000) * 2.4;
          p.x += (dx / Math.sqrt(d2 + 1)) * f;
          p.y += (dy / Math.sqrt(d2 + 1)) * f;
        }

        // wrap
        if (p.x < -p.r) p.x = w + p.r; if (p.x > w + p.r) p.x = -p.r;
        if (p.y < -p.r) p.y = h + p.r; if (p.y > h + p.r) p.y = -p.r;

        const g = ctx.createRadialGradient(p.x, p.y, 0, p.x, p.y, p.r);
        g.addColorStop(0, `rgba(147,164,196,${p.a * density})`);
        g.addColorStop(1, "rgba(147,164,196,0)");
        ctx.fillStyle = g;
        ctx.beginPath();
        ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
        ctx.fill();
      }
      raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);

    return () => {
      cancelAnimationFrame(raf);
      window.removeEventListener("resize", resize);
      canvas.parentElement?.removeEventListener("pointermove", onMove);
      canvas.parentElement?.removeEventListener("pointerleave", onLeave);
    };
  }, []);

  if (REDUCED) {
    return <div className="absolute inset-0 bg-gradient-to-t from-night via-transparent to-night/40" aria-hidden="true" />;
  }
  return <canvas ref={canvasRef} className="absolute inset-0 h-full w-full" aria-hidden="true" />;
}
