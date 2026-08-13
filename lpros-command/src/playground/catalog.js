/**
 * Playground catalog — sub-agents, browser playbooks, VM recipes.
 * Soldiers execute under Brain contracts (MEUFT). No capital actions without HOLD.
 */

export const AGENT_CATALOG = [
  {
    id: "brain",
    role: "Brain",
    title: "MEUFT Brain",
    summary: "Plans, routes, verifies, refuses. Merges soldier output into a MEUFT brief.",
    tools: ["economics", "evidence", "spawn"],
    inputs: ["q", "categoryId", "minPrice", "maxPrice", "productCost", "soldCount"],
    outputs: ["brief", "verdict", "next"],
    parallel: false,
    capitalGate: true,
    spawnDefault: ["scout", "intel", "economics"],
  },
  {
    id: "scout",
    role: "Soldier:Scout",
    title: "Scout / pipeline",
    summary: "Official Browse pipeline rank — high-PV SKUs, scam filter.",
    tools: ["browse", "ranker", "filters"],
    inputs: ["q", "categoryId", "minPrice", "maxPrice", "costRatio"],
    outputs: ["top", "market", "viz"],
    parallel: true,
    capitalGate: false,
  },
  {
    id: "intel",
    role: "Soldier:Intel",
    title: "Competitor intel",
    summary: "Density, price ladder, seller HHI from Browse (ZIK-class, no HTML scrape).",
    tools: ["browse", "ladder", "hhi"],
    inputs: ["q", "categoryId", "minPrice", "maxPrice"],
    outputs: ["market", "lethalCandidates"],
    parallel: true,
    capitalGate: false,
  },
  {
    id: "crawler",
    role: "Soldier:Crawler",
    title: "Category crawler",
    summary: "Paginated Browse crawl (not eBay HTML). Local :8790 for long runs.",
    tools: ["browse-pages"],
    inputs: ["q", "categoryId", "crawlPages"],
    outputs: ["items", "topByPerceivedValue"],
    parallel: false,
    capitalGate: false,
  },
  {
    id: "economics",
    role: "Soldier:Economics",
    title: "Economics engine",
    summary: "Fee-true net, listings-needed, stress forecast. Cash is truth.",
    tools: ["netProfitPerSale", "listingsNeeded", "stressForecast"],
    inputs: ["price", "cost", "listings", "str", "target"],
    outputs: ["net", "forecast"],
    parallel: true,
    capitalGate: false,
  },
  {
    id: "evidence",
    role: "Soldier:Evidence",
    title: "Evidence officer",
    summary: "Harden a candidate with Terapeak sold + dual supplier quotes.",
    tools: ["hardenCandidate"],
    inputs: ["title", "salePrice", "soldCount", "productCost", "altProductCost"],
    outputs: ["decision", "flags", "economics"],
    parallel: false,
    capitalGate: true,
  },
  {
    id: "copy",
    role: "Soldier:Copy",
    title: "Listing copy",
    summary: "Deterministic title / bullets / specifics. Does not publish.",
    tools: ["draftListing"],
    inputs: ["title", "salePrice", "categoryId"],
    outputs: ["draft"],
    parallel: true,
    capitalGate: false,
  },
  {
    id: "factory",
    role: "Soldier:Factory",
    title: "Listing factory",
    summary: "Packages from a completed orch job — promote only via HOLD gate.",
    tools: ["assemblePackages"],
    inputs: ["orchJobId", "maxPackages"],
    outputs: ["packages", "clusters"],
    parallel: false,
    capitalGate: true,
  },
  {
    id: "fulfill",
    role: "Soldier:Fulfill",
    title: "Fulfillment gate",
    summary: "HOLD/AUTO decision. Never auto-orders without supplier confirm.",
    tools: ["fulfillDecision"],
    inputs: ["buyerTotal", "supplierCost", "supplierConfirmed"],
    outputs: ["gate"],
    parallel: false,
    capitalGate: true,
  },
  {
    id: "browser",
    role: "Soldier:Browser",
    title: "Browser operator",
    summary: "Allowlisted fetch + playbook capture. No eBay HTML search scrape.",
    tools: ["fetch", "playbook", "getItem"],
    inputs: ["url", "playbookId", "itemId"],
    outputs: ["snapshot", "capture"],
    parallel: true,
    capitalGate: false,
  },
  {
    id: "vm",
    role: "Soldier:VM",
    title: "VM operator",
    summary: "Local runtime snapshot + allowlisted recipes (tests, dry mission, env).",
    tools: ["snapshot", "recipes"],
    inputs: ["recipe"],
    outputs: ["snapshot", "run"],
    parallel: false,
    capitalGate: false,
  },
  {
    id: "swarm",
    role: "Meta:Swarm",
    title: "Research swarm",
    summary: "Scout ∥ Intel → Quality → Evidence → Copy → Brain (existing swarm).",
    tools: ["runResearchSwarm"],
    inputs: ["q", "categoryId", "minPrice", "maxPrice", "deepCrawl"],
    outputs: ["brief", "lethalBoard", "viz"],
    parallel: false,
    capitalGate: false,
  },
];

