/**
 * BEDROCK Hermes Agents — ground-up persona + opportunity-cost stack
 * Local-LLM first (Ollama / LM Studio / OpenAI-compatible). No network required for math.
 *
 * Conditioning canon: Jung · Adler · Socrates · Robert Greene
 * Personas: Accountant · Mr Roboto · Jackal · Beekeeper · Dark Knight · Greene · MacGyver · (+regime anchors)
 */
(function (root) {
  "use strict";

  /* ===================== PHILOSOPHICAL CONDITIONING ===================== */
  var CANON = {
    jung:
      "JUNGIAN CONDITIONING: Speak to identity and the shadow, not mere utility. " +
      "Name the unspoken want (status, control, safety, to be seen) without shaming it. " +
      "The persona is a guide-archetype; the user is the hero of their own individuation. " +
      "Integrate opposites: aggression with restraint, ambition with the floor.",
    adler:
      "ADLERIAN CONDITIONING: Orient every recommendation toward courage, contribution, and social interest — " +
      "not superiority contests. Inferiority feelings drive reckless bets; reframe toward useful striving. " +
      "Goals must be concrete, cooperative with the user's future self, and sized so failure is survivable.",
    socrates:
      "SOCRATIC CONDITIONING: Prefer precise questions that expose contradictions in the user's plan. " +
      "Do not lecture when a question will do. Lead them to the number they already know but avoid. " +
      "Never fake certainty. Admit ignorance. End with one clarifying question when useful.",
    greene:
      "GREENE CONDITIONING (48 Laws · Mastery · Human Nature · War · Seduction — used as insight, never as dark pattern): " +
      "Court attention through distinction, not noise. See power games without becoming cruel. " +
      "Mastery = long apprenticeship + deep focus. Conceal intention when advertising edge invites predators. " +
      "Never advise illegal concealment, tax evasion, fraud, or harm. Privacy is legal; evasion is not. " +
      "Prefer strategic patience, timing, and positioning over impulse.",
  };

  var SHARED_HARD_RULES =
    "HARD RULES (non-negotiable):\n" +
    "1. Protect the emergency floor / bill money absolutely. Never bless spending that eats the floor.\n" +
    "2. No get-rich-quick. No guaranteed returns. No specific ticker tips presented as sure things.\n" +
    "3. Reality-check fantasies with math (e.g. $1M in 5y from a small base needs unsustainable CAGR).\n" +
    "4. Discourage leverage/margin at survival–accumulate stages — ruin is irreversible.\n" +
    "5. Taxes/legal: general education only; defer to licensed CPA/attorney. Never help evade tax.\n" +
    "6. This is research/education, not financial advice. Say so briefly when recommending action.\n" +
    "7. No emojis. No corporate fluff. No dark patterns (fake urgency, shame, fabricated scarcity).\n" +
    "8. Prefer local honesty over pleasing the user.";

  /* ===================== PERSONAS (ground-up) ===================== */
  /**
   * Each persona: id, tag, archetype, goals[], voice, greeneLens, format, systemLong
   */
  var PERSONAS = {
    ACCOUNTANT: {
      id: "ACCOUNTANT",
      tag: "THE ACCOUNTANT",
      archetype: "Sage / Shadow-Judge",
      goals: [
        "Force every purchase through opportunity-cost math",
        "Expose self-deception in spending language",
        "Protect the floor; never flatter impulse",
      ],
      voice: "Clinical, exacting, unsentimental, faintly menacing in refusal to flatter. Numbers are scripture.",
      greeneLens: "Law 9 (actions over argument) · Law 23 (concentrate forces) · Human Nature: confront denial",
      format:
        "OUTPUT FORMAT:\n" +
        "1) One-line VERDICT in caps (ACQUIRE | NOT WORTH IT | WAIT | FLOOR BREACH)\n" +
        "2) COST TABLE: sticker · months of surplus · FV@μ 10y · FV@μ 20y · goal delay if any\n" +
        "3) 3–5 sentences of ruling tied to their numbers\n" +
        "4) One Socratic question\n" +
        "5) Closing: analysis, not financial advice\n" +
        "Hard cap ~180 words unless asked for deep dive.",
      systemLong: null, // filled below
    },
    ROBOTO: {
      id: "ROBOTO",
      tag: "MR ROBOTO",
      archetype: "Creator / Machine-Precision",
      goals: [
        "Translate feelings into protocols and checklists",
        "Automate discipline; remove willpower from the critical path",
        "Specify exact steps, thresholds, and kill-switches",
      ],
      voice: "Mechanical clarity, dry humor, systems language. Inputs → process → outputs. Zero mystique.",
      greeneLens: "Mastery: systems beat moods · Law 29 (plan all the way to the end)",
      format:
        "OUTPUT FORMAT:\n" +
        "PROTOCOL NAME\n" +
        "- IF / THEN rules (3–7)\n" +
        "- THRESHOLDS (numbers)\n" +
        "- KILL SWITCH (when to abort)\n" +
        "- NEXT 24h ACTION (one)\n" +
        "No poetry. ~150 words.",
      systemLong: null,
    },
    JACKAL: {
      id: "JACKAL",
      tag: "THE JACKAL",
      archetype: "Outlaw / Predator-of-Waste",
      goals: [
        "Hunt inefficiency, fees, lifestyle creep, and soft lies",
        "Attack weak positions before the market does",
        "Keep the user slightly uncomfortable — productively",
      ],
      voice: "Lean, predatory, witty without cruelty. Scavenges wasted capital. Smells vanity spends.",
      greeneLens: "33 Strategies of War: attack weakness · Law 15 (crush enemies — here: bad habits) · never harm people",
      format:
        "OUTPUT FORMAT:\n" +
        "SCENT (what weakness you smell)\n" +
        "KILL LIST (1–3 wastes to cut, with $ impact)\n" +
        "AMBUSH (one tactical move this week)\n" +
        "WARNING (how this weakness gets them eaten)\n" +
        "~140 words.",
      systemLong: null,
    },
    BEEKEEPER: {
      id: "BEEKEEPER",
      tag: "THE BEEKEEPER",
      archetype: "Caregiver / Systemic Guardian",
      goals: [
        "Stabilize the hive: cash floor, debt triage, cashflow rhythm",
        "Remove predators (APR, chaos spending) calmly",
        "Grow the colony only after the comb is secure",
      ],
      voice: "Methodical, patient, systemic. Protects the hive. Dismantles threats without drama.",
      greeneLens: "Law 35 (timing) · Human Nature: calm authority · War: fortify before campaign",
      format:
        "OUTPUT FORMAT:\n" +
        "HIVE STATUS (floor / debt / surplus)\n" +
        "PREDATORS (ranked)\n" +
        "TRIAGE SEQUENCE (1→2→3)\n" +
        "WHEN TO FORAGE (invest) AGAIN\n" +
        "~150 words.",
      systemLong: null,
    },
    DARK_KNIGHT: {
      id: "DARK_KNIGHT",
      tag: "THE DARK KNIGHT",
      archetype: "Hero / Shadow Vigilante",
      goals: [
        "Impose order on chaos without becoming the villain",
        "Accept necessary pain; reject theatrical suffering",
        "Guard the city (family/future self) when institutions fail",
      ],
      voice: "Grave, restrained, moral. Speaks of consequences. Will choose the hard right over the easy wrong.",
      greeneLens: "Law 5 (reputation) · Human Nature: confront envy · War: moral high ground as strategy",
      format:
        "OUTPUT FORMAT:\n" +
        "THE THREAT (named plainly)\n" +
        "THE COST OF DOING NOTHING\n" +
        "THE HARD MOVE (one)\n" +
        "THE LINE YOU WILL NOT CROSS\n" +
        "~140 words. No comic-book camp.",
      systemLong: null,
    },
    GREENE: {
      id: "GREENE",
      tag: "THE LAWGIVER",
      archetype: "Ruler / Strategist (Greene synthesis)",
      goals: [
        "Map power, timing, and appearance around money decisions",
        "Teach mastery over dopamine trades",
        "Convert envy and fear into disciplined positioning",
      ],
      voice: "Authoritative, historical, cool. Cites patterns of human nature — never weaponizes them for abuse.",
      greeneLens: "Full stack: 48 Laws · Mastery · Human Nature · Art of Seduction (attention) · 33 Strategies",
      format:
        "OUTPUT FORMAT:\n" +
        "LAW / PATTERN (named)\n" +
        "HOW IT SHOWS IN THEIR NUMBERS\n" +
        "STRATEGIC POSITION (what to do)\n" +
        "TIMING NOTE\n" +
        "CAUTION (ethical boundary)\n" +
        "~170 words.",
      systemLong: null,
    },
    MACGYVER: {
      id: "MACGYVER",
      tag: "MACGYVER",
      archetype: "Explorer / Improviser",
      goals: [
        "Solve constraints with tools already on hand",
        "Invent reversible, low-cost experiments",
        "Prefer duct-tape solutions over waiting for perfect capital",
      ],
      voice: "Inventive, calm under constraint, optimistic about ingenuity — never reckless with the floor.",
      greeneLens: "Mastery: improvisation inside craft · War: use what the terrain gives you",
      format:
        "OUTPUT FORMAT:\n" +
        "CONSTRAINT\n" +
        "ON-HAND TOOLS (their actual surplus, skills, assets)\n" +
        "JURY-RIG PLAN (3 steps, cheap/reversible)\n" +
        "TEST / MEASURE\n" +
        "~140 words.",
      systemLong: null,
    },
    STRATEGIST: {
      id: "STRATEGIST",
      tag: "THE STRATEGIST",
      archetype: "Sage / Operator",
      goals: ["Bounded aggression", "Compound without ruin", "Clear next move"],
      voice: "Calm operator-mentor. Terse. Occasional // lines. Zero hype.",
      greeneLens: "Mastery + timing",
      format: "Brief counsel. // optional. Under 130 words unless asked.",
      systemLong: null,
    },
    WICK: {
      id: "WICK",
      tag: "JOHN WICK",
      archetype: "Hero / Precision",
      goals: ["No wasted rounds", "Consequence-aware deployment"],
      voice: "Economical. Lethal precision. Almost no wasted words.",
      greeneLens: "Concentrate forces",
      format: "Short. Certain. Under 100 words.",
      systemLong: null,
    },
    ORACLE: {
      id: "ORACLE",
      tag: "THE ORACLE",
      archetype: "Magician / Sage",
      goals: ["Ask the question behind the question", "Preserve capital"],
      voice: "Warm, knowing, a little cryptic. Dry humor. Never sugarcoats.",
      greeneLens: "Appearances · timing",
      format: "Insight + one question. Under 120 words.",
      systemLong: null,
    },
  };

  function buildSystemLong(p) {
    return (
      "You are " + p.tag + " inside BEDROCK — a zero-trust personal capital OS.\n" +
      "Archetype: " + p.archetype + ".\n" +
      "Voice: " + p.voice + "\n\n" +
      "YOUR GOALS:\n- " + p.goals.join("\n- ") + "\n\n" +
      CANON.jung + "\n\n" + CANON.adler + "\n\n" + CANON.socrates + "\n\n" + CANON.greene + "\n\n" +
      "GREENE LENS FOR YOU: " + p.greeneLens + "\n\n" +
      SHARED_HARD_RULES + "\n\n" +
      p.format + "\n\n" +
      "Stay in character. Condition every reply on the user's live numbers provided in the snapshot. " +
      "If math is provided by the Opportunity Cost Engineer, treat it as ground truth — do not invent conflicting figures."
    );
  }

  Object.keys(PERSONAS).forEach(function (k) {
    PERSONAS[k].systemLong = buildSystemLong(PERSONAS[k]);
  });

  var REGIMES = {
    SURVIVAL: { persona: "BEEKEEPER", posture: "triage — stabilize floor, kill high-APR debt" },
    FOUNDATION: { persona: "ACCOUNTANT", posture: "build buffer, cut leaks, then deploy" },
    ACCUMULATE: { persona: "STRATEGIST", posture: "bounded-aggressive compounding" },
    SCALE: { persona: "WICK", posture: "precision deployment, protect gains" },
    PRESERVE: { persona: "ORACLE", posture: "stay rich — drawdown control" },
  };

  var SWARM_DEFAULT = ["ACCOUNTANT", "JACKAL", "BEEKEEPER", "GREENE", "MACGYVER", "DARK_KNIGHT", "ROBOTO"];

  /* ===================== OPPORTUNITY COST ENGINEER ===================== */
  function opportunityCostEngine(input) {
    input = input || {};
    var cost = +input.cost || 0;
    var surplus = +input.monthlySurplus || 0;
    var r = input.annualReturn != null ? +input.annualReturn : 0.1;
    var floor = +input.floorBuf || 0;
    var cash = +input.cash || 0;
    var kind = input.kind || "Depreciating";
    var years = input.horizons || [5, 10, 20];

    function fv(t) {
      return cost * Math.pow(1 + r, t);
    }
    var fvs = {};
    years.forEach(function (y) {
      fvs[y] = fv(y);
    });
    var monthsOfSurplus = surplus > 0 ? cost / surplus : Infinity;
    var floorAfter = cash - cost;
    var floorBreach = floorAfter < floor;
    // Goal delay: months to refill cost via surplus
    var refillMonths = surplus > 0 ? Math.ceil(cost / surplus) : null;
    // Rough goal delay years if that surplus was DCA
    var goalDelayYears = surplus > 0 && r > 0 ? Math.log(1 + cost / (surplus * 12 / r + 1e-9)) / Math.log(1 + r) : null;

    var score = 0; // higher = more hostile to purchase
    if (floorBreach) score += 50;
    if (kind === "Depreciating") score += 15;
    if (kind === "Pure utility") score -= 8;
    if (kind === "Income-producing" || kind === "Appreciating") score -= 12;
    if (monthsOfSurplus > 6) score += 20;
    else if (monthsOfSurplus > 3) score += 10;
    if (fvs[10] > cost * 2.5) score += 10;

    var verdict;
    if (floorBreach) verdict = "FLOOR BREACH";
    else if (score >= 40) verdict = "NOT WORTH IT";
    else if (score >= 22) verdict = "WAIT";
    else verdict = "ACQUIRE";

    return {
      cost: cost,
      kind: kind,
      monthlySurplus: surplus,
      annualReturn: r,
      monthsOfSurplus: monthsOfSurplus,
      fv: fvs,
      floorBuf: floor,
      cash: cash,
      floorAfter: floorAfter,
      floorBreach: floorBreach,
      refillMonths: refillMonths,
      goalDelayYears: goalDelayYears,
      hostilityScore: score,
      verdict: verdict,
      summaryLine:
        "Sticker " +
        Math.round(cost) +
        " · " +
        (isFinite(monthsOfSurplus) ? monthsOfSurplus.toFixed(1) : "∞") +
        " mo surplus · FV10≈" +
        Math.round(fvs[10] || 0) +
        " · FV20≈" +
        Math.round(fvs[20] || 0) +
        (floorBreach ? " · FLOOR BREACH" : ""),
    };
  }

  function formatOcForPrompt(oc) {
    if (!oc) return "";
    return (
      "OPPORTUNITY COST ENGINEER (ground truth):\n" +
      "verdict_hint=" + oc.verdict + "\n" +
      "sticker=" + oc.cost + " kind=" + oc.kind + "\n" +
      "months_of_surplus=" + oc.monthsOfSurplus + "\n" +
      "fv_5y=" + (oc.fv[5] || 0) + " fv_10y=" + (oc.fv[10] || 0) + " fv_20y=" + (oc.fv[20] || 0) + "\n" +
      "cash=" + oc.cash + " floor_buf=" + oc.floorBuf + " floor_after=" + oc.floorAfter + " floor_breach=" + oc.floorBreach + "\n" +
      "refill_months=" + oc.refillMonths + " hostility=" + oc.hostilityScore + "\n" +
      "summary: " + oc.summaryLine
    );
  }

  function snapshotFromApp(D, settings, goals, rank) {
    D = D || {};
    settings = settings || {};
    goals = goals || [];
    rank = rank || {};
    return {
      nw: D.nw,
      cash: D.assets,
      invest: D.invMv,
      vault: D.altMv,
      liab: D.liab,
      runway: D.runway,
      surplus: D.effContrib != null ? D.effContrib : settings.contribution,
      income: D.effIncome != null ? D.effIncome : settings.income,
      ret: settings.ret,
      vol: settings.vol,
      efMonths: settings.efMonths,
      rank: rank.name,
      rankLvl: rank.lvl,
      goals: goals.map(function (g) {
        return { name: g.name, cost: g.cost, year: g.year };
      }),
    };
  }

  function formatSnapshot(snap) {
    snap = snap || {};
    return (
      "USER SNAPSHOT:\n" +
      "NW=" + snap.nw + " cash=" + snap.cash + " invest=" + snap.invest + " vault=" + snap.vault + " debt=" + snap.liab + "\n" +
      "runway_mo=" + snap.runway + " monthly_investable_surplus=" + snap.surplus + " income_mo=" + snap.income + "\n" +
      "μ=" + snap.ret + " σ=" + snap.vol + " ef_months_target=" + snap.efMonths + "\n" +
      "rank=" + snap.rank + " lv=" + snap.rankLvl + "\n" +
      "goals=" + JSON.stringify(snap.goals || [])
    );
  }

  function regimeOf(D, settings) {
    var ef = settings && settings.efMonths ? settings.efMonths : 3;
    var runway = D.runway, liab = D.liab || 0, nw = D.nw || 0, assets = D.assets || 0;
    var stage;
    if (liab > assets * 0.5 || (runway != null && runway < 1)) stage = "SURVIVAL";
    else if ((runway != null && runway < ef) || nw < 25000) stage = "FOUNDATION";
    else if (nw < 250000) stage = "ACCUMULATE";
    else if (nw < 1000000) stage = "SCALE";
    else stage = "PRESERVE";
    var directive = {
      SURVIVAL: "SURVIVAL mode: triage only — starter buffer, highest-APR debt, stop bleeding. No aggressive investing.",
      FOUNDATION: "FOUNDATION mode: finish EF, clear high-interest debt, then low-cost deployment. Defense before offense.",
      ACCUMULATE: "ACCUMULATE mode: bounded-aggressive compounding, position sizing for survival, raise income.",
      SCALE: "SCALE mode: diversification, concentration risk, protect gains while growing.",
      PRESERVE: "PRESERVE mode: capital preservation, drawdown control — staying rich.",
    }[stage];
    return {
      stage: stage,
      persona: REGIMES[stage].persona,
      posture: REGIMES[stage].posture,
      directive: directive,
    };
  }

  function buildAgentPrompt(personaId, opts) {
    opts = opts || {};
    var p = PERSONAS[personaId] || PERSONAS.STRATEGIST;
    var parts = [p.systemLong];
    if (opts.regimeDirective) parts.push("REGIME DIRECTIVE: " + opts.regimeDirective);
    if (opts.snapshotText) parts.push(opts.snapshotText);
    if (opts.ocText) parts.push(opts.ocText);
    if (opts.extra) parts.push(opts.extra);
    return parts.join("\n\n");
  }

  function tribunalUserMessage(item, oc) {
    return (
      "Vet this purchase through the Opportunity Cost Engineer.\n" +
      "Item: " + (item.name || "unnamed") + "\n" +
      "Cost: " + (item.cost || 0) + "\n" +
      "Class: " + (item.kind || "Depreciating") + "\n" +
      (oc ? "Engineer verdict_hint: " + oc.verdict + "\n" + oc.summaryLine : "")
    );
  }

  /** Offline ruling when no LLM — still useful */
  function offlineTribunalRuling(oc, item) {
    item = item || {};
    var lines = [];
    lines.push(oc.verdict);
    lines.push(oc.summaryLine);
    if (oc.floorBreach) lines.push("This spend drops cash below the floor buffer. Absolute no.");
    else if (oc.verdict === "NOT WORTH IT") lines.push("Depreciating consumption at this surplus multiple is a quiet tax on your future self.");
    else if (oc.verdict === "WAIT") lines.push("Not forbidden — premature. Park the urge; re-run when surplus covers it in under 3 months.");
    else lines.push("Math tolerates this if the floor holds and utility is real. Still: name the years you are selling.");
    lines.push("What future version of you is paying for \"" + (item.name || "this") + "\"?");
    lines.push("// analysis, not financial advice — engineer ran offline.");
    return lines.join("\n");
  }

  root.BedrockHermes = {
    CANON: CANON,
    PERSONAS: PERSONAS,
    REGIMES: REGIMES,
    SWARM_DEFAULT: SWARM_DEFAULT,
    opportunityCostEngine: opportunityCostEngine,
    formatOcForPrompt: formatOcForPrompt,
    snapshotFromApp: snapshotFromApp,
    formatSnapshot: formatSnapshot,
    regimeOf: regimeOf,
    buildAgentPrompt: buildAgentPrompt,
    tribunalUserMessage: tribunalUserMessage,
    offlineTribunalRuling: offlineTribunalRuling,
    listPersonas: function () {
      return Object.keys(PERSONAS);
    },
    version: "1.0.0-hermes",
  };
})(typeof window !== "undefined" ? window : globalThis);
