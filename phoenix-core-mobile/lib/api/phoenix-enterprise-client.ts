/**
 * Phoenix Core Enterprise API Client
 * Connects the mobile app to the Phoenix Core Enterprise backend
 * Provides real-time device detection, monitoring, and control
 */

import axios, { AxiosInstance } from 'axios';
import AsyncStorage from '@react-native-async-storage/async-storage';

export interface StorageDevice {
  device_id: string;
  device_name: string;
  device_type: 'usb' | 'ssd' | 'hdd' | 'nvme' | 'vdd' | 'sd_card';
  vendor: string;
  model: string;
  serial_number: string;
  size_bytes: number;
  used_bytes: number;
  free_bytes: number;
  status: 'mounted' | 'unmounted' | 'disconnected';
  mount_point?: string;
  removable: boolean;
  read_only: boolean;
  health_status: 'healthy' | 'warning' | 'critical';
  temperature?: number;
  smart_data?: Record<string, any>;
}

export interface SystemMetrics {
  cpu_percent: number;
  memory_percent: number;
  memory_available_mb: number;
  memory_total_mb: number;
  disk_percent: number;
  disk_free_gb: number;
  disk_total_gb: number;
  uptime_seconds: number;
  timestamp: string;
}

export interface HardwareProfile {
  cpu_model: string;
  cpu_cores: number;
  cpu_threads: number;
  cpu_frequency_ghz: number;
  ram_gb: number;
  disk_total_gb: number;
  gpu_model?: string;
  os_name: string;
  os_version: string;
  hostname: string;
  architecture: string;
}

export interface StorageSummary {
  total_devices: number;
  usb_devices: number;
  ssd_devices: number;
  hdd_devices: number;
  nvme_devices: number;
  vdd_devices: number;
  capacity: {
    total_bytes: number;
    used_bytes: number;
    free_bytes: number;
  };
  devices: StorageDevice[];
}

export interface BuildJob {
  job_id: string;
  status: 'pending' | 'running' | 'completed' | 'failed' | 'cancelled';
  recipe_id: string;
  device_id: string;
  progress_percent: number;
  current_step: string;
  estimated_time_remaining: number;
  created_at: string;
  started_at?: string;
  completed_at?: string;
  error_message?: string;
}

export interface Recipe {
  recipe_id: string;
  name: string;
  description: string;
  os_name: string;
  os_version: string;
  image_url?: string;
  image_size_mb: number;
  estimated_write_time_seconds: number;
  supported_devices: string[];
}

class PhoenixEnterpriseClient {
  private api: AxiosInstance;
  private backendUrl: string;
  private authToken: string | null = null;

