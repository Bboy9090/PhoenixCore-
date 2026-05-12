export type RiskLevel = "low" | "medium" | "high" | "critical";

export type AgentStatus = "ok" | "degraded" | "not_ready";

export type ImplementationStatus = "contract_only" | "partial" | "active";

export type OperationState =
  | "requested"
  | "previewed"
  | "blocked"
  | "ready_for_execution"
  | "queued"
  | "running"
  | "succeeded"
  | "failed"
  | "cancelled"
  | "not_implemented";

export type SafetyGateStatus = "passed" | "failed" | "warning" | "not_evaluated";

export type ErrorSeverity = "info" | "warning" | "error" | "critical";

export interface AgentHealth {
  status: AgentStatus;
  version: string;
  contract_version: string;
  implementation_status: ImplementationStatus;
  timestamp: string;
  capabilities?: string[];
}

export interface HostSummary {
  os: string;
  os_version?: string;
  arch: string;
  hostname: string;
  is_live_environment?: boolean;
  desktop_session?: string | null;
}

export interface SafetyPolicySummary {
  preview_required_for_destructive_operations: boolean;
  system_disks_protected_by_default: boolean;
  explicit_device_identity_required: boolean;
  policy_version?: string;
}

export interface SystemSummary {
  host: HostSummary;
  agent: AgentHealth;
  safety: SafetyPolicySummary;
}

export interface Device {
  device_id: string;
  display_name: string;
  stable_path?: string | null;
  physical_path?: string | null;
  serial?: string | null;
  vendor?: string | null;
  model?: string | null;
  size_bytes: number;
  removable: boolean;
  system_disk: boolean;
  read_only: boolean;
  bus?: string | null;
  partition_count: number;
  identity_fingerprint: string;
  risk_level: RiskLevel;
  warnings?: string[];
}

export interface DeviceListResponse {
  devices: Device[];
  scan_id: string;
  timestamp: string;
}

export interface DeviceRef {
  device_id: string;
  identity_fingerprint: string;
  stable_path?: string | null;
}

export interface SafetyGateResult {
  gate: string;
  status: SafetyGateStatus;
  message?: string;
  evidence?: Record<string, unknown>;
}

export interface SafetyEvaluationRequest {
  operation_type: string;
  target_device?: DeviceRef;
  parameters?: Record<string, unknown>;
}

export interface SafetyEvaluationResponse {
  safe_to_proceed: boolean;
  risk_level: RiskLevel;
  gates: SafetyGateResult[];
  warnings?: string[];
  errors?: string[];
}

export interface OperationPreviewRequest {
  operation_type: string;
  target_device?: DeviceRef;
  parameters?: Record<string, unknown>;
  requested_by?: string;
  dry_run?: boolean;
}

export interface OperationPreviewResponse {
  preview_id: string;
  operation_type: string;
  status: "previewed" | "blocked" | "not_implemented";
  risk_level: RiskLevel;
  target_device?: Device;
  required_gates: SafetyGateResult[];
  warnings?: string[];
  proposed_changes?: string[];
  expires_at: string;
  safety_token: string;
  correlation_id?: string;
}

export interface OperationExecuteRequest {
  preview_id: string;
  safety_token: string;
  acknowledged_risk: boolean;
  target_device?: DeviceRef;
  idempotency_key?: string;
}

export interface OperationStatusResponse {
  operation_id: string;
  preview_id?: string;
  operation_type: string;
  status: OperationState;
  progress_percent?: number;
  current_step?: string | null;
  created_at: string;
  updated_at?: string | null;
  warnings?: string[];
  error?: AgentError;
}

export interface ReportBundleRequest {
  operation_id?: string;
  include_logs?: boolean;
  include_device_snapshot?: boolean;
  redaction_level?: "standard" | "strict";
}

export interface ReportBundleResponse {
  status: "not_implemented" | "queued" | "ready";
  report_id?: string | null;
  download_url?: string | null;
  correlation_id?: string;
}

export interface LogExportResponse {
  status: "not_implemented" | "ready";
  operation_id?: string | null;
  download_url?: string | null;
  correlation_id?: string;
}

export interface AgentError {
  code: string;
  message: string;
  severity: ErrorSeverity;
  details?: Record<string, unknown>;
  correlation_id?: string;
}

export interface ErrorResponse {
  error: AgentError;
}

export interface PhoenixAgentClientOptions {
  baseUrl?: string;
  fetchImpl?: typeof fetch;
  headers?: Record<string, string>;
  placeholderMode?: boolean;
}

export class PhoenixAgentClientError extends Error {
  readonly agentError: AgentError;
  readonly status: number;

  constructor(agentError: AgentError, status: number) {
    super(agentError.message);
    this.name = "PhoenixAgentClientError";
    this.agentError = agentError;
    this.status = status;
    Object.setPrototypeOf(this, PhoenixAgentClientError.prototype);
  }
}

