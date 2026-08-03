/* MARTIN Build — visual phase scenes (SVG) for the 5-step walk */
window.MARTIN_WALK = {
  phases: [
    {
      id: "mill",
      num: "01",
      title: "Mill & sticker",
      subtitle: "Select DF · rip for grain · acclimate",
      hero: "Buy oversized stock. Reject pith. Sticker 14+ days. Re-dimension for vertical grain before any joinery.",
      sheets: ["M6_cutlist.svg", "M8_mill.svg", "M7_shop.svg"],
      viz: "mill",
      highlights: [
        { title: "Buy list", body: "6×6 / 2×12 / 1×12 DF Select + 8/4 white oak ≈ 322 bf" },
        { title: "2×12 yield", body: "Outer thirds → rails & cap. Pith zone → waste / stakes." },
        { title: "Sticker", body: "¾″ stickers every 12–16″ · seal ends · weight the top." },
      ],
    },
    {
      id: "base",
      num: "02",
      title: "Site & pad",
      subtitle: "Leveling pad · drained sleeves · tip-out piers",
      hero: "Measure the 143″ opening and driveway drop. Pour a level pad with four sleeved socket piers that tip out for winter.",
      sheets: ["M4_pad_piers.svg", "M1_general.svg"],
      viz: "base",
      highlights: [
        { title: "Pad", body: '155″ × 28″ × 6″ + field-verified drop makeup (default 5″)' },
        { title: "Sleeves", body: "Sized to 2½×4½ tenon + ¼″ clear · ⌀½″ drain hole" },
        { title: "Piers", body: "14″ sq × 18″ tip-out · 4000 psi air-entrained" },
      ],
    },
    {
      id: "timber",
      num: "03",
      title: "Timber & nuki",
      subtitle: "Posts · mortises · rails · floating boards",
      hero: "Mill posts and rails to finished size. Cut Japanese through-mortises. Plow grooves. Dry-assemble the privacy run with oak kusabi — no nails.",
      sheets: ["M3_joinery.svg", "M2_elevation.svg", "M7_shop.svg"],
      viz: "timber",
      highlights: [
        { title: "Posts", body: "6×6 → 3½×5½×77″ · foot tenon 2½×4½×12″" },
        { title: "Nuki", body: "1½×7¼ rails · mortise +1/16″ height ease · oak wedges" },
        { title: "Boards", body: "¾×5½ float in ⅜×⅞ plows · ¼″ gaps · zero fasteners" },
      ],
    },
    {
      id: "gate",
      num: "04",
      title: "Gate & latch",
      subtitle: "Hozo · drawbore · wooden pintles",
      hero: "Build the 36″ leaf with drawbored mortise & tenon, half-lap brace, and lift-off wooden pintles. Latch into the house or P0.",
      sheets: ["M5_gate_latch.svg", "M3_joinery.svg"],
      viz: "gate",
      highlights: [
        { title: "Hozo", body: "⅛″ drawbore offset · ⌀⅜″ white oak pegs from MFT stops" },
        { title: "Hinge", body: "Wooden pintles on P1 — gate lifts straight up for winter" },
        { title: "Latch", body: "A: oak bar into house sleeve · B: mortise in P0" },
      ],
    },
    {
      id: "finish",
      num: "05",
      title: "Paint & set",
      subtitle: "Owner gray · drop in · lock",
      hero: "Mask locking faces. Primer + two coats owner gray. Drop posts into sleeves, re-wedge rails, hang the gate, walk for plumb.",
      sheets: ["M1_general.svg", "M6_cutlist.svg"],
      viz: "finish",
      highlights: [
        { title: "Paint", body: "Mask wedges, tenons, peg holes, sleeve contact, hinge faces" },
        { title: "Set", body: "Posts drop free · rails re-wedge snug · plumb ≤⅛″ / 65″" },
        { title: "Winter", body: "Reverse: wedges → rails → boards → gate → posts → tip piers" },
      ],
    },
  ],

  /** Draw a phase-specific SVG scene into a container */
  drawScene(phaseId, el, opts = {}) {
    const gray = opts.grayHex || "#6e7578";
    const scenes = {
      mill: () => `<svg viewBox="0 0 720 360" class="walk-svg" aria-label="Mill stock yield">
        <defs>
          <linearGradient id="gWood" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0%" stop-color="#c4b09a"/><stop offset="100%" stop-color="#8a7358"/>
          </linearGradient>
          <pattern id="rings" width="14" height="14" patternUnits="userSpaceOnUse">
            <circle cx="7" cy="7" r="5" fill="none" stroke="#5a4634" stroke-width=".6" opacity=".35"/>
          </pattern>
        </defs>
        <rect width="720" height="360" fill="#1a2228"/>
        <text x="36" y="42" fill="#8fad78" font-family="IBM Plex Mono,monospace" font-size="12" letter-spacing="2">2×12 YIELD · OUTER THIRDS</text>
        <!-- board face -->
        <g transform="translate(40,70)">
          <rect width="400" height="120" rx="4" fill="url(#gWood)" stroke="#f3f1ec" stroke-width="1.5"/>
          <rect width="400" height="120" fill="url(#rings)"/>
          <rect x="0" width="120" height="120" fill="#6e7578" opacity=".55"/>
          <rect x="280" width="120" height="120" fill="#6e7578" opacity=".55"/>
          <rect x="120" width="160" height="120" fill="#1a1f24" opacity=".35" stroke="#c4a35a" stroke-dasharray="5 4"/>
          <text x="60" y="66" text-anchor="middle" fill="#f3f1ec" font-family="IBM Plex Mono,monospace" font-size="13" font-weight="600">RAIL</text>
          <text x="200" y="66" text-anchor="middle" fill="#c4a35a" font-family="IBM Plex Mono,monospace" font-size="13" font-weight="600">PITH</text>
          <text x="340" y="66" text-anchor="middle" fill="#f3f1ec" font-family="IBM Plex Mono,monospace" font-size="13" font-weight="600">GATE</text>
        </g>
        <!-- sticker stack -->
        <g transform="translate(480,70)">
          <text x="0" y="-12" fill="#a8afb3" font-family="IBM Plex Mono,monospace" font-size="11">STICKER 14+ DAYS</text>
          ${[0,1,2,3,4].map((i)=>`
            <rect y="${i*36}" width="200" height="22" rx="2" fill="${i%2?'#9a8b74':'#b09a80'}" stroke="#1a1f24"/>
            <rect y="${i*36+22}" width="200" height="8" fill="none"/>
            <rect x="20" y="${i*36+24}" width="8" height="6" fill="#5a6a4a"/>
            <rect x="96" y="${i*36+24}" width="8" height="6" fill="#5a6a4a"/>
            <rect x="172" y="${i*36+24}" width="8" height="6" fill="#5a6a4a"/>
          `).join("")}
        </g>
        <text x="36" y="240" fill="#a8afb3" font-family="Libre Franklin,sans-serif" font-size="14">6×6 → posts · 2×12 → nuki/cap · 1×12 → boards · oak → wedges/pegs</text>
        <g transform="translate(36,270)">
          <rect width="140" height="54" rx="8" fill="#222a30" stroke="#5a6a4a"/>
          <text x="70" y="24" text-anchor="middle" fill="#8fad78" font-size="11" font-family="IBM Plex Mono,monospace">POSTS</text>
          <text x="70" y="42" text-anchor="middle" fill="#f3f1ec" font-size="13" font-family="Newsreader,serif">3½×5½</text>
          <rect x="156" width="140" height="54" rx="8" fill="#222a30" stroke="#5a6a4a"/>
          <text x="226" y="24" text-anchor="middle" fill="#8fad78" font-size="11" font-family="IBM Plex Mono,monospace">RAILS</text>
          <text x="226" y="42" text-anchor="middle" fill="#f3f1ec" font-size="13" font-family="Newsreader,serif">1½×7¼</text>
          <rect x="312" width="140" height="54" rx="8" fill="#222a30" stroke="#5a6a4a"/>
          <text x="382" y="24" text-anchor="middle" fill="#8fad78" font-size="11" font-family="IBM Plex Mono,monospace">BOARDS</text>
          <text x="382" y="42" text-anchor="middle" fill="#f3f1ec" font-size="13" font-family="Newsreader,serif">¾×5½</text>
          <rect x="468" width="140" height="54" rx="8" fill="#222a30" stroke="#c4a35a"/>
          <text x="538" y="24" text-anchor="middle" fill="#c4a35a" font-size="11" font-family="IBM Plex Mono,monospace">OAK</text>
          <text x="538" y="42" text-anchor="middle" fill="#f3f1ec" font-size="13" font-family="Newsreader,serif">kusabi · peg</text>
        </g>
      </svg>`,

      base: () => `<svg viewBox="0 0 720 360" class="walk-svg" aria-label="Pad and piers section">
        <rect width="720" height="360" fill="#1a2228"/>
        <text x="36" y="42" fill="#8fad78" font-family="IBM Plex Mono,monospace" font-size="12" letter-spacing="2">PAD SECTION · DRAINED SLEEVES</text>
        <!-- gravel -->
        <rect x="60" y="280" width="600" height="40" fill="#4a4844"/>
        <text x="360" y="305" text-anchor="middle" fill="#c5cbcf" font-size="12" font-family="IBM Plex Mono,monospace">#57 GRAVEL</text>
        <!-- makeup -->
        <rect x="80" y="250" width="560" height="30" fill="#7a7870"/>
        <text x="360" y="270" text-anchor="middle" fill="#f3f1ec" font-size="11" font-family="IBM Plex Mono,monospace">DROP MAKEUP</text>
        <!-- pad -->
        <rect x="70" y="210" width="580" height="40" fill="#b8b6b0" stroke="#f3f1ec"/>
        <text x="360" y="235" text-anchor="middle" fill="#1a1f24" font-size="13" font-family="IBM Plex Mono,monospace" font-weight="600">LEVEL PAD TOP</text>
        <!-- four piers + sleeves + tenons -->
        ${[120,260,400,540].map((x,i)=>`
          <rect x="${x}" y="150" width="70" height="60" fill="#9a9890" stroke="#1a1f24"/>
          <rect x="${x+18}" y="100" width="34" height="110" fill="none" stroke="#8fad78" stroke-width="2" stroke-dasharray="4 3"/>
          <rect x="${x+22}" y="70" width="26" height="100" fill="#d9dcde" stroke="#1a1f24"/>
          <rect x="${x+16}" y="40" width="38" height="40" fill="#d9dcde" stroke="#1a1f24"/>
          <text x="${x+35}" y="34" text-anchor="middle" fill="#8fad78" font-size="12" font-family="IBM Plex Mono,monospace">P${i}</text>
        `).join("")}
        <text x="36" y="345" fill="#a8afb3" font-size="13" font-family="Libre Franklin,sans-serif">Sleeve = tenon + ¼″ clear for winter pull · drain at bottom · tip-out piers</text>
      </svg>`,

      timber: () => `<svg viewBox="0 0 720 360" class="walk-svg" aria-label="Timber nuki assembly">
        <rect width="720" height="360" fill="#1a2228"/>
        <text x="36" y="42" fill="#8fad78" font-family="IBM Plex Mono,monospace" font-size="12" letter-spacing="2">NUKI THROUGH-RAILS · NO NAILS</text>
        <!-- posts -->
        ${[80,280,480,640].map((x,i)=>`
          <rect x="${x}" y="60" width="28" height="250" fill="#d9dcde" stroke="#1a1f24" stroke-width="1.5"/>
          <text x="${x+14}" y="52" text-anchor="middle" fill="#8fad78" font-size="11" font-family="IBM Plex Mono,monospace">P${i}</text>
          <!-- mortise windows -->
          <rect x="${x-6}" y="110" width="40" height="36" fill="#1a2228" stroke="#5a6a4a"/>
          <rect x="${x-6}" y="170" width="40" height="36" fill="#1a2228" stroke="#5a6a4a"/>
          <rect x="${x-6}" y="230" width="40" height="36" fill="#1a2228" stroke="#5a6a4a"/>
        `).join("")}
        <!-- rails sliding through P1-P3 -->
        <rect class="anim-slide" x="260" y="118" width="420" height="20" fill="${gray}" stroke="#1a1f24"/>
        <rect class="anim-slide" x="260" y="178" width="420" height="20" fill="${gray}" stroke="#1a1f24" style="animation-delay:.15s"/>
        <rect class="anim-slide" x="260" y="238" width="420" height="20" fill="${gray}" stroke="#1a1f24" style="animation-delay:.3s"/>
        <!-- wedges -->
        ${[280,480,640].map((x)=>`
          <polygon points="${x+30},128 ${x+48},138 ${x+30},148" fill="#c4a35a"/>
          <polygon points="${x+30},188 ${x+48},198 ${x+30},208" fill="#c4a35a"/>
          <polygon points="${x+30},248 ${x+48},258 ${x+30},268" fill="#c4a35a"/>
        `).join("")}
        <!-- floating boards hint -->
        ${[320,350,380,410,440].map((x)=>`
          <rect x="${x}" y="148" width="14" height="22" fill="#cfd3d5" stroke="#9aa3a6"/>
          <rect x="${x}" y="208" width="14" height="22" fill="#cfd3d5" stroke="#9aa3a6"/>
        `).join("")}
        <text x="36" y="340" fill="#a8afb3" font-size="13" font-family="Libre Franklin,sans-serif">Kusabi wedges lock · boards float in plowed grooves · reverse for winter</text>
      </svg>`,

      gate: () => `<svg viewBox="0 0 720 360" class="walk-svg" aria-label="Gate hozo joinery">
        <rect width="720" height="360" fill="#1a2228"/>
        <text x="36" y="42" fill="#8fad78" font-family="IBM Plex Mono,monospace" font-size="12" letter-spacing="2">GATE LEAF · HOZO + DRAWBORE</text>
        <!-- posts -->
        <rect x="80" y="50" width="30" height="270" fill="#d9dcde" stroke="#1a1f24"/>
        <rect x="280" y="50" width="30" height="270" fill="#d9dcde" stroke="#1a1f24"/>
        <text x="95" y="44" text-anchor="middle" fill="#8fad78" font-size="12" font-family="IBM Plex Mono,monospace">P0</text>
        <text x="295" y="44" text-anchor="middle" fill="#8fad78" font-size="12" font-family="IBM Plex Mono,monospace">P1</text>
        <!-- gate -->
        <g class="anim-swing" transform-origin="295px 180px">
          <rect x="120" y="60" width="150" height="250" fill="#e8eaeb" stroke="#5a6a4a" stroke-width="2"/>
          <rect x="120" y="60" width="22" height="250" fill="#d9dcde" stroke="#1a1f24"/>
          <rect x="248" y="60" width="22" height="250" fill="#d9dcde" stroke="#1a1f24"/>
          <rect x="142" y="100" width="106" height="18" fill="${gray}" stroke="#1a1f24"/>
          <rect x="142" y="160" width="106" height="18" fill="${gray}" stroke="#1a1f24"/>
          <rect x="142" y="220" width="106" height="18" fill="${gray}" stroke="#1a1f24"/>
          <line x1="142" y1="250" x2="248" y2="90" stroke="#5a6a4a" stroke-width="6"/>
          <!-- pegs -->
          <circle cx="150" cy="109" r="4" fill="#c4a35a"/>
          <circle cx="150" cy="169" r="4" fill="#c4a35a"/>
          <circle cx="150" cy="229" r="4" fill="#c4a35a"/>
          <circle cx="260" cy="109" r="4" fill="#c4a35a"/>
          <circle cx="260" cy="169" r="4" fill="#c4a35a"/>
          <circle cx="260" cy="229" r="4" fill="#c4a35a"/>
        </g>
        <!-- latch bar -->
        <rect x="40" y="155" width="90" height="18" fill="#aeb6ba" stroke="#1a1f24"/>
        <text x="85" y="148" text-anchor="middle" fill="#c4a35a" font-size="11" font-family="IBM Plex Mono,monospace">LATCH</text>
        <!-- callouts -->
        <g transform="translate(380,80)">
          <rect width="300" height="220" rx="10" fill="#222a30" stroke="#3d5a4c"/>
          <text x="20" y="36" fill="#8fad78" font-size="12" font-family="IBM Plex Mono,monospace">JOINERY</text>
          <text x="20" y="70" fill="#f3f1ec" font-size="16" font-family="Newsreader,serif">Hozo ほぞ — drawbored M&T</text>
          <text x="20" y="100" fill="#a8afb3" font-size="13" font-family="Libre Franklin,sans-serif">⅛″ offset pulls joint closed</text>
          <text x="20" y="140" fill="#f3f1ec" font-size="16" font-family="Newsreader,serif">Half-lap brace — no fasteners</text>
          <text x="20" y="180" fill="#f3f1ec" font-size="16" font-family="Newsreader,serif">Wooden pintles — lift off</text>
          <text x="20" y="210" fill="#a8afb3" font-size="13" font-family="Libre Franklin,sans-serif">36″ clear · aligns with Prairie bands</text>
        </g>
      </svg>`,

      finish: () => `<svg viewBox="0 0 720 360" class="walk-svg" aria-label="Finished fence set">
        <defs>
          <linearGradient id="sky" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stop-color="#2a3540"/><stop offset="100%" stop-color="#1a2228"/>
          </linearGradient>
        </defs>
        <rect width="720" height="360" fill="url(#sky)"/>
        <text x="36" y="42" fill="#8fad78" font-family="IBM Plex Mono,monospace" font-size="12" letter-spacing="2">SET · OWNER GRAY · REMOVABLE</text>
        <rect x="40" y="280" width="640" height="28" fill="#9a9890"/>
        ${[70,220,400,580].map((x)=>`
          <rect x="${x}" y="90" width="24" height="190" fill="${gray}" stroke="#1a1f24"/>
        `).join("")}
        <rect x="210" y="140" width="400" height="16" fill="${gray}" stroke="#1a1f24"/>
        <rect x="210" y="185" width="400" height="16" fill="${gray}" stroke="#1a1f24"/>
        <rect x="210" y="230" width="400" height="16" fill="${gray}" stroke="#1a1f24"/>
        <rect x="210" y="90" width="400" height="12" fill="${gray}" stroke="#1a1f24"/>
        ${Array.from({length:12},(_,i)=>`<rect x="${230+i*32}" y="156" width="14" height="24" fill="#b8bdc0" opacity=".85"/>`).join("")}
        ${Array.from({length:12},(_,i)=>`<rect x="${230+i*32}" y="201" width="14" height="24" fill="#b8bdc0" opacity=".85"/>`).join("")}
        <!-- gate -->
        <rect x="100" y="100" width="100" height="170" fill="${gray}" stroke="#8fad78" stroke-width="2"/>
        <line x1="110" y1="250" x2="190" y2="110" stroke="#5a6a4a" stroke-width="4"/>
        <text x="360" y="330" text-anchor="middle" fill="#a8afb3" font-size="13" font-family="Libre Franklin,sans-serif">143″ × 65″ · Japanese joinery · winter knock-down ready</text>
      </svg>`,
    };
    const fn = scenes[phaseId] || scenes.mill;
    el.innerHTML = fn();
  },
};
