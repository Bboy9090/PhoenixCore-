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

test("devices endpoint returns mock data only", async () => {
  const response = await fetch(`${baseUrl}/v1/devices`);
  const body = await response.json() as { devices: Array<Record<string, unknown>>; source: string };

  assert.equal(response.status, 200);
  assert.equal(body.source, "mock");
  assert.ok(body.devices.length >= 2);
  assert.ok(body.devices.every((device) => device.mock === true));
});

test("device detail endpoint returns a mock device or 404", async () => {
  const found = await fetch(`${baseUrl}/v1/devices/mock-removable-001`);
  const foundBody = await found.json() as Record<string, unknown>;
  assert.equal(found.status, 200);
  assert.equal(foundBody.id, "mock-removable-001");
  assert.equal(foundBody.mock, true);

  const missing = await fetch(`${baseUrl}/v1/devices/not-real`);
  const missingBody = await missing.json() as { error: { code: string } };
  assert.equal(missing.status, 404);
  assert.equal(missingBody.error.code, "device.not_found");
});

test("preview endpoint does not mutate mock device state", async () => {
  const beforeDevices = await (await fetch(`${baseUrl}/v1/devices`)).json() as { devices: unknown[] };

  const preview = await fetch(`${baseUrl}/v1/operations/preview`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      operationId: "usb.build",
      targetDeviceId: "mock-removable-001"
    })
  });
  const previewBody = await preview.json() as Record<string, unknown>;
  const afterDevices = await (await fetch(`${baseUrl}/v1/devices`)).json() as { devices: unknown[] };

  assert.equal(preview.status, 200);
  assert.equal(previewBody.operationId, "usb.build");
  assert.equal(previewBody.previewOnly, true);
  assert.equal(previewBody.mutatesSystem, false);
  assert.equal(previewBody.commitAvailable, false);
  assert.deepEqual(afterDevices.devices, beforeDevices.devices);
});
