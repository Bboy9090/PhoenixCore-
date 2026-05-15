/**
 * ARCWYRE System Bridge
 * Provides a safe interface between the frontend and the PhoenixCore host.
 * Falls back to mock data if @tauri-apps/api is unavailable (e.g. in a browser or offline build).
 */

// We use dynamic imports to prevent hard-failing if the package is missing at compile time
let tauriApi: any = null;

async function getTauri() {
  if (tauriApi !== null) return tauriApi;
  try {
    // @ts-ignore - We ignore this because it might be missing in the offline environment
    tauriApi = await import('@tauri-apps/api/tauri');
    return tauriApi;
  } catch (e) {
    console.warn('ARCWYRE Bridge: Tauri API not found, using mock mode.');
    tauriApi = false;
    return false;
  }
}

export async function invoke<T>(command: string, args: Record<string, any> = {}): Promise<T> {
  const tauri = await getTauri();
  if (tauri && tauri.invoke) {
    return tauri.invoke(command, args);
  }

  // MOCK FALLBACKS
  console.log(`[Mock Bridge] Invoking: ${command}`, args);
  
  switch (command) {
    case 'get_build_status':
      return {
        is_running: false,
        is_paused: false,
        stage: 'completed',
        progress: 100,
        total_lines: 1000,
        current_line: 1000,
        elapsed_time: 360,
        estimated_time_remaining: 0,
        iso_path: '/path/to/arcwyre-mock.iso',
        iso_size: 4294967296,
        error_message: null,
        build_id: 'MOCK-STABLE-01'
      } as unknown as T;
    
    case 'get_hardware_info':
      return {
        cpu_info: 'ARCWYRE Hyper-Core (Mocked)',
        gpu_info: ['Forged Graphics Accelerator'],
        ram_info: '32 GB Steel-Memory',
        storage_info: '1 TB Black-Steel NVMe'
      } as unknown as T;

    case 'get_partitions':
      return [
        {
          device: '/dev/sda1',
          mount_point: '/',
          filesystem: 'ext4',
          total_size: 500000000000,
          used_size: 150000000000,
          available_size: 350000000000,
          usage_percent: 30,
          is_read_only: false,
          is_removable: false,
          is_system_disk: true
        }
      ] as unknown as T;

    default:
      return {} as T;
  }
}
