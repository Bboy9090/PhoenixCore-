import type { RiskLevel } from "./device";

export interface OperationCatalogEntry {
  operationId: string;
  label: string;
  owner: "Phoenix Agent" | "BootForge" | "Phoenix Key" | "Phoenix OS";
  destructive: boolean;
  previewOnly: boolean;
  blocked: boolean;
  requiredFutureGates: string[];
  safeNextStep: string;
}

export interface OperationPreviewRequest {
  operationId?: string;
  operationType?: string;
  operation_type?: string;
  targetDeviceId?: string;
  target_device_id?: string;
  parameters?: Record<string, unknown>;
}

export interface OperationPreviewResponse {
  previewId: string;
  operationId: string;
  previewOnly: true;
  mutatesSystem: false;
  commitAvailable: false;
  blocked: boolean;
  riskLevel: RiskLevel;
  requiredFutureGates: string[];
  safeNextStep: string;
  warnings: string[];
  expiresAt: string;
}

export interface BlockedOperationResponse {
  operationId: string;
  blocked: true;
  reason: string;
  requiredFutureGates: string[];
  safeNextStep: string;
}
