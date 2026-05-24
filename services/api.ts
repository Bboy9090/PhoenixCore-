/**
 * Phoenix Core API Service
 * Connects the mobile app to the real Phoenix Core backend
 */

import axios, { AxiosInstance, AxiosResponse } from 'axios';

// ─── Types ────────────────────────────────────────────────────────────────────

export interface USBDevice {
  id: string;
  path: string;
  name: string;
  friendly_name: string;
  size_bytes: number;
  size_human: string;
  size_gb: number;
  removable: boolean;
  is_system_disk: boolean;
  vendor?: string;
  model?: string;
  serial?: string;
  filesystem?: string;
  mount_point?: string;
  partitions: PartitionInfo[];
  health_status: string;
  write_speed_mbps?: number;
  risk_level: 'low' | 'medium' | 'high' | 'critical';
}

export interface PartitionInfo {
  id: string;
  label?: string;
  filesystem?: string;
  size_bytes: number;
  size_human: string;
  mount_points: string[];
}

export interface DeviceListResponse {
  devices: USBDevice[];
  total: number;
  scan_time_ms: number;
  host_os: string;
  timestamp: string;
}

export interface LowLevelUSBDevice {
  id: string;
  name: string;
  vendor_id?: number;
  product_id?: number;
  vendor_name?: string;
  manufacturer?: string;
  product_name?: string;
  serial_number?: string;
  platform: string;
  transport: string;
  mode: string;
  recommended_workflow: string;
  usb_version?: string;
  speed?: string;
  platform_path?: string;
  bus_number?: number;
  device_address?: number;
  location_id?: string;
  current_required_ma?: number;
  current_available_ma?: number;
  class_code?: number;
  subclass_code?: number;
  protocol_code?: number;
  raw_source: string;
}

export interface LowLevelUSBListResponse {
  devices: LowLevelUSBDevice[];
  total: number;
  scan_time_ms: number;
  host_os: string;
  timestamp: string;
  detection_mode: string;
  source: string;
}

export interface HardwareProfile {
  system_name: string;
  manufacturer: string;
  model: string;
  platform: string;
  platform_version: string;
  architecture: string;
  cpu: CPUInfo;
  memory: MemoryInfo;
  gpus: GPUInfo[];
  storage: StorageDevice[];
  bios_version?: string;
  serial_number?: string;
  detection_confidence: string;
  oclp_compatible: boolean;
  recommended_os: string[];
}

export interface CPUInfo {
  name: string;
  manufacturer: string;
  architecture: string;
  cores_physical: number;
  cores_logical: number;
  frequency_mhz: number;
  usage_percent: number;
}

export interface MemoryInfo {
  total_bytes: number;
  total_human: string;
  available_bytes: number;
  used_bytes: number;
  percent: number;
}

export interface GPUInfo {
  name: string;
  vendor: string;
  vram_bytes?: number;
}

export interface StorageDevice {
  name: string;
  path: string;
  size_bytes: number;
  size_human: string;
  filesystem?: string;
  mount_point?: string;
  is_removable: boolean;
}

export interface SystemMetrics {
  cpu_percent: number;
  cpu_per_core: number[];
  memory_percent: number;
  memory_used_bytes: number;
  memory_total_bytes: number;
  swap_percent: number;
  disk_usage_percent: number;
  disk_io: DiskIOStats;
  network: NetworkStats;
  temperature?: number;
  uptime_seconds: number;
  load_average: number[];
  process_count: number;
  timestamp: string;
}

export interface DiskIOStats {
  read_bytes: number;
  write_bytes: number;
  read_count: number;
  write_count: number;
}

export interface NetworkStats {
  bytes_sent: number;
  bytes_recv: number;
  packets_sent: number;
  packets_recv: number;
}

export interface BuildRecipe {
  id: string;
  name: string;
  os_type: string;
  description: string;
  required_size_gb: number;
  partition_scheme: string;
  filesystem: string;
  supports_oclp: boolean;
  supports_multiboot: boolean;
  estimated_time_minutes: number;
  steps: string[];
}

export interface SafetyCheckResponse {
  safe_to_proceed: boolean;
  risk_level: string;
  warnings: string[];
  errors: string[];
  confirmation_token: string;
  device_info?: USBDevice;
}