export const PLAYBOOKS = [
  {
    id: "terapeak",
    title: "Terapeak sold comps",
    caveat: "Assistive — Marketplace Insights often 403. Paste counts; do not scrape Hub HTML.",
    steps: [
      { id: "sign-in", label: "Sign in to Seller Hub → Product research (Terapeak)" },
      { id: "search", label: "Search candidate title / EPID / GTIN" },
      { id: "capture", label: "Capture avg sold $, sold count 90d, sell-through, active count" },
      { id: "verify", label: "POST capture into Evidence (soldCount + demandSource=terapeak)" },
      { id: "agree", label: "Confirm Terapeak and Browse agree directionally" },
    ],
  },
  {
    id: "supplier",
    title: "Supplier reality check",
    caveat: "Dual quotes required before PASS. No orders without HOLD_REVIEW.",
    steps: [
      { id: "open", label: "Open wholesale / CJ / private supplier page" },
      { id: "landed", label: "Record landed cost + handling days" },
      { id: "alt", label: "Get a second quote (altProductCost)" },
      { id: "paste", label: "Paste both costs into Evidence / mission form" },
    ],
  },
  {
    id: "ops-pass",
    title: "Ops after PASS",
    caveat: "CSV/Seller Hub works without Sell OAuth. Live Inventory needs user token.",
    steps: [
      { id: "promote", label: "Promote PASS row into SKU registry" },
      { id: "export", label: "Export CSV/JSON for Seller Hub" },
      { id: "photos", label: "Original photos only — do not copy competitor images" },
      { id: "ingest", label: "Order ingest → HOLD until supplier confirmed + tracking" },
    ],
  },
  {
    id: "getitem",
    title: "Official getItem page content",
    caveat: "Use Browse getItem — not HTML scrape of search results.",
    steps: [
      { id: "id", label: "Paste eBay item id or /itm/ URL" },
      { id: "fetch", label: "Playground fetches via getItem (images, specifics, description)" },
      { id: "inspect", label: "Inspect in desk — beat-this URL is reference only" },
    ],
  },
];

export const VM_RECIPES = [
  {
    id: "health",
    title: "API health",
    summary: "In-process health + auth flags (no secrets).",
    spawn: false,
    localOnly: false,
  },
  {
    id: "env",
    title: "VM snapshot",
    summary: "Node, CPU, memory, cwd, data dir, eBay env present.",
    spawn: false,
    localOnly: false,
  },
  {
    id: "node",
    title: "Node version",
    summary: "process.version + platform.",
    spawn: false,
    localOnly: false,
  },
  {
    id: "data-dir",
    title: "Data directory",
    summary: "List playground / orch / exports files (names only).",
    spawn: false,
    localOnly: false,
  },
  {
    id: "dry-mission",
    title: "Dry research mission",
    summary: "Synthetic products + spreadsheet (no eBay). Proves the worker path.",
    spawn: false,
    localOnly: false,
  },
  {
    id: "unit-tests",
    title: "Command unit tests",
    summary: "npm test in lpros-command. Local :8790 / CLI only — not Netlify.",
    spawn: true,
    localOnly: true,
  },
];

export const JOB_KINDS = ["agent", "browser", "vm", "research", "spawn"];
export const JOB_STATUSES = ["queued", "running", "hold", "done", "failed", "cancelled"];
export const PRIORITIES = ["P0", "P1", "P2"];

export const PRESETS = [
  {
    id: "live-intel",
    title: "Live product research",
    agent: "intel",
    dryRun: false,
    spawn: [],
    input: { q: "solid wood desk organizer", categoryId: "25339", minPrice: 35, maxPrice: 150, limit: 80 },
  },
  {
    id: "dry-brain",
    title: "Dry Brain swarm",
    agent: "brain",
    dryRun: true,
    spawn: ["scout", "intel", "economics"],
    input: { q: "solid wood desk organizer", categoryId: "25339", minPrice: 35, maxPrice: 150, price: 49, cost: 18 },
  },
  {
    id: "evidence-harden",
    title: "Harden evidence",
    agent: "evidence",
    dryRun: false,
    spawn: [],
    input: {
      title: "Solid wood desk organizer oak",
      salePrice: 49,
      soldCount: 28,
      productCost: 18,
      altProductCost: 19.5,
      leadTimeDays: 7,
    },
  },
  {
    id: "copy-draft",
    title: "Draft listing copy",
    agent: "copy",
    dryRun: false,
    spawn: [],
    input: { title: "Walnut desk organizer upgrade", salePrice: 59 },
  },
  {
    id: "vm-health",
    title: "VM health",
    agent: "vm",
    dryRun: false,
    spawn: [],
    input: { recipe: "health" },
  },
  {
    id: "browser-terapeak",
    title: "Terapeak playbook",
    agent: "browser",
    dryRun: false,
    spawn: [],
    input: { playbookId: "terapeak" },
  },
];

export function getAgent(id) {
  return AGENT_CATALOG.find((a) => a.id === id) || null;
}

export function getPlaybook(id) {
  return PLAYBOOKS.find((p) => p.id === id) || null;
}

export function getRecipe(id) {
  return VM_RECIPES.find((r) => r.id === id) || null;
}

export function getPreset(id) {
  return PRESETS.find((p) => p.id === id) || null;
}
