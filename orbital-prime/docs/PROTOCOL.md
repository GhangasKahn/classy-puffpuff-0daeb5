# ORBITAL PRIME — GOD-TIER PROMPT SYSTEM
## Multi-stage agent protocol · Art direction freeze → rebuild · No feature creep

**Version:** 1.0  
**Standard:** Commissioned instrument-grade frontend (Awwwards-caliber craft, no award claims)  
**Product:** Orbital Prime — mission cluster for night-sky / orbital observation  
**Hard rule:** No new features beyond the locked scope. Design and engineering quality only.

---

# HOW TO USE IN CURSOR

1. Open an empty or clean project folder for the rebuild (do not “patch” the old file into god-tier).
2. Paste **STAGE 0** first. Wait for the Art Direction Freeze document. Approve or revise once.
3. Paste **STAGE 1** with the freeze document attached. Wait for the Motion Grammar + Layout Score.
4. Paste **STAGE 2** — implement shell only.
5. Paste **STAGE 3** — bind data (existing connectors only).
6. Paste **STAGE 4** — motion implementation against the grammar.
7. Paste **STAGE 5** — adversarial audit + refine loop until rubric ≥ threshold.
8. Paste **STAGE 6** — handoff.

If the agent tries to add Starlink trains, social feeds, accounts, or new APIs: **reject**. Scope is frozen.

---

# GLOBAL CONSTITUTION (applies to every stage)

```xml
<constitution>
  <principle id="P1">Truth before persuasion. No invented proof, launches, users, or awards.</principle>
  <principle id="P2">Concept before components. No section exists without a job: orient, measure, or decide.</principle>
  <principle id="P3">One governing idea: “The instrument between you and the sky.”</principle>
  <principle id="P4">One signature interaction: ISS lock → gauges + radar + FACE bearing (+ AR path when available).</principle>
  <principle id="P5">One motion personality: precise, mechanical, weighted. Most UI does not move.</principle>
  <principle id="P6">Orange #FF6A00 is signal only (≤10% of surface). Not decoration.</principle>
  <principle id="P7">No generic AI residue: no gradient orbs, purple chrome, particle starfields, three equal cards, fake glass, empty parallax.</principle>
  <principle id="P8">Mobile is primary (390px authored first). Desktop is expansion, not the source.</principle>
  <principle id="P9">Accessibility and performance are design requirements, not cleanup.</principle>
  <principle id="P10">No feature creep. Scope lock below is absolute.</principle>
</constitution>
```

### Scope lock (features allowed — nothing else)

| Allowed | Forbidden |
|---------|-----------|
| ISS live position + look angles | New satellite programs beyond existing catalog toggles |
| SGP4 passes + naked-eye filter | Accounts, auth, social, chat |
| Weather gate + hourly PERFECT/MARGINAL/OBSTRUCTED | New APIs requiring secrets |
| RainViewer radar | Blog, shop, waitlist |
| Cluster HMI UI | 3D Earth WebGL hero (unless already trivial and on-scope) |
| Sky plot radar sweep + ground track | “Community” or fake live counts |
| Depth 1–4 density modes | Extra marketing pages |
| Hero parallax + section reveal | Scroll-jacking full-page takeovers |
| AR HUD + trajectory when possible | Native app rewrite |
| Physics formulas already defined | Any “nice to have” not listed |

---

# STAGE 0 — ART DIRECTION FREEZE
## Technique: Step-back + structured output + negative constraints + self-critique

```xml
<stage id="0" name="Art Direction Freeze">
  <role>
    You are a principal art director who has shipped instrument and editorial interfaces.
    You do not implement code in this stage. You produce a binding design constitution.
  </role>

  <step_back>
    Before any layout: What must Orbital Prime feel like in one sentence?
    What must it refuse to feel like?
    What is the single object of attention on the Night Sky surface?
  </step_back>

  <task>
    Produce ART_DIRECTION_FREEZE.md with EXACTLY these sections:

    1. Governing concept (1 sentence)
    2. Emotional register (3 adjectives max)
    3. Anti-references (5 bullets of what we will not resemble)
    4. Color tokens (hex + usage rule for each)
    5. Type system:
       - Display / Body / Data roles
       - Recommended families (system-safe + web)
       - Scale table for 390px and 1200px (px or rem)
       - Tracking / measure rules
    6. Grid & spacing (base unit, section padding, cluster internal rhythm)
    7. Cluster geometry (describe zones as a diagram in text/ASCII)
    8. Orange budget rule
    9. Imagery rule (hero subject, forbidden subjects)
    10. What “done” looks like for art direction (5 binary checks)

    Constraints:
    - No implementation code
    - No new features
    - No moodboard essay — only binding decisions
  </task>

  <self_critique>
    After drafting, list 5 ways this freeze could still produce a generic dark UI.
    Revise the freeze to close those holes.
    Output final freeze only.
  </self_critique>
</stage>
```

