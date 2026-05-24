import { describe, it, expect, beforeEach, vi } from 'vitest';
import { useSystemStore } from '@stores/systemStore';
import { systemService } from '@services/systemService';

// Mock Tauri invoke
vi.mock('@tauri-apps/api/tauri', () => ({
  invoke: vi.fn(),
}));

describe('System Store', () => {
  beforeEach(() => {
    // Reset store before each test
    useSystemStore.setState({
      systemInfo: null,
      diskInfo: null,
      processes: null,
      cpuUsage: 0,
      memoryUsage: 0,
      isLoading: false,
      error: null,
    });
  });

  it('should initialize with default state', () => {
    const store = useSystemStore.getState();
    expect(store.systemInfo).toBeNull();
    expect(store.cpuUsage).toBe(0);
    expect(store.memoryUsage).toBe(0);
    expect(store.isLoading).toBe(false);
    expect(store.error).toBeNull();
  });

  it('should set system info', () => {
    const store = useSystemStore.getState();
    const mockInfo = {
      hostname: 'phoenix-desktop',
      osVersion: 'Phoenix OS 2.0',
      kernel: 'Linux 6.1.0',
      uptime: 3600,
      cpuCount: 8,
      cpuModel: 'Intel Core i7',
      totalMemory: 16000000000,
      architecture: 'x86_64',
    };

    store.setSystemInfo(mockInfo);
    const updated = useSystemStore.getState();
    expect(updated.systemInfo).toEqual(mockInfo);
    expect(updated.systemInfo?.hostname).toBe('phoenix-desktop');
  });

  it('should set CPU and memory usage', () => {
    const store = useSystemStore.getState();
    store.setUsage(45.5, 62.3);
    
    const updated = useSystemStore.getState();
    expect(updated.cpuUsage).toBe(45.5);
    expect(updated.memoryUsage).toBe(62.3);
  });

  it('should set loading state', () => {
    const store = useSystemStore.getState();
    store.setLoading(true);
    
    let updated = useSystemStore.getState();
    expect(updated.isLoading).toBe(true);
    
    store.setLoading(false);
    updated = useSystemStore.getState();
    expect(updated.isLoading).toBe(false);
  });

  it('should set error message', () => {
    const store = useSystemStore.getState();
    const errorMsg = 'Failed to fetch system info';
    store.setError(errorMsg);
    
    let updated = useSystemStore.getState();
    expect(updated.error).toBe(errorMsg);
    
    store.setError(null);
    updated = useSystemStore.getState();
    expect(updated.error).toBeNull();
  });

  it('should set disk info', () => {
    const store = useSystemStore.getState();
    const mockDisks = [
      {
        device: '/dev/sda1',
        mountPoint: '/',
        filesystem: 'ext4',
        totalSize: 500000000000,
        usedSize: 250000000000,
        availableSize: 250000000000,
        usagePercent: 50,
        isReadOnly: false,
      },
    ];

    store.setDiskInfo(mockDisks);
    const updated = useSystemStore.getState();
    expect(updated.diskInfo).toEqual(mockDisks);
    expect(updated.diskInfo?.[0].device).toBe('/dev/sda1');
  });

  it('should reset all state', () => {
    const store = useSystemStore.getState();
    store.setUsage(80, 90);
    store.setLoading(true);
    store.setError('Test error');
    
    store.reset();
    const updated = useSystemStore.getState();
    expect(updated.cpuUsage).toBe(0);
    expect(updated.memoryUsage).toBe(0);
    expect(updated.isLoading).toBe(false);
    expect(updated.error).toBeNull();
  });

  it('should handle multiple state updates', () => {
    const store = useSystemStore.getState();
    
    store.setLoading(true);
    store.setUsage(25, 35);
    store.setError(null);
    
    const updated = useSystemStore.getState();
    expect(updated.isLoading).toBe(true);
    expect(updated.cpuUsage).toBe(25);
    expect(updated.memoryUsage).toBe(35);
    expect(updated.error).toBeNull();
  });
});

