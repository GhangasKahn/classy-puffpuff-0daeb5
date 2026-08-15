/* SHINOBI//82 KAGE — Loadout Ledger
   Masses are an allocation model that sums to the design-brief mission totals.
   They are engineering targets, not scale readings. */

(function () {
  "use strict";

  var OUNCE = 28.349523125;
  var STUDIO_CAP = 58.36;

  var MODULES = [
    { id: "handle", name: "KUSABI-Lock chassis", g: 8.4, group: "chassis", hint: "Ti-6Al-4V open frame and wedge. Required for any carried blade." },
    { id: "saya", name: "Kiri / honoki saya", g: 4.8, group: "chassis", hint: "Vented wooden sheath; snaps onto the handle as the power-grip swell." },
    { id: "inlay", name: "Kurogaki contact inlays", g: 1.2, group: "chassis", hint: "Removable, mechanical, no adhesive. Optional wet traction." },
    { id: "tether", name: "Dyneema tether", g: 0.35, group: "chassis", hint: "Adjustable pinky loop. Not a locked finger ring." },
    { id: "kumiko", name: "KUMIKO-42 blade", g: 4.32, group: "blade", hint: "Flat back, 15° single flat bevel. Scribe, chamfer, kumiko fit." },
    { id: "mizu", name: "MIZU-82 blade", g: 9.1, group: "blade", hint: "MagnaMax development candidate. Fish, food, EDC, seam work." },
    { id: "nata", name: "NATA-60 blade", g: 11.85, group: "blade", hint: "MagnaCut, 24° single bevel. Whittling, notching, controlled chisel cuts." },
    { id: "railstone", name: "RAILSTONE diamond tag", g: 1.9, group: "kit", hint: "600 / 1,200 grit faces. Doubles as T-handle for the capped spike." },
    { id: "film", name: "1 μm diamond film", g: 0.25, group: "kit", hint: "Replaceable finishing strip stored under the tag." },
    { id: "tweezer", name: "β-titanium pinbone tweezer", g: 0.55, group: "kit", hint: "Nests in the saya. For detection and extraction, not leverage." },
    { id: "s50", name: "S-50 spinal wire + channel", g: 1.76, group: "wire", hint: "0.8 × 500 mm. Backcountry trout and most bass. Includes its nested cassette share." },
    { id: "l80", name: "L-80 spinal wire + channel", g: 6.46, group: "wire", hint: "1.2 × 800 mm. Adult Niagara salmon. Includes its nested cassette share." },
    { id: "xl", name: "XL spinal wire + channel", g: 7.42, group: "wire", hint: "1.5 × 800 mm. Unusually large Chinook. Optional." }
  ];

  var MISSIONS = {
    kumiko: {
      label: "Kumiko pocket",
      ids: ["handle", "kumiko", "saya"],
      note: "Shop-first. One marking geometry. No river kit."
    },
    river: {
      label: "Backcountry river",
      ids: ["handle", "mizu", "saya", "s50"],
      note: "Trout and bass ikejime path. Still under one ounce in the model."
    },
    trail: {
      label: "Trailcraft",
      ids: ["handle", "nata", "saya", "railstone", "film"],
      note: "Whittling and controlled chopping. Not batoning."
    },
    niagara: {
      label: "Niagara salmon",
      ids: ["handle", "mizu", "saya", "railstone", "l80"],
      note: "A salmon-capable wire cannot honestly stay under one ounce."
    },
    studio: {
      label: "Complete studio",
      ids: MODULES.map(function (m) { return m.id; }),
      note: "Every module in the tray. The brief’s 58.36 g ceiling."
    }
  };

  var GRINDS = {
    mizu: {
      title: "MIZU-82 · hamaguri 60/40",
      copy: "Presentation face carries most of the bevel. Reverse face stays nearly flat so the blade can register, then peel. Heel is thicker; the distal third is allowed a little compliance for ribs and skin. Apex target 12° / 14°, with a reinforced 15° / 17° heel. Factory tooth is 800–1,000 grit diamond, deburred at 1 μm — a mirror polish can skate on fish skin.",
      apex: "12° / 14°",
      steel: "MagnaMax candidate · 62.5–63.0 HRC"
    },
    kumiko: {
      title: "KUMIKO-42 · kataba flat",
      copy: "A perfectly flat ura and a 15° single flat bevel. No urasuki hollow. This is the geometry Zen-Wu already uses on travel knives and plane irons: a back you can register to a square, a bevel you can repeat on a stone. Right- and left-hand versions are mirrored constructions, not flipped sharpening.",
      apex: "15° single",
      steel: "ZW-V1 candidate, dovetail-laminated"
    },
    nata: {
      title: "NATA-60 · 24° single bevel",
      copy: "A thicker single bevel for whittling, chamfering, notching, and chisel-style chopping into the work — not through bone, not through a log. The extra included angle exists so the edge survives trail abuse that would roll MIZU. It is still a knife. It is not an axe.",
      apex: "24° single",
      steel: "MagnaCut · hardness pending Zen-Wu HT"
    }
  };

  var state = {
    selected: { handle: true, kumiko: true, saya: true },
    mission: "kumiko",
    hand: "right",
    grind: "kumiko",
    menu: false,
    built: false
  };

  function $(id) { return document.getElementById(id); }

  function totalG() {
    return MODULES.reduce(function (sum, m) {
      return sum + (state.selected[m.id] ? m.g : 0);
    }, 0);
  }

  function fmt(n) {
    return (Math.round(n * 100) / 100).toFixed(2);
  }

  function matchingMission() {
    var ids = Object.keys(state.selected).filter(function (id) { return state.selected[id]; }).sort().join(",");
    for (var key in MISSIONS) {
      var want = MISSIONS[key].ids.slice().sort().join(",");
      if (want === ids) return key;
    }
    return null;
  }

  function applyMission(key) {
    var ids = MISSIONS[key].ids;
    state.selected = {};
    ids.forEach(function (id) { state.selected[id] = true; });
    state.mission = key;
    if (key === "kumiko") setGrind("kumiko");
    if (key === "river" || key === "niagara") setGrind("mizu");
    if (key === "trail") setGrind("nata");
    render();
  }

  function setGrind(id) {
    state.grind = id;
    var spec = GRINDS[id];
    if (!spec) return;
    $("grind-title").textContent = spec.title;
    $("grind-copy").textContent = spec.copy;
    $("grind-apex").textContent = spec.apex;
    $("grind-steel").textContent = spec.steel;
    document.querySelectorAll(".edge-tab").forEach(function (btn) {
      btn.setAttribute("aria-selected", btn.getAttribute("data-grind") === id ? "true" : "false");
    });
    drawGrind(id);
  }

  function drawGrind(id) {
    var svg = $("grind-svg");
    if (!svg) return;
    var flip = state.hand === "left";
    var paths = {
      mizu: convex(flip),
      kumiko: flatBevel(flip, 15),
      nata: flatBevel(flip, 24)
    };
    svg.innerHTML = paths[id] || paths.mizu;
  }

  function convex(flip) {
    var t = flip ? "translate(640,0) scale(-1,1)" : "";
    return (
      '<g transform="' + t + '">' +
      '<text x="24" y="36" fill="#d9d1c0" font-size="18" font-family="IBM Plex Sans,sans-serif">URA · near-flat reverse</text>' +
      '<text x="400" y="36" fill="#d9d1c0" font-size="18" font-family="IBM Plex Sans,sans-serif">OMOTE · hamaguri</text>' +
      '<path d="M80 220 L560 220 L560 188 C 430 150, 300 128, 80 168 Z" fill="#8a93a3"/>' +
      '<path d="M80 220 L560 220 L560 188 C 490 176, 400 168, 80 196 Z" fill="#f3ead8"/>' +
      '<path d="M80 168 L80 220" stroke="#8a2a1a" stroke-width="3"/>' +
      '<path d="M80 196 L560 188" stroke="#2c3a6b" stroke-width="2" fill="none"/>' +
      '<text x="96" y="158" fill="#faf6ec" font-size="16">apex</text>' +
      '<text x="500" y="250" fill="#d9d1c0" font-size="16">spine</text>' +
      "</g>"
    );
  }

  function flatBevel(flip, deg) {
    var t = flip ? "translate(640,0) scale(-1,1)" : "";
    var drop = deg > 18 ? 70 : 48;
    return (
      '<g transform="' + t + '">' +
      '<text x="24" y="36" fill="#d9d1c0" font-size="18" font-family="IBM Plex Sans,sans-serif">FLAT BACK · register</text>' +
      '<text x="400" y="36" fill="#d9d1c0" font-size="18" font-family="IBM Plex Sans,sans-serif">' + deg + "° single bevel</text>" +
      '<path d="M80 210 L560 210 L560 ' + (210 - drop) + ' Z" fill="#8a93a3"/>' +
      '<path d="M80 210 L560 210" stroke="#f3ead8" stroke-width="3"/>' +
      '<path d="M80 210 L560 ' + (210 - drop) + '" stroke="#2c3a6b" stroke-width="2"/>' +
      '<text x="90" y="198" fill="#faf6ec" font-size="16">apex</text>' +
      "</g>"
    );
  }

  function buildModules() {
    var root = $("module-list");
    root.innerHTML = "";
    MODULES.forEach(function (m) {
      var row = document.createElement("div");
      row.className = "mod";
      var id = "mod-" + m.id;
      var input = document.createElement("input");
      input.type = "checkbox";
      input.id = id;
      input.checked = !!state.selected[m.id];
      input.addEventListener("change", function (e) {
        state.selected[m.id] = e.target.checked;
        state.mission = matchingMission();
        render();
      });
      var label = document.createElement("label");
      label.htmlFor = id;
      label.innerHTML = "<strong>" + m.name + "</strong><br><span class='note' style='margin:0'>" + m.hint + "</span>";
      var g = document.createElement("div");
      g.className = "g";
      g.textContent = fmt(m.g) + " g";
      row.appendChild(input);
      row.appendChild(label);
      row.appendChild(g);
      root.appendChild(row);
    });
    state.built = true;
  }

  function syncModules() {
    MODULES.forEach(function (m) {
      var input = $("mod-" + m.id);
      if (input) input.checked = !!state.selected[m.id];
    });
  }

  function renderMissions() {
    document.querySelectorAll(".mission").forEach(function (btn) {
      var key = btn.getAttribute("data-mission");
      btn.setAttribute("aria-pressed", state.mission === key ? "true" : "false");
    });
  }

  function renderScale() {
    var g = totalG();
    $("grams").textContent = fmt(g);
    $("ounces").textContent = (g / OUNCE).toFixed(3) + " oz";
    var pct = Math.min(100, (g / STUDIO_CAP) * 100);
    $("bar-fill").style.width = pct + "%";
    $("oz-mark").style.left = (OUNCE / STUDIO_CAP) * 100 + "%";
    var mission = state.mission ? MISSIONS[state.mission] : null;
    var line = fmt(g) + " grams selected.";
    if (g <= OUNCE + 0.005) line += " At or under one ounce in the model.";
    else line += " Over one ounce in the model.";
    if (mission) line += " Mission: " + mission.label + ". " + mission.note;
    else line += " Custom allocation. Not a named mission.";
    $("ledger-live").textContent = line;
    $("ledger-note").textContent = mission
      ? mission.note + " Component masses are an allocation model, not a scale reading."
      : "Custom stack. Component masses are an allocation model summing toward the brief’s mission totals — not a weighed prototype.";
  }

  function renderHand() {
    document.querySelectorAll("[data-hand]").forEach(function (btn) {
      btn.setAttribute("aria-pressed", btn.getAttribute("data-hand") === state.hand ? "true" : "false");
    });
    $("hand-live").textContent = state.hand === "right"
      ? "Right-hand geometry. Single-bevel tools are chiral; left-hand is a mirrored construction."
      : "Left-hand geometry. Blade, ura, and lamination are fully mirrored — not sharpened from the other side.";
    drawGrind(state.grind);
  }

  function render() {
    if (!state.built) buildModules();
    else syncModules();
    renderMissions();
    renderScale();
    renderHand();
  }

  function openMail(e) {
    e.preventDefault();
    var name = $("f-name").value.trim();
    var email = $("f-email").value.trim();
    var hand = $("f-hand").value;
    var use = $("f-use").value.trim();
    var note = $("f-note").value.trim();
    var err = $("form-error");
    var ok = $("form-ok");
    err.textContent = "";
    ok.textContent = "";
    if (!name || !email || !note) {
      err.textContent = "Name, email, and a note are required. Nothing was sent.";
      $("f-name").focus();
      return;
    }
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      err.textContent = "That email does not look usable. Nothing was sent.";
      $("f-email").focus();
      return;
    }
    var g = totalG();
    var body = [
      "SHINOBI//82 KAGE — collaboration note",
      "",
      "Name: " + name,
      "Email: " + email,
      "Dominant hand: " + hand,
      "Intended work: " + (use || "(not specified)"),
      "Ledger total (model): " + fmt(g) + " g / " + (g / OUNCE).toFixed(3) + " oz",
      "Mission: " + (state.mission ? MISSIONS[state.mission].label : "custom"),
      "Modules: " + MODULES.filter(function (m) { return state.selected[m.id]; }).map(function (m) { return m.name; }).join(", "),
      "",
      note,
      "",
      "This message was composed on the specification site. It is not an order."
    ].join("\n");
    var href = "mailto:fetesky@gmail.com?subject=" + encodeURIComponent("SHINOBI//82 KAGE — note from " + name) +
      "&body=" + encodeURIComponent(body);
    ok.innerHTML = "This page cannot send mail by itself. It will open your email client to <a href=\"" + href + "\">fetesky@gmail.com</a>. If nothing opens, copy that address and paste the note yourself.";
    window.location.href = href;
  }

  function bindTabs() {
    var tabs = Array.prototype.slice.call(document.querySelectorAll(".edge-tab"));
    tabs.forEach(function (btn, i) {
      btn.addEventListener("click", function () { setGrind(btn.getAttribute("data-grind")); });
      btn.addEventListener("keydown", function (e) {
        var next = i;
        if (e.key === "ArrowDown" || e.key === "ArrowRight") next = (i + 1) % tabs.length;
        else if (e.key === "ArrowUp" || e.key === "ArrowLeft") next = (i - 1 + tabs.length) % tabs.length;
        else if (e.key === "Home") next = 0;
        else if (e.key === "End") next = tabs.length - 1;
        else return;
        e.preventDefault();
        tabs[next].focus();
        setGrind(tabs[next].getAttribute("data-grind"));
      });
    });
  }

  function bind() {
    document.querySelectorAll(".mission").forEach(function (btn) {
      btn.addEventListener("click", function () { applyMission(btn.getAttribute("data-mission")); });
    });
    bindTabs();
    document.querySelectorAll("[data-hand]").forEach(function (btn) {
      btn.addEventListener("click", function () {
        state.hand = btn.getAttribute("data-hand");
        renderHand();
      });
    });
    $("collab-form").addEventListener("submit", openMail);
    $("menu-btn").addEventListener("click", function () {
      state.menu = !state.menu;
      $("drawer").classList.toggle("open", state.menu);
      $("menu-btn").setAttribute("aria-expanded", state.menu ? "true" : "false");
    });
    $("still-btn").addEventListener("click", function () {
      var on = document.documentElement.classList.toggle("still");
      try { localStorage.setItem("kage-still", on ? "1" : "0"); } catch (err) {}
      $("still-btn").setAttribute("aria-pressed", on ? "true" : "false");
      $("still-btn").textContent = on ? "Motion off" : "Still the tray";
    });
    document.querySelectorAll("#drawer a").forEach(function (a) {
      a.addEventListener("click", function () {
        state.menu = false;
        $("drawer").classList.remove("open");
        $("menu-btn").setAttribute("aria-expanded", "false");
      });
    });
    var reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    try {
      if (localStorage.getItem("kage-still") === "1" || reduce) {
        document.documentElement.classList.add("still");
        $("still-btn").setAttribute("aria-pressed", "true");
        $("still-btn").textContent = "Motion off";
      }
    } catch (err) {}
  }

  function reveal() {
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches || document.documentElement.classList.contains("still")) {
      document.querySelectorAll(".rise").forEach(function (el) { el.classList.add("in"); });
      return;
    }
    if (!("IntersectionObserver" in window)) {
      document.querySelectorAll(".rise").forEach(function (el) { el.classList.add("in"); });
      return;
    }
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) {
        if (en.isIntersecting) {
          en.target.classList.add("in");
          io.unobserve(en.target);
        }
      });
    }, { threshold: 0.12 });
    document.querySelectorAll(".rise").forEach(function (el) { io.observe(el); });
    setTimeout(function () {
      document.querySelectorAll(".rise:not(.in)").forEach(function (el) { el.classList.add("in"); });
    }, 2800);
  }

  document.addEventListener("DOMContentLoaded", function () {
    document.documentElement.classList.add("has-js");
    bind();
    applyMission("kumiko");
    setGrind("kumiko");
    reveal();
    var y = $("year");
    if (y) y.textContent = String(new Date().getFullYear());
  });
})();
