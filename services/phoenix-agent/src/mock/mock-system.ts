import os from "node:os";

export interface MockSystemStatus {
  service: "Phoenix Agent";
  status: "ok";
  source: "mock";
  nonDestructive: true;
  platform: NodeJS.Platform;
  arch: string;
  hostname: string;
  uptimeSeconds: number;
  agent: {
    version: string;
    contractVersion: string;
    commitEnabled: false;
  };
  timestamp: string;
}

export function getMockSystemStatus(): MockSystemStatus {
  return {
    service: "Phoenix Agent",
    status: "ok",
    source: "mock",
    nonDestructive: true,
    platform: process.platform,
    arch: process.arch,
    hostname: os.hostname(),
    uptimeSeconds: Math.round(process.uptime()),
    agent: {
      version: "0.1.0",
      contractVersion: "0.1.0",
      commitEnabled: false
    },
    timestamp: new Date().toISOString()
  };
}
