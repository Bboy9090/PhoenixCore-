/**
 * Phoenix Core mobile client — talks to the FastAPI backend (`backend/main.py`)
 * running on the operator's machine (same LAN). USB creation executes on that host,
 * not on the phone.
 *
 * Set EXPO_PUBLIC_API_URL to your backend base URL, e.g. http://192.168.1.10:8000
 */

import AsyncStorage from '@react-native-async-storage/async-storage';

import { API_BASE_URL } from '../config';

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
  smart_data?: Record<string, unknown>;
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
  failure_stage?: string;
  rollback_available?: boolean;
  preflight_note?: string;
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

export interface SafetyCheckResult {
  safe: boolean;
  warnings: string[];
  errors: string[];
  confirmation_token?: string;
  risk_level?: string;
  device_risk?: Record<string, unknown>;
  schema_version?: string;
}

export interface HostCapabilities {
  destructiveUsbWriteNative: boolean;
  raw: Record<string, unknown>;
}

type BackendDevice = {
  id?: string;
  path: string;
  name?: string;
  friendly_name?: string;
  size_bytes?: number;
  vendor?: string | null;
  model?: string | null;
  serial?: string | null;
  removable?: boolean;
  mount_point?: string | null;
  health_status?: string;
  risk_level?: string;
};

function mapBackendDevice(d: BackendDevice): StorageDevice {
  const size = d.size_bytes ?? 0;
  const removable = d.removable ?? false;
  let deviceType: StorageDevice['device_type'] = 'hdd';
  if (removable) deviceType = 'usb';
  const path = d.path || '';
  const nameLower = `${path} ${d.name || ''} ${d.model || ''}`.toLowerCase();
  if (nameLower.includes('nvme')) deviceType = 'nvme';

  return {
    device_id: d.path,
    device_name: d.friendly_name || d.name || d.path,
    device_type: deviceType,
    vendor: d.vendor || '',
    model: d.model || '',
    serial_number: d.serial || '',
    size_bytes: size,
    used_bytes: 0,
    free_bytes: size,
    status: d.mount_point ? 'mounted' : 'unmounted',
    mount_point: d.mount_point || undefined,
    removable,
    read_only: false,
    health_status:
      d.health_status === 'warning' || d.risk_level === 'high'
        ? 'warning'
        : d.risk_level === 'critical'
          ? 'critical'
          : 'healthy',
  };
}

function mapRecipe(r: Record<string, unknown>): Recipe {
  const id = String(r.id ?? r.recipe_id ?? '');
  const reqGb = Number(r.required_size_gb ?? 8);
  const estMin = Number(r.estimated_time_minutes ?? 15);
  return {
    recipe_id: id,
    name: String(r.name ?? id),
    description: String(r.description ?? ''),
    os_name: String(r.os_type ?? 'custom'),
    os_version: '',
    image_size_mb: Math.ceil(reqGb * 1024),
    estimated_write_time_seconds: estMin * 60,
    supported_devices: ['usb'],
  };
}

function mapJobStatus(s: string): BuildJob['status'] {
  switch (s) {
    case 'complete':
      return 'completed';
    case 'failed':
      return 'failed';
    case 'cancelled':
      return 'cancelled';
    case 'idle':
    case 'preparing':
    case 'formatting':
    case 'writing':
    case 'verifying':
    case 'patching':
      return 'running';
    default:
      return 'running';
  }
}

class PhoenixEnterpriseClient {
  private backendUrl: string;
  private authToken: string | null = null;
  /** Last token from safety check — required for startBuild */
  private lastConfirmationToken: string | null = null;
  private lastCapabilities: HostCapabilities | null = null;

  constructor(backendUrl?: string) {
    this.backendUrl = (backendUrl || API_BASE_URL).replace(/\/$/, '');
  }

  public setBackendUrl(url: string): void {
    this.backendUrl = url.replace(/\/$/, '');
  }

  public getBackendUrl(): string {
    return this.backendUrl;
  }

  private async request<T>(
    method: string,
    path: string,
    body?: Record<string, unknown>
  ): Promise<T> {
    const url = `${this.backendUrl}${path}`;
    const headers: Record<string, string> = {
      Accept: 'application/json',
    };
    const token = await this.getAuthToken();
    if (token) headers.Authorization = `Bearer ${token}`;
    if (body) headers['Content-Type'] = 'application/json';

    const res = await fetch(url, {
      method,
      headers,
      body: body ? JSON.stringify(body) : undefined,
    });

    const text = await res.text();
    if (!res.ok) {
      let detail = text;
      try {
        const j = JSON.parse(text) as { detail?: string };
        if (j.detail) detail = typeof j.detail === 'string' ? j.detail : JSON.stringify(j.detail);
      } catch {
        /* keep text */
      }
      throw new Error(detail || `HTTP ${res.status}`);
    }
    if (!text) return {} as T;
    return JSON.parse(text) as T;
  }

