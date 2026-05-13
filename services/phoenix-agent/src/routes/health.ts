import type { HealthResponse } from "../types/agent";

export function getHealth(): HealthResponse {
  return {
    service: "Phoenix Agent",
    status: "ok",
    version: "0.1.0",
    contractVersion: "0.1.0",
    nonDestructive: true,
    timestamp: new Date().toISOString()
  };
}
