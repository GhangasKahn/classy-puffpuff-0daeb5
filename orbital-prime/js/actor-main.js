#!/usr/bin/env node
/* OP-01 observe entry.
   On Apify: Actor input → dataset of passes + OUTPUT record.
   Standalone: node js/actor-main.js --lat=42.8864 --lon=-78.8784
   Never invents telemetry. */

import { observe } from "./observe.js";

function fromArgv(argv) {
  const out = {};
  for (const a of argv.slice(2)) {
    const m = /^--([^=]+)=(.*)$/.exec(a);
    if (m) out[m[1]] = m[2];
  }
  return out;
}

function mergeInput(primary = {}, fallback = {}) {
  return {
    lat: primary.lat ?? fallback.lat,
    lon: primary.lon ?? fallback.lon,
    sat: primary.sat ?? fallback.sat,
    hours: primary.hours ?? fallback.hours,
    altKm: primary.altKm ?? fallback.altKm
  };
}

async function main() {
  const argvInput = fromArgv(process.argv);
  const envInput = {
    lat: process.env.OP_LAT,
    lon: process.env.OP_LON,
    sat: process.env.OP_SAT,
    hours: process.env.OP_HOURS,
    altKm: process.env.OP_ALT_KM
  };
  const onApify = Boolean(process.env.APIFY_IS_AT_HOME || process.env.APIFY_LOCAL_STORAGE_DIR);

  if (onApify) {
    const { Actor } = await import("apify");
    await Actor.init();
    const input = mergeInput((await Actor.getInput()) || {}, mergeInput(argvInput, envInput));
    const result = await observe(input);
    if (Array.isArray(result.passes) && result.passes.length) {
      await Actor.pushData(result.passes);
    }
    await Actor.setValue("OUTPUT", result);
    if (!result.ok) {
      await Actor.fail(result.error || "observe failed");
      return;
    }
    await Actor.exit();
    return;
  }

  const input = mergeInput(argvInput, {
    lat: envInput.lat ?? 42.8864,
    lon: envInput.lon ?? -78.8784,
    sat: envInput.sat ?? "25544",
    hours: envInput.hours ?? 36,
    altKm: envInput.altKm
  });
  const result = await observe(input);
  process.stdout.write(`${JSON.stringify(result, null, 2)}\n`);
  if (!result.ok) process.exitCode = 1;
}

main().catch((e) => {
  console.error(e?.message || e);
  process.exitCode = 1;
});
