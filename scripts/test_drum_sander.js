#!/usr/bin/env node
/** Smoke test: DS-18 shop app is visible, routed, and complete. */
const fs = require("fs");
const path = require("path");

const root = path.resolve(__dirname, "..");
const app = path.join(root, "shop/drum-sander/app");
let failed = 0;

function ok(cond, msg) {
  if (!cond) {
    console.error("FAIL", msg);
    failed++;
  } else {
    console.log("ok  ", msg);
  }
}

const html = fs.readFileSync(path.join(app, "index.html"), "utf8");
ok(html.includes('data-panel="overview"'), "overview panel exists");
ok(/<section class="panel on"[^>]*data-panel="overview"/.test(html), "overview visible without JS");
ok(html.includes('id="overview"'), "overview has id for #overview");
ok(html.includes("<noscript>"), "noscript reveals panels");
ok(html.includes("type=\"importmap\""), "Three.js import map");
ok(html.includes("three@0.160"), "pins Three.js r160");
ok(html.includes('src="data.js"'), "data.js script");
ok(html.includes('src="app.js"'), "app.js module");
ok(html.includes("Build the DS-18"), "overview heading in static HTML");
ok(html.includes("18″ × 6″ OD"), "stats visible without JS");
ok(html.includes("1.5 HP"), "motor spec in HTML");
ok(html.includes("id=\"vizStage\""), "viz stage");
ok(html.includes("id=\"cutBody\""), "cut list table");
ok(html.includes("id=\"shopBody\""), "shopping table");
ok(html.includes("Baltic birch"), "cut list content in HTML");
ok(html.includes("pillow-block"), "shopping content in HTML");
ok(html.includes("DS1_general.svg"), "plan links");

const css = fs.readFileSync(path.join(app, "styles.css"), "utf8");
ok(css.includes(".panel{display:none"), "panels hidden by default");
ok(css.includes(".panel.on{display:block}"), "active panel shown");

const js = fs.readFileSync(path.join(app, "app.js"), "utf8");
ok(js.includes("location.hash"), "hash routing");
ok(js.includes("#overview"), "overview hash");
ok(js.includes("mountScene"), "loads Three.js scene");
ok(js.includes("drawFallbackSvg"), "SVG fallback");
ok(js.includes("localStorage"), "persists checklists");

const scene = fs.readFileSync(path.join(app, "scene.js"), "utf8");
ok(scene.includes('import("three")'), "dynamic import of three");
ok(scene.includes("OrbitControls"), "orbit controls");
ok(scene.includes("setExplode"), "explode API");
ok(scene.includes("drumG"), "drum group for spin");
ok(scene.includes("drawFallbackSvg"), "exports SVG fallback");

const data = fs.readFileSync(path.join(app, "data.js"), "utf8");
ok(data.includes("window.DS_DATA"), "DS_DATA global");
ok(data.includes("assembly"), "assembly steps");
ok(data.includes("cutlist"), "cut list data");
ok(data.includes("shopping"), "shopping data");
const vm = require("vm");
const ctx = { window: {} };
vm.runInNewContext(data, ctx);
const DS = ctx.window.DS_DATA;
ok(DS.assembly.length === 12, "12 assembly steps");
ok(DS.cutlist.length >= 12, "cut list line items");
const shopSum = DS.shopping.reduce((a, s) => a + s.est, 0);
ok(shopSum === 766, "shopping total $766 (got " + shopSum + ")");
ok(DS.meta.drumLen === 18 && DS.meta.drumOd === 6, "drum 18×6");

const toml = fs.readFileSync(path.join(root, "netlify.toml"), "utf8");
ok(toml.includes("/shop/drum-sander/app"), "netlify redirect for app");
ok(toml.includes("/shop/drum-sander/app/plans/*"), "SVG content-type for plans");

const required = [
  "shop/index.html",
  "shop/drum-sander/index.html",
  "shop/drum-sander/cad/drum_sander.scad",
  "shop/drum-sander/app/index.html",
  "shop/drum-sander/app/plans/DS1_general.svg",
  "shop/drum-sander/app/plans/DS2_plywood.svg",
  "shop/drum-sander/app/plans/DS3_drum.svg",
  "shop/drum-sander/app/plans/DS4_table.svg",
  "shop/drum-sander/app/plans/DS5_drive.svg",
  "shop/drum-sander/app/plans/DS6_cutlist.svg",
  "shop/drum-sander/app/manifest.json",
  "shop/drum-sander/app/icon.svg",
  "shop/drum-sander/app/service-worker.js",
];
for (const f of required) {
  ok(fs.existsSync(path.join(root, f)), f);
}

if (failed) {
  console.error("\n" + failed + " failure(s)");
  process.exit(1);
}
console.log("\nall smoke checks passed");
