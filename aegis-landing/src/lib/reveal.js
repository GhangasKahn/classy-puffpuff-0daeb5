import gsap from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";

gsap.registerPlugin(ScrollTrigger);

export const REDUCED =
  typeof window !== "undefined" &&
  window.matchMedia("(prefers-reduced-motion: reduce)").matches;

/* Measured Sage reveals: weighted fade-ups, nothing bounces.
   Reduced motion: elements simply appear. */
export function revealUp(ctxScope, targets, { y = 40, stagger = 0.08, trigger = null, start = "top 82%" } = {}) {
  if (REDUCED) {
    gsap.set(targets, { opacity: 1, y: 0 });
    return;
  }
  gsap.fromTo(
    targets,
    { opacity: 0, y },
    {
      opacity: 1, y: 0,
      duration: 1.1,
      ease: "power3.out",
      stagger,
      ...(trigger ? { scrollTrigger: { trigger, start } } : {}),
    }
  );
}

export { gsap, ScrollTrigger };
