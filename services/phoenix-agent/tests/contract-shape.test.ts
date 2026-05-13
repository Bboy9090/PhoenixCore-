import assert from "node:assert/strict";
import { after, before, test } from "node:test";
import type { Server } from "node:http";
import { BLOCKED_OPERATION_IDS, REQUIRED_FUTURE_GATES } from "../src/policy/blocked-operations";
import { startPhoenixAgentServer } from "../src/server";

let server: Server;
let baseUrl: string;

before(async () => {
  const started = await startPhoenixAgentServer({ port: 0 });
  server = started.server;
  baseUrl = started.url;
});

after(async () => {
  await new Promise<void>((resolve, reject) => {
    server.close((error) => (error ? reject(error) : resolve()));
  });
});

test("system status exposes mock non-destructive service shape", async () => {
  const response = await fetch(`${baseUrl}/v1/system/status`);
  const body = await response.json() as Record<string, unknown>;

  assert.equal(response.status, 200);
  assert.equal(body.service, "Phoenix Agent");
  assert.equal(body.source, "mock");
  assert.equal(body.nonDestructive, true);
  assert.equal(typeof body.platform, "string");
});

test("operation catalog includes blocked destructive operations", async () => {
  const response = await fetch(`${baseUrl}/v1/operations/catalog`);
  const body = await response.json() as { operations: Array<Record<string, unknown>> };
  const ids = body.operations.map((operation) => operation.operationId);

  assert.equal(response.status, 200);
  for (const operationId of BLOCKED_OPERATION_IDS) {
    assert.ok(ids.includes(operationId), `${operationId} missing from catalog`);
  }
});

test("safety policy and blocked operation shapes are stable", async () => {
  const policy = await (await fetch(`${baseUrl}/v1/safety/policy`)).json() as Record<string, unknown>;
  assert.equal(policy.previewFirst, true);
  assert.equal(policy.nonDestructiveMockOnly, true);
  assert.equal(policy.commitEnabled, false);
  assert.deepEqual(policy.requiredFutureGates, [...REQUIRED_FUTURE_GATES]);

  const blocked = await (await fetch(`${baseUrl}/v1/safety/blocked-operations`)).json() as {
    operations: Array<Record<string, unknown>>;
    requiredFutureGates: string[];
  };
  assert.deepEqual(blocked.requiredFutureGates, [...REQUIRED_FUTURE_GATES]);

  for (const operation of blocked.operations) {
    assert.equal(operation.blocked, true);
    assert.equal(operation.previewOnly, true);
    assert.equal(operation.destructive, true);
    assert.deepEqual(operation.requiredFutureGates, [...REQUIRED_FUTURE_GATES]);
  }
});
