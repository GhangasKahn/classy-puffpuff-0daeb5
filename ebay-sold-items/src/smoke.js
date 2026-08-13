/**
 * Optional live smoke against Sandbox/Production.
 * Requires ebay-sold-items/.env with real App ID + Cert ID.
 * Usage: npm run smoke
 */
import { config } from "./config.js";
import { getAppToken } from "./ebay/client.js";
import { buildAltComps } from "./ebay/comps.js";

async function main() {
  console.log("env=", config.env, "apiRoot=", config.apiRoot);
  if (!config.appId || !config.certId) {
    console.error("Missing credentials — copy .env.example to .env");
    process.exit(1);
  }
  const token = await getAppToken();
  console.log("OAuth OK, token length=", token.length);

  const comps = await buildAltComps({
    category: "Watch",
    ref: "Rolex",
    limit: 5,
  });
  console.log(
    JSON.stringify(
      {
        evidenceStatus: comps.evidenceStatus,
        listingsNeeded: comps.listingsNeeded,
        suggestedValue: comps.suggestedValue,
        soldCount: comps.soldCount,
        activeCount: comps.activeCount,
        note: comps.note,
        sample: comps.comps.slice(0, 2),
        errors: comps.errors,
      },
      null,
      2
    )
  );
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