**Human gate:** Approve ART_DIRECTION_FREEZE.md before Stage 1.

---

# STAGE 1 — MOTION GRAMMAR + COMPOSITION SCORE
## Technique: Plan-and-solve + motion personality lock + few-shot anti-patterns

```xml
<stage id="1" name="Motion Grammar and Composition">
  <role>Motion director + HMI designer. No feature invention.</role>

  <input>Attach ART_DIRECTION_FREEZE.md</input>

  <anti_patterns>
    BAD: parallax on every section
    BAD: staggered fade on 20 elements
    BAD: bounce easings on gauges
    BAD: continuous background particle fields
    GOOD: one hero depth move; one radar continuous system; discrete reveals; heavy ease settle
  </anti_patterns>

  <task>
    Produce MOTION_AND_COMPOSITION.md:

    A. Motion personality paragraph (precise/mechanical/weighted)
    B. Easing tokens (name, cubic-bezier, when used)
    C. Duration tokens (xs/sm/md/lg)
    D. Allowed animated properties (prefer transform/opacity only)
    E. Motion inventory — MAX 12 moments. Table: id | trigger | element | purpose | reduced-motion fallback
    F. Signature interaction storyboard (5 steps, text only)
    G. Composition rules for cluster at 390px and 900px+
    H. Depth 1–4: exactly what is visible/hidden (no vague language)

    If inventory exceeds 12 moments, cut until 12.
  </task>

  <verification>
    For each motion moment, answer: “If this were removed, would orientation or measurement suffer?”
    Delete any moment with answer no.
  </verification>
</stage>
```

**Human gate:** Approve motion inventory count ≤ 12.

---

# STAGE 2 — STRUCTURAL SHELL (NO DATA)
## Technique: Decomposition + implementation constraints

```xml
<stage id="2" name="Structural Shell">
  <role>Senior frontend engineer implementing a frozen art direction. Zero new features.</role>

  <input>
    ART_DIRECTION_FREEZE.md
    MOTION_AND_COMPOSITION.md
  </input>

  <task>
    Build the static shell only:
    - index.html (or minimal Vite structure)
    - Design tokens as CSS variables
    - Header with depth 1–4 controls (wired to data-depth on body)
    - Hero with approved imagery treatment (placeholder OK if asset pending, but composition final)
    - Night Sky CLUSTER geometry matching freeze (empty gauges OK)
    - Physics / Starship / Live / Manifest / AR sections as composed surfaces (not card spam)
    - Footer
    - Responsive behavior at 390 and 1200
    - Depth CSS fully working
    - Reduced-motion CSS hooks present

    Forbidden in this stage: API calls, canvas drawing logic, AR camera, animations beyond CSS hooks.
  </task>

  <acceptance>
    - Depth 1–4 visibly changes structure
    - Cluster does not look like three stacked cards
    - Orange appears only as signal accents
    - No horizontal scroll at 390px
  </acceptance>
</stage>
```

---

# STAGE 3 — DATA BINDING (SCOPE LOCK)
## Technique: ReAct-style connector discipline + honest failure states

```xml
<stage id="3" name="Data Binding">
  <role>Systems engineer. Connect only approved public sources.</role>

  <approved_connectors>
    - ISS: api.wheretheiss.at/v1/satellites/25544
    - TLE: celestrak.org GP API + satellite.js SGP4
    - Weather: api.open-meteo.com (current + hourly)
    - Radar: api.rainviewer.com/public/weather-maps.json + tiles
    - Kp: services.swpc.noaa.gov planetary K-index JSON
  </approved_connectors>

  <task>
    Bind live data into the frozen cluster:
    1. Location: GPS + manual + Buffalo preset; honest failure on local file GPS
    2. ISS gauges + look angles + FACE copy + compass
    3. Sky plot + ground track (full width; parent-based canvas sizing; never collapsed)
    4. SGP4 passes + NAKED-EYE / DAY / ECLIPSED labeling
    5. Weather gate + hourly cross-check vs passes
    6. RainViewer radar panel with honest empty state
    7. AR HUD path: HTTPS camera; content/file → HUD-only + clear message
    8. Absolute orientation when available

    Every async path needs loading / success / failure UI that matches art direction.
  </task>

  <constraint>No new endpoints. No mock “demo mode” that pretends to be live without labeling.</constraint>
</stage>
```

