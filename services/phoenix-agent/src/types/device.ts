export type RiskLevel = "low" | "medium" | "high" | "critical";

export interface MockDevice {
  id: string;
  displayName: string;
  stablePath: string | null;
  physicalPath: string | null;
  serial: string | null;
  vendor: string;
  model: string;
  sizeBytes: number;
  removable: boolean;
  systemDisk: boolean;
  readOnly: boolean;
  bus: string;
  partitionCount: number;
  identityFingerprint: string;
  riskLevel: RiskLevel;
  warnings: string[];
  mock: true;
}

export interface DeviceListResponse {
  devices: MockDevice[];
  count: number;
  source: "mock";
  timestamp: string;
}
