#!/usr/bin/env node

import { createHash } from "node:crypto";
import {
  lstatSync,
  readFileSync,
  statSync,
  writeFileSync,
} from "node:fs";
import { basename, resolve } from "node:path";

function fail(message) {
  throw new Error(message);
}

function sha256File(path) {
  return createHash("sha256").update(readFileSync(path)).digest("hex");
}

function takeArgs(argv) {
  const values = new Map();
  const artifacts = [];
  for (let index = 0; index < argv.length; index += 2) {
    const key = argv[index];
    const value = argv[index + 1];
    if (!key?.startsWith("--") || value === undefined) {
      fail(`invalid argument sequence near ${key ?? "<end>"}`);
    }
    if (key === "--artifact") {
      artifacts.push(value);
    } else {
      if (values.has(key)) fail(`duplicate argument: ${key}`);
      values.set(key, value);
    }
  }
  return { values, artifacts };
}

function required(values, key) {
  const value = values.get(key)?.trim();
  if (!value) fail(`missing required argument: ${key}`);
  return value;
}

const { values, artifacts } = takeArgs(process.argv.slice(2));
const product = required(values, "--product");
const channel = required(values, "--channel");
const version = required(values, "--version");
const sourceCommit = required(values, "--source-commit").toLowerCase();
const output = resolve(required(values, "--output"));

if (!/^[0-9a-f]{40}$/.test(sourceCommit)) {
  fail("--source-commit must be a 40-character Git SHA");
}
if (!/^[0-9A-Za-z][0-9A-Za-z._+-]*$/.test(version)) {
  fail("--version contains unsupported characters");
}
if (artifacts.length === 0) {
  fail("at least one --artifact is required");
}

const seen = new Set();
const artifactRecords = artifacts.map((input) => {
  const path = resolve(input);
  if (seen.has(path)) fail(`duplicate artifact path: ${input}`);
  seen.add(path);
  const linkInfo = lstatSync(path);
  if (linkInfo.isSymbolicLink()) fail(`release artifact cannot be a symlink: ${input}`);
  const info = statSync(path);
  if (!info.isFile() || info.size <= 0) {
    fail(`release artifact must be a non-empty regular file: ${input}`);
  }
  return {
    filename: basename(path),
    size_bytes: info.size,
    sha256: sha256File(path),
  };
}).sort((left, right) => left.filename.localeCompare(right.filename));

const duplicateNames = new Set();
for (const artifact of artifactRecords) {
  if (duplicateNames.has(artifact.filename)) {
    fail(`duplicate artifact filename: ${artifact.filename}`);
  }
  duplicateNames.add(artifact.filename);
}

const repository = process.env.GITHUB_REPOSITORY ?? "local";
const runId = process.env.GITHUB_RUN_ID ?? "local";
const receipt = {
  schema_version: "bws.release-provenance/v1",
  product,
  channel,
  version,
  source: {
    repository,
    commit: sourceCommit,
  },
  workflow: {
    name: process.env.GITHUB_WORKFLOW ?? "local",
    run_id: runId,
    run_number: process.env.GITHUB_RUN_NUMBER ?? "local",
    run_attempt: process.env.GITHUB_RUN_ATTEMPT ?? "local",
    url:
      process.env.GITHUB_SERVER_URL && repository !== "local" && runId !== "local"
        ? `${process.env.GITHUB_SERVER_URL}/${repository}/actions/runs/${runId}`
        : null,
  },
  artifacts: artifactRecords,
  release_boundary: {
    manual_publish_required: true,
    source_commit_bound: true,
    symlink_artifacts_rejected: true,
    hash_algorithm: "sha256",
  },
};

writeFileSync(output, `${JSON.stringify(receipt, null, 2)}\n`, "utf8");
writeFileSync(
  `${output}.sha256`,
  `${sha256File(output)}  ${basename(output)}\n`,
  "utf8",
);

console.log(JSON.stringify({
  status: "RELEASE_PROVENANCE_WRITTEN",
  output,
  artifact_count: artifactRecords.length,
  source_commit: sourceCommit,
}, null, 2));
