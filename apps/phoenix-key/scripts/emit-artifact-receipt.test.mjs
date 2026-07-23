#!/usr/bin/env node

import assert from "node:assert/strict";
import { createHash } from "node:crypto";
import { mkdtempSync, mkdirSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { basename, dirname, resolve } from "node:path";
import { spawnSync } from "node:child_process";
import { fileURLToPath } from "node:url";

const scriptDir = resolve(fileURLToPath(new URL(".", import.meta.url)));
const scriptPath = resolve(scriptDir, "emit-artifact-receipt.mjs");
const fixtureRoot = mkdtempSync(resolve(tmpdir(), "phoenix-key-artifact-receipt-"));
const msiPath = resolve(fixtureRoot, "msi", "Phoenix Key_3.1.0_x64_en-US.msi");
const nsisPath = resolve(fixtureRoot, "nsis", "Phoenix Key_3.1.0_x64-setup.exe");
const observationPath = resolve(fixtureRoot, "phoenix-key.signature-observation.json");
const commit = "1".repeat(40);
const workflow = "Phoenix Key Windows Lifecycle";
const buildCommand = "npm run desktop:build -- lifecycle-input";

function sha256(value) {
  return createHash("sha256").update(value).digest("hex");
}

try {
  mkdirSync(dirname(msiPath), { recursive: true });
  mkdirSync(dirname(nsisPath), { recursive: true });
  const msiPayload = Buffer.from("phoenix-key-msi-fixture\n", "utf8");
  const nsisPayload = Buffer.from("phoenix-key-nsis-fixture\n", "utf8");
  writeFileSync(msiPath, msiPayload);
  writeFileSync(nsisPath, nsisPayload);
  writeFileSync(
    observationPath,
    `${JSON.stringify([
      {
        filename: "Phoenix Key_3.1.0_x64_en-US.msi",
        probe_status: "UnknownError",
        probe_message: "The file format could not expose a signature status, and no signer certificate was present.",
        signer_present: false,
        timestamp_present: false
      },
      {
        filename: "Phoenix Key_3.1.0_x64-setup.exe",
        probe_status: "NotSigned",
        probe_message: "The file is not digitally signed.",
        signer_present: false,
        timestamp_present: false
      }
    ], null, 2)}\n`,
    "utf8"
  );

  const result = spawnSync(process.execPath, [scriptPath], {
    encoding: "utf8",
    env: {
      ...process.env,
      SOURCE_COMMIT: commit,
      PHOENIX_KEY_BUNDLE_ROOT: fixtureRoot,
      PHOENIX_KEY_BUILD_WORKFLOW: workflow,
      PHOENIX_KEY_BUILD_COMMAND: buildCommand,
      GITHUB_RUN_ID: "12345",
      GITHUB_RUN_NUMBER: "9",
      GITHUB_SERVER_URL: "https://github.com",
      GITHUB_REPOSITORY: "Bboy9090/PhoenixCore-"
    }
  });

  assert.equal(result.status, 0, result.stderr || result.stdout);
  const output = JSON.parse(result.stdout);
  assert.equal(output.status, "PHOENIX_KEY_ARTIFACT_RECEIPT_WRITTEN");
  assert.equal(output.workflow, workflow);
  assert.equal(output.artifacts.length, 2);

  const receiptPath = resolve(fixtureRoot, "phoenix-key.source-artifact.json");
  const receiptText = readFileSync(receiptPath, "utf8");
  const receipt = JSON.parse(receiptText);

  assert.equal(receipt.schema_version, "bws.source-app-artifact/v1");
  assert.equal(receipt.app_id, "phoenix-usb-creator");
  assert.equal(receipt.source.commit, commit);
  assert.equal(receipt.source.version, "3.1.0");
  assert.equal(receipt.build.workflow, workflow);
  assert.equal(receipt.build.command, buildCommand);
  assert.equal(receipt.status, "verified-build-output-not-packaged");
  assert.equal(receipt.release_eligible, false);
  assert.equal(receipt.build.signature_observation, "phoenix-key.signature-observation.json");
  assert.deepEqual(receipt.lifecycle_receipts, {
    install: "not-run",
    launch: "not-run",
    update: "not-run",
    rollback: "not-run",
    uninstall: "not-run"
  });

  const byKind = Object.fromEntries(receipt.artifacts.map((artifact) => [artifact.kind, artifact]));
  assert.equal(byKind["windows-msi"].size_bytes, msiPayload.length);
  assert.equal(byKind["windows-msi"].sha256, sha256(msiPayload));
  assert.equal(byKind["windows-msi"].signature.status, "absent-unsigned-preview");
  assert.equal(byKind["windows-msi"].signature.producer_probe_status, "UnknownError");
  assert.equal(byKind["windows-msi"].signature.signer_present, false);
  assert.equal(byKind["windows-nsis"].size_bytes, nsisPayload.length);
  assert.equal(byKind["windows-nsis"].sha256, sha256(nsisPayload));
  assert.equal(byKind["windows-nsis"].signature.status, "absent-unsigned-preview");
  assert.equal(byKind["windows-nsis"].signature.producer_probe_status, "NotSigned");
  assert.equal(byKind["windows-nsis"].signature.signer_present, false);

  const checksumLine = readFileSync(`${receiptPath}.sha256`, "utf8").trim();
  assert.equal(checksumLine, `${sha256(Buffer.from(receiptText, "utf8"))}  ${basename(receiptPath)}`);

  console.log("PHOENIX_KEY_ARTIFACT_RECEIPT_TEST_PASS");
} finally {
  rmSync(fixtureRoot, { recursive: true, force: true });
}
