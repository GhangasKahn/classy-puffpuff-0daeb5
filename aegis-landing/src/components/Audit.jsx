import { useEffect, useRef } from "react";
import { gsap, revealUp } from "../lib/reveal";

/* ACCUSATION AUDIT — the skeptic's lines, said harder than they would,
   answered only with what is true. */
const ROWS = [
  {
    accusation: "“This is another app harvesting my health data to sell.”",
    answer: "There is no server to sell from. Symptoms, heart rate, SpO₂ — all of it stays in your browser's local storage. Export it as JSON or delete it, any time, in one tap.",
  },
  {
    accusation: "“Air apps have been wrong before. Why trust this one?”",
    answer: "Don't trust it — read it. Every value is labeled with its model source, and the score expands into its seven components. When the data is modeled rather than measured, the app says so on the same screen.",
  },
  {
    accusation: "“It'll just tell me to panic, like everything else.”",
    answer: "It scores exposure, calmly, and stops. The only hard interruption is deliberate: report an emergency-level symptom and it stops scoring entirely and shows one thing — call 911. It is not a medical device and refuses to act like one.",
  },
];

export default function Audit() {
  const root = useRef(null);

  useEffect(() => {
    const ctx = gsap.context(() => {
      revealUp(root, ".audit-row", { y: 30, stagger: 0.12, trigger: root.current });
    }, root);
    return () => ctx.revert();
  }, []);

  return (
    <section ref={root} className="border-t border-line bg-deep/50">
      <div className="mx-auto max-w-5xl px-6 py-28 md:px-10 md:py-36">
        <p className="audit-row font-mono text-[11px] uppercase tracking-[0.28em] text-air">The audit</p>
        <h2 className="audit-row mt-3 text-3xl font-extrabold tracking-tight text-ink md:text-5xl">
          Say the worst part <span className="font-drama font-medium italic text-muted">out loud.</span>
        </h2>
        <div className="mt-14 space-y-10">
          {ROWS.map((r) => (
            <div key={r.accusation} className="audit-row grid gap-4 border-l-2 border-ember pl-6 md:grid-cols-2 md:gap-10">
              <p className="font-drama text-2xl italic leading-snug text-ink md:text-3xl">{r.accusation}</p>
              <p className="text-sm leading-relaxed text-muted md:text-base">{r.answer}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
