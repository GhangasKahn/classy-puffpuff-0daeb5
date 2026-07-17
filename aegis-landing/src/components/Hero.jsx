import { useEffect, useRef } from "react";
import { gsap, revealUp } from "../lib/reveal";
import SmokeField from "./SmokeField";
import { compass16 } from "../lib/useLiveAir";

const APP_URL = "/aegis-air-mvp/";
const HERO_IMG = "https://images.unsplash.com/photo-1493246507139-91e8fad9978e?auto=format&fit=crop&w=2000&q=70";

/* THE OPENING SHOT — full-bleed misted mountains under a live smoke field.
   Content pinned bottom-left. Id language: the feeling of knowing. */
export default function Hero({ live }) {
  const root = useRef(null);

  useEffect(() => {
    const ctx = gsap.context(() => {
      revealUp(root, ".hero-reveal", { y: 44, stagger: 0.08 });
    }, root);
    return () => ctx.revert();
  }, []);

  return (
    <section id="hero" ref={root} className="relative flex min-h-[100dvh] flex-col justify-end overflow-hidden">
      <img
        src={HERO_IMG}
        alt="Mist moving through a dark mountain ridge at dusk"
        className="absolute inset-0 h-full w-full object-cover"
        fetchPriority="high"
      />
      <div className="absolute inset-0 bg-gradient-to-t from-night via-night/60 to-night/20" aria-hidden="true" />
      <SmokeField windDir={live.windDir} windSpd={live.windSpd} pm25={live.pm25} />

      <div className="relative z-10 w-full px-6 pb-16 pt-40 md:px-14 md:pb-20 lg:w-2/3">
        <p className="hero-reveal mb-5 font-mono text-[11px] uppercase tracking-[0.28em] text-air">
          Aegis Air — personal exposure instrument
        </p>
        <h1 className="leading-none">
          <span className="hero-reveal block text-4xl font-extrabold tracking-tight text-ink md:text-6xl">
            The smoke won&rsquo;t warn you.
          </span>
          <span className="hero-reveal mt-2 block font-drama text-7xl italic text-ink md:text-[9.5rem] md:leading-[0.95]">
            Aegis will.
          </span>
        </h1>
        <p className="hero-reveal mt-7 max-w-xl text-base leading-relaxed text-muted md:text-lg">
          It seems like every air app hands you one number for a whole city and calls
          it safety. Aegis reads <em className="font-drama italic text-ink">your</em> sky — wind,
          fires, 72-hour forecast — and scores your personal risk, transparently, on your device.
        </p>
        <div className="hero-reveal mt-9 flex flex-wrap items-center gap-4">
          <a href={APP_URL} className="btn-magnetic rounded-full bg-ember px-8 py-4 text-base font-bold text-deep">
            <span className="slide bg-air" aria-hidden="true" />
            <span>Read my sky — free</span>
          </a>
          <a href="#method" className="lift font-mono text-sm text-muted underline decoration-line underline-offset-4 hover:text-ink">
            Not yet — show me how it&rsquo;s scored
          </a>
        </div>

        {/* the field is live, and says so */}
        <div className="hero-reveal mt-10 flex items-center gap-3 font-mono text-[11px] uppercase tracking-widest text-muted">
          <span className="pulse-dot inline-block h-2 w-2 rounded-full bg-air" aria-hidden="true" />
          {live.ready && live.windDir != null
            ? <span className="readout">This haze drifts with the real wind — {compass16(live.windDir)}, {Math.round(live.windSpd ?? 0)} km/h over Buffalo right now</span>
            : <span>Reading the sky…</span>}
        </div>
      </div>
    </section>
  );
}
