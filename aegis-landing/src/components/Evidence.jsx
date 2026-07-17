import { useEffect, useRef } from "react";
import { gsap, revealUp } from "../lib/reveal";

/* PROOF — a bento of only-true things, typeset as instrument readouts. */
export default function Evidence() {
  const root = useRef(null);

  useEffect(() => {
    const ctx = gsap.context(() => {
      revealUp(root, ".ev", { y: 34, stagger: 0.1, trigger: root.current });
    }, root);
    return () => ctx.revert();
  }, []);

  const stat = (big, small, cls = "") => (
    <div className={`ev rounded-card border border-line bg-surface p-6 ${cls}`}>
      <div className="readout font-mono text-4xl text-ink md:text-5xl">{big}</div>
      <p className="mt-2 text-sm text-muted">{small}</p>
    </div>
  );

  return (
    <section id="proof" ref={root} className="mx-auto max-w-6xl px-6 pb-28 md:px-10 md:pb-36">
      <p className="ev font-mono text-[11px] uppercase tracking-[0.28em] text-air">The record</p>
      <h2 className="ev mt-3 text-3xl font-extrabold tracking-tight text-ink md:text-5xl">
        Claims we can <span className="font-drama font-medium italic text-ember">actually</span> make.
      </h2>
      <div className="mt-12 grid gap-4 md:grid-cols-4">
        {stat("0", "accounts, servers, trackers. Your health data lives in your browser and exports as a file you own.", "md:col-span-2")}
        {stat("72 h", "of PM2.5, AQI and aerosol forecast, charted from CAMS atmosphere models.")}
        {stat("2,600 km", "wildfire scan radius against NASA's EONET open-event catalog.")}
        {stat("7", "visible score components — every point traceable to a source.", "")}
        {stat("±45°", "upwind sector matching between live wind and each fire's bearing.")}
        <div className="ev rounded-card border border-line bg-deep p-6 md:col-span-2">
          <div className="font-mono text-[10px] uppercase tracking-[0.22em] text-muted">Sources — public, inspectable</div>
          <p className="readout mt-3 font-mono text-sm leading-loose text-ink">
            open-meteo.com · CAMS (Copernicus) · eonet.gsfc.nasa.gov · openstreetmap.org
          </p>
          <p className="mt-2 text-xs text-muted">
            Modeled environmental data — clearly labeled as such, everywhere it appears.
          </p>
        </div>
      </div>
    </section>
  );
}
