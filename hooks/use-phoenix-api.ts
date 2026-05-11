/**
 * Hook for interacting with PhoenixCore Industrial Backend API
 * Provides hardware detection, USB device enumeration, recipe building, and build progress tracking
 */

import { useEffect, useState, useCallback } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';

const API_BASE_URL = process.env.EXPO_PUBLIC_API_URL || 'http://localhost:5000/api/v1';

// Types
export interface DetectedHardware {
  system: {
    manufacturer: string;
    model: string;
    serial_number?: string;
  };
  cpu: {
    name: string;
    manufacturer: string;
    architecture: string;
    cores: number;
    threads: number;
  };
  memory: {
    total_gb: number;
    modules: Array<{
      capacity_gb: number;
      speed_mhz?: number;
      manufacturer: string;
    }>;
  };
  gpu: Array<{
    name: string;
    vram_gb: number;
    type: string;
  }>;
  storage: Array<{
    device: string;
    name: string;
    size_gb: number;
    filesystem: string;
    is_removable: boolean;
    health_status: string;
  }>;
  network: Array<{
    name: string;
    type: string;
    mac_address: string;
  }>;
}

export interface HardwareDetectionResponse {
  status: 'success' | 'error';
  device_id: string;
  detected_at: string;
  hardware: DetectedHardware;
  platform: {
    os: string;
    version: string;
    architecture: string;
    bios_mode: string;
  };
  detection_confidence: string;
  compatible_os: string[];
  incompatible_os: string[];
  incompatible_reason: string;
}

export interface USBDevice {
  device_id: string;
  path: string;
  name: string;
  size_gb: number;
  filesystem: string;
  vendor: string;
  model: string;
  serial: string;
  is_removable: boolean;
  health_status: string;
  write_speed_mbps: number;
  mountpoint?: string;
}

export interface DeploymentRecipe {
  recipe_id: string;
  name: string;
  version: string;
  created_at: string;
  deployment_type: 'SINGLE_BOOT' | 'MULTIBOOT' | 'RECOVERY';
  target_device: {
    device_id: string;
    size_gb: number;
    confirm_erase: boolean;
  };
  partition_scheme: string;
  os_images: Array<{
    image_id: string;
    name: string;
    os_family: string;
    version: string;
    architecture: string;
    size_gb: number;
    status: string;
  }>;
  tools: string[];
  bootloader: {
    type: string;
    boot_mode: string;
    timeout_seconds: number;
  };
  safety: {
    dry_run: boolean;
    verify_after_write: boolean;
    safety_level: string;
    confirmations_required: number;
  };
  metadata: {
    total_size_gb: number;
    estimated_write_time_minutes: number;
    target_platform: string;
    tags: string[];
  };
}

export interface BuildProgress {
  build_id: string;
  state: 'idle' | 'preparing' | 'downloading' | 'writing' | 'verifying' | 'complete' | 'error' | 'cancelled';
  stage: string;
  stage_progress: number;
  overall_progress: number;
  current_operation: string;
  speed_mbps: number;
  eta_seconds: number;
  timestamp: string;
  error_message?: string;
}

// API Functions
const apiCall = async (endpoint: string, options: RequestInit = {}) => {
  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
    ...options,
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.message || `API error: ${response.statusText}`);
  }

  return response.json();
};

export const detectHardware = async (): Promise<HardwareDetectionResponse> => {
  return apiCall('/hardware/detect', {
    method: 'POST',
    body: JSON.stringify({
      include_storage: true,
      include_network: true,
      timeout_seconds: 30,
    }),
  });
};

export const listUSBDevices = async (minSizeGb: number = 4): Promise<USBDevice[]> => {
  const response = await apiCall(`/usb/devices?min_size_gb=${minSizeGb}`);
  return response.devices;
};

