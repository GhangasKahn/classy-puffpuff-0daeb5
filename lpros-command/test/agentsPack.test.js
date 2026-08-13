/**
 * Elite Hermes packs must exist as OpenClaw-style markdown workspaces.
 */
import { describe, it } from "node:test";
import assert from "node:assert/strict";
import { existsSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const root = resolve(dirname(fileURLToPath(import.meta.url)), "../../lpros-agents");
const REQUIRED = ["SOUL.md", "IDENTITY.md", "AGENTS.md", "TOOLS.md", "HEARTBEAT.md", "MEMORY.md"];

describe("lpros-agents elite packs", () => {
  it("root constitution and operator card exist", () => {
    assert.ok(existsSync(resolve(root, "AGENTS.md")));
    assert.ok(existsSync(resolve(root, "MEUFT.md")));
    assert.ok(existsSync(resolve(root, "USER.md")));
    assert.ok(existsSync(resolve(root, ".cursor/skills/create-elite-agent/SKILL.md")));
  });

  for (const agent of ["scout", "verifier"]) {
    it(`${agent} has the full OpenClaw workspace`, () => {
      for (const f of REQUIRED) {
        assert.ok(existsSync(resolve(root, agent, f)), `${agent}/${f}`);
      }
    });
  }
});
