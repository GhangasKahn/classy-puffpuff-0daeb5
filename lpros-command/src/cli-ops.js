#!/usr/bin/env node
/**
 * Real-world ops CLI: promote → export → dry-run publish → ingest order
 */
import { pathToFileURL } from "node:url";
import { resolve, dirname } from "node:path";
import { fileURLToPath } from "node:url";
import { promoteCandidate, listSkus } from "./ops/skus.js";
import { exportPackages, exportSku } from "./ops/packages.js";
import { ingestOrder, listOrders, attachTracking } from "./ops/orders.js";
import { dryRunPublish, publishSku } from "./ebay/inventory.js";
import { dryRunTrackingPush } from "./ebay/fulfillment.js";
import { authStatus } from "./ebay/userToken.js";

const root = resolve(dirname(fileURLToPath(import.meta.url)), "../..");
await import(pathToFileURL(resolve(root, "ebay-sold-items/src/config.js")).href);

const [cmd, ...rest] = process.argv.slice(2);
const args = Object.fromEntries(
  rest.flatMap((a, i, arr) => {
    if (!a.startsWith("--")) return [];
    const k = a.slice(2);
    const v = arr[i + 1] && !arr[i + 1].startsWith("--") ? arr[i + 1] : true;
    return [[k, v]];
  })
);

function out(x) {
  console.log(JSON.stringify(x, null, 2));
}

switch (cmd) {
  case "auth":
    out(authStatus());
    break;
  case "skus":
    out(listSkus({ status: args.status }));
    break;
  case "promote":
    out(
      promoteCandidate(
        {
          title: args.title || "Solid oak desk organizer upgrade",
          salePrice: Number(args.price || 49),
          url: args.url,
          perceivedValue: Number(args.pv || 0.55),
          decision: "PASS",
        },
        {
          evidence: {
            soldCount: Number(args.sold || 20),
            productCost: Number(args.cost || 18),
            altProductCost: Number(args["alt-cost"] || 19),
            leadTimeDays: Number(args.lead || 7),
          },
          categoryId: args["category-id"] || "25339",
          requireHarden: true,
          quantity: Number(args.qty || 3),
        }
      )
    );
    break;
  case "export":
    out(exportPackages({ status: args.status || "ready", format: args.format || "both" }));
    break;
  case "package":
    out(exportSku(args.sku));
    break;
  case "publish":
    out(await publishSku(args.sku, { live: Boolean(args.live) }));
    break;
  case "dry-run":
    out(dryRunPublish(args.sku));
    break;
  case "orders":
    out(listOrders({ status: args.status }));
    break;
  case "ingest":
    out(
      ingestOrder({
        orderId: args.id,
        sku: args.sku,
        buyerTotal: Number(args.total || args.price || 49),
        supplierCost: args.cost != null ? Number(args.cost) : undefined,
        supplierConfirmed: Boolean(args.confirmed),
        supplierLeadDays: Number(args.lead || 7),
        title: args.title,
      })
    );
    break;
  case "tracking":
    out(
      attachTracking(args.id, {
        trackingNumber: args.tracking,
        carrier: args.carrier || "USPS",
      })
    );
    break;
  case "push-tracking":
    out(dryRunTrackingPush(args.id));
    break;
  default:
    console.log(`Usage:
  node src/cli-ops.js auth
  node src/cli-ops.js promote --title "..." --price 49 --sold 28 --cost 18 --alt-cost 19
  node src/cli-ops.js skus [--status ready]
  node src/cli-ops.js export [--status ready]
  node src/cli-ops.js dry-run --sku SKU
  node src/cli-ops.js publish --sku SKU [--live]
  node src/cli-ops.js ingest --sku SKU --total 49 [--cost 18] [--confirmed]
  node src/cli-ops.js tracking --id ORDER --tracking 9400... --carrier USPS
  node src/cli-ops.js orders`);
    process.exit(cmd ? 1 : 0);
}
