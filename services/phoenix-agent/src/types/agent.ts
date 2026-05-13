import type { Server } from "node:http";

export type AgentStatus = "ok" | "degraded" | "not_ready";

export interface HealthResponse {
  service: "Phoenix Agent";
  status: AgentStatus;
  version: string;
  contractVersion: string;
  nonDestructive: true;
  timestamp: string;
}

export interface JsonRouteResponse<TBody = unknown> {
  statusCode: number;
  body: TBody;
}

export interface StartedPhoenixAgentServer {
  server: Server;
  url: string;
  port: number;
}

export interface PhoenixAgentServerOptions {
  host?: string;
  port?: number;
  logger?: Pick<Console, "log" | "error"> | false;
}
