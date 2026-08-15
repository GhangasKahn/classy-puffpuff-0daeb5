/* SHINOBI//82 KAGE — kusabi assembler and site behavior */
(function () {
  "use strict";

  const MASS = {
    handle: 7.2,
    inlay: 1.6,
    mizu: 8.4,
    kumiko: 5.1,
    nata: 8.0,
    saya: 4.9,
    diamond: 1.7,
    spike: 1.4,
    tweezer: 0.55,
    cassette: 1.9,
    s50: 1.7,
    l80: 4.3,
    tether: 0.35,
  };

  const BRIEF_TARGETS = {
    kumiko: 17.52,
    river: 24.06,
    trail: 27.2,
    niagara: 30.66,
    studio: 58.36,
  };

  const PRESETS = {
    kumiko: { hand: "right", blades: ["kumiko"], mods: ["saya", "tether"] },
    river: { hand: "right", blades: ["mizu"], mods: ["saya", "diamond", "tweezer", "s50", "tether"] },
    trail: { hand: "right", blades: ["nata", "kumiko"], mods: ["saya", "diamond", "tether"] },
    niagara: { hand: "right", blades: ["mizu"], mods: ["saya", "diamond", "spike", "tweezer", "l80", "tether"] },
    studio: {
      hand: "right",
      blades: ["mizu", "kumiko", "nata"],
      mods: ["inlay", "saya", "diamond", "spike", "tweezer", "s50", "l80", "tether"],
    },
  };

  const BLADE_COPY = {
    mizu: {
      purpose:
        "River and food work: skin release, pinbone tracing, trout to catfish breakdown, camp meals. Inclusive edge about 25°. Not a square-registering marking face.",
      steel: "MagnaMax candidate, 62.5–63.0 HRC pending prototype coupons",
    },
    kumiko: {
      purpose:
        "Bench work: scribing, kumiko fitting, chamfering, layout against a square. Dead-flat back, 15° single flat bevel. Mirrored left- and right-hand versions required.",
      steel: "Proposed ZW-V1 or MagnaCut rail in the Zen-Wu urade-fuyo language",
    },
    nata: {
      purpose:
        "Trailcraft: whittling, notching, controlled chisel-style chopping. 24° single bevel. Not batoning, prying, or splitting heavy bone.",
      steel: "MagnaCut, within Zen-Wu’s demonstrated heat-treatment range",
    },
    mixed: {
      purpose:
        "More than one iron is seated in the ledger. Carry the geometries you will actually use; the lock is shared, the edges are not.",
      steel: "See each selected iron",
    },
    none: {
      purpose: "Select at least one blade module. The handle does not cut.",
      steel: "—",
    },
  };

  const $ = (sel, root = document) => root.querySelector(sel);
  const $$ = (sel, root = document) => Array.from(root.querySelectorAll(sel));

  function gramsToOz(g) {
    return g / 28.349523125;
  }

  function currentBlades() {
    return $$('input[name="blade"]:checked').map((el) => el.value);
  }

  function currentMods() {
    return $$('input[name="mod"]:checked').map((el) => el.value);
  }

  function currentHand() {
    const el = $('input[name="hand"]:checked');
    return el ? el.value : "right";
  }

  function lineItems() {
    const blades = currentBlades();
    const mods = new Set(currentMods());
    const rows = [{ id: "handle", label: "Kusabi-Lock handle, Ti-6Al-4V", g: MASS.handle }];
    if (mods.has("inlay")) rows.push({ id: "inlay", label: "Kurogaki mechanical inlays", g: MASS.inlay });
    if (blades.includes("mizu")) rows.push({ id: "mizu", label: "MIZU-82 blade module", g: MASS.mizu });
    if (blades.includes("kumiko")) rows.push({ id: "kumiko", label: "KUMIKO-42 blade module", g: MASS.kumiko });
    if (blades.includes("nata")) rows.push({ id: "nata", label: "NATA-60 blade module", g: MASS.nata });
    if (mods.has("saya")) rows.push({ id: "saya", label: "Kiri/honoki saya · power grip", g: MASS.saya });
    if (mods.has("diamond")) rows.push({ id: "diamond", label: "Diamond tag 600/1200 + 1 µm film", g: MASS.diamond });
    if (mods.has("spike")) rows.push({ id: "spike", label: "Capped ikejime spike", g: MASS.spike });
    if (mods.has("tweezer")) rows.push({ id: "tweezer", label: "Beta-titanium pinbone tweezer", g: MASS.tweezer });
    const wantsWire = mods.has("s50") || mods.has("l80");
    if (wantsWire) rows.push({ id: "cassette", label: "Vented wire cassette / collet", g: MASS.cassette });
    if (mods.has("s50")) rows.push({ id: "s50", label: "SHINKEI S-50 wire 0.8 × 500 mm", g: MASS.s50 });
    if (mods.has("l80")) rows.push({ id: "l80", label: "SHINKEI L-80 wire 1.2 × 800 mm", g: MASS.l80 });
    if (mods.has("tether")) rows.push({ id: "tether", label: "Dyneema tether", g: MASS.tether });
    return rows;
  }

  function activePreset() {
    const blades = currentBlades().slice().sort().join(",");
    const mods = currentMods().slice().sort().join(",");
    const hand = currentHand();
    for (const [id, p] of Object.entries(PRESETS)) {
      if (p.hand !== hand) continue;
      if (p.blades.slice().sort().join(",") !== blades) continue;
      if (p.mods.slice().sort().join(",") !== mods) continue;
      return id;
    }
    return null;
  }

  function grindPath(blades, hand) {
    const mirror = hand === "left" ? " scale(-1,1) translate(-320,0)" : "";
    const primary = blades[0] || "none";
    if (primary === "kumiko") {
      return {
        d: "M16 86 L304 86 L304 54 L16 18 Z",
        back: "M16 86 L304 86",
        label: "15° single flat bevel · dead-flat ura · urade-fuyo",
        transform: mirror,
      };
    }
    if (primary === "nata") {
      return {
        d: "M16 92 L304 92 L304 48 L16 12 Z",
        back: "M16 92 L304 92",
        label: "24° single bevel · reinforced heel · not a hatchet",
        transform: mirror,
      };
    }
    if (primary === "mizu") {
      return {
        d: "M16 88 C 70 84, 140 70, 304 62 L304 42 C 150 58, 70 62, 16 28 Z",
        back: "M16 88 C 90 90, 180 86, 304 78",
        label: "Hamaguri convex · ~25° inclusive · shallow reverse relief",
        transform: mirror,
      };
    }
    return {
      d: "",
      back: "",
      label: "Select a blade to inspect its section",
      transform: "",
    };
  }

  function renderGrind(blades, hand) {
    const svg = $("#grind-svg");
    const caption = $("#grind-caption");
    if (!svg) return;
    const g = grindPath(blades, hand);
    const shown = blades.length > 1 ? `${g.label} (section of ${blades[0].toUpperCase()}; other irons differ)` : g.label;
    svg.innerHTML = `
      <g transform="${g.transform}">
        <text x="16" y="18" fill="currentColor" font-size="11" letter-spacing="1.4">${hand === "left" ? "LEFT-HAND MIRROR" : "RIGHT-HAND DEFAULT"}</text>
        <path d="${g.d}" fill="rgba(111,142,170,0.28)" stroke="#6f8eaa" stroke-width="1.2"/>
        <path d="${g.back}" fill="none" stroke="#d7c39a" stroke-width="1.6"/>
        <line x1="16" y1="108" x2="304" y2="108" stroke="currentColor" stroke-opacity="0.25"/>
      </g>`;
    if (caption) caption.textContent = shown;
  }

  function renderAssembler() {
    const rows = lineItems();
    const total = rows.reduce((s, r) => s + r.g, 0);
    const blades = currentBlades();
    const hand = currentHand();
    const preset = activePreset();
    const copyKey = blades.length === 0 ? "none" : blades.length === 1 ? blades[0] : "mixed";
    const copy = BLADE_COPY[copyKey];

    const totalEl = $("#mass-total");
    const ozEl = $("#mass-oz");
    const list = $("#mass-lines");
    const purpose = $("#mass-purpose");
    const steel = $("#mass-steel");
    const model = $("#mass-model");
    const live = $("#assembler-live");

    if (totalEl) totalEl.textContent = total.toFixed(1) + " g";
    if (ozEl) ozEl.textContent = gramsToOz(total).toFixed(2) + " oz";
    if (list) {
      list.innerHTML = rows
        .map((r) => `<li><span>${r.label}</span><b class="num">${r.g.toFixed(2)} g</b></li>`)
        .join("");
    }
    if (purpose) purpose.textContent = copy.purpose;
    if (steel) steel.textContent = copy.steel;
    if (model) {
      if (preset && BRIEF_TARGETS[preset] != null) {
        model.textContent =
          "Working line-item model for this configuration. The design brief’s geometric target for the named “" +
          preset +
          "” loadout is " +
          BRIEF_TARGETS[preset].toFixed(2) +
          " g. Neither figure is a weighed prototype.";
      } else {
        model.textContent =
          "Working line-item model for configuration only. Not a scale reading. Physical prototypes must be weighed before any shipping claim.";
      }
    }
    $$(".presets button").forEach((btn) => {
      btn.setAttribute("aria-pressed", btn.dataset.preset === preset ? "true" : "false");
    });
    renderGrind(blades, hand);
    const instrument = $("#instrument");
    if (instrument) instrument.setAttribute("data-hand", hand);
    if (live) {
      live.textContent =
        "Loadout total " + total.toFixed(1) + " grams, " + gramsToOz(total).toFixed(2) + " ounces. " + copy.purpose;
    }
    updateBrief();
  }

  function applyPreset(id) {
    const p = PRESETS[id];
    if (!p) return;
    $$('input[name="hand"]').forEach((el) => {
      el.checked = el.value === p.hand;
    });
    $$('input[name="blade"]').forEach((el) => {
      el.checked = p.blades.includes(el.value);
    });
    $$('input[name="mod"]').forEach((el) => {
      el.checked = p.mods.includes(el.value);
    });
    renderAssembler();
    const assembler = $("#assembler");
    if (assembler) assembler.scrollIntoView({ block: "nearest" });
  }

  function updateBrief() {
    const preview = $("#brief-preview");
    const name = ($("#field-name") && $("#field-name").value.trim()) || "[name]";
    const use = ($("#field-use") && $("#field-use").value.trim()) || "[intended use]";
    const batch = ($("#field-batch") && $("#field-batch").value) || "undecided";
    const notes = ($("#field-notes") && $("#field-notes").value.trim()) || "";
    const rows = lineItems();
    const total = rows.reduce((s, r) => s + r.g, 0);
    const blades = currentBlades().map((b) => b.toUpperCase()).join(", ") || "none";
    const text =
      "SHINOBI//82 KAGE — production conversation\n\n" +
      "From: " +
      name +
      "\nDominant hand: " +
      currentHand() +
      "\nIntended use: " +
      use +
      "\nBatch interest: " +
      batch +
      "\n\nSelected configuration (working mass model, not a weighed prototype):\n" +
      rows.map((r) => "• " + r.label + " — " + r.g.toFixed(2) + " g").join("\n") +
      "\nTotal: " +
      total.toFixed(1) +
      " g / " +
      gramsToOz(total).toFixed(2) +
      " oz\nBlades: " +
      blades +
      "\n\nThis is a proposed collaboration specification, not an order and not an official Zen-Wu product listing.\n" +
      (notes ? "\nNotes:\n" + notes + "\n" : "");
    if (preview) preview.textContent = text;
    return text;
  }

  function composeMail(event) {
    if (event) event.preventDefault();
    const text = updateBrief();
    const subject = encodeURIComponent("SHINOBI//82 KAGE — production conversation");
    const body = encodeURIComponent(text);
    const href = "mailto:luke@zenwutoolworks.com?subject=" + subject + "&body=" + body;
    const status = $("#form-status");
    window.location.href = href;
    if (status) {
      status.textContent =
        "Your email application should open addressed to luke@zenwutoolworks.com with this brief. If nothing opens, copy the brief below and send it yourself. This page does not transmit the message.";
    }
  }

  function copyBrief() {
    const text = updateBrief();
    const status = $("#form-status");
    const done = (ok) => {
      if (status) {
        status.textContent = ok
          ? "Brief copied. Paste it into a message to luke@zenwutoolworks.com. This page does not send email."
          : "Copy failed. Select the brief text and copy it manually.";
      }
    };
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(text).then(
        () => done(true),
        () => done(false)
      );
    } else done(false);
  }

  function setTheme(next) {
    document.documentElement.setAttribute("data-theme", next);
    try {
      localStorage.setItem("shinobi-theme", next);
    } catch (e) {}
    const pressed = next === "hiru" ? "true" : "false";
    const label = next === "hiru" ? "Switch to night palette" : "Switch to shop-day palette";
    const btn = $("#theme-toggle");
    const rail = $("#theme-toggle-rail");
    if (btn) {
      btn.setAttribute("aria-pressed", pressed);
      btn.setAttribute("aria-label", label);
      btn.textContent = next === "hiru" ? "夜" : "昼";
    }
    if (rail) {
      rail.setAttribute("aria-pressed", pressed);
      rail.setAttribute("aria-label", label);
    }
  }

  function setMotion(off) {
    document.documentElement.setAttribute("data-motion", off ? "off" : "on");
    try {
      localStorage.setItem("shinobi-motion", off ? "off" : "on");
    } catch (e) {}
    $$("[data-motion-toggle]").forEach((btn) => {
      btn.setAttribute("aria-pressed", off ? "true" : "false");
    });
  }

  function initTheme() {
    let theme = "yoru";
    try {
      theme = localStorage.getItem("shinobi-theme") || "yoru";
    } catch (e) {}
    setTheme(theme);
    const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    let motion = reduce ? "off" : "on";
    try {
      const stored = localStorage.getItem("shinobi-motion");
      if (stored) motion = stored;
    } catch (e) {}
    setMotion(motion === "off");
  }

  function initNav() {
    const bar = $(".topbar");
    const toggle = $("#menu-toggle");
    const links = $$(".nav-links a, .rail a.chap");
    if (toggle && bar) {
      toggle.addEventListener("click", () => {
        const open = bar.classList.toggle("is-open");
        toggle.setAttribute("aria-expanded", open ? "true" : "false");
      });
      $$(".nav-links a").forEach((a) =>
        a.addEventListener("click", () => {
          bar.classList.remove("is-open");
          toggle.setAttribute("aria-expanded", "false");
        })
      );
    }
    window.addEventListener(
      "scroll",
      () => {
        if (bar) bar.classList.toggle("is-scrolled", window.scrollY > 8);
      },
      { passive: true }
    );

    const sections = ["arrival", "recognition", "revelation", "proof", "resolution"]
      .map((id) => document.getElementById(id))
      .filter(Boolean);
    if (!("IntersectionObserver" in window) || !sections.length) return;
    const io = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (!entry.isIntersecting) return;
          const id = entry.target.id;
          links.forEach((a) => {
            const match = a.getAttribute("href") === "#" + id;
            if (match) a.setAttribute("aria-current", "true");
            else a.removeAttribute("aria-current");
          });
        });
      },
      { rootMargin: "-40% 0px -50% 0px", threshold: 0.01 }
    );
    sections.forEach((s) => io.observe(s));
  }

  function init() {
    initTheme();
    initNav();
    const root = $("#assembler");
    if (root) {
      root.addEventListener("change", renderAssembler);
      $$(".presets button").forEach((btn) => {
        btn.addEventListener("click", () => applyPreset(btn.dataset.preset));
      });
      applyPreset("river");
    }
    const form = $("#brief-form");
    if (form) {
      form.addEventListener("submit", composeMail);
      form.addEventListener("input", updateBrief);
    }
    const copyBtn = $("#copy-brief");
    if (copyBtn) copyBtn.addEventListener("click", copyBrief);
    $$("#theme-toggle, #theme-toggle-rail").forEach((themeBtn) => {
      themeBtn.addEventListener("click", () => {
        const now = document.documentElement.getAttribute("data-theme") === "hiru" ? "yoru" : "hiru";
        setTheme(now);
      });
    });
    $$("[data-motion-toggle]").forEach((btn) => {
      btn.addEventListener("click", () => {
        const off = document.documentElement.getAttribute("data-motion") !== "off";
        setMotion(off);
      });
    });
    const year = $("#year");
    if (year) year.textContent = String(new Date().getFullYear());
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init);
  else init();
})();
