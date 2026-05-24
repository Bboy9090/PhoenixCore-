export interface SystemInfo {
  hostname: string;
  osVersion: string;
  kernel: string;
  uptime: number;
  cpuCount: number;
  cpuModel: string;
  totalMemory: number;
  architecture: string;
}

export interface DiskInfo {
  device: string;
  mountPoint: string;
  filesystem: string;
  totalSize: number;
  usedSize: number;
  availableSize: number;
  usagePercent: number;
  isReadOnly: boolean;
}

export interface ProcessInfo {
  pid: number;
  name: string;
  user: string;
  cpuUsage: number;
  memoryUsage: number;
  status: string;
}

export interface NetworkInterface {
  name: string;
  ipAddress: string;
  macAddress: string;
  status: 'up' | 'down';
  bytesReceived: number;
  bytesSent: number;
}

export interface HardwareInfo {
  cpuInfo: string;
  gpuInfo: string[];
  ramInfo: string;
  storageInfo: string;
  biosInfo: string;
}

export interface RecoveryPoint {
  id: string;
  name: string;
  description: string;
  createdAt: Date;
  size: number;
  type: 'system' | 'user' | 'custom';
}

export interface BackupInfo {
  id: string;
  name: string;
  location: string;
  size: number;
  createdAt: Date;
  status: 'pending' | 'in_progress' | 'completed' | 'failed';
  progress: number;
}

export interface PartitionInfo {
  device: string;
  mount_point: string;
  filesystem: string;
  total_size: number;
  used_size: number;
  available_size: number;
  usage_percent: number;
  is_read_only: boolean;
  is_system_disk: boolean;
  is_removable: boolean;
}

export interface ScanResult {
  device: string;
  status: string;
  errors: string[];
  warnings: string[];
}

export interface RepairResult {
  device: string;
  success: boolean;
  message: string;
}

export interface CacheResult {
  success: boolean;
  space_freed: number;
  message: string;
}
