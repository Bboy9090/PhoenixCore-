import assert from "node:assert/strict";
import { after, before, test } from "node:test";
import type { Server } from "node:http";
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

test("health endpoint responds with non-destructive Phoenix Agent status", async () => {
  const response = await fetch(`${baseUrl}/health`);
  const body = await response.json() as Record<string, unknown>;

  assert.equal(response.status, 200);
  assert.equal(body.service, "Phoenix Agent");
  assert.equal(body.status, "ok");
  assert.equal(body.nonDestructive, true);
  assert.equal(typeof body.version, "string");
});