export interface BuildJobResponse {
  job_id: string;
  status: string;
  message: string;
  confirmation_token?: string;
  estimated_time_minutes: number;
}

export interface BuildProgress {
  job_id: string;
  status: string;
  progress_percent: number;
  current_step: string;
  steps_completed: number;
  steps_total: number;
  bytes_written: number;
  bytes_total: number;
  elapsed_seconds: number;
  estimated_remaining_seconds?: number;
  speed_mbps?: number;
  log_messages: string[];
  error?: string;
}

export interface OCLPModel {
  model_id: string;
  name: string;
  max_native_macos: string;
  oclp_max_macos: string;
  required_kexts: string[];
}

export interface OCLPCompatibility {
  model: string;
  compatible: boolean;
  model_name: string;
  max_native_macos: string;
  oclp_max_macos: string;
  supported_macos_versions: string[];
  required_kexts: string[];
  warnings: string[];
  notes: string;
}

export interface OSImage {
  id: string;
  name: string;
  os_type: string;
  version: string;
  architecture: string;
  size_bytes: number;
  size_human: string;
  checksum_sha256?: string;
  download_url?: string;
  local_path?: string;
  verified: boolean;
  description: string;
}

export interface HealthStatus {
  status: string;
  version: string;
  uptime_seconds: number;
  platform: string;
  features: Record<string, boolean>;
  timestamp: string;
}

export interface DiagnosticsResult {
  overall_status: string;
  checks: Record<string, any>;
  platform: string;
  timestamp: string;
}

// ─── API Client ───────────────────────────────────────────────────────────────

class PhoenixCoreAPI {
  private client: AxiosInstance;
  private baseURL: string;

  constructor(baseURL: string = 'http://localhost:8000') {
    this.baseURL = baseURL;
    this.client = axios.create({
      baseURL,
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
        'X-Phoenix-Client': 'mobile/2.0.0',
      },
    });

    // Request interceptor
    this.client.interceptors.request.use(
      (config) => {
        console.log(`[API] ${config.method?.toUpperCase()} ${config.url}`);
        return config;
      },
      (error) => Promise.reject(error)
    );

