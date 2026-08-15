(() => {
  "use strict";

  const root = document.documentElement;
  const header = document.querySelector("[data-header]");
  const menuButton = document.querySelector("[data-menu]");
  const navigation = document.getElementById("site-nav");
  const motionButton = document.querySelector("[data-motion-toggle]");

  const setHeaderState = () => {
    if (header) header.classList.toggle("is-scrolled", window.scrollY > 24);
  };

  setHeaderState();
  window.addEventListener("scroll", setHeaderState, { passive: true });

  if (menuButton && navigation) {
    const closeMenu = ({ restoreFocus = false } = {}) => {
      navigation.classList.remove("is-open");
      menuButton.setAttribute("aria-expanded", "false");
      if (restoreFocus) menuButton.focus();
    };

    menuButton.addEventListener("click", () => {
      const willOpen = menuButton.getAttribute("aria-expanded") !== "true";
      navigation.classList.toggle("is-open", willOpen);
      menuButton.setAttribute("aria-expanded", String(willOpen));
      if (willOpen) navigation.querySelector("a")?.focus();
    });

    navigation.addEventListener("click", (event) => {
      if (event.target.closest("a")) closeMenu();
    });

    document.addEventListener("keydown", (event) => {
      if (event.key === "Escape" && navigation.classList.contains("is-open")) {
        closeMenu({ restoreFocus: true });
      }
    });

    window.addEventListener("resize", () => {
      if (window.innerWidth > 940) closeMenu();
    });
  }

  const edges = {
    mizu: {
      name: "MIZU–82",
      label: "MIZU–82 / water line",
      description: "A low-point 82 millimeter fish and field blade.",
      status: "Primary field module",
      intent: "A narrow, low-point profile for controlled draw cuts, skin release, food work, and general carry.",
      geometry: "25° inclusive, 60:40 shallow hamaguri",
      steel: "MagnaMax, pending supply and heat-treatment trials",
      reference: "Near-flat reverse face to limit steering",
      limit: "Not for bone chopping, prying, or full-length salmon filleting",
      qualification: "Final edge angles, distal flex, hardness, and sanitation geometry must be set by physical testing.",
      length: "82 MM BLADE TARGET",
      blade: "M56 175 L112 125 L690 98 L820 122 L813 184 L124 199 Z",
      edge: "M56 175 L124 199 L813 184",
      spine: "M112 125 L690 98 L820 122",
      grind: "M18 23 L135 31 L151 41 L133 48 L18 57 Z",
      grindEdge: "M18 57 L133 48 L151 41"
    },
    kumiko: {
      name: "KUMIKO–42",
      label: "KUMIKO–42 / reference line",
      description: "A compact 42 millimeter flat-back joinery module.",
      status: "Hand-specific joinery module",
      intent: "A compact marking and fitting edge whose back is designed to register directly against a square, shoulder, or kumiko lattice.",
      geometry: "15° single flat bevel; fully mirrored hand versions",
      steel: "Maker-selected laminated steel, pending edge-stability trials",
      reference: "Dead-flat back; no decorative hollow",
      limit: "Not a general field blade or striking chisel",
      qualification: "Back flatness, bevel stability, lock repeatability, and handed steering require measured sample validation.",
      length: "42 MM BLADE TARGET",
      blade: "M350 180 L394 121 L748 121 L820 132 L820 184 L394 184 Z",
      edge: "M350 180 L394 184 L820 184",
      spine: "M394 121 L748 121 L820 132",
      grind: "M18 25 L142 25 L151 41 L18 58 Z",
      grindEdge: "M18 58 L151 41"
    },
    nata: {
      name: "NATA–60",
      label: "NATA–60 / supported line",
      description: "A 60 millimeter reinforced single-bevel carving module.",
      status: "Controlled trailcraft module",
      intent: "A short, supported profile for whittling, chamfering, notching, and controlled chisel-style cuts at camp or bench.",
      geometry: "24° single bevel with a supported heel",
      steel: "MagnaCut candidate, pending maker review",
      reference: "Flat reverse face for guided carving",
      limit: "Not for batoning, prying, heavy bone, or free-swing chopping",
      qualification: "The lock, tang shoulders, edge support, and hand clearance must survive off-axis and wet-use testing.",
      length: "60 MM BLADE TARGET",
      blade: "M238 170 L292 111 L708 103 L820 128 L815 187 L292 190 Z",
      edge: "M238 170 L292 190 L815 187",
      spine: "M292 111 L708 103 L820 128",
      grind: "M18 21 L138 28 L151 42 L18 60 Z",
      grindEdge: "M18 60 L151 42"
    }
  };

  const edgeButtons = [...document.querySelectorAll("[data-edge]")];
  const edgePanel = document.getElementById("edge-panel");
  const edgeNodes = {
    label: document.querySelector("[data-edge-label]"),
    description: document.querySelector("[data-edge-desc]"),
    status: document.querySelector("[data-status]"),
    name: document.querySelector("[data-edge-name]"),
    intent: document.querySelector("[data-edge-intent]"),
    geometry: document.querySelector("[data-geometry]"),
    steel: document.querySelector("[data-steel]"),
    reference: document.querySelector("[data-reference]"),
    limit: document.querySelector("[data-limit]"),
    qualification: document.querySelector("[data-qualification]"),
    length: document.querySelector("[data-edge-length]"),
    blade: document.querySelector("[data-module-blade]"),
    shadow: document.querySelector("[data-module-shadow]"),
    edge: document.querySelector("[data-module-edge]"),
    spine: document.querySelector("[data-module-spine]"),
    grind: document.querySelector("[data-grind] path:first-child"),
    grindEdge: document.querySelector("[data-grind] .grind-edge")
  };

  const setEdge = (key, { moveFocus = false } = {}) => {
    const edge = edges[key];
    const activeButton = edgeButtons.find((button) => button.dataset.edge === key);
    if (!edge || !activeButton) return;

    edgeButtons.forEach((button) => {
      const selected = button === activeButton;
      button.setAttribute("aria-selected", String(selected));
      button.tabIndex = selected ? 0 : -1;
    });

    if (edgePanel) edgePanel.setAttribute("aria-labelledby", activeButton.id);
    if (moveFocus) activeButton.focus();

    edgeNodes.label.textContent = edge.label;
    edgeNodes.description.textContent = edge.description;
    edgeNodes.status.textContent = edge.status;
    edgeNodes.name.textContent = edge.name;
    edgeNodes.intent.textContent = edge.intent;
    edgeNodes.geometry.textContent = edge.geometry;
    edgeNodes.steel.textContent = edge.steel;
    edgeNodes.reference.textContent = edge.reference;
    edgeNodes.limit.textContent = edge.limit;
    edgeNodes.qualification.textContent = edge.qualification;
    edgeNodes.length.textContent = edge.length;
    edgeNodes.blade.setAttribute("d", edge.blade);
    edgeNodes.shadow.setAttribute("d", edge.blade);
    edgeNodes.edge.setAttribute("d", edge.edge);
    edgeNodes.spine.setAttribute("d", edge.spine);
    edgeNodes.grind.setAttribute("d", edge.grind);
    edgeNodes.grindEdge.setAttribute("d", edge.grindEdge);
  };

  edgeButtons.forEach((button, index) => {
    button.addEventListener("click", () => setEdge(button.dataset.edge));
    button.addEventListener("keydown", (event) => {
      if (!["ArrowLeft", "ArrowRight", "Home", "End"].includes(event.key)) return;
      event.preventDefault();
      let nextIndex = index;
      if (event.key === "ArrowRight") nextIndex = (index + 1) % edgeButtons.length;
      if (event.key === "ArrowLeft") nextIndex = (index - 1 + edgeButtons.length) % edgeButtons.length;
      if (event.key === "Home") nextIndex = 0;
      if (event.key === "End") nextIndex = edgeButtons.length - 1;
      setEdge(edgeButtons[nextIndex].dataset.edge, { moveFocus: true });
    });
  });

  const loadouts = {
    kumiko: {
      name: "Kumiko pocket",
      grams: "17.52",
      ounces: "0.618 oz modeled target",
      items: [
        ["KAGE open-frame handle", "shared structure"],
        ["KUMIKO–42 module", "flat-back joinery edge"],
        ["Blade cover", "edge protection"]
      ]
    },
    river: {
      name: "Backcountry river",
      grams: "24.06",
      ounces: "0.849 oz modeled target",
      items: [
        ["KAGE open-frame handle", "shared structure"],
        ["MIZU–82 module", "fish and food edge"],
        ["KAGE saya / power grip", "carry and sustained grip"],
        ["Diamond maintenance tag", "field edge care"]
      ]
    },
    trail: {
      name: "Trailcraft",
      grams: "27.20",
      ounces: "0.959 oz modeled target",
      items: [
        ["KAGE open-frame handle", "shared structure"],
        ["NATA–60 module", "supported carving edge"],
        ["KAGE saya / power grip", "carry and sustained grip"],
        ["Diamond maintenance tag", "field edge care"]
      ]
    },
    salmon: {
      name: "Niagara salmon",
      grams: "30.66",
      ounces: "1.081 oz modeled target",
      items: [
        ["KAGE handle + MIZU–82", "primary cutting system"],
        ["KAGE saya / power grip", "carry and sustained grip"],
        ["Diamond tag / spike study", "separate maintenance tool"],
        ["1.2 × 800 mm wire study", "species-dependent module"],
        ["Pinbone tweezer study", "fine extraction"]
      ]
    },
    studio: {
      name: "Complete studio system",
      grams: "58.36",
      ounces: "2.059 oz modeled target",
      items: [
        ["KAGE open-frame handle", "shared structure"],
        ["MIZU–82 module", "fish and field"],
        ["KUMIKO–42 module", "fine joinery"],
        ["NATA–60 module", "supported carving"],
        ["Saya, maintenance, wire", "complete proposed kit"]
      ]
    }
  };

  const loadoutButtons = [...document.querySelectorAll("[data-loadout]")];
  const massNode = document.querySelector("[data-mass]");
  const massBar = document.querySelector("[data-mass-bar]");
  const massImperial = document.querySelector("[data-mass-imperial]");
  const loadoutName = document.querySelector("[data-loadout-name]");
  const loadoutList = document.querySelector("[data-loadout-list]");

  const setLoadout = (key) => {
    const loadout = loadouts[key];
    if (!loadout) return;

    loadoutButtons.forEach((button) => {
      const active = button.dataset.loadout === key;
      button.classList.toggle("is-active", active);
      button.setAttribute("aria-pressed", String(active));
    });

    massNode.textContent = loadout.grams;
    massBar.style.setProperty("--mass-percent", `${Math.min(100, (Number(loadout.grams) / 60) * 100)}%`);
    massImperial.textContent = loadout.ounces;
    loadoutName.textContent = loadout.name;
    loadoutList.replaceChildren(
      ...loadout.items.map(([item, purpose]) => {
        const listItem = document.createElement("li");
        const name = document.createElement("span");
        const note = document.createElement("small");
        name.textContent = item;
        note.textContent = purpose;
        listItem.append(name, note);
        return listItem;
      })
    );
  };

  loadoutButtons.forEach((button) => {
    button.addEventListener("click", () => setLoadout(button.dataset.loadout));
  });

  let userReducedMotion = false;
  try {
    userReducedMotion = localStorage.getItem("kage_reduced_motion") === "true";
  } catch (_) {
    userReducedMotion = false;
  }

  const applyMotionPreference = () => {
    root.classList.toggle("user-reduced-motion", userReducedMotion);
    if (!motionButton) return;
    motionButton.setAttribute("aria-pressed", String(userReducedMotion));
    motionButton.textContent = userReducedMotion ? "Use system motion" : "Reduce motion";
  };

  applyMotionPreference();

  motionButton?.addEventListener("click", () => {
    userReducedMotion = !userReducedMotion;
    try {
      localStorage.setItem("kage_reduced_motion", String(userReducedMotion));
    } catch (_) {
      // The preference still applies for this page view when storage is unavailable.
    }
    applyMotionPreference();
  });
})();