  private async setAuthToken(token: string): Promise<void> {
    this.authToken = token;
    await AsyncStorage.setItem('phoenix_auth_token', token);
  }

  private async getAuthToken(): Promise<string | null> {
    if (this.authToken) return this.authToken;
    const token = await AsyncStorage.getItem('phoenix_auth_token');
    if (token) this.authToken = token;
    return token;
  }

  public async clearAuthToken(): Promise<void> {
    this.authToken = null;
    await AsyncStorage.removeItem('phoenix_auth_token');
  }

  public async healthCheck(): Promise<{ status: string; version?: string }> {
    return this.request('GET', '/api/health');
  }

  /** Cached from last refreshCapabilities(); use for gating USB build UI. */
  public getLastCapabilities(): HostCapabilities | null {
    return this.lastCapabilities;
  }

  public async refreshCapabilities(): Promise<HostCapabilities> {
    const h = await this.request<{
      features?: { destructive_usb_write_native?: boolean };
      capabilities?: { destructive_usb_write_native?: boolean };
    }>('GET', '/api/health');
    const native =
      h.features?.destructive_usb_write_native === true ||
      h.capabilities?.destructive_usb_write_native === true;
    this.lastCapabilities = { destructiveUsbWriteNative: native, raw: h as Record<string, unknown> };
    return this.lastCapabilities;
  }

  public async getSystemStatus(): Promise<{ status: string; uptime?: number }> {
    const h = await this.healthCheck();
    return { status: h.status, uptime: 0 };
  }

  public async getAllDevices(): Promise<StorageDevice[]> {
    const data = await this.request<{ devices: BackendDevice[] }>('GET', '/api/devices');
    return (data.devices || []).map(mapBackendDevice);
  }

  /** USB workflow: server-side removable_only filter (stricter than client-side filter). */
  public async getUSBDevices(): Promise<StorageDevice[]> {
    const data = await this.request<{ devices: BackendDevice[] }>(
      'GET',
      '/api/devices?removable_only=true'
    );
    return (data.devices || []).map(mapBackendDevice);
  }

  public async getSSDDevices(): Promise<StorageDevice[]> {
    return [];
  }

  public async getHDDDevices(): Promise<StorageDevice[]> {
    const all = await this.getAllDevices();
    return all.filter((d) => !d.removable);
  }

  public async getVirtualDevices(): Promise<StorageDevice[]> {
    return [];
  }

  public async getStorageSummary(): Promise<StorageSummary> {
    const devices = await this.getAllDevices();
    const usb = devices.filter((d) => d.removable);
    const totalBytes = devices.reduce((s, d) => s + d.size_bytes, 0);
    return {
      total_devices: devices.length,
      usb_devices: usb.length,
      ssd_devices: 0,
      hdd_devices: devices.filter((d) => !d.removable).length,
      nvme_devices: devices.filter((d) => d.device_type === 'nvme').length,
      vdd_devices: 0,
      capacity: {
        total_bytes: totalBytes,
        used_bytes: 0,
        free_bytes: totalBytes,
      },
      devices,
    };
  }

  public async mountDevice(_deviceId: string): Promise<{ success: boolean; mount_point?: string }> {
    throw new Error(
      'Mount is not exposed on the Phoenix Core API. Eject or manage volumes on the host machine.'
    );
  }

  public async unmountDevice(_deviceId: string): Promise<{ success: boolean }> {
    throw new Error(
      'Unmount is not exposed on the Phoenix Core API. Manage volumes on the host machine.'
    );
  }

  public async eraseDevice(_deviceId: string, _filesystem?: string): Promise<{ success: boolean; job_id: string }> {
    throw new Error(
      'Use Bootable USB creation (with safety checks) instead of a raw erase API.'
    );
  }

  public async getSystemMetrics(): Promise<SystemMetrics> {
    const m = await this.request<Record<string, number | string | null>>('GET', '/api/system/metrics');
    const memTotal = Number(m.memory_total_bytes ?? 0);
    const memUsed = Number(m.memory_used_bytes ?? 0);
    return {
      cpu_percent: Number(m.cpu_percent ?? 0),
      memory_percent: Number(m.memory_percent ?? 0),
      memory_available_mb: Math.round((memTotal - memUsed) / (1024 * 1024)),
      memory_total_mb: Math.round(memTotal / (1024 * 1024)),
      disk_percent: Number(m.disk_usage_percent ?? 0),
      disk_free_gb: 0,
      disk_total_gb: 0,
      uptime_seconds: Number(m.uptime_seconds ?? 0),
      timestamp: String(m.timestamp ?? new Date().toISOString()),
    };
  }

