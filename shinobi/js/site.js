(() => {
  "use strict";

  const COMPONENTS = {
    frame: { id: "frame", name: "Kusabi Ti-6Al-4V frame and wedge", g: 9.3, locked: true },
    mizu: { id: "mizu", name: "MIZU-82 blade module", g: 8.4, exclusive: "blade" },
    kumiko: { id: "kumiko", name: "KUMIKO-42 blade module", g: 5.85, exclusive: "blade" },
    nata: { id: "nata", name: "NATA-60 blade module", g: 10.55, exclusive: "blade" },
    saya: { id: "saya", name: "Kiri / honoki saya", g: 3.9 },
    togi: { id: "togi", name: "TOGI plate — 600/1200 diamond and 1 μm strop", g: 2.05 },
    spike: { id: "spike", name: "KAGE-HARI miniature steel spike", g: 1.15 },
    tweezer: { id: "tweezer", name: "Beta-titanium pinbone tweezer", g: 0.55 },
    tether: { id: "tether", name: "Dyneema SK99 tether", g: 0.31 },
    locator: { id: "locator", name: "Linen locator tab", g: 0.18 },
    cassette: { id: "cassette", name: "SHINKEI vented cassette", g: 1.4 },
    s50: { id: "s50", name: "S-50 spinal wire 0.8 × 500 mm", g: 1.8 },
    l80: { id: "l80", name: "L-80 spinal wire 1.2 × 800 mm", g: 4.3 },
    inlay: { id: "inlay", name: "Kurogaki contact inlays", g: 1.15 },
    spareKumiko: { id: "spareKumiko", name: "KUMIKO-42 spare in chest", g: 5.85 },
    spareNata: { id: "spareNata", name: "NATA-60 spare in chest", g: 10.55 },
    spareMizu: { id: "spareMizu", name: "MIZU-82 spare in chest", g: 8.4 }
  };

  const PRESETS = {
    shop: ["frame", "kumiko", "saya", "tether", "locator", "togi"],
    river: ["frame", "mizu", "saya", "togi", "spike", "tether", "locator", "tweezer", "cassette", "s50"],
    trail: ["frame", "nata", "saya", "togi", "tether", "locator", "inlay"],
    niagara: ["frame", "mizu", "saya", "togi", "spike", "tether", "locator", "tweezer", "cassette", "s50", "l80"],
    studio: ["frame", "mizu", "saya", "togi", "spike", "tether", "locator", "tweezer", "cassette", "s50", "l80", "inlay", "spareKumiko", "spareNata"]
  };

  const TASKS = [
    { id: "scribe", label: "Joinery scribing and kumiko fitting", need: "kumiko", extra: null },
    { id: "trout", label: "Trout, panfish, and pinbone work", need: "mizu", extra: "tweezer" },
    { id: "ikejime", label: "Ikejime with KAGE-HARI — not the knife tip", need: "spike", extra: "togi" },
    { id: "shinkei", label: "Spinal wire on backcountry trout or bass", need: "s50", extra: "cassette" },
    { id: "salmon", label: "Niagara salmon breakdown and shinkeijime", need: "l80", extra: "mizu" },
    { id: "elk", label: "Seam work on deer or elk — not bone splitting", need: "mizu", extra: "inlay" },
    { id: "trail", label: "Whittling, notching, controlled chisel cuts", need: "nata", extra: null },
    { id: "hold", label: "Retention if the hand opens", need: "tether", extra: null },
    { id: "find", label: "Find the kit in wet grass", need: "saya", extra: "locator" },
    { id: "fillet", label: "Long one-pass salmon fillets", need: null, extra: null, refuse: true }
  ];

  const GRINDS = {
    mizu: {
      name: "MIZU-82 · 60/40 hamaguri",
      zones: {
        heel: { label: "Heel 0–22 mm", omote: "15°", ura: "17°", bet: "0.16 mm", job: "Opening cuts, tendons, the first controlled incision. Slightly thicker so the edge does not roll on cartilage." },
        belly: { label: "Belly 22–70 mm", omote: "12°", ura: "14°", bet: "0.10–0.13 mm", job: "Skin release and pinbone tracing. Acute enough to part without tearing; not a 10° sashimi apex." },
        tip: { label: "Kissaki 70–82 mm", omote: "14°", ura: "16°", bet: "0.14 mm", job: "Joints, fins, close bone. Reinforced so it can steer. It is not a brain spike." }
      }
    },
    kumiko: {
      name: "KUMIKO-42 · single flat bevel",
      zones: {
        heel: { label: "Full land 0–42 mm", omote: "15°", ura: "0° flat", bet: "0.12 mm", job: "The entire back is the reference. Registers to a square. No hollow. No belly that would rock the line." },
        belly: { label: "Same land", omote: "15°", ura: "0° flat", bet: "0.12 mm", job: "One angle, one plane. Chamfers and kumiko shoulders stay repeatable." },
        tip: { label: "Kiridashi point", omote: "15°", ura: "0° flat", bet: "0.14 mm", job: "Dovetail layout and inside corners. The hollow stops short of the point so the tip does not collapse." }
      }
    },
    nata: {
      name: "NATA-60 · 24° single bevel",
      zones: {
        heel: { label: "Chisel heel", omote: "24°", ura: "0° flat", bet: "0.22 mm", job: "Notching and controlled chopping. The angle is a chisel, not an axe." },
        belly: { label: "Working face", omote: "24°", ura: "0° flat", bet: "0.20 mm", job: "Whittling and feathering. Flat bevel, repeatable on the TOGI plate." },
        tip: { label: "Stopped point", omote: "24°", ura: "0° flat", bet: "0.24 mm", job: "Detail in camp wood. No baton face. No pry bevel." }
      }
    }
  };

  const state = {
    hand: "right",
    seated: new Set(PRESETS.river),
    zone: "belly"
  };

  const $ = (sel, root = document) => root.querySelector(sel);
  const $$ = (sel, root = document) => Array.from(root.querySelectorAll(sel));

  function grams() {
    return [...state.seated].reduce((sum, id) => sum + (COMPONENTS[id]?.g || 0), 0);
  }

  function ounces(g) {
    return g / 28.349523125;
  }

  function bladeId() {
    return ["mizu", "kumiko", "nata"].find((id) => state.seated.has(id)) || null;
  }

  function formatG(n) {
    return n.toFixed(2);
  }

  function taskStatus(task) {
    if (task.refuse) return { cls: "no", text: "Refused" };
    if (!task.need) return { cls: "warn", text: "Unspecified" };
    const hasNeed = state.seated.has(task.need);
    const hasExtra = !task.extra || state.seated.has(task.extra);
    if (hasNeed && hasExtra) return { cls: "", text: "Seated" };
    if (hasNeed) return { cls: "warn", text: "Partial" };
    return { cls: "no", text: "Unseated" };
  }

  function renderLedger() {
    const tbody = $("#ledger-body");
    const live = $("#ledger-live");
    const gEl = $("#mass-g");
    const ozEl = $("#mass-oz");
    const countEl = $("#mass-count");
    if (!tbody || !gEl) return;

    const rows = [...state.seated]
      .map((id) => COMPONENTS[id])
      .filter(Boolean)
      .sort((a, b) => a.name.localeCompare(b.name));

    tbody.innerHTML = rows
      .map(
        (row) => `<tr>
          <td>${row.name}</td>
          <td>${formatG(row.g)} g</td>
        </tr>`
      )
      .join("");

    const g = grams();
    gEl.textContent = formatG(g);
    ozEl.textContent = ounces(g).toFixed(3);
    if (countEl) countEl.textContent = String(rows.length);

    const matrix = $("#task-matrix");
    if (matrix) {
      matrix.innerHTML = TASKS.map((task) => {
        const status = taskStatus(task);
        return `<div class="matrix-row">
          <span>${task.label}</span>
          <span class="pill ${status.cls}">${status.text}</span>
        </div>`;
      }).join("");
    }

    const blade = bladeId();
    window.dispatchEvent(new CustomEvent("shinobi:seat", {
      detail: { blade, seated: [...state.seated] }
    }));
    window.dispatchEvent(new CustomEvent("shinobi:grind", {
      detail: { blade }
    }));

    const handMark = $("#hand-mark");
    if (handMark) {
      handMark.textContent = state.hand === "left" ? "Left-hand mirror" : "Right-hand default";
    }

    $$("input[name='blade']").forEach((input) => {
      input.checked = input.value === blade;
    });
    $$("input[name='hand']").forEach((input) => {
      input.checked = input.value === state.hand;
    });
    $$("input[data-part]").forEach((input) => {
      input.checked = state.seated.has(input.dataset.part);
    });

    if (live) {
      live.textContent = `Loadout seated at ${formatG(g)} grams, ${rows.length} line items, ${state.hand}-hand geometry.`;
    }
    renderGrind();
  }

  function renderGrind() {
    const blade = bladeId() || "mizu";
    const grind = GRINDS[blade];
    if (!grind) return;
    const zone = grind.zones[state.zone] || grind.zones.belly;
    const name = $("#grind-name");
    const label = $("#grind-zone-label");
    const omote = $("#grind-omote");
    const ura = $("#grind-ura");
    const bet = $("#grind-bet");
    const job = $("#grind-job");
    if (name) name.textContent = grind.name;
    if (label) label.textContent = zone.label;
    if (omote) omote.textContent = zone.omote;
    if (ura) ura.textContent = zone.ura;
    if (bet) bet.textContent = zone.bet;
    if (job) job.textContent = zone.job;
    $$("[data-zone]").forEach((btn) => {
      btn.setAttribute("aria-pressed", btn.dataset.zone === state.zone ? "true" : "false");
    });
    const wedge = $("#grind-wedge");
    if (wedge) {
      const map = { heel: "18 8, 92 48, 18 88", belly: "22 18, 92 48, 22 78", tip: "20 12, 92 48, 20 84" };
      wedge.setAttribute("points", map[state.zone] || map.belly);
    }
  }

  function seatBlade(id) {
    ["mizu", "kumiko", "nata"].forEach((blade) => state.seated.delete(blade));
    if (id) state.seated.add(id);
    state.seated.add("frame");
    renderLedger();
  }

  function togglePart(id, on) {
    if (id === "frame") return;
    if (["mizu", "kumiko", "nata"].includes(id)) {
      if (on) seatBlade(id);
      else {
        state.seated.delete(id);
        renderLedger();
      }
      return;
    }
    if (on) state.seated.add(id);
    else state.seated.delete(id);
    renderLedger();
  }

  function applyPreset(name) {
    const ids = PRESETS[name];
    if (!ids) return;
    state.seated = new Set(ids);
    renderLedger();
  }

  function syncMotionButton() {
    const btn = $("#motion-toggle");
    if (!btn) return;
    const off = document.documentElement.dataset.motion === "off";
    btn.setAttribute("aria-pressed", off ? "true" : "false");
    btn.textContent = off ? "Motion off" : "Motion on";
  }

  function initMotion() {
    const preferReduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    let stored = null;
    try {
      stored = localStorage.getItem("shinobi-motion");
    } catch {
      stored = null;
    }
    if (stored === "off" || stored === "on") {
      document.documentElement.dataset.motion = stored;
    } else if (preferReduce) {
      document.documentElement.dataset.motion = "off";
    } else {
      document.documentElement.dataset.motion = "on";
    }
    syncMotionButton();
    $("#motion-toggle")?.addEventListener("click", () => {
      const next = document.documentElement.dataset.motion === "off" ? "on" : "off";
      document.documentElement.dataset.motion = next;
      try {
        localStorage.setItem("shinobi-motion", next);
      } catch {
        /* ignore */
      }
      syncMotionButton();
    });
  }

  function initNav() {
    const dialog = $("#nav-dialog");
    const openBtn = $("#nav-open");
    const closeBtn = $("#nav-close");
    openBtn?.addEventListener("click", () => dialog?.showModal());
    closeBtn?.addEventListener("click", () => dialog?.close());
    dialog?.addEventListener("click", (event) => {
      if (event.target === dialog) dialog.close();
    });
    $$("[data-nav]").forEach((link) => {
      link.addEventListener("click", () => dialog?.close());
    });

    const links = $$(".nav-desktop a, .nav-dialog a");
    const sections = $$("main .act[id]");
    if (!("IntersectionObserver" in window) || !sections.length) return;
    const observer = new IntersectionObserver(
      (entries) => {
        const visible = entries
          .filter((entry) => entry.isIntersecting)
          .sort((a, b) => b.intersectionRatio - a.intersectionRatio)[0];
        if (!visible) return;
        links.forEach((link) => {
          const match = link.getAttribute("href") === `#${visible.target.id}`;
          if (match) link.setAttribute("aria-current", "true");
          else link.removeAttribute("aria-current");
        });
      },
      { rootMargin: "-30% 0px -55% 0px", threshold: [0.1, 0.25, 0.5] }
    );
    sections.forEach((section) => observer.observe(section));
  }

  function initLedger() {
    $$("input[name='hand']").forEach((input) => {
      input.addEventListener("change", () => {
        if (input.checked) {
          state.hand = input.value;
          renderLedger();
        }
      });
    });
    $$("input[name='blade']").forEach((input) => {
      input.addEventListener("change", () => {
        if (input.checked) seatBlade(input.value);
      });
    });
    $$("input[data-part]").forEach((input) => {
      input.addEventListener("change", () => togglePart(input.dataset.part, input.checked));
    });
    $$("[data-preset]").forEach((btn) => {
      btn.addEventListener("click", () => applyPreset(btn.dataset.preset));
    });
    renderLedger();
  }

  function currentLoadoutLines() {
    return [...state.seated]
      .map((id) => COMPONENTS[id])
      .filter(Boolean)
      .map((row) => `- ${row.name}: ${formatG(row.g)} g`)
      .join("\n");
  }

  function buildBrief() {
    const name = $("#inq-name")?.value.trim() || "";
    const email = $("#inq-email")?.value.trim() || "";
    const role = $("#inq-role")?.value || "";
    const notes = $("#inq-notes")?.value.trim() || "";
    const destination = $("#inq-to")?.value.trim() || "";
    return [
      "SHINOBI//82 KAGE — studio brief",
      "Generated on-device. Nothing was uploaded.",
      "",
      `Name: ${name || "(not given)"}`,
      `Email: ${email || "(not given)"}`,
      `Role: ${role || "(not given)"}`,
      `Handed geometry: ${state.hand}`,
      `Modeled mass: ${formatG(grams())} g / ${ounces(grams()).toFixed(3)} oz`,
      "",
      "Seated loadout (mass-model targets, not weighed prototypes):",
      currentLoadoutLines(),
      "",
      "Notes:",
      notes || "(none)",
      "",
      destination ? `Intended recipient: ${destination}` : "Intended recipient: (visitor will address)",
      "",
      "CAD for the shop: attach SHINOBI82-KAGE-Zen-Wu-review.zip.",
      "Master files are STEP AP214. STL on the site is viewing only.",
      "",
      "This is a proposed instrument and a proposed Zen-Wu collaboration.",
      "It is not an announced Zen-Wu product and not available for purchase from this page."
    ].join("\n");
  }

  function showStatus(kind, message) {
    const box = $("#form-status");
    if (!box) return;
    box.hidden = false;
    box.dataset.kind = kind;
    box.textContent = message;
  }

  function validateInquiry() {
    const name = $("#inq-name")?.value.trim();
    const email = $("#inq-email")?.value.trim();
    const role = $("#inq-role")?.value;
    const errors = [];
    if (!name) errors.push("Add a name so the brief can be addressed.");
    if (!email || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      errors.push("Add a usable email so a reply has somewhere to go.");
    }
    if (!role) errors.push("Say whether you are writing as a maker, woodworker, or field user.");
    return errors;
  }

  function downloadText(filename, text) {
    const blob = new Blob([text], { type: "text/plain;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);
  }

  function initForm() {
    $("#brief-download")?.addEventListener("click", () => {
      const errors = validateInquiry();
      if (errors.length) {
        showStatus("error", errors.join(" "));
        return;
      }
      downloadText("shinobi-82-kage-studio-brief.txt", buildBrief());
      showStatus(
        "ok",
        "Brief downloaded on this device. Nothing was sent. Attach it with the Zen-Wu review zip from the CAD bench."
      );
    });

    $("#brief-copy")?.addEventListener("click", async () => {
      const errors = validateInquiry();
      if (errors.length) {
        showStatus("error", errors.join(" "));
        return;
      }
      const text = buildBrief();
      try {
        await navigator.clipboard.writeText(text);
        showStatus("ok", "Brief copied. Paste it into your own mail client. This page did not send it.");
      } catch {
        showStatus("error", "Clipboard is blocked here. Use download instead.");
      }
    });

    $("#brief-mail")?.addEventListener("click", () => {
      const errors = validateInquiry();
      if (errors.length) {
        showStatus("error", errors.join(" "));
        return;
      }
      const to = $("#inq-to")?.value.trim();
      if (!to) {
        showStatus(
          "error",
          "Add a recipient address. This page will not choose one for you, and it will not pretend a message was delivered."
        );
        return;
      }
      const body = encodeURIComponent(buildBrief());
      const subject = encodeURIComponent("SHINOBI//82 KAGE studio brief");
      window.location.href = `mailto:${encodeURIComponent(to)}?subject=${subject}&body=${body}`;
      showStatus(
        "ok",
        "Your mail client should open with the brief. If nothing opens, download the file and attach it yourself."
      );
    });
  }

  function initYear() {
    const year = $("#year");
    if (year) year.textContent = String(new Date().getFullYear());
  }

  function initGrind() {
    $$("[data-zone]").forEach((btn) => {
      btn.addEventListener("click", () => {
        state.zone = btn.dataset.zone;
        renderGrind();
      });
    });
    renderGrind();
  }

  function initInventory() {
    const buttons = $$("[data-item]");
    const panels = $$("[data-item-panel]");
    if (!buttons.length) return;
    const activate = (id) => {
      buttons.forEach((btn) => btn.setAttribute("aria-selected", btn.dataset.item === id ? "true" : "false"));
      panels.forEach((panel) => {
        panel.hidden = panel.dataset.itemPanel !== id;
      });
    };
    buttons.forEach((btn) => {
      btn.addEventListener("click", () => activate(btn.dataset.item));
    });
    activate(buttons[0].dataset.item);
  }

  initMotion();
  initNav();
  initLedger();
  initGrind();
  initForm();
  initYear();
})();
