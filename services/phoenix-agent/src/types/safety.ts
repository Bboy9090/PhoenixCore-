export interface SafetyPolicy {
  previewFirst: true;
  nonDestructiveMockOnly: true;
  systemDisksProtectedByDefault: true;
  explicitDeviceIdentityRequired: true;
  uiAppsMayRequestOnly: true;
  agentOwnsPolicyChecks: true;
  rustSafetyGateRequiredForExecution: true;
  commitEnabled: false;
  requiredFutureGates: string[];
}