  public async getHardwareProfile(): Promise<HardwareProfile> {
    const h = await this.request<Record<string, unknown>>('GET', '/api/hardware');
    const cpu = (h.cpu as Record<string, unknown>) || {};
    const mem = (h.memory as Record<string, unknown>) || {};
    const totalMem = Number(mem.total_bytes ?? 0);
    return {
      cpu_model: String(cpu.name ?? 'Unknown'),
      cpu_cores: Number(cpu.cores_physical ?? 1),
      cpu_threads: Number(cpu.cores_logical ?? 1),
      cpu_frequency_ghz: Number(cpu.frequency_mhz ?? 0) / 1000,
      ram_gb: Math.round(totalMem / (1024 ** 3)),
      disk_total_gb: 0,
      os_name: String(h.platform ?? ''),
      os_version: String(h.platform_version ?? ''),
      hostname: '',
      architecture: String(h.architecture ?? ''),
    };
  }

  public async getSystemInfo(): Promise<Record<string, unknown>> {
    return this.request('GET', '/api/system/info');
  }

  public async getRecipes(): Promise<Recipe[]> {
    const data = await this.request<{ recipes: Record<string, unknown>[] }>('GET', '/api/recipes');
    return (data.recipes || []).map(mapRecipe);
  }

  public async getRecipe(recipeId: string): Promise<Recipe> {
    const r = await this.request<Record<string, unknown>>('GET', `/api/recipes/${encodeURIComponent(recipeId)}`);
    return mapRecipe(r);
  }

  public async safetyCheck(deviceId: string, recipeId: string): Promise<SafetyCheckResult> {
    const data = await this.request<{
      safe_to_proceed?: boolean;
      warnings?: string[];
      errors?: string[];
      confirmation_token?: string;
      risk_level?: string;
      device_risk?: Record<string, unknown>;
      schema_version?: string;
    }>('POST', '/api/safety-check', {
      device_path: deviceId,
      recipe_id: recipeId,
    });
    const token = data.confirmation_token || '';
    this.lastConfirmationToken = token || null;
    return {
      safe: Boolean(data.safe_to_proceed),
      warnings: data.warnings || [],
      errors: data.errors || [],
      confirmation_token: token,
      risk_level: data.risk_level,
      device_risk: data.device_risk,
      schema_version: data.schema_version,
    };
  }

  public async startBuild(deviceId: string, recipeId: string): Promise<BuildJob> {
    const token = this.lastConfirmationToken;
    if (!token || !token.startsWith('PHX-')) {
      throw new Error('Run safety check first — no valid confirmation token.');
    }
    const data = await this.request<{
      job_id: string;
      status?: string;
      message?: string;
    }>('POST', '/api/build/start', {
      recipe_id: recipeId,
      target_device_path: deviceId,
      dry_run: false,
      confirmation_token: token,
    });
    const recipe = await this.getRecipe(recipeId).catch(() => null);
    const eta = recipe?.estimated_write_time_seconds ?? 600;
    return {
      job_id: data.job_id,
      status: 'running',
      recipe_id: recipeId,
      device_id: deviceId,
      progress_percent: 0,
      current_step: 'Initializing',
      estimated_time_remaining: eta,
      created_at: new Date().toISOString(),
    };
  }

  public async getBuildProgress(jobId: string): Promise<BuildJob> {
    const p = await this.request<{
      job_id: string;
      status: string;
      progress_percent: number;
      current_step: string;
      elapsed_seconds?: number;
      error?: string | null;
      failure_stage?: string | null;
      rollback_available?: boolean;
      preflight?: { note?: string };
    }>('GET', `/api/build/${encodeURIComponent(jobId)}/progress`);

    const st = mapJobStatus(p.status);
    return {
      job_id: p.job_id,
      status: st,
      recipe_id: '',
      device_id: '',
      progress_percent: Math.round(p.progress_percent ?? 0),
      current_step: p.current_step || '',
      estimated_time_remaining: 0,
      created_at: '',
      error_message: p.error || undefined,
      failure_stage: p.failure_stage || undefined,
      rollback_available: p.rollback_available === true,
      preflight_note: p.preflight && typeof p.preflight === 'object' ? String(p.preflight.note || '') : undefined,
    };
  }

  public async cancelBuild(jobId: string): Promise<{ success: boolean }> {
    await this.request('POST', `/api/build/${encodeURIComponent(jobId)}/cancel`);
    return { success: true };
  }

  public async getBuildJobs(): Promise<BuildJob[]> {
    const data = await this.request<{ jobs: Array<Record<string, unknown>> }>('GET', '/api/build/jobs/list');
    return (data.jobs || []).map((j) => ({
      job_id: String(j.job_id ?? ''),
      status: mapJobStatus(String(j.status ?? 'running')),
      recipe_id: String(j.recipe_id ?? ''),
      device_id: String(j.target_device ?? ''),
      progress_percent: Number(j.progress_percent ?? 0),
      current_step: '',
      estimated_time_remaining: 0,
      created_at: '',
    }));
  }

  public async getBuildJob(jobId: string): Promise<BuildJob> {
    return this.getBuildProgress(jobId);
  }

  public subscribeToUpdates(_callback: (data: unknown) => void): () => void {
    return () => {};
  }
}

export const phoenixClient = new PhoenixEnterpriseClient();

export default PhoenixEnterpriseClient;
