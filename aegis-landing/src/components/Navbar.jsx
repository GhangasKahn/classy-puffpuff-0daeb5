import { useEffect, useState } from "react";

const APP_URL = "/aegis-air-mvp/";

/* Floating island — transparent over the hero, condenses to
   blurred glass with a hairline border once the sky is behind you. */
export default function Navbar() {
  const [scrolled, setScrolled] = useState(false);

  useEffect(() => {
    const hero = document.getElementById("hero");
    if (!hero) return;
    const obs = new IntersectionObserver(
      ([e]) => setScrolled(!e.isIntersecting),
      { rootMargin: "-80px 0px 0px 0px", threshold: 0 }
    );
    obs.observe(hero);
    return () => obs.disconnect();
  }, []);

  const link = "lift hidden md:inline text-sm text-muted hover:text-ink";

  return (
    <nav
      className={`fixed left-1/2 top-4 z-50 flex w-[min(94vw,780px)] -translate-x-1/2 items-center justify-between rounded-full px-5 py-2.5 transition-all duration-500 ${
        scrolled
          ? "border border-line bg-night/70 backdrop-blur-xl shadow-[0_8px_40px_rgba(0,0,0,.45)]"
          : "border border-transparent bg-transparent"
      }`}
      aria-label="Primary"
    >
      <a href="#hero" className="lift flex items-center gap-2.5 font-bold tracking-tight">
        <svg viewBox="0 0 512 512" className="h-6 w-6" aria-hidden="true">
          <path d="M256 64 416 122v140c0 96-68 156-160 190-92-34-160-94-160-190V122Z"
            fill="none" stroke="#22D3EE" strokeWidth="36" strokeLinejoin="round" />
          <path d="M170 230h120a24 24 0 1 0-24-24" fill="none" stroke="#FF6B3D" strokeWidth="30" strokeLinecap="round" />
          <path d="M170 310h90" fill="none" stroke="#93A4C4" strokeWidth="30" strokeLinecap="round" />
        </svg>
        <span className="text-ink">Aegis <span className="text-air">Air</span></span>
      </a>

      <div className="flex items-center gap-6">
        <a href="#instrument" className={link}>Instrument</a>
        <a href="#method" className={link}>Method</a>
        <a href="#proof" className={link}>Proof</a>
        <a
          href={APP_URL}
          className="btn-magnetic rounded-full bg-ember px-4 py-1.5 text-sm font-bold text-deep"
        >
          <span className="slide bg-air" aria-hidden="true" />
          <span>Open the app</span>
        </a>
      </div>
    </nav>
  );
}
