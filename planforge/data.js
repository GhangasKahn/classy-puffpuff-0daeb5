window.PLANFORGE_DATA = {
  metrics: [
    { value: "8", label: "Evidence classes", note: "Fact, assumption, and test stay distinct" },
    { value: "7", label: "Phase gates", note: "Intake through verified handoff" },
    { value: "R0–R4", label: "Risk classes", note: "Verification scales with consequence" },
    { value: "0", label: "Guessed dimensions", note: "The only acceptable target" }
  ],

  layers: [
    {
      id: "01", title: "Design basis", tag: "Why / what / constraints",
      description: "Requirements, evidence, assumptions, risk, decisions, calculations, and release boundary.",
      glyph: "basis"
    },
    {
      id: "02", title: "Controlled geometry", tag: "Datums / parameters / parts",
      description: "One governing source for every critical dimension, interface, tolerance, and movement allowance.",
      glyph: "geometry"
    },
    {
      id: "03", title: "Build sequence", tag: "Route / hold / assemble",
      description: "Tool-realistic operations, workholding, inspection points, assembly access, and irreversible gates.",
      glyph: "sequence"
    },
    {
      id: "04", title: "Verification", tag: "Falsify / correct / release",
      description: "Independent checks reconcile CAD, sheets, BOM, cut list, instructions, risks, and actual files.",
      glyph: "verify"
    }
  ],

  evidence: [
    { code: "G", key: "given", name: "Given", description: "Explicitly supplied by the user, a legible label, or a referenced authoritative document." },
    { code: "M", key: "measured", name: "Measured", description: "Obtained by a stated real-world method; instrument and uncertainty travel with the value." },
    { code: "S", key: "sourced", name: "Sourced", description: "Taken from an opened primary source with title, revision, section, and direct reference." },
    { code: "D", key: "derived", name: "Derived", description: "Calculated from declared inputs with equation, substituted units, and auditable result." },
    { code: "A", key: "assumed", name: "Assumed", description: "Temporary choice for missing non-blocking information; sensitivity and replacement method required." },
    { code: "E", key: "estimated", name: "Estimated", description: "Inferred from incomplete evidence; report a range and never use as an exact fabrication dimension." },
    { code: "T", key: "test", name: "Test-based", description: "Established by coupon, mock-up, proof test, fit check, calibration, or commissioning record." },
    { code: "P", key: "professional", name: "Professional-verify", description: "Requires a licensed or otherwise qualified reviewer before the affected release can advance." }
  ],

  riskTriggers: [
    { id: "decorative", level: 0, label: "Decorative / organizational", detail: "Negligible foreseeable injury consequence." },
    { id: "furniture", level: 1, label: "Ordinary furniture / hand jig", detail: "Modest loads, no high-energy motion." },
    { id: "loadbearing", level: 2, label: "Load-bearing / wall-mounted", detail: "Failure could injure or damage property." },
    { id: "vulnerable", level: 2, label: "Child, elder, or accessible use", detail: "User population raises consequence." },
    { id: "outdoor", level: 2, label: "Outdoor / four-season", detail: "Moisture, decay, wind, and anchorage matter." },
    { id: "powered", level: 3, label: "Powered cutter / high energy", detail: "Blade, abrasive, belt, motor, or stored energy." },
    { id: "lifting", level: 3, label: "Lifting / rigging / overhead", detail: "Suspended or substantial overhead load." },
    { id: "structure", level: 3, label: "Occupancy-related structure", detail: "Deck, stair, pergola, timber frame, or guard." },
    { id: "public", level: 4, label: "Public / life-safety system", detail: "Severe injury is a credible failure outcome." },
    { id: "critical", level: 4, label: "Critical guard / fall protection", detail: "A primary safeguard or life-safety function." }
  ],

  riskLevels: [
    { id: "R0", name: "Minimal", description: "Decorative or organizational object. Proportionate dimensional checks." },
    { id: "R1", name: "Ordinary", description: "Furniture or hand jig. Verify fit, stability, movement, and normal misuse." },
    { id: "R2", name: "Consequential", description: "Explicit loads, failure review, field verification, and prototype testing." },
    { id: "R3", name: "High energy / structural", description: "Authoritative standards, conservative boundaries, and qualified review." },
    { id: "R4", name: "Life safety", description: "Concept support only without the required licensed or qualified approval." }
  ],

  phases: [
    {
      id: 0, short: "Intake", title: "Intake + evidence",
      release: "CONCEPT",
      objective: "Establish what is known, what is desired, what was physically measured, and what can go wrong before geometry begins.",
      actions: [
        "Restate the real-world outcome and inventory every input.",
        "Separate observation from inference for each reference.",
        "Build evidence, assumption, and conflict registers.",
        "Classify risk R0–R4 and identify the minimum blocking facts."
      ],
      outputs: ["Interpreted brief", "Evidence register", "Risk class", "Blocking questions", "Initial sheet / file register"],
      gate: "Enough evidence to define measurable requirements"
    },
    {
      id: 1, short: "Baseline", title: "Requirements baseline",
      release: "PRELIMINARY",
      objective: "Translate vague intent into uniquely identified, measurable requirements with a verification method and a stated priority.",
      actions: [
        "Assign FUN, DIM, LOAD, MAT, TOOL, ERG, SAFE, DOC, and lifecycle IDs.",
        "Convert adjectives such as strong, accurate, and weatherproof into observable criteria.",
        "Map each MUST to a feature, calculation, test, note, or exception.",
        "Resolve material conflicts before freezing the baseline."
      ],
      outputs: ["Traceability matrix", "Success criteria", "Constraint matrix", "Approved concept brief"],
      gate: "No unresolved conflict controlling safety or primary geometry"
    },
    {
      id: 2, short: "Concepts", title: "Concept selection",
      release: "PRELIMINARY",
      objective: "Compare genuinely different architectures before expensive detail work makes the first idea feel inevitable.",
      actions: [
        "Create the simplest robust, balanced, and ambitious concepts where appropriate.",
        "Show load path, joint logic, movement strategy, maintenance, and credible failure modes.",
        "Score with user-derived weights and test sensitivity.",
        "Record the selected direction and useful features from rejected concepts."
      ],
      outputs: ["Concept sheets", "Decision matrix", "Sensitivity note", "Prototype questions"],
      gate: "Design direction approved"
    },
    {
      id: 3, short: "Skeleton", title: "Preliminary engineering",
      release: "PROTOTYPE",
      objective: "Build the parametric skeleton, assembly tree, and calculation basis before detailed dimensions proliferate.",
      actions: [
        "Establish coordinates, primary datums, master parameters, and dependencies.",
        "Create unique part, joint, dimension, calculation, and drawing IDs.",
        "Model principal geometry, motion, loads, movement, stability, and clearances.",
        "Allocate function- and process-appropriate tolerances."
      ],
      outputs: ["Parameter register", "Assembly tree", "Preliminary CAD", "Calculation basis", "Prototype plan"],
      gate: "Primary geometry closes and prototype questions are testable"
    },
    {
      id: 4, short: "Freeze", title: "Design-freeze review",
      release: "FABRICATION REVIEW",
      objective: "Challenge the whole system—fit, site, load, motion, grain, tooling, transport, clamping, finish, service, and review requirements.",
      actions: [
        "Run PASS / PASS WITH CONDITION / N/A / FAIL against each freeze item.",
        "Check assembly and disassembly access before the drawings hide it.",
        "Confirm stock, hardware, adhesives, finish, replacement components, and tool access.",
        "Issue a revision if any frozen parameter changes."
      ],
      outputs: ["Freeze checklist", "Final open-item list", "Authorized detailed-design basis"],
      gate: "No FAIL affecting safety or primary geometry"
    },
    {
      id: 5, short: "Detail", title: "Detailed documentation",
      release: "FABRICATION REVIEW",
      objective: "Resolve every fabricated part, purchased interface, operation, drawing, schedule, assembly state, and inspection point.",
      actions: [
        "Complete part geometry from declared datums, including hidden features and mating IDs.",
        "Reconcile BOM, cut list, hardware, joinery, finish, routing, and assembly schedules.",
        "Create orthographic, section, exploded, detail, safety, and full-size template views as applicable.",
        "Export actual digital artifacts from the controlled source model."
      ],
      outputs: ["Drawing set", "CAD / vector files", "Schedules", "Build manual", "Inspection plan"],
      gate: "Candidate package exists and opens"
    },
    {
      id: 6, short: "Verify", title: "Independent verification",
      release: "CONDITIONAL / READY / WITHHELD",
      objective: "Freeze a candidate, try to falsify it, correct it, and make the release boundary impossible to miss.",
      actions: [
        "Recalculate critical values from original inputs without copying prior conclusions.",
        "Reconcile each mating interface from both parts and each artifact against the registers.",
        "Inspect every sheet at intended size and dense details at 200% zoom.",
        "Repeat FMEA against final geometry and record discrepancies and corrections."
      ],
      outputs: ["Verification report", "Discrepancy log", "Final traceability", "Release recommendation"],
      gate: "No hard fail; all external reviews and release conditions are explicit"
    }
  ],

  releases: [
    "CONCEPT", "PRELIMINARY", "PROTOTYPE", "FABRICATION REVIEW",
    "READY WITH CONDITIONS", "FABRICATION-READY", "RELEASE WITHHELD"
  ],

  modules: [
    {
      id: "core", icon: "00", name: "Wood + joinery core", core: true,
      description: "Units, stock, grain, moisture, movement, joints, adhesives, hardware, tolerances, process, finish, assembly, inspection, and maintenance."
    },
    {
      id: "furniture", icon: "FC", name: "Furniture + casework",
      description: "Anthropometry, racking, sag, creep, fatigue, tipping, entrapment, drawers, doors, tops, anchorage, and user contact."
    },
    {
      id: "outdoor", icon: "04", name: "Outdoor / four-season",
      description: "Drainage, capillary breaks, end grain, freeze–thaw, decay, UV, corrosion, wind, uplift, anchorage, and renewal."
    },
    {
      id: "structure", icon: "ST", name: "Structural + timber",
      description: "Jurisdiction, adopted code, site loads, full load path, reduced sections, connections, bracing, foundation, and professional review."
    },
    {
      id: "machine", icon: "ME", name: "Powered machine",
      description: "High-energy motion, workholding, ejection, nip points, guards, dust, restart, isolation, containment, and commissioning."
    },
    {
      id: "lifting", icon: "LG", name: "Lifting + mobile",
      description: "Rated load, dynamics, stability, rated components, anti-drop control, travel stops, proof procedure, exclusion zone, and inspection."
    },
    {
      id: "heat", icon: "HF", name: "Heat + flame",
      description: "Fuel, flame envelope, ignition, ventilation, CO, combustible clearance, shutdown, coupon process, cooling, and fire watch."
    },
    {
      id: "controls", icon: "EC", name: "Electrical + controls",
      description: "Supply, protection, wiring, state model, interlocks, fault behavior, deterministic safeguards, logging, and qualified review."
    },
    {
      id: "solo", icon: "SA", name: "Solo + accessible build",
      description: "Mass, reach, force, work height, grip points, stable parking states, modularity, captive hardware, aids, and recovery breaks."
    }
  ],

  sheets: [
    {
      number: "GA-100", title: "General arrangement", type: "Orientation + envelope",
      src: "../fence/martin/fab/06_DRAWINGS/GA-100_arrangement.svg",
      purpose: "Answers: What is the complete assembly, its governing envelope, datums, principal interfaces, and release state?"
    },
    {
      number: "GA-110", title: "Dimensioned elevation", type: "Locate + inspect",
      src: "../fence/martin/fab/06_DRAWINGS/GA-110_elevation.svg",
      purpose: "Answers: Where are the controlling centers, openings, heights, pattern elements, and field-verification points?"
    },
    {
      number: "EX-200", title: "Exploded assembly", type: "Order + direction",
      src: "../fence/martin/fab/06_DRAWINGS/EX-200_exploded.svg",
      purpose: "Answers: Which parts exist, in what orientation and order do they assemble, and how do balloons map to the BOM?"
    },
    {
      number: "J-401", title: "Nuki joint detail", type: "Make + fit",
      src: "../fence/martin/fab/06_DRAWINGS/J-401_nuki.svg",
      purpose: "Answers: What are the mating geometries, datums, fit, wedge direction, bearing faces, and inspection criteria?"
    },
    {
      number: "P-304", title: "Gate part sheet", type: "Fabricate + verify",
      src: "../fence/martin/fab/06_DRAWINGS/P-304_gate.svg",
      purpose: "Answers: Can the gate components be fabricated and inspected without scaling a perspective image?"
    },
    {
      number: "QA-701", title: "Inspection plan", type: "Accept + record",
      src: "../fence/martin/fab/12_QA/QA-701_inspection.svg",
      purpose: "Answers: Which characteristics control acceptance, how are they measured, and what happens when one fails?"
    }
  ],

  drawingRules: [
    { id: "01", title: "Datum first", text: "Locate critical geometry from stable faces A, B, and C; avoid chain dimensions where accumulation matters." },
    { id: "02", title: "One governing source", text: "A critical dimension controls in one place. Repeated information is marked REF and never drives fabrication." },
    { id: "03", title: "Expose hidden work", text: "Use sections and details for mortises, hardware stacks, clearances, glue zones, and movement paths." },
    { id: "04", title: "Print-legible", text: "Inspect line hierarchy, text, leaders, hatching, clipping, overlaps, and calibration at final page size." }
  ],

  artifacts: [
    {
      code: "G", title: "Design basis", note: "Intent and evidence",
      items: [
        ["readme", "README + file manifest", "MD / PDF"],
        ["basis", "Requirements + design basis", "MD / PDF"],
        ["evidence", "Evidence + source register", "CSV"],
        ["risk", "Risk / FMEA register", "CSV / PDF"],
        ["calculations", "Calculation register", "Notebook / PDF"],
        ["change", "Decision + change log", "MD / JSON"]
      ]
    },
    {
      code: "A", title: "Geometry + drawings", note: "Controlled views",
      items: [
        ["cad", "Parametric source model", "FCStd / SCAD"],
        ["step", "Neutral solid export", "STEP"],
        ["arrangement", "General arrangement", "SVG / PDF"],
        ["exploded", "Exploded assembly", "SVG / PDF"],
        ["parts", "Individual part drawings", "SVG / PDF"],
        ["joinery", "Joinery + interface details", "SVG / PDF"],
        ["templates", "Calibrated 1:1 templates", "SVG / DXF"],
        ["drawing-set", "Indexed drawing set", "PDF"]
      ]
    },
    {
      code: "S", title: "Schedules", note: "Machine-readable",
      items: [
        ["bom", "Master BOM", "CSV"],
        ["cut-list", "Cut list + cut maps", "CSV / SVG"],
        ["hardware", "Hardware schedule", "CSV"],
        ["joints", "Joinery schedule", "CSV"],
        ["dimensions", "Dimension register", "CSV"],
        ["traceability", "Requirements traceability", "CSV"]
      ]
    },
    {
      code: "W", title: "Work instructions", note: "Build and service",
      items: [
        ["routing", "Operation routing", "CSV / PDF"],
        ["assembly", "Assembly + clamping plan", "PDF"],
        ["finish", "Finish schedule", "CSV / PDF"],
        ["inspection", "Inspection + test plan", "CSV / PDF"],
        ["maintenance", "Maintenance + repair guide", "PDF"],
        ["checksums", "Integrity manifest / checksums", "TXT / JSON"]
      ]
    }
  ],

  hardFails: [
    "A missing overall, interface, or mating dimension remains.",
    "Two controlling documents assign contradictory dimensions to one feature.",
    "Critical geometry comes only from an unscaled perspective image.",
    "A tolerance-sensitive assembly has no declared datum logic.",
    "A fabricated part is absent from the BOM, cut list, or drawing set.",
    "A cross-grain interface has no deliberate movement provision.",
    "A hidden joint, hardware stack, guard, or workholding method is unshown.",
    "A claimed file is absent, corrupt, empty, unrecomputed, or uninspected."
  ],

  lenses: [
    { name: "The builder", question: "Where must I guess, improvise workholding, or install inaccessible hardware?" },
    { name: "The metrologist", question: "What controls, from which datum, at what tolerance, measured with which tool?" },
    { name: "The wood scientist", question: "Where do grain, moisture, creep, decay, or incompatible materials defeat intent?" },
    { name: "The mechanic", question: "What binds, wears, loosens, overheats, collides, or stores dangerous energy?" },
    { name: "The safety reviewer", question: "What happens during misuse, a jam, power loss, service, or component failure?" },
    { name: "The skeptic", question: "Which conclusion rests on the weakest assumption or circular verification?" }
  ]
};
