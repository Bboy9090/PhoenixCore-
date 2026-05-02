/**
 * Bobby's PhoenixDrive API Hooks
 * React hooks for integrating with the backend API
 */

import { useEffect, useState, useCallback, useRef } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';

// Types
export interface HardwareInfo {
  system: {
    manufacturer: string;
    model: string;
    serial_number: string;
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
    modules: Array<any>;
  };
  gpu: Array<any>;
  storage: Array<any>;
  network: Array<any>;
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
  mountpoint: string;
}

export interface Recipe {
  recipe_id: string;
  name: string;
  version: string;
  created_at: string;
  deployment_type: string;
  target_device: {
    device_id: string;
    size_gb: number;
    confirm_erase: boolean;
  };
  partitions: Array<any>;
  os_images: Array<any>;
  tools: Array<any>;
  safety: {
    dry_run: boolean;
    verify_after_write: boolean;
    safety_level: string;
    confirmations_required: number;
  };
}

export interface BuildProgress {
  build_id: string;
  state: string;
  stage: string;
  stage_progress: number;
  overall_progress: number;
  current_operation: string;
  speed_mbps: number;
  eta_seconds: number;
  timestamp: string;
  error_message?: string;
}

// API Configuration
const API_BASE_URL = process.env.EXPO_PUBLIC_API_URL || 'http://localhost:5000';
const API_TIMEOUT = 30000; // 30 seconds

/**
 * Fetch wrapper with timeout and error handling
 */
async function fetchAPI<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), API_TIMEOUT);

  try {
    const response = await fetch(url, {
      ...options,
      signal: controller.signal,
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.message || `API error: ${response.statusText}`);
    }

    return await response.json();
  } finally {
    clearTimeout(timeoutId);
  }
}

/**
 * Hook: Detect system hardware
 */
export function useHardwareDetection() {
  return useQuery({
    queryKey: ['hardware', 'detect'],
    queryFn: async () => {
      const response = await fetchAPI<{
        status: string;
        hardware: HardwareInfo;
        compatible_os: Array<any>;
        incompatible_os: Array<any>;
      }>('/api/v1/hardware/detect', {
        method: 'POST',
        body: JSON.stringify({
          include_storage: true,
          include_network: false,
          timeout_seconds: 30,
        }),
      });

      if (response.status !== 'success') {
        throw new Error('Hardware detection failed');
      }

      return response;
    },
    staleTime: 5 * 60 * 1000, // 5 minutes
    retry: 2,
  });
}

/**
 * Hook: List USB devices
 */
export function useUSBDevices() {
  return useQuery({
    queryKey: ['usb', 'devices'],
    queryFn: async () => {
      const response = await fetchAPI<{
        status: string;
        devices: USBDevice[];
        total_devices: number;
      }>('/api/v1/usb/devices?include_system_drives=false&min_size_gb=4', {
        method: 'GET',
      });

      if (response.status !== 'success') {
        throw new Error('Failed to list USB devices');
      }

      return response.devices;
    },
    staleTime: 30 * 1000, // 30 seconds
    retry: 1,
  });
}

/**
 * Hook: Refresh USB devices
 */
export function useRefreshUSBDevices() {
  const { refetch } = useUSBDevices();

  return useCallback(() => {
    return refetch();
  }, [refetch]);
}

/**
 * Hook: Build recipe
 */
export function useBuildRecipe() {
  return useMutation({
    mutationFn: async (recipeData: {
      name: string;
      deployment_type: string;
      os_selections: string[];
      target_device_id: string;
      target_device_size_gb: number;
      tool_selections: string[];
      partition_scheme: string;
      bootloader_type: string;
      safety_level: string;
    }) => {
      const response = await fetchAPI<{
        status: string;
        recipe: Recipe;
      }>('/api/v1/recipe/build', {
        method: 'POST',
        body: JSON.stringify(recipeData),
      });

      if (response.status !== 'success') {
        throw new Error('Failed to build recipe');
      }

      return response.recipe;
    },
  });
}

/**
 * Hook: Validate recipe
 */
export function useValidateRecipe() {
  return useMutation({
    mutationFn: async (validationData: {
      recipe: Recipe;
      target_device_id: string;
      target_device_size_gb: number;
    }) => {
      const response = await fetchAPI<{
        status: string;
        valid: boolean;
        warnings: Array<any>;
        errors: Array<any>;
        estimated_time: string;
        estimated_size: string;
      }>('/api/v1/recipe/validate', {
        method: 'POST',
        body: JSON.stringify(validationData),
      });

      if (response.status !== 'success') {
        throw new Error('Recipe validation failed');
      }

      return response;
    },
  });
}

