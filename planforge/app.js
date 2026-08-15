(function () {
  "use strict";

  const D = window.PLANFORGE_DATA;
  const $ = (selector, root = document) => root.querySelector(selector);
  const $$ = (selector, root = document) => Array.from(root.querySelectorAll(selector));

  const storage = {
    get(key, fallback) {
      try {
        const raw = localStorage.getItem("planforge_" + key);
        return raw == null ? fallback : JSON.parse(raw);
      } catch (_) {
        return fallback;
      }
    },
    set(key, value) {
      try { localStorage.setItem("planforge_" + key, JSON.stringify(value)); } catch (_) {}
    }
  };

  const state = {
    view: "overview",
    assemblyStep: 4,
    phase: 0,
    modules: storage.get("modules", []),
    package: storage.get("package", {}),
    risk: storage.get("risk", [])
  };

  function escapeHTML(value) {
    return String(value == null ? "" : value)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  }

  function toast(message) {
    const node = $("#toast");
    node.textContent = message;
    node.classList.add("show");
    clearTimeout(toast.timer);
    toast.timer = setTimeout(() => node.classList.remove("show"), 2200);
  }

  async function copyText(text, message) {
    try {
      await navigator.clipboard.writeText(text);
      toast(message || "Copied to clipboard");
    } catch (_) {
      const area = document.createElement("textarea");
      area.value = text;
      area.style.position = "fixed";
      area.style.opacity = "0";
      document.body.appendChild(area);
      area.select();
      document.execCommand("copy");
      area.remove();
      toast(message || "Copied to clipboard");
    }
  }

  function downloadText(filename, text) {
    const blob = new Blob([text], { type: "text/plain;charset=utf-8" });
    const link = document.createElement("a");
    link.href = URL.createObjectURL(blob);
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    link.remove();
    setTimeout(() => URL.revokeObjectURL(link.href), 1000);
  }

  function setView(view, pushHash = true) {
    if (!$(`.view[data-view="${view}"]`)) view = "overview";
    state.view = view;
    $$(".view").forEach((node) => node.classList.toggle("active", node.dataset.view === view));
    $$("[data-view-link]").forEach((node) => node.classList.toggle("active", node.dataset.viewLink === view));
    $$(".nav-item").forEach((node) => node.classList.toggle("active", node.dataset.viewLink === view));
    if (pushHash && window.location.hash !== "#" + view) history.pushState(null, "", "#" + view);
    closeSidebar();
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  function closeSidebar() {
    $("#sidebar").classList.remove("open");
    $("#sidebarScrim").classList.remove("open");
    $("#menuButton").setAttribute("aria-expanded", "false");
  }

  function initNavigation() {
    $$("[data-view-link]").forEach((node) => {
      node.addEventListener("click", (event) => {
        if (node.tagName === "A") event.preventDefault();
        setView(node.dataset.viewLink);
      });
    });
    $("#menuButton").addEventListener("click", () => {
      const open = $("#sidebar").classList.toggle("open");
      $("#sidebarScrim").classList.toggle("open", open);
      $("#menuButton").setAttribute("aria-expanded", String(open));
    });
    $("#sidebarScrim").addEventListener("click", closeSidebar);
    window.addEventListener("popstate", () => setView(location.hash.slice(1) || "overview", false));
    setView(location.hash.slice(1) || "overview", false);
  }

  function layerGlyph(kind) {
    const common = `viewBox="0 0 180 90" aria-hidden="true"`;
    if (kind === "basis") return `<svg ${common}><path d="M34 16h78v58H34zM45 29h56M45 40h38M45 51h50M124 27h20v20h-20zM134 47v22M124 69h20"/><circle cx="134" cy="37" r="4"/></svg>`;
    if (kind === "geometry") return `<svg ${common}><path d="m37 62 47-38 58 25-48 34zM84 24v40m58-15v19L94 83V64M37 62v9l57 12"/><path d="M25 16h126M25 12v8m126-8v8M84 15v8"/></svg>`;
    if (kind === "sequence") return `<svg ${common}><path d="M28 61h32V29H28zm48-15h32V14H76zm48 30h32V44h-32z"/><path d="M60 45h12m36-16h20" stroke-dasharray="4 4"/><path d="m68 41 6 4-6 4m56-24 6 4-6 4"/></svg>`;
    return `<svg ${common}><circle cx="82" cy="44" r="28"/><path d="m65 44 11 11 23-26M122 18l27 27m0-27-27 27M25 74h130"/></svg>`;
  }

  function renderOverview() {
    $("#metricGrid").innerHTML = D.metrics.map((item) => `
      <article class="metric">
        <span>${escapeHTML(item.label)}</span>
        <strong>${escapeHTML(item.value)}</strong>
        <p>${escapeHTML(item.note)}</p>
      </article>`).join("");

    $("#layerGrid").innerHTML = D.layers.map((item) => `
      <article class="layer-card">
        <span class="layer-num">${item.id}</span>
        <div class="layer-glyph">${layerGlyph(item.glyph)}</div>
        <h3>${escapeHTML(item.title)}</h3>
        <p>${escapeHTML(item.description)}</p>
        <small>${escapeHTML(item.tag)}</small>
      </article>`).join("");

    $("#explodeBack").addEventListener("click", () => {
      state.assemblyStep = Math.max(1, state.assemblyStep - 1);
      drawAssembly();
    });
    $("#explodeForward").addEventListener("click", () => {
      state.assemblyStep = Math.min(4, state.assemblyStep + 1);
      drawAssembly();
    });
    drawAssembly();
  }

  function drawAssembly() {
    const step = state.assemblyStep;
    $("#explodeReadout").textContent = String(step).padStart(2, "0") + " / 04";
    const shown = (n) => n <= step ? 1 : 0.13;
    const hot = (n) => n === step ? "#ed7a52" : "#f2eee4";
    const label = ["", "Leg frames", "Long stretchers", "Cross bearers", "Worktop + stops"][step];
    $("#assemblyDiagram").innerHTML = `
      <svg viewBox="0 0 600 440" role="img" aria-label="Four-stage exploded trestle assembly diagram. Illustrative and not for fabrication.">
        <defs>
          <marker id="arrow" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto">
            <path d="M0 0 8 4 0 8Z" fill="#d4663f"/>
          </marker>
          <linearGradient id="woodTop" x1="0" x2="1">
            <stop offset="0" stop-color="#e6d5b1"/><stop offset="1" stop-color="#bfa77d"/>
          </linearGradient>
          <linearGradient id="woodSide" x1="0" x2="1">
            <stop offset="0" stop-color="#8d7656"/><stop offset="1" stop-color="#a98e65"/>
          </linearGradient>
          <filter id="shadow"><feDropShadow dx="0" dy="8" stdDeviation="7" flood-opacity=".25"/></filter>
        </defs>

        <g fill="none" stroke="#ffffff" stroke-opacity=".18" stroke-width="1">
          <path d="M45 365h500M73 386l449-201M80 340l310 82M170 240v178M300 180v240M430 125v290"/>
          <path d="M70 388v-18m80-18v-18m80-18v-18m80-18v-18m80-18v-18m80-18v-18"/>
        </g>

        <g opacity="${shown(1)}" filter="url(#shadow)">
          <g class="diagram-part" stroke="${hot(1)}" stroke-width="${step === 1 ? 2.6 : 1.2}">
            <path d="m126 278 34 11-17 109-31-10z" fill="#a98e65"/>
            <path d="m208 251 34 11 20 112-31-10z" fill="#a98e65"/>
            <path d="m125 281 82-31 35 12-82 31z" fill="url(#woodTop)"/>
            <path d="m112 388 31 10 119-24-31-10z" fill="#7a6549"/>
            <path d="m371 196 34 11-17 109-31-10z" fill="#a98e65"/>
            <path d="m452 169 34 11 20 112-31-10z" fill="#a98e65"/>
            <path d="m371 199 81-31 34 12-81 31z" fill="url(#woodTop)"/>
            <path d="m357 306 31 10 118-24-31-10z" fill="#7a6549"/>
          </g>
          <g fill="#d4663f" font-family="DM Mono,monospace" font-size="10">
            <circle cx="111" cy="387" r="11"/><text x="111" y="391" text-anchor="middle" fill="#fff">01</text>
            <path d="M99 387H68" stroke="#d4663f"/><text x="63" y="390" text-anchor="end">P-101 / LEG FRAME</text>
          </g>
        </g>

        <g opacity="${shown(2)}" class="diagram-part" filter="url(#shadow)" stroke="${hot(2)}" stroke-width="${step === 2 ? 2.6 : 1.2}">
          <path d="m166 294 242-85 17 8-242 87z" fill="#b99d70"/>
          <path d="m183 304 242-87v20l-242 87z" fill="#816b4e"/>
          <path d="m177 337 242-85 17 8-242 87z" fill="#b99d70"/>
          <path d="m194 347 242-87v20l-242 87z" fill="#816b4e"/>
          <path d="m170 306-21-7m278-78 23-8M182 347l-21 6m277-89 22-8" fill="none" stroke="#d4663f" stroke-dasharray="5 4" marker-end="url(#arrow)"/>
        </g>

        <g opacity="${shown(3)}" class="diagram-part" filter="url(#shadow)" stroke="${hot(3)}" stroke-width="${step === 3 ? 2.6 : 1.2}">
          <path d="m124 229 106 34 17-8-106-34z" fill="#ddc69a"/>
          <path d="m124 229 17-8v17l-17 8z" fill="#8b7453"/>
          <path d="m357 151 105 34 17-8-105-34z" fill="#ddc69a"/>
          <path d="m357 151 17-8v17l-17 8z" fill="#8b7453"/>
          <path d="M181 196v43m232-121v43" fill="none" stroke="#d4663f" stroke-dasharray="5 4" marker-end="url(#arrow)"/>
        </g>

        <g opacity="${shown(4)}" class="diagram-part" filter="url(#shadow)" stroke="${hot(4)}" stroke-width="${step === 4 ? 2.6 : 1.2}">
          <path d="m88 141 310-102 121 47-310 105z" fill="url(#woodTop)"/>
          <path d="m209 191 310-105v32L209 224z" fill="url(#woodSide)"/>
          <path d="m88 141 121 50v33L88 173z" fill="#9e855f"/>
          <path d="m105 146 294-96M133 158l294-96M161 169l294-96M189 181l294-96" stroke="#7e6a50" stroke-opacity=".45"/>
          <path d="M295 18v44" fill="none" stroke="#d4663f" stroke-dasharray="5 4" marker-end="url(#arrow)"/>
          <circle cx="474" cy="105" r="8" fill="#d4663f" stroke="none"/>
          <path d="m467 109-19 20" fill="none" stroke="#d4663f"/>
        </g>

        <g font-family="DM Mono,monospace">
          <text x="28" y="28" fill="#ed7a52" font-size="10" letter-spacing="2">ASSEMBLY ${String(step).padStart(2, "0")} / ${label.toUpperCase()}</text>
          <text x="28" y="47" fill="#fff" fill-opacity=".45" font-size="9">DEMO GEOMETRY · NTS · NOT FOR FABRICATION</text>
          <text x="482" y="407" fill="#fff" fill-opacity=".45" font-size="9">DATUM A / FLOOR</text>
          <path d="M480 394h70" stroke="#437885" stroke-width="2"/>
        </g>
      </svg>`;
  }

  function renderEvidence() {
    $("#evidenceGrid").innerHTML = D.evidence.map((item) => `
      <article class="evidence-card">
        <b class="ev ${item.key}">${item.code}</b>
        <div><h3>${item.name}</h3><p>${item.description}</p></div>
      </article>`).join("");

    $("#riskOptions").innerHTML = D.riskTriggers.map((item) => `
      <div class="risk-option">
        <input id="risk-${item.id}" type="checkbox" value="${item.id}" ${state.risk.includes(item.id) ? "checked" : ""} />
        <label for="risk-${item.id}"><b>R${item.level} trigger</b>${item.label}<br><small>${item.detail}</small></label>
      </div>`).join("");

    $("#riskScale").innerHTML = D.riskLevels.map((item) => `
      <article class="risk-level"><strong>${item.id}</strong><b>${item.name}</b><p>${item.description}</p></article>`).join("");

    $$("#riskOptions input").forEach((input) => input.addEventListener("change", updateRisk));
    updateRisk();
  }

  function updateRisk() {
    const checked = $$("#riskOptions input:checked").map((input) => input.value);
    state.risk = checked;
    storage.set("risk", checked);
    const max = checked.reduce((level, id) => {
      const trigger = D.riskTriggers.find((item) => item.id === id);
      return Math.max(level, trigger ? trigger.level : 0);
    }, 0);
    const detail = D.riskLevels[max];
    const result = $("#riskResult");
    result.className = "risk-result r" + max;
    result.innerHTML = `<span>Screening result</span><strong>${detail.id} / ${detail.name}</strong><p>${checked.length ? detail.description : "No trigger selected. Confirm intended use before treating this as R0."}</p>`;
  }

  function phaseGraphic(phase) {
    const index = phase.id;
    const blocks = Array.from({ length: 7 }, (_, i) => {
      const active = i <= index;
      const y = 244 - i * 27;
      const x = 44 + i * 13;
      const color = i === index ? "#d4663f" : active ? "#e8e2d5" : "#2c5155";
      return `<g opacity="${active ? 1 : .45}">
        <path d="M${x} ${y}h170l38-18H${x + 38}Z" fill="${color}" fill-opacity="${i === index ? .95 : .22}" stroke="${color}"/>
        <text x="${x + 10}" y="${y - 7}" fill="${color}" font-family="DM Mono,monospace" font-size="8">0${i} / ${D.phases[i].short.toUpperCase()}</text>
      </g>`;
    }).join("");
    return `<svg viewBox="0 0 300 290" aria-hidden="true">
      <path d="M28 264h245M28 36v228" stroke="#fff" stroke-opacity=".14"/>
      ${blocks}
      <circle cx="259" cy="${226 - index * 27}" r="6" fill="#e4b94e"/>
      <path d="M259 46v190" stroke="#e4b94e" stroke-dasharray="4 5" opacity=".55"/>
      <text x="28" y="22" fill="#fff" fill-opacity=".45" font-family="DM Mono,monospace" font-size="8">PACKAGE MATURITY / GATE ${index}</text>
    </svg>`;
  }

  function renderWorkflow() {
    $("#phaseRail").innerHTML = D.phases.map((phase) => `
      <button type="button" class="phase-button ${phase.id === state.phase ? "active" : ""}" data-phase="${phase.id}" role="tab" aria-selected="${phase.id === state.phase}">
        <span>0${phase.id}</span>
        <b>${phase.short}<small>${phase.release}</small></b>
      </button>`).join("");
    $$(".phase-button").forEach((button) => button.addEventListener("click", () => {
      state.phase = Number(button.dataset.phase);
      renderWorkflow();
    }));
    const phase = D.phases[state.phase];
    $("#phaseDetail").innerHTML = `
      <div>
        <p class="eyebrow">Phase 0${phase.id} / ${phase.release}</p>
        <h2>${phase.title}</h2>
        <p class="objective">${phase.objective}</p>
        <h3>Required operations</h3>
        <ul>${phase.actions.map((item) => `<li>${item}</li>`).join("")}</ul>
        <h3>Release outputs</h3>
        <ul>${phase.outputs.map((item) => `<li>${item}</li>`).join("")}</ul>
        <div class="phase-gate"><span>Advance only when</span><b>${phase.gate}</b></div>
      </div>
      <div class="phase-graphic">${phaseGraphic(phase)}</div>`;
    $("#releaseLadder").innerHTML = D.releases.map((release, index) => `
      <div class="release-step"><span>R${index}</span><b>${release}</b></div>`).join("");
  }

  function renderModules() {
    $("#moduleGrid").innerHTML = D.modules.map((module) => `
      <div class="module-card ${module.core ? "core" : ""}">
        <input id="module-${module.id}" type="checkbox" value="${module.id}" ${module.core || state.modules.includes(module.id) ? "checked" : ""} ${module.core ? "disabled" : ""} />
        <label for="module-${module.id}">
          <div class="module-top"><span class="module-icon">${module.icon}</span><span class="module-check">${module.core ? "Always active" : state.modules.includes(module.id) ? "Active ✓" : "Optional"}</span></div>
          <h3>${module.name}</h3><p>${module.description}</p>
        </label>
      </div>`).join("");
    $$("#moduleGrid input:not(:disabled)").forEach((input) => input.addEventListener("change", () => {
      state.modules = $$("#moduleGrid input:checked:not(:disabled)").map((node) => node.value);
      storage.set("modules", state.modules);
      renderModules();
    }));
    $("#moduleCount").textContent = `1 core + ${state.modules.length} conditional`;
    const selected = D.modules.filter((module) => module.core || state.modules.includes(module.id));
    $("#moduleStack").innerHTML = selected.map((module) => `<li>${module.name}</li>`).join("") +
      `<li>Fabrication drawing + artifact contract</li><li>Response + independent review contract</li><li>Completed project brief + evidence</li>`;
  }

  function renderDrawings() {
    $("#sheetList").innerHTML = D.sheets.map((sheet, index) => `
      <button type="button" class="sheet-tab ${index === 0 ? "active" : ""}" data-sheet="${index}" role="tab" aria-selected="${index === 0}">
        <span>${sheet.number}</span><b>${sheet.title}</b><small>${sheet.type}</small>
      </button>`).join("");
    $$(".sheet-tab").forEach((button) => button.addEventListener("click", () => selectSheet(Number(button.dataset.sheet))));
    $("#drawingRules").innerHTML = D.drawingRules.map((rule) => `
      <article class="rule-card"><span>${rule.id}</span><h3>${rule.title}</h3><p>${rule.text}</p></article>`).join("");
    selectSheet(0);
  }

  function selectSheet(index) {
    const sheet = D.sheets[index];
    $$(".sheet-tab").forEach((button, i) => {
      button.classList.toggle("active", i === index);
      button.setAttribute("aria-selected", String(i === index));
    });
    $("#sheetNumber").textContent = sheet.number;
    $("#sheetTitle").textContent = sheet.title;
    $("#sheetImage").src = sheet.src;
    $("#sheetImage").alt = sheet.title + " technical drawing";
    $("#sheetOpen").href = sheet.src;
    $("#sheetPurpose").textContent = sheet.purpose;
  }

  function renderPackage() {
    $("#artifactGroups").innerHTML = D.artifacts.map((group) => `
      <section class="artifact-group">
        <header class="artifact-head"><span>${group.code}</span><h3>${group.title}</h3><small>${group.note}</small></header>
        <div class="artifact-items">${group.items.map((item) => `
          <div class="artifact-item">
            <label><input type="checkbox" data-artifact="${item[0]}" ${state.package[item[0]] ? "checked" : ""} /><b>${item[1]}</b><small>${item[2]}</small></label>
          </div>`).join("")}</div>
      </section>`).join("");
    $$("#artifactGroups input").forEach((input) => input.addEventListener("change", () => {
      state.package[input.dataset.artifact] = input.checked;
      storage.set("package", state.package);
      updatePackageStatus();
    }));
    updatePackageStatus();
  }

  function updatePackageStatus() {
    const ids = D.artifacts.flatMap((group) => group.items.map((item) => item[0]));
    const done = ids.filter((id) => state.package[id]).length;
    const pct = Math.round(done / ids.length * 100);
    $("#packageCount").textContent = `${done} of ${ids.length} artifacts mapped`;
    $("#packageRing").style.background = `conic-gradient(var(--accent) ${pct}%,rgba(255,255,255,.12) ${pct}%)`;
    $("#packageRing span").textContent = pct + "%";
  }

  function formValues() {
    return Object.fromEntries(new FormData($("#briefForm")).entries());
  }

  function buildBrief(values) {
    const unknown = (value) => value && String(value).trim() ? String(value).trim() : "UNKNOWN";
    return `<PROJECT_BRIEF>
Project: ${unknown(values.title)}
Purpose/users: ${unknown(values.outcome)}
Project type: ${unknown(values.type)}
Intended release: ${unknown(values.release)}
Location/environment: ${unknown(values.location)}
Maximum envelope: ${unknown(values.envelope)}
Loads/workpiece range: ${unknown(values.loads)}
Hard constraints / unacceptable failures: ${unknown(values.constraints)}
Tools and skill: ${unknown(values.tools)}
Stock/material preference: ${unknown(values.stock)}
Budget: ${unknown(values.budget)}
Accessibility/solo-build limits: ${unknown(values.access)}
Aesthetic intent: ${unknown(values.aesthetic)}
References / known scale: ${unknown(values.references)}
Deliverables: ${unknown(values.deliverables)}
Unknowns: Retain every UNKNOWN above. Do not invent a controlling value.

Begin with Phase 0 under WOODWRIGHT PLANFORGE v1.0.
Separate observation from inference. Classify risk and evidence.
Do not use reference images as fabrication scale unless a trustworthy
measured reference and corrected camera geometry permit it.
</PROJECT_BRIEF>`;
  }

  function updateBrief() {
    const values = formValues();
    const required = ["title", "outcome", "envelope", "location", "loads", "constraints", "tools", "stock", "budget", "access", "aesthetic", "references", "deliverables"];
    const complete = required.filter((key) => values[key] && String(values[key]).trim()).length;
    $("#briefCompleteness").textContent = Math.round(complete / required.length * 100) + "% complete";
    $("#briefPreview").textContent = buildBrief(values);
  }

  function renderBrief() {
    $("#briefForm").addEventListener("input", updateBrief);
    $("#briefForm").addEventListener("change", updateBrief);
    $("#briefForm").addEventListener("submit", (event) => {
      event.preventDefault();
      updateBrief();
      toast("Phase 0 brief generated");
    });
    $("#briefForm").addEventListener("reset", () => setTimeout(updateBrief, 0));
    $("#fillExample").addEventListener("click", () => {
      const example = {
        title: "Knock-down hall bench / study case",
        outcome: "An indoor bench for one adult to sit while putting on shoes, with open shoe storage below and reversible winter disassembly.",
        type: "Furniture",
        release: "Fabrication review",
        envelope: "1100 × 380 × 460 mm maximum",
        location: "Conditioned residential entry / Buffalo, New York",
        loads: "User load UNKNOWN; design load and misuse cases must be established",
        constraints: "No wall anchorage; no exposed metal fasteners; must not tip during normal ingress",
        tools: "Intermediate builder; track saw, router, drill press, chisels, combination square; clamp inventory UNKNOWN",
        stock: "White oak preferred; actual boards, grade, and moisture content UNKNOWN",
        budget: "USD 700 excluding tools",
        access: "Solo build; maximum comfortable lift 18 kg; module through 760 mm doorway",
        aesthetic: "Quiet Arts-and-Crafts proportions; expressed wedged joinery; low visual mass",
        references: "No scaled reference supplied; style images are inspiration only",
        deliverables: "Design basis, PDF/SVG drawings, CAD source, BOM, cut list, joint details, assembly and inspection plan"
      };
      Object.entries(example).forEach(([name, value]) => {
        const field = $(`[name="${name}"]`, $("#briefForm"));
        if (field) field.value = value;
      });
      updateBrief();
      toast("Illustrative brief loaded");
    });
    $("#copyBrief").addEventListener("click", () => copyText($("#briefPreview").textContent, "Project brief copied"));
    $("#downloadBrief").addEventListener("click", () => {
      const values = formValues();
      const filename = (values.title || "planforge-project").toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "") + "-brief.txt";
      downloadText(filename, $("#briefPreview").textContent);
      toast("Brief downloaded");
    });
    updateBrief();
  }

  function renderAudit() {
    $("#hardFailList").innerHTML = D.hardFails.map((item, index) => `
      <div class="fail-item"><span>${String(index + 1).padStart(2, "0")}</span><p>${item}</p></div>`).join("");
    $("#lensList").innerHTML = D.lenses.map((item) => `
      <div class="lens"><b>${item.name}</b><p>${item.question}</p></div>`).join("");
    $("#copyAudit").addEventListener("click", () => copyText($(".final-command p").textContent, "Audit command copied"));
  }

  function initControls() {
    $("#resetModules").addEventListener("click", () => {
      state.modules = [];
      storage.set("modules", []);
      renderModules();
      toast("Conditional modules cleared");
    });
    $("#resetPackage").addEventListener("click", () => {
      state.package = {};
      storage.set("package", {});
      renderPackage();
      toast("Package checklist cleared");
    });
  }

  function init() {
    initNavigation();
    renderOverview();
    renderEvidence();
    renderWorkflow();
    renderModules();
    renderDrawings();
    renderPackage();
    renderBrief();
    renderAudit();
    initControls();
  }

  init();
})();
