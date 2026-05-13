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

for (const operationId of BLOCKED_OPERATION_IDS) {
  test(`commit blocks ${operationId}`, async () => {
    const response = await fetch(`${baseUrl}/v1/operations/commit`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ operationId })
    });
    const body = await response.json() as Record<string, unknown>;

    assert.equal(response.status, 403);
    assert.equal(body.operationId, operationId);
    assert.equal(body.blocked, true);
    assert.equal(typeof body.reason, "string");
    assert.ok((body.reason as string).length > 0);
    assert.equal(body.safeNextStep, "Call /v1/operations/preview and wait for a future safety-backed implementation PR.");
    assert.deepEqual(body.requiredFutureGates, [...REQUIRED_FUTURE_GATES]);
  });
}