/**
 * Hook: Safety check
 */
export function useSafetyCheck() {
  return useMutation({
    mutationFn: async (checkData: {
      recipe: Recipe;
      target_device_id: string;
      target_device_path: string;
    }) => {
      const response = await fetchAPI<{
        status: string;
        safe: boolean;
        checks: Array<{
          name: string;
          status: string;
          message: string;
        }>;
        risk_level: string;
        requires_confirmation: boolean;
      }>('/api/v1/safety/check', {
        method: 'POST',
        body: JSON.stringify(checkData),
      });

      if (response.status !== 'success') {
        throw new Error('Safety check failed');
      }

      return response;
    },
  });
}

/**
 * Hook: Start USB build
 */
export function useStartUSBBuild() {
  return useMutation({
    mutationFn: async (buildData: {
      recipe_id: string;
      device_path: string;
      dry_run: boolean;
    }) => {
      const response = await fetchAPI<{
        status: string;
        build_id: string;
        recipe_id: string;
        started_at: string;
        estimated_duration_minutes: number;
        ws_url: string;
      }>('/api/v1/usb/build', {
        method: 'POST',
        body: JSON.stringify(buildData),
      });

      if (response.status !== 'started') {
        throw new Error('Failed to start build');
      }

      return response;
    },
  });
}

/**
 * Hook: Get build status
 */
export function useBuildStatus(buildId: string | null) {
  return useQuery({
    queryKey: ['build', 'status', buildId],
    queryFn: async () => {
      if (!buildId) throw new Error('Build ID required');

      const response = await fetchAPI<{
        status: string;
        build_id: string;
        state: string;
        stage: string;
        stage_progress: number;
        overall_progress: number;
        current_operation: string;
        speed_mbps: number;
        eta_seconds: number;
        timestamp: string;
      }>(`/api/v1/usb/build/${buildId}/status`, {
        method: 'GET',
      });

      if (response.status !== 'success') {
        throw new Error('Failed to get build status');
      }

      return response;
    },
    enabled: !!buildId,
    refetchInterval: 2000, // Poll every 2 seconds
    retry: 1,
  });
}

/**
 * Hook: WebSocket build progress
 */
export function useBuildProgress(buildId: string | null) {
  const [progress, setProgress] = useState<BuildProgress | null>(null);
  const [error, setError] = useState<string | null>(null);
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    if (!buildId) return;

    const wsUrl = `${API_BASE_URL.replace('http', 'ws')}/ws/build/${buildId}`;

    try {
      const ws = new WebSocket(wsUrl);

      ws.onopen = () => {
        console.log('WebSocket connected');
        ws.send(JSON.stringify({ type: 'subscribe', buildId }));
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          setProgress(data);
          setError(null);
        } catch (e) {
          console.error('Failed to parse WebSocket message:', e);
        }
      };

      ws.onerror = (event) => {
        setError('WebSocket connection error');
        console.error('WebSocket error:', event);
      };

      ws.onclose = () => {
        console.log('WebSocket disconnected');
      };

      wsRef.current = ws;

      return () => {
        if (wsRef.current) {
          wsRef.current.close();
        }
      };
    } catch (e) {
      setError(`Failed to connect WebSocket: ${String(e)}`);
    }
  }, [buildId]);

  return { progress, error };
}

/**
 * Hook: Health check
 */
export function useAPIHealth() {
  return useQuery({
    queryKey: ['api', 'health'],
    queryFn: async () => {
      const response = await fetchAPI<{
        status: string;
        version: string;
        phoenix_core_available: boolean;
        timestamp: string;
      }>('/api/v1/health', {
        method: 'GET',
      });

      return response;
    },
    staleTime: 60 * 1000, // 1 minute
    retry: 2,
  });
}

/**
 * Hook: API error handler
 */
export function useAPIError(error: Error | null) {
  const [message, setMessage] = useState<string>('');

  useEffect(() => {
    if (error) {
      if (error.message.includes('Failed to fetch')) {
        setMessage('Cannot connect to backend API. Make sure the server is running.');
      } else if (error.message.includes('timeout')) {
        setMessage('Request timed out. Please try again.');
      } else {
        setMessage(error.message);
      }
    } else {
      setMessage('');
    }
  }, [error]);

  return message;
}
