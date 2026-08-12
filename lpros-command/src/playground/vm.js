/**
 * VM operator — runtime snapshot + allowlisted recipes.
 * No arbitrary shell. Spawn recipes are local-only (not Netlify).
 */
import { execFile } from "node:child_process";
import { cpus, freemem, hostname, loadavg, platform, release, totalmem, uptime } from "node:os";
import { existsSync, readdirSync } from "node:fs";
import { resolve, dirname } from "node:path";
import { fileURLToPath } from "node:url";
import { promisify } from "node:util";
import { dataPath, ensureDataDir } from "../ops/store.js";
import { authStatus } from "../ebay/userToken.js";
import { getRecipe } from "./catalog.js";
import { nid, persist } from "./store.js";

const execFileP = promisify(execFile);
const here = dirname(fileURLToPath(import.meta.url));
const commandRoot = resolve(here, "../..");

export function isServerless() {
  return Boolean(process.env.NETLIFY || process.env.AWS_LAMBDA_FUNCTION_NAME);
}

export function vmSnapshot() {
  const memTotal = totalmem();
  const memFree = freemem();
  return {
    hostname: hostname(),
    platform: platform(),
    release: release(),
    arch: process.arch,
    node: process.version,
    pid: process.pid,
    cwd: process.cwd(),
    uptimeSec: Math.round(uptime()),
    loadavg: loadavg(),
    cpus: cpus().length,
    memory: {
      totalMb: Math.round(memTotal / 1048576),
      freeMb: Math.round(memFree / 1048576),
      usedPct: Math.round((1 - memFree / memTotal) * 100),
    },
    serverless: isServerless(),
    dataDir: dataPath(),
    ebayEnvSet: Boolean(process.env.EBAY_ENV),
    ebayAppIdSet: Boolean(process.env.EBAY_PRD_APP_ID || process.env.EBAY_APP_ID),
    auth: authStatus(),
    note: isServerless()
      ? "Netlify function — spawn recipes disabled; long marathons need local :8790"
      : "Local VM worker — recipes may spawn npm test / dry mission",
  };
}

function listDirNames(rel) {
  const dir = dataPath(rel);
  if (!existsSync(dir)) return [];
  return readdirSync(dir).slice(0, 40);
}

async function runSpawn(cmd, args, cwd, timeoutMs = 45000) {
  if (isServerless()) {
    throw Object.assign(new Error("spawn recipes are local-only (not Netlify)"), { status: 409 });
  }
  const { stdout, stderr } = await execFileP(cmd, args, {
    cwd,
    timeout: timeoutMs,
    maxBuffer: 800_000,
    env: { ...process.env, FORCE_COLOR: "0" },
  });
  return {
    stdout: String(stdout || "").slice(0, 8000),
    stderr: String(stderr || "").slice(0, 2000),
  };
}

export async function runRecipe(recipeId, extra = {}) {
  const recipe = getRecipe(recipeId);
  if (!recipe) throw Object.assign(new Error(`unknown recipe: ${recipeId}`), { status: 400 });
  if (recipe.localOnly && isServerless()) {
    throw Object.assign(new Error(`${recipe.id} is local-only — run on :8790`), { status: 409 });
  }

  const started = Date.now();
  let result;
  switch (recipe.id) {
    case "health":
      result = {
        ok: true,
        service: "lpros-command",
        auth: authStatus(),
        serverless: isServerless(),
      };
      break;
    case "env":
    case "node":
      result = vmSnapshot();
      break;
    case "data-dir":
      ensureDataDir("playground");
      result = {
        dataDir: dataPath(),
        playground: listDirNames("playground"),
        orch: listDirNames("orch"),
        exports: listDirNames("exports"),
      };
      break;
    case "dry-mission": {
      const { deployMission } = await import("../orchestrate/runner.js");
      const job = await deployMission(
        {
          q: extra.q || "desk organizer",
          categoryId: extra.categoryId || "25339",
          dryRun: true,
          variantCount: 40,
          sheetRows: 20,
        },
        { sync: true }
      );
      result = {
        orchJobId: job.id,
        status: job.status,
        productCount: job.results?.productCount,
        variantCount: job.results?.variants?.length,
      };
      break;
    }
    case "unit-tests":
      result = await runSpawn("npm", ["test"], commandRoot, 60000);
      break;
    default:
      throw Object.assign(new Error(`recipe not implemented: ${recipe.id}`), { status: 400 });
  }

  const run = {
    id: nid("vm"),
    recipe: recipe.id,
    title: recipe.title,
    status: "done",
    ms: Date.now() - started,
    result,
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
  };
  persist("vm", run);
  return run;
}

export async function runVmJob(input = {}) {
  if (!input.recipe || input.recipe === "env") {
    const snap = vmSnapshot();
    if (!input.recipe) return { snapshot: snap };
    const run = await runRecipe("env", input);
    return { snapshot: snap, run };
  }
  const run = await runRecipe(input.recipe, input);
  return { snapshot: vmSnapshot(), run };
}
