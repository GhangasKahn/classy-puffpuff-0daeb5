/**
 * Browser operator — allowlisted fetch + playbook sessions + official getItem.
 * Never scrapes eBay search HTML. Private/link-local hosts are blocked (SSRF).
 */
import { getPlaybook } from "./catalog.js";
import { listKind, load, nid, persist } from "./store.js";

const FETCH_TIMEOUT_MS = 8000;
const MAX_BYTES = 400_000;

export const ALLOWED_HOSTS = new Set([
  "example.com",
  "www.example.com",
  "developer.ebay.com",
  "apidocs.ebay.com",
  "github.com",
  "raw.githubusercontent.com",
  "en.wikipedia.org",
  "www.wikipedia.org",
]);

const BLOCKED_HOST_RE =
  /^(localhost|127\.|10\.|0\.|169\.254\.|192\.168\.|172\.(1[6-9]|2\d|3[0-1])\.|\[::1\]|::1)/i;

export function hostnameAllowed(hostname) {
  const h = String(hostname || "")
    .toLowerCase()
    .replace(/\.$/, "");
  if (!h) return false;
  if (BLOCKED_HOST_RE.test(h)) return false;
  if (ALLOWED_HOSTS.has(h)) return true;
  if (h === "www.ebay.com" || h === "ebay.com") return "ebay-item-only";
  return false;
}

export function parseItemId(urlOrId) {
  const s = String(urlOrId || "").trim();
  if (/^\d{8,19}$/.test(s)) return s;
  try {
    const u = new URL(s);
    const m = u.pathname.match(/\/itm\/(?:[^/]+\/)?(\d{8,19})/);
    if (m) return m[1];
    const q = u.searchParams.get("item") || u.searchParams.get("itm");
    if (q && /^\d{8,19}$/.test(q)) return q;
  } catch {
    /* ignore */
  }
  return null;
}

function assertSafeUrl(raw) {
  let u;
  try {
    u = new URL(String(raw));
  } catch {
    throw Object.assign(new Error("invalid url"), { status: 400 });
  }
  if (u.protocol !== "https:") {
    throw Object.assign(new Error("https only"), { status: 400 });
  }
  if (BLOCKED_HOST_RE.test(u.hostname)) {
    throw Object.assign(new Error("private host blocked"), { status: 403 });
  }
  const allow = hostnameAllowed(u.hostname);
  if (!allow) {
    throw Object.assign(new Error(`host not allowlisted: ${u.hostname}`), { status: 403 });
  }
  return { url: u, allow };
}

function extractPreview(html, url) {
  const text = String(html || "")
    .replace(/<script[\s\S]*?<\/script>/gi, " ")
    .replace(/<style[\s\S]*?<\/style>/gi, " ")
    .replace(/<[^>]+>/g, " ")
    .replace(/\s+/g, " ")
    .trim();
  const title =
    String(html || "")
      .match(/<title[^>]*>([\s\S]*?)<\/title>/i)?.[1]
      ?.replace(/\s+/g, " ")
      .trim() || url;
  return { title: title.slice(0, 180), excerpt: text.slice(0, 1200), chars: text.length };
}

export function listSessions(limit = 40) {
  return listKind("browser", limit);
}

export function createSession({ playbookId = "terapeak", url = "", note = "" } = {}) {
  const pb = getPlaybook(playbookId) || getPlaybook("terapeak");
  const session = {
    id: nid("br"),
    playbookId: pb.id,
    url: url || null,
    note: note || "",
    stepIndex: 0,
    steps: pb.steps.map((s) => ({ ...s, done: false, capture: null })),
    snapshots: [],
    captures: [],
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
  };
  persist("browser", session);
  return session;
}

export function getSession(id) {
  return load("browser", id);
}

export function advanceSession(id, { capture } = {}) {
  const session = load("browser", id);
  if (!session) return null;
  const step = session.steps[session.stepIndex];
  if (step) {
    step.done = true;
    if (capture) step.capture = capture;
  }
  session.stepIndex = Math.min(session.stepIndex + 1, session.steps.length);
  session.updatedAt = new Date().toISOString();
  persist("browser", session);
  return session;
}

export function addCapture(id, capture) {
  const session = load("browser", id);
  if (!session) return null;
  const row = { at: new Date().toISOString(), ...capture };
  session.captures.push(row);
  session.updatedAt = row.at;
  persist("browser", session);
  return session;
}

export async function fetchAllowed(rawUrl) {
  const { url, allow } = assertSafeUrl(rawUrl);
  if (allow === "ebay-item-only") {
    const itemId = parseItemId(url.href);
    if (!itemId) {
      throw Object.assign(
        new Error("eBay HTML search is blocked — paste an /itm/ URL or item id (getItem)"),
        { status: 403 }
      );
    }
    const { getBrowseItem } = await import("../../../ebay-sold-items/src/ebay/browse.js");
    const item = await getBrowseItem(itemId);
    return {
      mode: "getitem",
      url: url.href,
      itemId,
      title: item?.title,
      price: item?.price,
      image: item?.image,
      images: item?.images,
      descriptionExcerpt: (item?.description || item?.shortDescription || "").slice(0, 800),
      itemSpecifics: item?.localizedAspects || item?.itemSpecifics,
      listingUrl: item?.itemWebUrl || url.href,
      caveat: "Official Browse getItem — not HTML scrape",
    };
  }

  const ac = new AbortController();
  const t = setTimeout(() => ac.abort(), FETCH_TIMEOUT_MS);
  try {
    const res = await fetch(url.href, {
      signal: ac.signal,
      redirect: "follow",
      headers: { "User-Agent": "LPROS-Playground/1.0 (allowlisted research fetch)" },
    });
    const buf = Buffer.from(await res.arrayBuffer());
    const sliced = buf.subarray(0, MAX_BYTES);
    const ctype = res.headers.get("content-type") || "";
    const body = sliced.toString("utf8");
    const preview =
      ctype.includes("html") || body.includes("<html")
        ? extractPreview(body, url.href)
        : { title: url.href, excerpt: body.slice(0, 1200), chars: body.length };
    return {
      mode: "fetch",
      url: url.href,
      status: res.status,
      contentType: ctype,
      truncated: buf.length > MAX_BYTES,
      ...preview,
    };
  } finally {
    clearTimeout(t);
  }
}

export async function runBrowserJob(input = {}) {
  if (input.sessionId && input.action === "advance") {
    return { session: advanceSession(input.sessionId, { capture: input.capture }) };
  }
  if (input.playbookId && !input.url && !input.itemId) {
    const session = createSession({ playbookId: input.playbookId, note: input.note });
    return { session, playbook: getPlaybook(session.playbookId) };
  }
  const target = input.url || input.itemId;
  if (!target) {
    const session = createSession({ playbookId: input.playbookId || "terapeak" });
    return { session, playbook: getPlaybook(session.playbookId) };
  }
  const snapshot = await fetchAllowed(input.url || `https://www.ebay.com/itm/${input.itemId}`);
  let session = null;
  if (input.sessionId) {
    session = load("browser", input.sessionId);
    if (session) {
      session.snapshots.push({ at: new Date().toISOString(), ...snapshot });
      session.url = snapshot.url || session.url;
      session.updatedAt = new Date().toISOString();
      persist("browser", session);
    }
  }
  return { snapshot, session };
}
