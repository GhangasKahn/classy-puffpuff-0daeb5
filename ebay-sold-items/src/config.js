import { readFileSync, existsSync } from "node:fs";
import { resolve, dirname } from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const root = resolve(__dirname, "..");

/** Minimal .env loader (no dependency). Does not override existing process.env. */
export function loadEnv(file = resolve(root, ".env")) {
  if (!existsSync(file)) return;
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
    if (process.env[key] === undefined) process.env[key] = val;
  }
}

loadEnv();

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

export const config = {
  env: isProd ? "production" : "sandbox",
  appId: appId || "",
  certId: certId || "",
  devId: devId || "",
  marketplaceId: process.env.EBAY_MARKETPLACE_ID || "EBAY_US",
  port: Number(process.env.PORT || 8787),
  host: process.env.HOST || "127.0.0.1",
  corsOrigins: (process.env.CORS_ORIGINS || "*").split(",").map((s) => s.trim()),
  apiRoot: isProd ? "https://api.ebay.com" : "https://api.sandbox.ebay.com",
  /** Application token scope for Browse (+ Insights when entitled). */
  scope: "https://api.ebay.com/oauth/api_scope",
};

export function assertEbayConfigured() {
  if (!config.appId || !config.certId) {
    const err = new Error(
      "eBay credentials missing. Copy ebay-sold-items/.env.example → .env and fill App ID + Cert ID."
    );
    err.code = "EBAY_CONFIG";
    throw err;
  }
}
