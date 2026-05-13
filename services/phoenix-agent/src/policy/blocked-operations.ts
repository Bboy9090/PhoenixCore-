import type { BlockedOperationResponse, OperationCatalogEntry } from "../types/operation";

export const REQUIRED_FUTURE_GATES = Object.freeze([
  "policy approval",
  "Rust safety gate",
  "device fingerprint",
  "preview freshness",
  "audit log",
  "dry-run verification",
  "explicit user confirmation",
  "test coverage"
]);

export const BLOCKED_OPERATION_IDS = Object.freeze([
  "usb.build",
  "usb.erase",
  "disk.erase",
  "disk.mount",
  "disk.unmount",
  "bootcamp.install",
  "oclp.patch",
  "workflow.run",
  "remote.command",
  "bulk.operation",
  "firmware.flash",
  "restore.write"
]);

const BLOCKED_REASONS: Record<string, string> = {
  "usb.build": "USB build is blocked in PR8 because it would write boot media.",
  "usb.erase": "USB erase is blocked in PR8 because it would modify storage media.",
  "disk.erase": "Disk erase is blocked in PR8 because destructive disk mutation is disabled.",
  "disk.mount": "Disk mount is blocked in PR8 because system device mutation is disabled.",
  "disk.unmount": "Disk unmount is blocked in PR8 because system device mutation is disabled.",
  "bootcamp.install": "BootCamp install is blocked in PR8 because driver installation mutates the host.",
  "oclp.patch": "OCLP patching is blocked in PR8 because boot/system patching is disabled.",
  "workflow.run": "Workflow execution is blocked in PR8 because workflows may chain destructive steps.",
  "remote.command": "Remote command execution is blocked in PR8 because fleet trust is not designed.",
  "bulk.operation": "Bulk operations are blocked in PR8 because remote multi-device execution is disabled.",
  "firmware.flash": "Firmware flashing is blocked in PR8 because firmware mutation is high risk.",
  "restore.write": "Restore writes are blocked in PR8 because image writes are destructive."
};

export function isBlockedOperation(operationId: string): boolean {
  return BLOCKED_OPERATION_IDS.includes(operationId);
}

export function createBlockedOperationResponse(operationId: string): BlockedOperationResponse {
  return {
    operationId,
    blocked: true,
    reason:
      BLOCKED_REASONS[operationId] ??
      "Phoenix Agent PR8 rejects commits. This skeleton is preview-only and non-destructive.",
    requiredFutureGates: [...REQUIRED_FUTURE_GATES],
    safeNextStep: "Call /v1/operations/preview and wait for a future safety-backed implementation PR."
  };
}

export function getBlockedOperationCatalog(): OperationCatalogEntry[] {
  return BLOCKED_OPERATION_IDS.map((operationId) => ({
    operationId,
    label: operationId,
    owner:
      operationId.startsWith("bootcamp") || operationId.startsWith("oclp") || operationId.startsWith("usb")
        ? "BootForge"
        : "Phoenix Agent",
    destructive: true,
    previewOnly: true,
    blocked: true,
    requiredFutureGates: [...REQUIRED_FUTURE_GATES],
    safeNextStep: "Use preview only until future gates are implemented."
  }));
}