  constructor(backendUrl: string = 'http://localhost:8000') {
    this.backendUrl = backendUrl;
    this.api = axios.create({
      baseURL: `${backendUrl}/api`,
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Add request interceptor for auth token
    this.api.interceptors.request.use(
      async (config) => {
        const token = await this.getAuthToken();
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      },
      (error) => Promise.reject(error)
    );
  }

  /**
   * Set the backend URL for remote connections
   */
  public setBackendUrl(url: string): void {
    this.backendUrl = url;
    this.api.defaults.baseURL = `${url}/api`;
  }

  /**
   * Get the current backend URL
   */
  public getBackendUrl(): string {
    return this.backendUrl;
  }

  /**
   * Store auth token locally
   */
  private async setAuthToken(token: string): Promise<void> {
    this.authToken = token;
    await AsyncStorage.setItem('phoenix_auth_token', token);
  }

  /**
   * Retrieve stored auth token
   */
  private async getAuthToken(): Promise<string | null> {
    if (this.authToken) {
      return this.authToken;
    }
    const token = await AsyncStorage.getItem('phoenix_auth_token');
    if (token) {
      this.authToken = token;
    }
    return token;
  }

  /**
   * Clear auth token
   */
  public async clearAuthToken(): Promise<void> {
    this.authToken = null;
    await AsyncStorage.removeItem('phoenix_auth_token');
  }

  /**
   * Health check - verify backend is running
   */
  public async healthCheck(): Promise<{ status: string; version: string }> {
    const response = await this.api.get('/health');
    return response.data;
  }

  /**
   * Get system status
   */
  public async getSystemStatus(): Promise<{ status: string; uptime: number }> {
    const response = await this.api.get('/status');
    return response.data;
  }

  /**
   * Get all storage devices
   */
  public async getAllDevices(): Promise<StorageDevice[]> {
    const response = await this.api.get('/storage/devices');
    return response.data.devices || [];
  }

  /**
   * Get USB drives only
   */
  public async getUSBDevices(): Promise<StorageDevice[]> {
    const response = await this.api.get('/storage/devices/usb');
    return response.data.devices || [];
  }

  /**
   * Get SSDs only
   */
  public async getSSDDevices(): Promise<StorageDevice[]> {
    const response = await this.api.get('/storage/devices/ssd');
    return response.data.devices || [];
  }

  /**
   * Get HDDs only
   */
  public async getHDDDevices(): Promise<StorageDevice[]> {
    const response = await this.api.get('/storage/devices/hdd');
    return response.data.devices || [];
  }

  /**
   * Get virtual disks only
   */
  public async getVirtualDevices(): Promise<StorageDevice[]> {
    const response = await this.api.get('/storage/devices/vdd');
    return response.data.devices || [];
  }

  /**
   * Get storage summary
   */
  public async getStorageSummary(): Promise<StorageSummary> {
    const response = await this.api.get('/storage/summary');
    return response.data;
  }

  /**
   * Mount a device
   */
  public async mountDevice(deviceId: string): Promise<{ success: boolean; mount_point?: string }> {
    const response = await this.api.post(`/storage/devices/${deviceId}/mount`);
    return response.data;
  }

  /**
   * Unmount a device
   */
  public async unmountDevice(deviceId: string): Promise<{ success: boolean }> {
    const response = await this.api.post(`/storage/devices/${deviceId}/unmount`);
    return response.data;
  }

  /**
   * Erase and format a device
   */
  public async eraseDevice(deviceId: string, filesystem: string = 'ext4'): Promise<{ success: boolean; job_id: string }> {
    const response = await this.api.post(`/storage/devices/${deviceId}/erase`, { filesystem });
    return response.data;
  }

  /**
   * Get system metrics
   */
  public async getSystemMetrics(): Promise<SystemMetrics> {
    const response = await this.api.get('/system/metrics');
    return response.data;
  }

  /**
   * Get hardware profile
   */
  public async getHardwareProfile(): Promise<HardwareProfile> {
    const response = await this.api.get('/hardware');
    return response.data;
  }

  /**
   * Get system information
   */
  public async getSystemInfo(): Promise<Record<string, any>> {
    const response = await this.api.get('/system/info');
    return response.data;
  }

  /**
   * Get available recipes
   */
  public async getRecipes(): Promise<Recipe[]> {
    const response = await this.api.get('/recipes');
    return response.data.recipes || [];
  }

  /**
   * Get specific recipe details
   */
  public async getRecipe(recipeId: string): Promise<Recipe> {
    const response = await this.api.get(`/recipes/${recipeId}`);
    return response.data;
  }

  /**
   * Perform safety check before build
   */
  public async safetyCheck(deviceId: string, recipeId: string): Promise<{ safe: boolean; warnings: string[]; errors: string[] }> {
    const response = await this.api.post('/safety-check', { device_id: deviceId, recipe_id: recipeId });
    return response.data;
  }

  /**
   * Start a USB build job
   */
  public async startBuild(deviceId: string, recipeId: string): Promise<BuildJob> {
    const response = await this.api.post('/build/start', { device_id: deviceId, recipe_id: recipeId });
    return response.data;
  }

  /**
   * Get build job progress
   */
  public async getBuildProgress(jobId: string): Promise<BuildJob> {
    const response = await this.api.get(`/build/${jobId}/progress`);
    return response.data;
  }

  /**
   * Cancel a build job
   */
  public async cancelBuild(jobId: string): Promise<{ success: boolean }> {
    const response = await this.api.post(`/build/${jobId}/cancel`);
    return response.data;
  }

  /**
   * Get all build jobs
   */
  public async getBuildJobs(): Promise<BuildJob[]> {
    const response = await this.api.get('/build/jobs');
    return response.data.jobs || [];
  }

  /**
   * Get specific build job details
   */
  public async getBuildJob(jobId: string): Promise<BuildJob> {
    const response = await this.api.get(`/build/${jobId}`);
    return response.data;
  }

  /**
   * Stream real-time updates (WebSocket)
   */
  public subscribeToUpdates(callback: (data: any) => void): () => void {
    const wsUrl = this.backendUrl.replace('http', 'ws');
    const ws = new WebSocket(`${wsUrl}/api/ws`);

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        callback(data);
      } catch (error) {
        console.error('Failed to parse WebSocket message:', error);
      }
    };

    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };

    // Return unsubscribe function
    return () => {
      if (ws.readyState === WebSocket.OPEN) {
        ws.close();
      }
    };
  }
}

// Export singleton instance
export const phoenixClient = new PhoenixEnterpriseClient();

export default PhoenixEnterpriseClient;