    // Response interceptor
    this.client.interceptors.response.use(
      (response) => response,
      (error) => {
        const message = error.response?.data?.detail || error.message || 'Unknown error';
        console.error(`[API Error] ${message}`);
        return Promise.reject(new Error(message));
      }
    );
  }

  setBaseURL(url: string) {
    this.baseURL = url;
    this.client.defaults.baseURL = url;
  }

  getBaseURL(): string {
    return this.baseURL;
  }

  // ── Health ──────────────────────────────────────────────────────────────────

  async getHealth(): Promise<HealthStatus> {
    const res = await this.client.get<HealthStatus>('/api/health');
    return res.data;
  }

  async ping(): Promise<boolean> {
    try {
      await this.client.get('/', { timeout: 5000 });
      return true;
    } catch {
      return false;
    }
  }

  // ── Devices ─────────────────────────────────────────────────────────────────

  async listDevices(): Promise<DeviceListResponse> {
    const res = await this.client.get<DeviceListResponse>('/api/devices');
    return res.data;
  }

  async listLowLevelUSBDevices(): Promise<LowLevelUSBListResponse> {
    const res = await this.client.get<LowLevelUSBListResponse>('/api/devices/usb/low-level');
    return res.data;
  }

  async getDevice(deviceId: string): Promise<USBDevice> {
    const res = await this.client.get<USBDevice>(`/api/devices/${deviceId}`);
    return res.data;
  }

  async refreshDevices(): Promise<DeviceListResponse> {
    const res = await this.client.post<DeviceListResponse>('/api/devices/refresh');
    return res.data;
  }

  // ── Hardware ─────────────────────────────────────────────────────────────────

  async getHardwareProfile(): Promise<HardwareProfile> {
    const res = await this.client.get<HardwareProfile>('/api/hardware');
    return res.data;
  }

  async listHardwareProfiles(): Promise<{ profiles: any[]; total: number }> {
    const res = await this.client.get('/api/hardware/profiles');
    return res.data;
  }

  // ── System Monitoring ────────────────────────────────────────────────────────

  async getSystemMetrics(): Promise<SystemMetrics> {
    const res = await this.client.get<SystemMetrics>('/api/system/metrics');
    return res.data;
  }

  async getSystemInfo(): Promise<any> {
    const res = await this.client.get('/api/system/info');
    return res.data;
  }

  async getUSBActivity(): Promise<any> {
    const res = await this.client.get('/api/system/usb-activity');
    return res.data;
  }

  // ── Recipes ──────────────────────────────────────────────────────────────────

  async listRecipes(): Promise<{ recipes: BuildRecipe[]; total: number }> {
    const res = await this.client.get('/api/recipes');
    return res.data;
  }

  async getRecipe(recipeId: string): Promise<BuildRecipe> {
    const res = await this.client.get<BuildRecipe>(`/api/recipes/${recipeId}`);
    return res.data;
  }

  // ── Safety & Build ───────────────────────────────────────────────────────────

  async safetyCheck(devicePath: string, recipeId: string): Promise<SafetyCheckResponse> {
    const res = await this.client.post<SafetyCheckResponse>('/api/safety-check', {
      device_path: devicePath,
      recipe_id: recipeId,
    });
    return res.data;
  }

  async startBuild(params: {
    recipe_id: string;
    target_device_path: string;
    os_image_path?: string;
    dry_run?: boolean;
    confirmation_token?: string;
    oclp_enabled?: boolean;
    oclp_target_model?: string;
    oclp_macos_version?: string;
  }): Promise<BuildJobResponse> {
    const res = await this.client.post<BuildJobResponse>('/api/build/start', params);
    return res.data;
  }

  async getBuildProgress(jobId: string): Promise<BuildProgress> {
    const res = await this.client.get<BuildProgress>(`/api/build/${jobId}/progress`);
    return res.data;
  }

  async cancelBuild(jobId: string): Promise<{ message: string; job_id: string }> {
    const res = await this.client.post(`/api/build/${jobId}/cancel`);
    return res.data;
  }

  async listBuildJobs(): Promise<{ jobs: any[]; total: number }> {
    const res = await this.client.get('/api/build/jobs/list');
    return res.data;
  }

  // ── OCLP ─────────────────────────────────────────────────────────────────────

  async listOCLPModels(): Promise<{ models: OCLPModel[]; total: number }> {
    const res = await this.client.get('/api/oclp/models');
    return res.data;
  }

  async checkOCLPCompatibility(model: string): Promise<OCLPCompatibility> {
    const res = await this.client.get<OCLPCompatibility>(`/api/oclp/check/${model}`);
    return res.data;
  }

  async getMacOSVersions(): Promise<{ versions: { version: string; name: string }[] }> {
    const res = await this.client.get('/api/oclp/macos-versions');
    return res.data;
  }

  async detectMacModel(): Promise<any> {
    const res = await this.client.get('/api/oclp/detect');
    return res.data;
  }

  // ── OS Images ────────────────────────────────────────────────────────────────

  async listOSImages(): Promise<{ images: OSImage[]; total: number }> {
    const res = await this.client.get('/api/images');
    return res.data;
  }

  async getOSImage(imageId: string): Promise<OSImage> {
    const res = await this.client.get<OSImage>(`/api/images/${imageId}`);
    return res.data;
  }

  // ── Workflows ────────────────────────────────────────────────────────────────

  async listWorkflows(): Promise<{ workflows: any[]; total: number }> {
    const res = await this.client.get('/api/workflows');
    return res.data;
  }

  async runWorkflow(params: {
    workflow_id: string;
    device_path: string;
    dry_run?: boolean;
    oclp_enabled?: boolean;
    oclp_target_model?: string;
    oclp_macos_version?: string;
  }): Promise<any> {
    const res = await this.client.post('/api/workflows/run', params);
    return res.data;
  }

  // ── Diagnostics ──────────────────────────────────────────────────────────────

  async runDiagnostics(): Promise<DiagnosticsResult> {
    const res = await this.client.get<DiagnosticsResult>('/api/diagnostics');
    return res.data;
  }
}

// Singleton instance
export const api = new PhoenixCoreAPI();
export default api;
