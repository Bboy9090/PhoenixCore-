import { useState, useEffect } from 'react';
import { SystemInfo, DiskInfo, ProcessInfo } from '../system';

interface SystemState {
  systemInfo: SystemInfo | null;
  diskInfo: DiskInfo[] | null;
  processes: ProcessInfo[] | null;
  cpuUsage: number;
  memoryUsage: number;
  isLoading: boolean;
  error: string | null;
}

const initialState: SystemState = {
  systemInfo: null,
  diskInfo: null,
  processes: null,
  cpuUsage: 0,
  memoryUsage: 0,
  isLoading: false,
  error: null,
};

let globalState = { ...initialState };
const listeners = new Set<(state: SystemState) => void>();

const setState = (partial: Partial<SystemState>) => {
  globalState = { ...globalState, ...partial };
  listeners.forEach((listener) => listener(globalState));
};

export const useSystemStore = <T>(selector: (state: SystemState & any) => T): T => {
  const [state, setLocalState] = useState(globalState);

  useEffect(() => {
    const listener = (newState: SystemState) => setLocalState(newState);
    listeners.add(listener);
    return () => {
      listeners.delete(listener);
    };
  }, []);

  const actions = {
    setSystemInfo: (info: SystemInfo) => setState({ systemInfo: info }),
    setDiskInfo: (info: DiskInfo[]) => setState({ diskInfo: info }),
    setProcesses: (processes: ProcessInfo[]) => setState({ processes }),
    setUsage: (cpu: number, memory: number) => setState({ cpuUsage: cpu, memoryUsage: memory }),
    setLoading: (loading: boolean) => setState({ isLoading: loading }),
    setError: (error: string | null) => setState({ error }),
    reset: () => setState(initialState),
  };

  return selector({ ...state, ...actions });
};
