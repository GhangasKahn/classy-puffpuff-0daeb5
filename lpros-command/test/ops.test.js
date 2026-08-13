import assert from "node:assert/strict";
import { describe, it } from "node:test";
import { promoteCandidate, listSkus, removeSku } from "../src/ops/skus.js";
import { exportPackages, buildListingPackage } from "../src/ops/packages.js";
import { ingestOrder, attachTracking, trackingPushPayload } from "../src/ops/orders.js";
import { dryRunPublish } from "../src/ebay/inventory.js";
import { authStatus } from "../src/ebay/userToken.js";

describe("real-world ops loop", () => {
  it("promotes → exports → dry-run publish → ingest order HOLD", () => {
    const row = promoteCandidate(
      {
        title: "Solid oak desk organizer clutter tray upgrade",
        salePrice: 49,
        url: "https://www.ebay.com/itm/123",
        perceivedValue: 0.55,
      },
      {
        evidence: {
          soldCount: 22,
          productCost: 17,
          altProductCost: 18,
          leadTimeDays: 6,
          demandSource: "terapeak",
        },
        categoryId: "25339",
        requireHarden: true,
        quantity: 2,
        sku: "LPROS-TEST-OAK-49",
      }
    );
    assert.equal(row.decision, "PASS");
    assert.equal(row.status, "ready");
    assert.ok(row.draft?.title);

    const pkg = buildListingPackage(row);
    assert.equal(pkg.sku, "LPROS-TEST-OAK-49");
    assert.ok(pkg.inventoryItem.product.title);
    assert.ok(pkg.blockers.some((b) => /imageUrls|policy/i.test(b)));

    const exported = exportPackages({ status: "ready", format: "both" });
    assert.ok(exported.count >= 1);
    assert.ok(exported.files.some((f) => f.type === "csv"));
    assert.ok(exported.files.some((f) => f.type === "json"));

    const dry = dryRunPublish("LPROS-TEST-OAK-49");
    assert.equal(dry.mode, "dry_run");
    assert.equal(dry.canGoLive, false);

    const { order, gate } = ingestOrder({
      orderId: "TEST-ORDER-1",
      sku: "LPROS-TEST-OAK-49",
      buyerTotal: 49,
      supplierConfirmed: false,
    });
    assert.equal(gate.action, "HOLD_REVIEW");
    assert.ok(order.supplierCost === 17);

    const shipped = attachTracking("TEST-ORDER-1", {
      trackingNumber: "9400111899223344556677",
      carrier: "USPS",
    });
    assert.equal(shipped.status, "shipped");
    const push = trackingPushPayload("TEST-ORDER-1");
    assert.equal(push.ready, true);

    assert.ok(listSkus().count >= 1);
    assert.ok(authStatus().mode === "export_and_dry_run" || authStatus().mode === "live_sell_capable");

    removeSku("LPROS-TEST-OAK-49");
  });
});
