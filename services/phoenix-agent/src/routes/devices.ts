import { getMockDevice, listMockDevices, listMockRemovableDevices } from "../mock/mock-devices";
import type { JsonRouteResponse } from "../types/agent";

export function listDevices() {
  return listMockDevices();
}

export function listRemovableDevices() {
  return listMockRemovableDevices();
}

export function getDevice(id: string): JsonRouteResponse {
  const device = getMockDevice(id);

  if (!device) {
    return {
      statusCode: 404,
      body: {
        error: {
          code: "device.not_found",
          message: `Mock device not found: ${id}`,
          severity: "warning"
        }
      }
    };
  }

  return {
    statusCode: 200,
    body: device
  };
}
