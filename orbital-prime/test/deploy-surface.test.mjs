import { describe, it } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { createRequire } from "node:module";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const root = join(here, "../..");
const require = createRequire(import.meta.url);
const feed = require(join(root, "netlify/functions/op-feed.js"));
const html = readFileSync(join(here, "../index.html"), "utf8");
const toml = readFileSync(join(root, "netlify.toml"), "utf8");

const REQUIRED_IDS = [
  "loc-form", "lat", "lon", "loc-status", "btn-gps", "btn-buf", "btn-audio",
  "btn-ar", "btn-share", "btn-ics", "btn-speak", "btn-alert", "sat-select",
  "gate", "gate-word", "gate-why", "next-pass", "next-when", "next-meta",
  "best-window", "tminus", "scrub-fill", "scrub-a", "scrub-l", "face",
  "az", "el", "range", "mag", "lock-src", "residual", "gauge-az", "gauge-el",
  "sky-plot", "compass", "compass-read", "kp", "hourly-list", "pass-body",
  "manifest-body", "radar-img", "radar-empty", "radar-cap", "radar-well",
  "ground-track", "ar-video", "ar-hud", "clock", "depth-toast",
  "unit-stage", "unit-gl", "unit-2d", "feeds"
];

describe("op-feed allowlist", () => {
  it("rejects unknown src (not an open proxy)", () => {
    assert.equal(feed.resolve("https://evil.example", {}).error, "unknown src");
    assert.equal(feed.resolve("iss-not", {}).error, "unknown src");
  });

  it("allows only the public connectors", () => {
    assert.match(feed.resolve("iss", {}).url, /wheretheiss\.at/);
    assert.match(feed.resolve("kp", {}).url, /swpc\.noaa\.gov/);
    assert.match(feed.resolve("stations", {}).url, /GROUP=stations/);
    assert.match(feed.resolve("tle", { catnr: "25544" }).url, /CATNR=25544/);
    assert.equal(feed.resolve("tle", { catnr: "nope" }).error, "bad catnr");
  });

  it("answers OPTIONS without hitting upstream", async () => {
    const res = await feed.handler({ httpMethod: "OPTIONS", queryStringParameters: { src: "iss" } });
    assert.equal(res.statusCode, 204);
  });

  it("rejects POST", async () => {
    const res = await feed.handler({ httpMethod: "POST", queryStringParameters: { src: "iss" } });
    assert.equal(res.statusCode, 405);
  });
});

describe("Netlify publish surface", () => {
  it("sends /orbital to /orbital-prime/", () => {
    assert.match(toml, /from = "\/orbital"/);
    assert.match(toml, /to = "\/orbital-prime\/"/);
    assert.match(toml, /from = "\/orbital-prime\/api\/feed"/);
    assert.match(toml, /to = "\/\.netlify\/functions\/op-feed"/);
  });

  it("does not cache the instrument HTML", () => {
    assert.match(toml, /\/orbital-prime\/index\.html/);
    assert.match(toml, /Cache-Control = "no-cache"/);
  });
});

describe("service worker deploy strategy", () => {
  const sw = readFileSync(join(here, "../service-worker.js"), "utf8");

  it("is network-first for navigations and scripts so deploys reach returning visitors", () => {
    assert.match(sw, /orbital-prime-v9/);
    assert.match(sw, /request\.mode === "navigate"/);
    assert.match(sw, /function isVolatile/);
    assert.match(sw, /LIVE_HOSTS/);
    assert.match(sw, /\/\.netlify\/functions\//);
  });
});

describe("HTML id contract", () => {
  it("keeps every id the instrument JS paints", () => {
    for (const id of REQUIRED_IDS) {
      assert.ok(html.includes(`id="${id}"`), `missing #${id}`);
    }
  });
});
