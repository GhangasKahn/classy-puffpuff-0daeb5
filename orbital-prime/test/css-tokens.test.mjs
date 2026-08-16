import { describe, it } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

const root = dirname(fileURLToPath(import.meta.url));
const css = readFileSync(join(root, "../styles/orbital.css"), "utf8");
const html = readFileSync(join(root, "../index.html"), "utf8");
const sw = readFileSync(join(root, "../service-worker.js"), "utf8");

describe("motion tokens actually exist in CSS", () => {
  it("defines easing and duration tokens from MOTION_AND_COMPOSITION", () => {
    assert.match(css, /--ease-settle:\s*cubic-bezier\(0\.16,\s*1,\s*0\.3,\s*1\)/);
    assert.match(css, /--ease-track:\s*cubic-bezier\(0\.4,\s*0,\s*0\.2,\s*1\)/);
    assert.match(css, /--dur-xs:\s*80ms/);
    assert.match(css, /--dur-sm:\s*160ms/);
    assert.match(css, /--dur-md:\s*280ms/);
    assert.match(css, /--dur-lg:\s*480ms/);
  });

  it("implements the classes JS toggles", () => {
    assert.match(css, /\.is-pending\s*\{/);
    assert.match(css, /\.is-in\s*\{/);
    assert.match(css, /\.is-settle\s*\{/);
    assert.match(css, /@keyframes op-settle/);
    assert.match(css, /@keyframes op-in/);
  });
});

describe("contrast and focus", () => {
  it("does not set module numbers as orange-on-paper text", () => {
    assert.doesNotMatch(css, /\.mod-n\s*\{[^}]*color:\s*var\(--orange\)/);
    assert.match(css, /\.mod-n\s*\{[^}]*background:\s*var\(--yellow\)/);
  });

  it("uses focus-visible instead of outline none on inputs", () => {
    assert.match(css, /:focus-visible/);
    assert.doesNotMatch(css, /\.field input \{[^}]*outline:\s*none/);
  });

  it("paints small status as ink-on-chip, not orange/green text", () => {
    assert.match(css, /\.feeds li\[data-status="live"\] \.feed-st \{ background: var\(--yellow\)/);
    assert.doesNotMatch(css, /\.feeds li\[data-status="live"\] \.feed-st \{ color: var\(--ok\)/);
    assert.doesNotMatch(css, /#hourly-list li\[data-class="perfect"\] b \{ color: var\(--ok\)/);
    assert.match(css, /#residual\[data-grade="lock"\] \{ background: var\(--yellow\)/);
  });

  it("self-hosts catalog faces and does not load Google Fonts", () => {
    assert.match(css, /url\("\.\.\/fonts\/archivo-black-latin-400\.woff2"\)/);
    assert.match(css, /url\("\.\.\/fonts\/inter-latin-400\.woff2"\)/);
    assert.match(css, /url\("\.\.\/fonts\/space-mono-latin-400\.woff2"\)/);
    assert.doesNotMatch(html, /fonts\.googleapis\.com/);
    assert.doesNotMatch(html, /fonts\.gstatic\.com/);
  });
});

describe("hardware unit wiring", () => {
  it("ships a hero unit stage with GL and 2D canvases", () => {
    assert.match(html, /id="unit-stage"/);
    assert.match(html, /id="unit-gl"/);
    assert.match(html, /id="unit-2d"/);
    assert.match(sw, /js\/gl\/unit\.js/);
    assert.match(sw, /orbital-prime-v9/);
    assert.match(sw, /js\/pass-worker\.js/);
    assert.match(sw, /js\/sat-boot\.js/);
    assert.match(sw, /network-first|isVolatile/);
    assert.match(html, /orbital\.css\?v=9/);
    assert.match(html, /main\.js\?v=9/);
    assert.doesNotMatch(html, /user-scalable=no/);
    assert.doesNotMatch(html, /maximum-scale=1/);
    assert.match(html, /og\.svg/);
    assert.match(css, /@media print/);
  });
});
