#!/usr/bin/env node

import { mkdtempSync, readFileSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join, resolve } from "node:path";
import { spawnSync } from "node:child_process";

const root = mkdtempSync(join(tmpdir(), "phoenix-release-provenance-"));
const artifactA = join(root, "Phoenix-Key.msi");
const artifactB = join(root, "Phoenix-Key.exe");
const output = join(root, "RELEASE-PROVENANCE.json");
writeFileSync(artifactA, "msi-fixture");
writeFileSync(artifactB, "exe-fixture");

const script = resolve("scripts/release/emit-release-provenance.mjs");
const result = spawnSync(process.execPath, [
  script,
  "--product", "phoenix-key",
  "--channel", "windows-direct",
  "--version", "3.2.0",
  "--source-commit", "a".repeat(40),
  "--artifact", artifactA,
  "--artifact", artifactB,
  "--output", output,
], {
  encoding: "utf8",
  env: {
    ...process.env,
    GITHUB_REPOSITORY: "Bboy9090/PhoenixCore-",
    GITHUB_WORKFLOW: "fixture",
    GITHUB_RUN_ID: "123",
    GITHUB_RUN_NUMBER: "7",
    GITHUB_RUN_ATTEMPT: "1",
    GITHUB_SERVER_URL: "https://github.com",
  },
});

if (result.status !== 0) {
  throw new Error(result.stderr || result.stdout || "provenance fixture failed");
}

const receipt = JSON.parse(readFileSync(output, "utf8"));
if (receipt.schema_version !== "bws.release-provenance/v1") throw new Error("wrong schema");
if (receipt.source.commit !== "a".repeat(40)) throw new Error("commit not bound");
if (receipt.artifacts.length !== 2) throw new Error("wrong artifact count");
if (!receipt.artifacts.every((item) => /^[0-9a-f]{64}$/.test(item.sha256))) {
  throw new Error("artifact SHA-256 missing");
}
if (receipt.release_boundary.manual_publish_required !== true) {
  throw new Error("manual publish boundary missing");
}
if (!readFileSync(`${output}.sha256`, "utf8").includes("RELEASE-PROVENANCE.json")) {
  throw new Error("receipt checksum sidecar missing");
}

console.log("RELEASE_PROVENANCE_TEST=pass");
