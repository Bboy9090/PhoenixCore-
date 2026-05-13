import http, { type IncomingMessage, type RequestListener, type ServerResponse } from "node:http";
import { URL } from "node:url";
import type { JsonRouteResponse, PhoenixAgentServerOptions, StartedPhoenixAgentServer } from "./types/agent";
import { getDevice, listDevices, listRemovableDevices } from "./routes/devices";
import { getHealth } from "./routes/health";
import { commitOperation, listOperationCatalog, previewOperation } from "./routes/operations";
import { getSafetyPolicy, getBlockedOperations } from "./routes/safety";
import { getSystemStatus } from "./routes/system";

type HttpMethod = "GET" | "POST" | "OPTIONS" | "UNSUPPORTED";

export function createPhoenixAgentRequestHandler(): RequestListener {
  return async (request, response) => {
    try {
      const method = normalizeMethod(request.method);

      if (method === "OPTIONS") {
        sendJson(response, 204, {});
        return;
      }

      const url = new URL(request.url ?? "/", "http://localhost");
      const path = normalizePath(url.pathname);
      const body = method === "POST" ? await readJsonBody(request) : undefined;
      const routeResponse = routeRequest(method, path, body);

      sendJson(response, routeResponse.statusCode, routeResponse.body);
    } catch (error) {
      sendJson(response, 500, {
        error: {
          code: "agent.internal_error",
          message: error instanceof Error ? error.message : "Unknown Phoenix Agent error",
          severity: "error"
        }
      });
    }
  };
}

export function routeRequest(method: HttpMethod, path: string, body: unknown): JsonRouteResponse {
  if (method === "UNSUPPORTED") {
    return {
      statusCode: 405,
      body: {
        error: {
          code: "method.not_allowed",
          message: "Phoenix Agent mock supports GET, POST, and OPTIONS only.",
          severity: "warning"
        }
      }
    };
  }

  if (method === "GET" && path === "/health") {
    return { statusCode: 200, body: getHealth() };
  }

  if (method === "GET" && (path === "/v1/system/status" || path === "/system/summary")) {
    return { statusCode: 200, body: getSystemStatus() };
  }

  if (method === "GET" && (path === "/v1/devices" || path === "/devices")) {
    return { statusCode: 200, body: listDevices() };
  }

  if (method === "GET" && (path === "/v1/devices/removable" || path === "/devices/removable")) {
    return { statusCode: 200, body: listRemovableDevices() };
  }

  if (method === "GET" && path.startsWith("/v1/devices/")) {
    return getDevice(decodeURIComponent(path.slice("/v1/devices/".length)));
  }

  if (method === "GET" && path === "/v1/operations/catalog") {
    return { statusCode: 200, body: listOperationCatalog() };
  }

  if (method === "POST" && (path === "/v1/operations/preview" || path === "/operations/preview")) {
    return { statusCode: 200, body: previewOperation(asObject(body)) };
  }

  if (method === "POST" && (path === "/v1/operations/commit" || path === "/operations/execute")) {
    return commitOperation(body);
  }

  if (method === "GET" && path === "/v1/safety/policy") {
    return { statusCode: 200, body: getSafetyPolicy() };
  }

  if (method === "GET" && path === "/v1/safety/blocked-operations") {
    return { statusCode: 200, body: getBlockedOperations() };
  }

  return {
    statusCode: 404,
    body: {
      error: {
        code: "route.not_found",
        message: `Phoenix Agent mock route not found: ${method} ${path}`,
        severity: "warning"
      }
    }
  };
}

export async function startPhoenixAgentServer(
  options: PhoenixAgentServerOptions = {}
): Promise<StartedPhoenixAgentServer> {
  const host = options.host ?? "127.0.0.1";
  const port = options.port ?? 7788;
  const server = http.createServer(createPhoenixAgentRequestHandler());

  await new Promise<void>((resolve, reject) => {
    server.once("error", reject);
    server.listen(port, host, () => {
      server.off("error", reject);
      resolve();
    });
  });

  const address = server.address();
  const actualPort = typeof address === "object" && address ? address.port : port;
  const url = `http://${host}:${actualPort}`;

  if (options.logger) {
    options.logger.log(`Phoenix Agent mock listening at ${url}`);
  }

  return { server, url, port: actualPort };
}

function normalizeMethod(method: string | undefined): HttpMethod {
  if (method === "GET" || method === "POST" || method === "OPTIONS") {
    return method;
  }

  return "UNSUPPORTED";
}

function normalizePath(path: string): string {
  if (path === "/") {
    return "/";
  }

  return path.replace(/\/+$/, "");
}

function asObject(body: unknown): Record<string, unknown> {
  return body && typeof body === "object" ? (body as Record<string, unknown>) : {};
}

async function readJsonBody(request: IncomingMessage): Promise<unknown> {
  const chunks: Buffer[] = [];

  for await (const chunk of request) {
    chunks.push(typeof chunk === "string" ? Buffer.from(chunk) : chunk);
  }

  const raw = Buffer.concat(chunks).toString("utf8").trim();

  if (!raw) {
    return {};
  }

  return JSON.parse(raw) as unknown;
}

function sendJson(response: ServerResponse, statusCode: number, body: unknown): void {
  const payload = statusCode === 204 ? "" : JSON.stringify(body);

  response.writeHead(statusCode, {
    "Access-Control-Allow-Headers": "Content-Type",
    "Access-Control-Allow-Methods": "GET,POST,OPTIONS",
    "Access-Control-Allow-Origin": "http://localhost",
    "Content-Type": "application/json; charset=utf-8"
  });
  response.end(payload);
}
