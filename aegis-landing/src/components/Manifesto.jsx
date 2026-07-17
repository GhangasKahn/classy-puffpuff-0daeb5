import { useEffect, useRef } from "react";
import { gsap, revealUp, REDUCED, ScrollTrigger } from "../lib/reveal";

const TEXTURE = "https://images.unsplash.com/photo-1470071459604-3b5ec3a7fe05?auto=format&fit=crop&w=1800&q=60";

/* THE NEED TO BELIEVE — a worldview to join, not features to compare. */
export default function Manifesto() {
  const root = useRef(null);

  useEffect(() => {
    const ctx = gsap.context(() => {
      revealUp(root, ".mf", { y: 36, stagger: 0.12, trigger: root.current });
      if (!REDUCED) {
        gsap.to(".mf-texture", {
          yPercent: 18,
          ease: "none",
          scrollTrigger: { trigger: root.current, start: "top bottom", end: "bottom top", scrub: true },
        });
      }
    }, root);
    return () => ctx.revert();
  }, []);

  return (
    <section id="method" ref={root} className="relative overflow-hidden bg-deep py-32 md:py-44">
      <img
        src={TEXTURE}
        alt=""
        aria-hidden="true"
        loading="lazy"
        className="mf-texture absolute inset-0 h-[125%] w-full object-cover opacity-[0.13]"
      />
      <div className="absolute inset-0 bg-gradient-to-b from-night via-transparent to-night" aria-hidden="true" />
      <div className="relative mx-auto max-w-5xl px-6 md:px-10">
        <p className="mf text-base text-muted md:text-xl">
          Most air apps optimize for: <span className="text-ink/70">one city, one number, one shrug.</span>
        </p>
        <p className="mf mt-8 font-drama text-5xl italic leading-[1.05] text-ink md:text-8xl">
          We built for <span className="text-ember">your&nbsp;lungs</span>, on
          <span className="text-air"> your&nbsp;device</span> — and we show the math.
        </p>
        <p className="mf mt-10 max-w-2xl font-mono text-sm leading-relaxed text-muted">
          Every point of your exposure score traces to a source you can read: air burden,
          rising-smoke trend, upwind fires, your own sensitivity. No black box. No account. No server.
        </p>
      </div>
    </section>
  );
}
