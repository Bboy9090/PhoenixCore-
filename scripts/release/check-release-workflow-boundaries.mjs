#!/usr/bin/env node

import { readFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const scriptDirectory = dirname(fileURLToPath(import.meta.url));
const repositoryRoot = resolve(scriptDirectory, "../..");

const workflows = {
  windowsDirect: ".github/workflows/windows-signed-release.yml",
  macDirect: ".github/workflows/macos-signed-release.yml",
  microsoftStore: ".github/workflows/microsoft-store-release.yml",
  macAppStore: ".github/workflows/macos-app-store.yml",
  googlePlay: ".github/workflows/android-store-release.yml",
};

function text(path) {
  return readFileSync(resolve(repositoryRoot, path), "utf8").replace(/\r\n/g, "\n");
}

function requireContains(source, needle, message) {
  if (!source.includes(needle)) throw new Error(message);
}

function requireAbsent(source, needle, message) {
  if (source.includes(needle)) throw new Error(message);
}

function requireBefore(source, first, second, message) {
  const firstIndex = source.indexOf(first);
  const secondIndex = source.indexOf(second);
  if (firstIndex < 0 || secondIndex < 0 || firstIndex >= secondIndex) {
    throw new Error(message);
  }
}

for (const path of Object.values(workflows)) {
  const source = text(path);
  requireContains(
    source,
    'branches:\n      - "store-release/phoenix-key-v*"',
    `${path}: release preflight must cover versioned store-release branches`,
  );
  requireContains(
    source,
    "emit-release-provenance.mjs",
    `${path}: publishable artifact path must emit release provenance`,
  );
}

const windowsDirect = text(workflows.windowsDirect);
requireContains(
  windowsDirect,
  "  build-sign-release:\n    if: github.event_name == 'workflow_dispatch'",
  "Windows direct publishing must require manual dispatch",
);
requireContains(
  windowsDirect,
  "permissions:\n  contents: read",
  "Windows direct workflow must default to read-only repository permissions",
);
requireContains(
  windowsDirect,
  "Import-PfxCertificate",
  "Windows direct workflow must import the signing certificate before Tauri bundles the app",
);
requireContains(
  windowsDirect,
  'certificateThumbprint = $certificate.Thumbprint',
  "Windows direct workflow must pass the imported certificate thumbprint to Tauri",
);
requireContains(
  windowsDirect,
  'npx tauri build --config "$env:TAURI_WINDOWS_SIGNING_CONFIG"',
  "Windows direct workflow must use Tauri signing during the application build",
);
requireContains(
  windowsDirect,
  'Get-Item "src-tauri/target/release/phoenix-key.exe"',
  "Windows direct workflow must verify the signed application executable, not only installers",
);
requireBefore(
  windowsDirect,
  "- name: Restore and import code-signing certificate",
  "- name: Build signed application and release installers",
  "Windows signing certificate import must happen before Tauri build",
);
requireBefore(
  windowsDirect,
  "- name: Build signed application and release installers",
  "- name: Verify application and installer Authenticode",
  "Windows application and installers must be verified after the signed build",
);

const macDirect = text(workflows.macDirect);
requireContains(
  macDirect,
  "  build-sign-notarize:\n    if: github.event_name == 'workflow_dispatch'",
  "macOS direct publishing must require manual dispatch",
);
requireContains(
  macDirect,
  "permissions:\n  contents: read",
  "macOS direct workflow must default to read-only repository permissions",
);

const microsoftStore = text(workflows.microsoftStore);
requireContains(
  microsoftStore,
  "  publish:\n    if: github.event_name == 'workflow_dispatch'",
  "Microsoft Store publishing must require manual dispatch",
);
requireContains(
  microsoftStore,
  "permissions:\n  contents: read",
  "Microsoft Store workflow must default to read-only repository permissions",
);

const macAppStore = text(workflows.macAppStore);
requireContains(
  macAppStore,
  "  package-and-upload:\n    if: github.event_name == 'workflow_dispatch'",
  "Mac App Store upload must require manual dispatch",
);

const googlePlay = text(workflows.googlePlay);
requireContains(
  googlePlay,
  "  build-signed-aab:\n    if: github.event_name == 'workflow_dispatch'",
  "Google Play upload must require manual dispatch",
);
requireContains(
  googlePlay,
  "track: ${{ inputs.play_track || 'internal' }}",
  "Google Play fallback track must remain internal",
);
requireContains(
  googlePlay,
  "status: ${{ inputs.release_status || 'draft' }}",
  "Google Play fallback status must remain draft",
);
requireAbsent(
  googlePlay,
  "track: ${{ inputs.play_track || 'production' }}",
  "Google Play must never default to production",
);
requireAbsent(
  googlePlay,
  "status: ${{ inputs.release_status || 'completed' }}",
  "Google Play must never default to completed",
);

console.log("RELEASE_WORKFLOW_BOUNDARIES=pass");
