import assert from "node:assert/strict";
import { mkdtempSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { describe, it } from "node:test";
import { applyEnvFile } from "../src/config.js";
import { sellerHandle } from "../src/ebay/identity.js";

describe("sellerHandle (username → userId)", () => {
  it("prefers username when present", () => {
    assert.equal(sellerHandle({ username: "woodshop", userId: "u1" }), "woodshop");
  });
  it("falls back to immutable userId when username is gone", () => {
    assert.equal(sellerHandle({ userId: "usr_abc" }), "usr_abc");
    assert.equal(sellerHandle({ legacyUserId: "legacy" }), "legacy");
  });
  it("accepts a plain string", () => {
    assert.equal(sellerHandle("mill"), "mill");
    assert.equal(sellerHandle(null), "");
  });
});

describe("applyEnvFile", () => {
  it("fills empty process.env keys from a .env file", () => {
    const dir = mkdtempSync(join(tmpdir(), "ebay-env-"));
    const file = join(dir, ".env");
    const key = `EBAY_TEST_${Date.now()}`;
    writeFileSync(file, `${key}=from-file\n`);
    process.env[key] = "";
    assert.equal(applyEnvFile(file), true);
    assert.equal(process.env[key], "from-file");
    delete process.env[key];
  });
});
