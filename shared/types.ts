/**
 * Unified type exports
 * Import shared types from this single entry point.
 */

export type * from "../drizzle/schema";

export type OperationState = 
  | "queued" 
  | "previewing" 
  | "safety_evaluating" 
  | "awaiting_confirmation" 
  | "verified"
  | "executing" 
  | "executing_mock"
  | "progress_streaming" 
  | "verifying" 
  | "reporting" 
  | "completed" 
  | "failed" 
  | "rolled_back" 
  | "cancelled"
  | "blocked";

export type SafetyLevel = 
  | "read_only" 
  | "preview_only" 
  | "removable_only"
  | "internal_restricted"
  | "system_protected"
  | "firmware_adjacent"
  | "recovery_only";

export interface DeviceIdentity {
  vendor: string;
  model: string;
  serial?: string;
  capacity?: number;
  transport: "sata" | "nvme" | "usb" | "sd" | "network" | "internal";
  classification: "removable" | "internal" | "system" | "external";
  safetyClassification: "protected" | "writable" | "restricted" | "recovery_only";
}

export interface OperationMetadata {
  operationId: string;
  actorId: number;
  deviceIdentity: DeviceIdentity;
  targetSummary: string;
  previewSummary: string;
  riskLevel: SafetyLevel;
  timestamp: string;
  auditHash?: string; // TODO: Implement signed hashes in Rust
  rollbackPossible: boolean;
  reportBundleId?: string; // TODO: Map to ReportBundle storage
}
export * from "./_core/errors";
export * from "./sdk";
