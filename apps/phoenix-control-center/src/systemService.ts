import { invoke } from './lib/bridge';
import { SystemInfo, DiskInfo, ProcessInfo, NetworkInterface, HardwareInfo } from './system';

/**
 * System Service - Communicates with Tauri backend for system operations
 */

export const systemService = {
  /**
   * Get system information
   */
  async getSystemInfo(): Promise<SystemInfo> {
    try {
      return await invoke('get_system_info');
    } catch (error) {
      console.error('Failed to get system info:', error);
      throw error;
    }
  },

  /**
   * Get disk information
   */
  async getDiskInfo(): Promise<DiskInfo[]> {
    try {
      return await invoke('get_disk_info');
    } catch (error) {
      console.error('Failed to get disk info:', error);
      throw error;
    }
  },

  /**
   * Get running processes
   */
  async getProcesses(): Promise<ProcessInfo[]> {
    try {
      return await invoke('get_processes');
    } catch (error) {
      console.error('Failed to get processes:', error);
      throw error;
    }
  },

  /**
   * Get CPU usage percentage
   */
  async getCpuUsage(): Promise<number> {
    try {
      return await invoke('get_cpu_usage');
    } catch (error) {
      console.error('Failed to get CPU usage:', error);
      throw error;
    }
  },

  /**
   * Get memory usage percentage
   */
  async getMemoryUsage(): Promise<number> {
    try {
      return await invoke('get_memory_usage');
    } catch (error) {
      console.error('Failed to get memory usage:', error);
      throw error;
    }
  },

  /**
   * Get network interfaces
   */
  async getNetworkInterfaces(): Promise<NetworkInterface[]> {
    try {
      return await invoke('get_network_interfaces');
    } catch (error) {
      console.error('Failed to get network interfaces:', error);
      throw error;
    }
  },

  /**
   * Get hardware information
   */
  async getHardwareInfo(): Promise<HardwareInfo> {
    try {
      return await invoke('get_hardware_info');
    } catch (error) {
      console.error('Failed to get hardware info:', error);
      throw error;
    }
  },

  /**
   * Scan for disk errors
   */
  async scanDiskErrors(device: string): Promise<{ errors: string[]; status: string }> {
    try {
      return await invoke('scan_disk_errors', { device });
    } catch (error) {
      console.error('Failed to scan disk errors:', error);
      throw error;
    }
  },

  /**
   * Repair disk
   */
  async repairDisk(device: string): Promise<{ success: boolean; message: string }> {
    try {
      return await invoke('repair_disk', { device });
    } catch (error) {
      console.error('Failed to repair disk:', error);
      throw error;
    }
  },

  /**
   * Create system recovery point
   */
  async createRecoveryPoint(name: string, description: string): Promise<{ id: string; status: string }> {
    try {
      return await invoke('create_recovery_point', { name, description });
    } catch (error) {
      console.error('Failed to create recovery point:', error);
      throw error;
    }
  },

  /**
   * Restore from recovery point
   */
  async restoreRecoveryPoint(id: string): Promise<{ success: boolean; message: string }> {
    try {
      return await invoke('restore_recovery_point', { id });
    } catch (error) {
      console.error('Failed to restore recovery point:', error);
      throw error;
    }
  },

  /**
   * Get system logs
   */
  async getSystemLogs(lines: number = 100): Promise<string[]> {
    try {
      return await invoke('get_system_logs', { lines });
    } catch (error) {
      console.error('Failed to get system logs:', error);
      throw error;
    }
  },

  /**
   * Clear system cache
   */
  async clearSystemCache(): Promise<{ success: boolean; spacedFreed: number }> {
    try {
      return await invoke('clear_system_cache');
    } catch (error) {
      console.error('Failed to clear system cache:', error);
      throw error;
    }
  },

  /**
   * Optimize system
   */
  async optimizeSystem(): Promise<{ success: boolean; message: string }> {
    try {
      return await invoke('optimize_system');
    } catch (error) {
      console.error('Failed to optimize system:', error);
      throw error;
    }
  },
};