export class PhoenixAgentClient {
  private readonly baseUrl: string;
  private readonly fetchImpl: typeof fetch;
  private readonly headers: Record<string, string>;
  private readonly placeholderMode: boolean;

  constructor(options: PhoenixAgentClientOptions = {}) {
    this.baseUrl = (options.baseUrl ?? "http://localhost:7788").replace(/\/+$/, "");
    this.fetchImpl = options.fetchImpl ?? fetch;
    this.headers = options.headers ?? {};
    this.placeholderMode = options.placeholderMode ?? true;
  }

  getHealth(): Promise<AgentHealth> {
    return this.request<AgentHealth>("GET", "/health");
  }

  getSystemSummary(): Promise<SystemSummary> {
    return this.request<SystemSummary>("GET", "/system/summary");
  }

  listDevices(): Promise<DeviceListResponse> {
    return this.request<DeviceListResponse>("GET", "/devices");
  }

  listRemovableDrives(): Promise<DeviceListResponse> {
    return this.request<DeviceListResponse>("GET", "/devices/removable");
  }

  evaluateSafety(request: SafetyEvaluationRequest): Promise<SafetyEvaluationResponse> {
    return this.request<SafetyEvaluationResponse>("POST", "/safety/evaluate", request);
  }

  previewOperation(request: OperationPreviewRequest): Promise<OperationPreviewResponse> {
    return this.request<OperationPreviewResponse>("POST", "/operations/preview", {
      ...request,
      dry_run: request.dry_run ?? true
    });
  }

  getOperationStatus(operationId: string): Promise<OperationStatusResponse> {
    return this.request<OperationStatusResponse>(
      "GET",
      `/operations/${encodeURIComponent(operationId)}`
    );
  }

  executeOperationPlaceholder(request: OperationExecuteRequest): Promise<OperationStatusResponse> {
    // TODO(PR8+): Wire this only after Phoenix Agent has real policy checks,
    // Rust safety gates, audit logging, preview freshness checks, and tests.
    if (this.placeholderMode) {
      return Promise.resolve({
        operation_id: "not_implemented",
        preview_id: request.preview_id,
        operation_type: "placeholder",
        status: "not_implemented",
        progress_percent: 0,
        current_step: "Execution is intentionally not implemented in this contract scaffold.",
        created_at: new Date(0).toISOString(),
        warnings: [
          "Phoenix Agent execution is contract-only. No destructive operation was requested."
        ],
        error: {
          code: "operation.not_implemented",
          message: "Operation execution is intentionally not implemented in this SDK scaffold.",
          severity: "warning"
        }
      });
    }

    return this.request<OperationStatusResponse>("POST", "/operations/execute", request);
  }

  exportLogsPlaceholder(operationId?: string): Promise<LogExportResponse> {
    // TODO(PR7+): Replace placeholder with a Phoenix Agent endpoint call after
    // log redaction and report policies exist.
    if (this.placeholderMode) {
      return Promise.resolve({
        status: "not_implemented",
        operation_id: operationId ?? null
      });
    }

    const query = operationId ? `?operation_id=${encodeURIComponent(operationId)}` : "";
    return this.request<LogExportResponse>("GET", `/logs/export${query}`);
  }

  createReportBundlePlaceholder(request: ReportBundleRequest = {}): Promise<ReportBundleResponse> {
    // TODO(PR7+): Replace placeholder after report bundle generation is backed
    // by crates/report or an approved Agent implementation.
    if (this.placeholderMode) {
      return Promise.resolve({
        status: "not_implemented",
        report_id: null,
        download_url: null,
        correlation_id: request.operation_id
      });
    }

    return this.request<ReportBundleResponse>("POST", "/reports/bundle", request);
  }

  private async request<T>(
    method: "GET" | "POST",
    path: string,
    body?: unknown
  ): Promise<T> {
    const response = await this.fetchImpl(`${this.baseUrl}${path}`, {
      method,
      headers: {
        "Content-Type": "application/json",
        "X-Phoenix-Agent-Client": "typescript-contract-0.1.0",
        ...this.headers
      },
      body: body === undefined ? undefined : JSON.stringify(body)
    });

    const text = await response.text();
    const data = text.length > 0 ? JSON.parse(text) as T | ErrorResponse : undefined;

    if (!response.ok) {
      const errorResponse = isErrorResponse(data) ? data : {
        error: {
          code: "agent.http_error",
          message: `Phoenix Agent request failed with status ${response.status}.`,
          severity: "error" as ErrorSeverity
        }
      };
      throw new PhoenixAgentClientError(errorResponse.error, response.status);
    }

    return data as T;
  }
}

function isErrorResponse(value: unknown): value is ErrorResponse {
  return (
    typeof value === "object" &&
    value !== null &&
    "error" in value &&
    typeof (value as { error?: unknown }).error === "object"
  );
}
