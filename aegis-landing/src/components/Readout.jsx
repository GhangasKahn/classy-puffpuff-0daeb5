import { useEffect, useRef } from "react";
import { gsap, revealUp } from "../lib/reveal";
import { compass16 } from "../lib/useLiveAir";

/* THE EGO BEGINS — instrument readouts of the real, current models.
   Every number on this strip is live. None of it is decoration. */
export default function Readout({ live }) {
  const root = useRef(null);

  useEffect(() => {
    const ctx = gsap.context(() => {
      revealUp(root, ".ro", { y: 24, stagger: 0.08, trigger: root.current });
    }, root);
    return () => ctx.revert();
  }, []);

  const cell = (label, value, unit) => (
    <div className="ro flex flex-col gap-1 border-l border-line pl-4">
      <span className="font-mono text-[10px] uppercase tracking-[0.2em] text-muted">{label}</span>
      <span className="readout font-mono text-2xl text-ink md:text-3xl">
        {value ?? "—"}<span className="ml-1 text-sm text-muted">{unit}</span>
      </span>
    </div>
  );

  return (
    <section className="border-y border-line bg-deep/60">
      <div ref={root} className="mx-auto grid max-w-6xl grid-cols-2 gap-y-8 px-6 py-10 md:grid-cols-5 md:px-10">
        <div className="ro col-span-2 flex flex-col justify-center pr-6 md:col-span-1">
          <span className="flex items-center gap-2 font-mono text-[10px] uppercase tracking-[0.2em] text-air">
            <span className="pulse-dot inline-block h-1.5 w-1.5 rounded-full bg-air" aria-hidden="true" />
            Live · CAMS / Open-Meteo
          </span>
          <span className="mt-1 text-sm text-muted">Buffalo, NY — the same models the instrument reads</span>
        </div>
        {cell("US AQI", live.aqi != null ? Math.round(live.aqi) : null, "")}
        {cell("PM2.5", live.pm25 != null ? live.pm25.toFixed(1) : null, "µg/m³")}
        {cell("Wind", live.windSpd != null ? `${Math.round(live.windSpd)}` : null, `km/h ${compass16(live.windDir)}`)}
        {cell("Aerosol depth", live.aod != null ? live.aod.toFixed(2) : null, "AOD")}
      </div>
    </section>
  );
}
