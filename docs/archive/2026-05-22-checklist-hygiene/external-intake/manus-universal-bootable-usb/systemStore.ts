import { create } from 'zustand';
import { SystemInfo, DiskInfo, ProcessInfo } from '@types/system';

interface SystemStore {
  systemInfo: SystemInfo | null;
  diskInfo: DiskInfo[] | null;
  processes: ProcessInfo[] | null;
  cpuUsage: number;
  memoryUsage: number;
  isLoading: boolean;
  error: string | null;
  
  setSystemInfo: (info: SystemInfo) => void;
  setDiskInfo: (info: DiskInfo[]) => void;
  setProcesses: (processes: ProcessInfo[]) => void;
  setUsage: (cpu: number, memory: number) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  reset: () => void;
}

export const useSystemStore = create<SystemStore>((set) => ({
  systemInfo: null,
  diskInfo: null,
  processes: null,
  cpuUsage: 0,
  memoryUsage: 0,
  isLoading: false,
  error: null,

  setSystemInfo: (info: SystemInfo) => set({ systemInfo: info }),
  setDiskInfo: (info: DiskInfo[]) => set({ diskInfo: info }),
  setProcesses: (processes: ProcessInfo[]) => set({ processes }),
  setUsage: (cpu: number, memory: number) => set({ cpuUsage: cpu, memoryUsage: memory }),
  setLoading: (loading: boolean) => set({ isLoading: loading }),
  setError: (error: string | null) => set({ error }),
  reset: () => set({
    systemInfo: null,
    diskInfo: null,
    processes: null,
    cpuUsage: 0,
    memoryUsage: 0,
    error: null,
  }),
}));
