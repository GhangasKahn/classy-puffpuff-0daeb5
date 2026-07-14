import { describe, expect, it } from "vitest";
import {
  isBucketSized,
  parseOriginList,
  pickCorsOrigin,
  resolveVaultConflict,
  versionsToPrune,
  PAD_BUCKETS,
} from "../src/logic";

describe("resolveVaultConflict", () => {
  it("accepts matching base and returns next version", () => {
    expect(resolveVaultConflict(3, 3)).toEqual({ ok: true, next: 4 });
    expect(resolveVaultConflict(0, 0)).toEqual({ ok: true, next: 1 });
  });

  it("rejects stale or raced base", () => {
    expect(resolveVaultConflict(5, 4)).toEqual({ ok: false, current: 5 });
    expect(resolveVaultConflict(1, 0)).toEqual({ ok: false, current: 1 });
  });
});

describe("versionsToPrune", () => {
  it("keeps the newest N", () => {
    const desc = Array.from({ length: 35 }, (_, i) => 35 - i);
    const drop = versionsToPrune(desc, 30);
    expect(drop).toHaveLength(5);
    expect(drop).toEqual([5, 4, 3, 2, 1]);
  });

  it("drops nothing under the cap", () => {
    expect(versionsToPrune([3, 2, 1], 30)).toEqual([]);
  });
});

describe("cors helpers", () => {
  it("parses origin list", () => {
    expect(parseOriginList("https://a.com, https://b.com")).toEqual([
      "https://a.com",
      "https://b.com",
    ]);
  });

  it("echoes allowed origin only", () => {
    const allowed = ["https://app.example.com", "http://localhost:5173"];
    expect(pickCorsOrigin("https://app.example.com", allowed)).toBe(
      "https://app.example.com"
    );
    expect(pickCorsOrigin("https://evil.test", allowed)).toBe(
      "https://app.example.com"
    );
  });
});

describe("pad buckets", () => {
  it("recognizes doctrine bucket sizes", () => {
    for (const b of PAD_BUCKETS) expect(isBucketSized(b)).toBe(true);
    expect(isBucketSized(100)).toBe(false);
  });
});
