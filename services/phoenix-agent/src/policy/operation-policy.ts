import { randomUUID } from "node:crypto";
import {
  createBlockedOperationResponse,
  getBlockedOperationCatalog,
  isBlockedOperation,
  REQUIRED_FUTURE_GATES
} from "./blocked-operations";
import type {
  BlockedOperationResponse,
  OperationCatalogEntry,
  OperationPreviewRequest,
  OperationPreviewResponse
} from "../types/operation";

export function normalizeOperationId(input: unknown): string {
  if (!input || typeof input !== "object") {
    return "unknown.operation";
  }

  const body = input as Record<string, unknown>;
  const value = body.operationId ?? body.operationType ?? body.operation_type ?? body.type;

  return typeof value === "string" && value.trim().length > 0
    ? value.trim()
    : "unknown.operation";
}

export function getOperationCatalog(): OperationCatalogEntry[] {
  return [
    {
      operationId: "system.inspect",
      label: "Inspect system status",
      owner: "Phoenix Agent",
      destructive: false,
      previewOnly: true,
      blocked: false,
      requiredFutureGates: [],
      safeNextStep: "Use GET /v1/system/status for mock status."
    },
    {
      operationId: "device.list",
      label: "List mock devices",
      owner: "Phoenix Agent",
      destructive: false,
      previewOnly: true,
      blocked: false,
      requiredFutureGates: [],
      safeNextStep: "Use GET /v1/devices for mock data."
    },
    ...getBlockedOperationCatalog()
  ];
}

export function createOperationPreview(request: OperationPreviewRequest): OperationPreviewResponse {
  const operationId = normalizeOperationId(request);
  const blocked = isBlockedOperation(operationId);
  const expiresAt = new Date(Date.now() + 5 * 60 * 1000).toISOString();

  return {
    previewId: `preview-${randomUUID()}`,
    operationId,
    previewOnly: true,
    mutatesSystem: false,
    commitAvailable: false,
    blocked,
    riskLevel: blocked ? "critical" : "low",
    requiredFutureGates: blocked ? [...REQUIRED_FUTURE_GATES] : [],
    safeNextStep: blocked
      ? "Review this preview only. Commit remains blocked until future gates exist."
      : "This PR8 skeleton returns previews only; no commit path is enabled.",
    warnings: [
      "Phoenix Agent PR8 is mock-only.",
      "No disk, USB, BootCamp, OCLP, workflow, or remote command operation was executed."
    ],
    expiresAt
  };
}

export function rejectOperationCommit(request: unknown): { statusCode: 403 | 409; body: BlockedOperationResponse } {
  const operationId = normalizeOperationId(request);
  const statusCode = isBlockedOperation(operationId) ? 403 : 409;

  return {
    statusCode,
    body: createBlockedOperationResponse(operationId)
  };
}