export const buildRecipe = async (
  name: string,
  deploymentType: string,
  osSelections: string[],
  toolSelections: string[],
  targetDeviceId: string,
  targetDeviceSizeGb: number,
  partitionScheme?: string,
  bootloaderType?: string,
  safetyLevel?: string
): Promise<DeploymentRecipe> => {
  return apiCall('/recipe/build', {
    method: 'POST',
    body: JSON.stringify({
      name,
      deployment_type: deploymentType,
      os_selections: osSelections,
      tool_selections: toolSelections,
      target_device_id: targetDeviceId,
      target_device_size_gb: targetDeviceSizeGb,
      partition_scheme: partitionScheme || 'HYBRID',
      bootloader_type: bootloaderType || 'GRUB',
      safety_level: safetyLevel || 'STANDARD',
    }),
  });
};

export const startUSBBuild = async (
  recipeId: string,
  devicePath: string,
  dryRun?: boolean,
  verifyAfterWrite?: boolean
): Promise<{ build_id: string; status: string; estimated_duration_minutes: number }> => {
  return apiCall('/usb/build', {
    method: 'POST',
    body: JSON.stringify({
      recipe_id: recipeId,
      device_path: devicePath,
      dry_run: dryRun || false,
      verify_after_write: verifyAfterWrite !== false,
    }),
  });
};

export const getBuildStatus = async (buildId: string): Promise<BuildProgress> => {
  return apiCall(`/usb/build/${buildId}/status`);
};

export const validateSafety = async (
  recipeId: string,
  devicePath: string,
  safetyLevel?: string
): Promise<any> => {
  return apiCall('/safety/validate', {
    method: 'POST',
    body: JSON.stringify({
      recipe_id: recipeId,
      device_path: devicePath,
      safety_level: safetyLevel || 'STANDARD',
    }),
  });
};

// React Hooks
export const useHardwareDetection = () => {
  return useQuery({
    queryKey: ['hardware-detection'],
    queryFn: detectHardware,
    staleTime: 60000,
    retry: 2,
  });
};

export const useUSBDevices = (minSizeGb: number = 4) => {
  return useQuery({
    queryKey: ['usb-devices', minSizeGb],
    queryFn: () => listUSBDevices(minSizeGb),
    staleTime: 10000,
    refetchInterval: 5000,
    retry: 1,
  });
};

export const useBuildRecipe = () => {
  return useMutation({
    mutationFn: ({
      name,
      deploymentType,
      osSelections,
      toolSelections,
      targetDeviceId,
      targetDeviceSizeGb,
      partitionScheme,
      bootloaderType,
      safetyLevel,
    }: {
      name: string;
      deploymentType: string;
      osSelections: string[];
      toolSelections: string[];
      targetDeviceId: string;
      targetDeviceSizeGb: number;
      partitionScheme?: string;
      bootloaderType?: string;
      safetyLevel?: string;
    }) =>
      buildRecipe(
        name,
        deploymentType,
        osSelections,
        toolSelections,
        targetDeviceId,
        targetDeviceSizeGb,
        partitionScheme,
        bootloaderType,
        safetyLevel
      ),
  });
};

export const useStartUSBBuild = () => {
  return useMutation({
    mutationFn: ({
      recipeId,
      devicePath,
      dryRun,
      verifyAfterWrite,
    }: {
      recipeId: string;
      devicePath: string;
      dryRun?: boolean;
      verifyAfterWrite?: boolean;
    }) => startUSBBuild(recipeId, devicePath, dryRun, verifyAfterWrite),
  });
};

export const useBuildProgress = (buildId: string | null) => {
  const [progress, setProgress] = useState<BuildProgress | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!buildId) return;

    const pollInterval = setInterval(async () => {
      try {
        const status = await getBuildStatus(buildId);
        setProgress(status);

        if (status.state === 'complete' || status.state === 'error' || status.state === 'cancelled') {
          clearInterval(pollInterval);
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Unknown error');
      }
    }, 1000);

    return () => clearInterval(pollInterval);
  }, [buildId]);

  return { progress, error };
};

export const useSafetyValidation = () => {
  return useMutation({
    mutationFn: ({
      recipeId,
      devicePath,
      safetyLevel,
    }: {
      recipeId: string;
      devicePath: string;
      safetyLevel?: string;
    }) => validateSafety(recipeId, devicePath, safetyLevel),
  });
};
