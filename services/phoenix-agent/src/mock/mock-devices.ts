import type { DeviceListResponse, MockDevice } from "../types/device";

export const MOCK_DEVICES: readonly MockDevice[] = Object.freeze([
  {
    id: "mock-removable-001",
    displayName: "Mock Phoenix USB Candidate",
    stablePath: "/dev/disk/by-id/mock-phoenix-usb-candidate",
    physicalPath: "mock://usb/001",
    serial: "PHX-MOCK-USB-001",
    vendor: "Phoenix",
    model: "Mock Removable Drive",
    sizeBytes: 32_000_000_000,
    removable: true,
    systemDisk: false,
    readOnly: false,
    bus: "usb",
    partitionCount: 1,
    identityFingerprint: "mock-fingerprint-removable-001",
    riskLevel: "medium",
    warnings: ["Mock device only. No real hardware is scanned or mutated."],
    mock: true
  },
  {
    id: "mock-system-001",
    displayName: "Mock Protected System Disk",
    stablePath: "/dev/disk/by-id/mock-protected-system",
    physicalPath: "mock://system/001",
    serial: "PHX-MOCK-SYS-001",
    vendor: "Phoenix",
    model: "Mock System Disk",
    sizeBytes: 512_000_000_000,
    removable: false,
    systemDisk: true,
    readOnly: false,
    bus: "nvme",
    partitionCount: 4,
    identityFingerprint: "mock-fingerprint-system-001",
    riskLevel: "critical",
    warnings: ["System disks are protected by default."],
    mock: true
  }
]);

export function listMockDevices(): DeviceListResponse {
  return {
    devices: [...MOCK_DEVICES],
    count: MOCK_DEVICES.length,
    source: "mock",
    timestamp: new Date().toISOString()
  };
}

export function listMockRemovableDevices(): DeviceListResponse {
  const devices = MOCK_DEVICES.filter((device) => device.removable && !device.systemDisk);

  return {
    devices,
    count: devices.length,
    source: "mock",
    timestamp: new Date().toISOString()
  };
}

export function getMockDevice(id: string): MockDevice | undefined {
  return MOCK_DEVICES.find((device) => device.id === id);
}
