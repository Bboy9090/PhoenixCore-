import {
  getBlockedOperationCatalog,
  REQUIRED_FUTURE_GATES
} from "../policy/blocked-operations";
import type { SafetyPolicy } from "../types/safety";

export function getSafetyPolicy(): SafetyPolicy {
  return {
    previewFirst: true,
    nonDestructiveMockOnly: true,
    systemDisksProtectedByDefault: true,
    explicitDeviceIdentityRequired: true,
    uiAppsMayRequestOnly: true,
    agentOwnsPolicyChecks: true,
    rustSafetyGateRequiredForExecution: true,
    commitEnabled: false,
    requiredFutureGates: [...REQUIRED_FUTURE_GATES]
  };
}

export function getBlockedOperations() {
  const operations = getBlockedOperationCatalog();

  return {
    operations,
    count: operations.length,
    requiredFutureGates: [...REQUIRED_FUTURE_GATES]
  };
}