---

# STAGE 4 — MOTION IMPLEMENTATION
## Technique: Grammar compliance check

```xml
<stage id="4" name="Motion Implementation">
  <input>MOTION_AND_COMPOSITION.md inventory only</input>

  <task>
    Implement ONLY the approved ≤12 motion moments.
    Wire depth toasts.
    Hero parallax + section reveals.
    Radar sweep with visibility pause.
    Compass easing.
    prefers-reduced-motion compliance verified.

    Delete any animation not on the inventory list.
  </task>

  <self_verify>
    List every requestAnimationFrame and scroll listener.
    Map each to an inventory id. Orphans must be removed.
  </self_verify>
</stage>
```

---

# STAGE 5 — ADVERSARIAL AUDIT + SELF-REFINE LOOP
## Technique: Generator / Auditor / Optimizer (adversarial trinity) + rubric scoring

```xml
<stage id="5" name="Adversarial Audit">
  <roles>
    <generator>Implementer of fixes</generator>
    <auditor>Hostile design critic; assumes the work is generic until proven otherwise</auditor>
    <optimizer>Applies only fixes that raise rubric scores without adding features</optimizer>
  </roles>

  <rubric max="10">
    R1 Strategic fit to “instrument between you and the sky” (0–10)
    R2 Concept originality / non-template identity (0–10)
    R3 Typography craft (0–10)
    R4 Composition / cluster hierarchy (0–10)
    R5 Motion restraint and purpose (0–10)
    R6 Interaction clarity (go/no-go in 30s) (0–10)
    R7 Mobile authorship (0–10)
    R8 Performance & stability (0–10)
    R9 Accessibility basics (0–10)
    R10 Orange discipline & visual signal hierarchy (0–10)
  </rubric>

  <pass_threshold>
    No dimension below 8. Mean ≥ 8.5.
  </pass_threshold>

  <auditor_protocol>
    1. Screenshot-level critique in text: hero, cluster, mobile nav, pass list, empty states.
    2. Answer: “If the logo is removed, is this still Orbital Prime?”
    3. Answer: “What still looks like every other dark AI dashboard?”
    4. Produce a punch list of at most 10 concrete fixes (no features).
  </auditor_protocol>

  <refine_loop>
    Repeat: audit → fix punch list → re-score.
    Stop when threshold met OR three loops with no score gain (then report blockers honestly).
  </refine_loop>
</stage>
```

---

# STAGE 6 — HANDOFF
## Technique: Constrained completion package

```xml
<stage id="6" name="Handoff">
  <task>
    Deliver only:

    1. Runnable project
    2. Governing concept (1 sentence)
    3. Signature interaction (1 sentence)
    4. Motion inventory final count
    5. Public data sources used
    6. Known limits (camera on content://, TLE CORS, compass variance)
    7. Rubric scores from final audit
    8. Explicit statement of features NOT added (creep rejection list)

    Do not claim awards. Do not claim “perfect.” Claim only what was built and measured.
  </task>
</stage>
```

---

# META-PROMPT (paste when the agent drifts)

```text
STOP. Re-read the constitution and scope lock.
You are not allowed to add features.
You are only allowed to raise craft: type, composition, motion restraint, hierarchy, states, performance.
Return to the current stage acceptance criteria.
If blocked, state the blocker in one sentence and propose a design-only resolution.
```

---

# OPERATOR CHEAT SHEET

| Stage | Output | Human action |
|-------|--------|--------------|
| 0 | ART_DIRECTION_FREEZE.md | Approve / edit once |
| 1 | MOTION_AND_COMPOSITION.md | Approve ≤12 motions |
| 2 | Static shell | Spot-check depth + cluster |
| 3 | Live data | Spot-check ISS + passes + weather |
| 4 | Motion | Spot-check reduced-motion |
| 5 | Audit loops | Demand scores; reject feature suggestions |
| 6 | Handoff | Ship or kill |

---

# DESIGN NORTH STARS (pin these)

1. Few ingredients, mastered.  
2. Big type + small type tension.  
3. Something large moves with purpose; most things don’t.  
4. Art direction is visible without the logo.  
5. Observer can decide go / no-go in thirty seconds.

---

**End of system.**  
This is a protocol, not a vibe. Run the stages in order. Kill feature ideas on sight.
'''
