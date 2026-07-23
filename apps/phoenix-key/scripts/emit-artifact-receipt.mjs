#!/usr/bin/env node

import { createHash } from "node:crypto";
import { readFileSync, readdirSync, statSync, writeFileSync } from "node:fs";
import { basename, join, relative, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const scriptDir = resolve(fileURLToPath(new URL(".", import.meta.url)));
const appRoot = resolve(scriptDir, "..");
const bundleRoot = resolve(appRoot, "src-tauri", "target", "release", "bundle");
const packageJson = JSON.parse(readFileSync(resolve(appRoot, "package.json"), "utf8"));

function requireValue(condition, message) {
  if (!condition) {
    throw new Error(message);
  }
}

function sha256(path) {
  return createHash("sha256").update(readFileSync(path)).digest("hex");
}

function findArtifacts(directory, extension, kind) {
  const absolute = resolve(bundleRoot, directory);
  const entries = readdirSync(absolute, { withFileTypes: true })
    .filter((entry) => entry.isFile() && entry.name.toLowerCase().endsWith(extension))
    .map((entry) => resolve(absolute, entry.name))
    .sort();

  requireValue(entries.length > 0, `no ${kind} artifacts found in ${absolute}`);
  return entries.map((path) => ({
    kind,
    filename: basename(path),
    archive_path: relative(bundleRoot, path).replaceAll("\\", "/"),
    size_bytes: statSync(path).size,
    sha256: sha256(path),
    signature: {
      scheme: "authenticode",
      status: "absent-unsigned-preview"
    }
  }));
}

const sourceCommit = process.env.SOURCE_COMMIT ?? "";
requireValue(/^[0-9a-f]{40}$/.test(sourceCommit), "SOURCE_COMMIT must be a 40-character lowercase Git commit");
requireValue(packageJson.version === "3.1.0", "unexpected Phoenix Key package version");

const artifacts = [
  ...findArtifacts("msi", ".msi", "windows-msi"),
  ...findArtifacts("nsis", ".exe", "windows-nsis")
];

const receipt = {
  schema_version: "bws.source-app-artifact/v1",
  app_id: "phoenix-usb-creator",
  product_alias: "Phoenix Key",
  display_name: "Phoenix USB Creator / Phoenix Key",
  source: {
    repository: "Bboy9090/PhoenixCore-",
    commit: sourceCommit,
    version: packageJson.version
  },
  target: {
    operating_system: "windows",
    architecture: "x86_64",
    runtime: "tauri-v1",
    package_formats: ["msi", "nsis"]
  },
  build: {
    workflow: "Phoenix Key Desktop",
    workflow_run_id: process.env.GITHUB_RUN_ID ?? "local",
    workflow_run_number: process.env.GITHUB_RUN_NUMBER ?? "local",
    workflow_url: process.env.GITHUB_SERVER_URL && process.env.GITHUB_REPOSITORY && process.env.GITHUB_RUN_ID
      ? `${process.env.GITHUB_SERVER_URL}/${process.env.GITHUB_REPOSITORY}/actions/runs/${process.env.GITHUB_RUN_ID}`
      : null,
    node: "22",
    rust: "stable",
    command: "npm run desktop:build",
    boundary_check: "pass",
    compilation: "pass"
  },
  dependency_boundary: {
    libbootforge_repository: "Bboy9090/Bootforge-usb",
    libbootforge_commit: "7b4b4dded69945df78b50933f052046a093d8a89",
    tauri_major: 1
  },
  artifacts,
  lifecycle_receipts: {
    install: "not-run",
    launch: "not-run",
    update: "not-run",
    rollback: "not-run",
    uninstall: "not-run"
  },
  safety_boundary: {
    browser_hardware_fabrication: "prohibited",
    dashboard_physical_write: "disabled",
    normal_desktop_flow: "read-only-dry-run"
  },
  artifact_class: "unsigned-preview",
  status: "verified-build-output-not-packaged",
  release_eligible: false
};

const outputPath = join(bundleRoot, "phoenix-key.source-artifact.json");
writeFileSync(outputPath, `${JSON.stringify(receipt, null, 2)}\n`, "utf8");
writeFileSync(`${outputPath}.sha256`, `${sha256(outputPath)}  ${basename(outputPath)}\n`, "utf8");

console.log(JSON.stringify({
  status: "PHOENIX_KEY_ARTIFACT_RECEIPT_WRITTEN",
  output: relative(appRoot, outputPath).replaceAll("\\", "/"),
  artifacts: artifacts.map(({ kind, filename, size_bytes, sha256: digest }) => ({
    kind,
    filename,
    size_bytes,
    sha256: digest
  }))
}, null, 2));