describe('System Service', () => {
  it('should call get_system_info command', async () => {
    const { invoke } = await import('@tauri-apps/api/tauri');
    const mockInvoke = vi.mocked(invoke);
    
    mockInvoke.mockResolvedValueOnce({
      hostname: 'test-host',
      osVersion: 'Phoenix OS',
      kernel: 'Linux',
      uptime: 1000,
      cpuCount: 4,
      cpuModel: 'Test CPU',
      totalMemory: 8000000000,
      architecture: 'x86_64',
    });

    const result = await systemService.getSystemInfo();
    
    expect(mockInvoke).toHaveBeenCalledWith('get_system_info');
    expect(result.hostname).toBe('test-host');
  });

  it('should call get_cpu_usage command', async () => {
    const { invoke } = await import('@tauri-apps/api/tauri');
    const mockInvoke = vi.mocked(invoke);
    
    mockInvoke.mockResolvedValueOnce(45.5);

    const result = await systemService.getCpuUsage();
    
    expect(mockInvoke).toHaveBeenCalledWith('get_cpu_usage');
    expect(result).toBe(45.5);
  });

  it('should call get_memory_usage command', async () => {
    const { invoke } = await import('@tauri-apps/api/tauri');
    const mockInvoke = vi.mocked(invoke);
    
    mockInvoke.mockResolvedValueOnce(62.3);

    const result = await systemService.getMemoryUsage();
    
    expect(mockInvoke).toHaveBeenCalledWith('get_memory_usage');
    expect(result).toBe(62.3);
  });

  it('should call get_disk_info command', async () => {
    const { invoke } = await import('@tauri-apps/api/tauri');
    const mockInvoke = vi.mocked(invoke);
    
    mockInvoke.mockResolvedValueOnce([
      {
        device: '/dev/sda1',
        mountPoint: '/',
        filesystem: 'ext4',
        totalSize: 500000000000,
        usedSize: 250000000000,
        availableSize: 250000000000,
        usagePercent: 50,
        isReadOnly: false,
      },
    ]);

    const result = await systemService.getDiskInfo();
    
    expect(mockInvoke).toHaveBeenCalledWith('get_disk_info');
    expect(result).toHaveLength(1);
    expect(result[0].device).toBe('/dev/sda1');
  });

  it('should handle service errors', async () => {
    const { invoke } = await import('@tauri-apps/api/tauri');
    const mockInvoke = vi.mocked(invoke);
    
    mockInvoke.mockRejectedValueOnce(new Error('Service unavailable'));

    await expect(systemService.getSystemInfo()).rejects.toThrow();
  });

  it('should call scan_disk_errors with device parameter', async () => {
    const { invoke } = await import('@tauri-apps/api/tauri');
    const mockInvoke = vi.mocked(invoke);
    
    mockInvoke.mockResolvedValueOnce({
      device: '/dev/sdb1',
      status: 'scanning',
      errors: [],
      warnings: [],
    });

    const result = await systemService.scanDiskErrors('/dev/sdb1');
    
    expect(mockInvoke).toHaveBeenCalledWith('scan_disk_errors', { device: '/dev/sdb1' });
    expect(result.device).toBe('/dev/sdb1');
  });

  it('should call repair_disk with device parameter', async () => {
    const { invoke } = await import('@tauri-apps/api/tauri');
    const mockInvoke = vi.mocked(invoke);
    
    mockInvoke.mockResolvedValueOnce({
      device: '/dev/sdb1',
      success: true,
      message: 'Repair completed',
    });

    const result = await systemService.repairDisk('/dev/sdb1');
    
    expect(mockInvoke).toHaveBeenCalledWith('repair_disk', { device: '/dev/sdb1' });
    expect(result.success).toBe(true);
  });

  it('should call get_hardware_info command', async () => {
    const { invoke } = await import('@tauri-apps/api/tauri');
    const mockInvoke = vi.mocked(invoke);
    
    mockInvoke.mockResolvedValueOnce({
      cpuInfo: 'Intel Core i7 @ 3.6 GHz',
      gpuInfo: ['NVIDIA GeForce RTX 3080'],
      ramInfo: '16 GB (8 GB used)',
      storageInfo: '/: 500 GB / 500 GB',
      biosInfo: 'BIOS v2.0',
    });

    const result = await systemService.getHardwareInfo();
    
    expect(mockInvoke).toHaveBeenCalledWith('get_hardware_info');
    expect(result.cpuInfo).toContain('Intel');
  });
});

describe('System Monitoring Edge Cases', () => {
  it('should handle zero CPU usage', () => {
    const store = useSystemStore.getState();
    store.setUsage(0, 0);
    
    const updated = useSystemStore.getState();
    expect(updated.cpuUsage).toBe(0);
    expect(updated.memoryUsage).toBe(0);
  });

  it('should handle maximum CPU usage', () => {
    const store = useSystemStore.getState();
    store.setUsage(100, 100);
    
    const updated = useSystemStore.getState();
    expect(updated.cpuUsage).toBe(100);
    expect(updated.memoryUsage).toBe(100);
  });

  it('should handle very large memory values', () => {
    const store = useSystemStore.getState();
    const largeMemory = 1099511627776; // 1TB in bytes
    
    const mockInfo = {
      hostname: 'test',
      osVersion: 'Phoenix OS',
      kernel: 'Linux',
      uptime: 0,
      cpuCount: 1,
      cpuModel: 'Test',
      totalMemory: largeMemory,
      architecture: 'x86_64',
    };
    
    store.setSystemInfo(mockInfo);
    const updated = useSystemStore.getState();
    expect(updated.systemInfo?.totalMemory).toBe(largeMemory);
  });

  it('should handle empty disk list', () => {
    const store = useSystemStore.getState();
    store.setDiskInfo([]);
    
    const updated = useSystemStore.getState();
    expect(updated.diskInfo).toEqual([]);
    expect(updated.diskInfo?.length).toBe(0);
  });

  it('should handle concurrent state updates', () => {
    const store = useSystemStore.getState();
    
    // Simulate rapid updates
    store.setUsage(10, 20);
    store.setUsage(20, 30);
    store.setUsage(30, 40);
    
    const updated = useSystemStore.getState();
    expect(updated.cpuUsage).toBe(30);
    expect(updated.memoryUsage).toBe(40);
  });
});
