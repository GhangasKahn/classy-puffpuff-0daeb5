import { useEffect, useRef } from "react";
import { gsap, revealUp } from "../lib/reveal";

const APP_URL = "/aegis-air-mvp/";

/* CONFESSION, then THE CLOSE.
   One honest cost. One held breath. One calibrated question. One door. */
export default function Close() {
  const root = useRef(null);

  useEffect(() => {
    const ctx = gsap.context(() => {
      revealUp(root, ".confess", { y: 30, stagger: 0.1, trigger: ".confess-block" });
      revealUp(root, ".close-el", { y: 40, stagger: 0.1, trigger: ".close-block", start: "top 78%" });
    }, root);
    return () => ctx.revert();
  }, []);

  return (
    <section ref={root}>
      {/* Confession */}
      <div className="confess-block mx-auto max-w-4xl px-6 py-28 md:px-10">
        <p className="confess font-mono text-[11px] uppercase tracking-[0.28em] text-ember">A confession</p>
        <p className="confess mt-6 font-drama text-3xl italic leading-snug text-ink md:text-5xl">
          Aegis is not a medical device. It reads modeled forecasts, not the sensor on your street.
          It will never diagnose you.
        </p>
        <p className="confess mt-6 max-w-2xl text-base leading-relaxed text-muted">
          That restraint is the point. Instruments that overclaim get ignored on the day it matters.
          Aegis shows you where every number comes from, tells you when data is modeled,
          and refuses to interpret what it cannot defend — so that when it says the sky is turning,
          you have a reason to believe it.
        </p>
      </div>

      {/* the held breath — a deliberate rhythm break before the ask */}
      <div className="h-24 md:h-40" aria-hidden="true" />

      {/* The Close */}
      <div className="close-block mx-auto max-w-4xl px-6 pb-32 text-center md:px-10 md:pb-44">
        <p className="close-el text-base text-muted md:text-lg">
          Every smoke day you guess through is an exposure you never measured.
        </p>
        <h2 className="close-el mt-6 font-drama text-5xl italic leading-[1.02] text-ink md:text-8xl">
          What would this season look like if you already <span className="text-air">knew</span>?
        </h2>
        <div className="close-el mt-12 flex flex-col items-center gap-5">
          <a href={APP_URL} className="btn-magnetic rounded-full bg-ember px-10 py-5 text-lg font-bold text-deep">
            <span className="slide bg-air" aria-hidden="true" />
            <span>Open Aegis Air — free, no account</span>
          </a>
          <a href="#method" className="lift font-mono text-sm text-muted underline decoration-line underline-offset-4 hover:text-ink">
            Not yet — read the method once more
          </a>
        </div>
        <p className="close-el mt-8 font-mono text-[11px] uppercase tracking-[0.2em] text-muted">
          Installs from the browser · works offline · your data never leaves the device
        </p>
      </div>
    </section>
  );
}
