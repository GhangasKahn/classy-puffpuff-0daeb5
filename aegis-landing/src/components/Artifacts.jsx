import { useEffect, useRef, useState } from "react";
import { gsap, revealUp, REDUCED } from "../lib/reveal";
import { compass16 } from "../lib/useLiveAir";

/* FUNCTIONAL ARTIFACTS — working micro-UIs, not marketing cards.
   Each one is a small, honest piece of the instrument itself. */

/* 1 — Diagnostic Shuffler: the transparent score, cycling its real components */
function Shuffler() {
  const [cards, setCards] = useState([
    { k: "AIR BURDEN", v: "+16.4", note: "US AQI, linear to 300", tone: "text-ember" },
    { k: "UPWIND FIRE", v: "+4.7", note: "wind ∩ EONET bearing", tone: "text-ember" },
    { k: "SENSITIVITY", v: "×1.15", note: "your profile, capped ×1.6", tone: "text-air" },
  ]);

  useEffect(() => {
    if (REDUCED) return;
    const id = setInterval(() => {
      setCards(prev => {
        const next = [...prev];
        next.unshift(next.pop());
        return next;
      });
    }, 3000);
    return () => clearInterval(id);
  }, []);

  return (
    <div className="relative h-44" aria-label="Score components cycling">
      {cards.map((c, i) => (
        <div
          key={c.k}
          className="shuffle-card absolute inset-x-0 rounded-card border border-line bg-night p-4"
          style={{
            transform: `translateY(${i * 26}px) scale(${1 - i * 0.045})`,
            zIndex: 10 - i,
            opacity: 1 - i * 0.28,
            filter: i > 0 ? `blur(${i * 0.6}px)` : "none",
          }}
        >
          <div className="flex items-baseline justify-between">
            <span className="font-mono text-[10px] uppercase tracking-[0.22em] text-muted">{c.k}</span>
            <span className={`readout font-mono text-xl font-medium ${c.tone}`}>{c.v}</span>
          </div>
          <p className="mt-1.5 text-xs text-muted">{c.note}</p>
        </div>
      ))}
    </div>
  );
}

/* 2 — Telemetry Typewriter: a live feed typing what the instrument sees */
function Typewriter({ live }) {
  const msgs = useRef([]);
  const [text, setText] = useState("");
  const [msgIdx, setMsgIdx] = useState(0);

  useEffect(() => {
    msgs.current = live.ready && live.aqi != null
      ? [
          `US AQI ${Math.round(live.aqi)} · PM2.5 ${live.pm25?.toFixed(1)} µg/m³ over Buffalo`,
          `wind ${Math.round(live.windSpd ?? 0)} km/h from ${compass16(live.windDir)} — plume sector computed`,
          `72-hour CAMS outlook loaded · trend scored`,
          `EONET wildfire catalog scanned within 2,600 km`,
        ]
      : [
          "connecting to CAMS atmosphere models…",
          "wind field · fire catalog · 72 h outlook",
          "all scoring runs on your device",
        ];
  }, [live]);

  useEffect(() => {
    if (REDUCED) {
      setText(msgs.current[0] ?? "");
      return;
    }
    let i = 0, alive = true;
    const line = msgs.current[msgIdx % Math.max(msgs.current.length, 1)] ?? "";
    const type = () => {
      if (!alive) return;
      if (i <= line.length) {
        setText(line.slice(0, i));
        i += 1;
        setTimeout(type, 34);
      } else {
        setTimeout(() => alive && setMsgIdx(m => m + 1), 2100);
      }
    };
    type();
    return () => { alive = false; };
  }, [msgIdx, live.ready]);

  return (
    <div className="flex h-44 flex-col rounded-card border border-line bg-night p-4">
      <div className="flex items-center gap-2 font-mono text-[10px] uppercase tracking-[0.22em] text-muted">
        <span className="pulse-dot inline-block h-1.5 w-1.5 rounded-full bg-ember" aria-hidden="true" />
        Live feed
      </div>
      <p className="readout mt-4 flex-1 font-mono text-sm leading-relaxed text-ink">
        {text}
        <span className="tw-cursor ml-0.5 inline-block h-4 w-[7px] translate-y-[3px] bg-ember" aria-hidden="true" />
      </p>
      <span className="font-mono text-[10px] text-muted">source: open-meteo · cams · eonet</span>
    </div>
  );
}

/* 3 — Pulse Waveform: the check-in, drawn as an EKG that never claims to be one */
function Waveform() {
  return (
    <div className="flex h-44 flex-col rounded-card border border-line bg-night p-4">
      <div className="flex items-center justify-between font-mono text-[10px] uppercase tracking-[0.22em] text-muted">
        <span>Check-in · symptoms &amp; vitals</span>
        <span className="readout text-air">HR Δ vs your baseline</span>
      </div>
      <svg viewBox="0 0 300 80" className="mt-3 flex-1" preserveAspectRatio="none" aria-hidden="true">
        <path
          d="M0 40 H55 L68 40 74 18 82 62 90 40 H140 L153 40 159 22 167 58 175 40 H225 L238 40 244 16 252 64 260 40 H300"
          fill="none" stroke="#22D3EE" strokeWidth="2" className="ekg-path"
        />
        <path
          d="M0 40 H55 L68 40 74 18 82 62 90 40 H140 L153 40 159 22 167 58 175 40 H225 L238 40 244 16 252 64 260 40 H300"
          fill="none" stroke="#22D3EE" strokeWidth="2" opacity="0.15"
        />
      </svg>
      <span className="font-mono text-[10px] text-muted">SpO₂ recorded, never scored — by design</span>
    </div>
  );
}

export default function Artifacts({ live }) {
  const root = useRef(null);

  useEffect(() => {
    const ctx = gsap.context(() => {
      revealUp(root, ".artifact", { y: 40, stagger: 0.15, trigger: root.current });
    }, root);
    return () => ctx.revert();
  }, []);

  const blocks = [
    {
      title: "A score you can audit",
      desc: "Seven components, visible math, capped at 100. Open any day's number and read exactly why.",
      ui: <Shuffler />,
    },
    {
      title: "The sky, streamed",
      desc: "Wind, particle burden, fire catalog, 72-hour outlook — read continuously from public atmosphere models.",
      ui: <Typewriter live={live} />,
    },
    {
      title: "Your body, on the record",
      desc: "Symptoms, heart rate, time outdoors — logged against the air that was there when you felt it.",
      ui: <Waveform />,
    },
  ];

  return (
    <section id="instrument" ref={root} className="mx-auto max-w-6xl px-6 py-28 md:px-10 md:py-36">
      <p className="artifact font-mono text-[11px] uppercase tracking-[0.28em] text-air">The instrument</p>
      <h2 className="artifact mt-3 max-w-2xl text-3xl font-extrabold tracking-tight text-ink md:text-5xl">
        Three dials. <span className="font-drama font-medium italic text-muted">Nothing hidden behind them.</span>
      </h2>
      <div className="mt-14 grid gap-6 md:grid-cols-3">
        {blocks.map(b => (
          <article key={b.title} className="artifact rounded-card border border-line bg-surface p-5 shadow-[0_16px_50px_rgba(0,0,0,.35)]">
            {b.ui}
            <h3 className="mt-5 text-lg font-bold text-ink">{b.title}</h3>
            <p className="mt-2 text-sm leading-relaxed text-muted">{b.desc}</p>
          </article>
        ))}
      </div>
    </section>
  );
}
