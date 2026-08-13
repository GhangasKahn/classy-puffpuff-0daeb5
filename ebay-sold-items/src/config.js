import { readFileSync, existsSync } from "node:fs";
import { resolve, dirname } from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const root = resolve(__dirname, "..");

const ENV_FILES = [
  resolve(root, ".env"),
  resolve(root, ".env.local"),
  resolve(root, "../lpros-command/.env"),
  resolve(root, "../.env"),
];

function missing(val) {
  return val == null || val === "";
}

/** Minimal .env loader. Fills unset/empty keys; does not override real values. */
export function loadEnv(file) {
  const files = file ? [file] : ENV_FILES;
  for (const f of files) applyEnvFile(f);
}

export function applyEnvFile(file) {
  if (!file || !existsSync(file)) return false;
  const text = readFileSync(file, "utf8");
  for (const line of text.split(/\r?\n/)) {
    const trimmed = line.trim();
    if (!trimmed || trimmed.startsWith("#")) continue;
    const eq = trimmed.indexOf("=");
    if (eq < 1) continue;
    const key = trimmed.slice(0, eq).trim();
    let val = trimmed.slice(eq + 1).trim();
    if (
      (val.startsWith('"') && val.endsWith('"')) ||
      (val.startsWith("'") && val.endsWith("'"))
    ) {
      val = val.slice(1, -1);
    }
    if (missing(process.env[key])) process.env[key] = val;
  }
  return true;
}

loadEnv();

export function readConfig() {
  const envName = (process.env.EBAY_ENV || "sandbox").toLowerCase();
  const isProd = envName === "production" || envName === "prod" || envName === "prd";
  const appId = isProd
    ? process.env.EBAY_PRD_APP_ID || process.env.EBAY_APP_ID
    : process.env.EBAY_SBX_APP_ID || process.env.EBAY_APP_ID;
  const certId = isProd
    ? process.env.EBAY_PRD_CERT_ID || process.env.EBAY_CERT_ID
    : process.env.EBAY_SBX_CERT_ID || process.env.EBAY_CERT_ID;
  const devId = isProd
    ? process.env.EBAY_PRD_DEV_ID || process.env.EBAY_DEV_ID
    : process.env.EBAY_SBX_DEV_ID || process.env.EBAY_DEV_ID;
  return {
    env: isProd ? "production" : "sandbox",
    appId: appId || "",
    certId: certId || "",
    devId: devId || "",
    marketplaceId: process.env.EBAY_MARKETPLACE_ID || "EBAY_US",
    port: Number(process.env.PORT || 8787),
    host: process.env.HOST || "127.0.0.1",
    corsOrigins: (process.env.CORS_ORIGINS || "*").split(",").map((s) => s.trim()),
    apiRoot: isProd ? "https://api.ebay.com" : "https://api.sandbox.ebay.com",
    scope: "https://api.ebay.com/oauth/api_scope",
  };
}

/** Live view of env — Netlify/process env wins; .env fills gaps. */
export const config = new Proxy(
  {},
  {
    get(_t, prop) {
      if (prop === "then") return undefined;
      return readConfig()[prop];
    },
    ownKeys() {
      return Reflect.ownKeys(readConfig());
    },
    getOwnPropertyDescriptor(_t, prop) {
      const cur = readConfig();
      if (!Object.hasOwn(cur, prop)) return undefined;
      return { configurable: true, enumerable: true, value: cur[prop] };
    },
  }
);

export function assertEbayConfigured() {
  if (!config.appId || !config.certId) {
    const err = new Error(
      "eBay credentials missing. Set EBAY_PRD_APP_ID + EBAY_PRD_CERT_ID and EBAY_ENV=production on this host (Netlify site env, or ebay-sold-items/.env for local :8790)."
    );
    err.code = "EBAY_CONFIG";
    throw err;
  }
}
