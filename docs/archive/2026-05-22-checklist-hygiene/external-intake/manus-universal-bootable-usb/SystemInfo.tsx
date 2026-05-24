import React, { useEffect, useState } from 'react';
import { systemService } from '@services/systemService';
import { HardwareInfo } from '@types/system';
import { Cpu, HardDrive, Monitor, RefreshCw } from 'lucide-react';
import { SkeletonHardwareCard } from '@components/LoadingSkeleton';
import { ErrorDisplay } from '@components/ErrorBoundary';

export default function SystemInfo() {
  const [hardware, setHardware] = useState<HardwareInfo | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [refreshing, setRefreshing] = useState(false);

  const fetchHardware = async () => {
    try {
      const data = await systemService.getHardwareInfo();
      setHardware(data);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch hardware info');
    }
  };

  useEffect(() => {
    setLoading(true);
    fetchHardware().finally(() => setLoading(false));
  }, []);

  const handleRefresh = async () => {
    setRefreshing(true);
    await fetchHardware();
    setRefreshing(false);
  };

  return (
    <div className="p-8 space-y-8">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-slate-900 dark:text-white">System Information</h1>
          <p className="text-slate-600 dark:text-slate-400 mt-2">Detailed hardware and system details</p>
        </div>
        <button
          onClick={handleRefresh}
          disabled={refreshing || loading}
          className="btn-secondary flex items-center gap-2"
        >
          <RefreshCw size={18} className={refreshing ? 'animate-spin' : ''} />
          Refresh
        </button>
      </div>

      {error && (
        <ErrorDisplay
          error={error}
          onDismiss={() => setError(null)}
        />
      )}

      {loading && !hardware ? (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {Array.from({ length: 4 }).map((_, idx) => (
            <SkeletonHardwareCard key={idx} />
          ))}
        </div>
      ) : hardware ? (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="card">
            <div className="flex items-center gap-3 mb-4">
              <Cpu className="text-phoenix-600" size={24} />
              <h2 className="text-lg font-semibold text-slate-900 dark:text-white">Processor</h2>
            </div>
            <p className="text-slate-600 dark:text-slate-400">{hardware.cpu_info}</p>
          </div>

          <div className="card">
            <div className="flex items-center gap-3 mb-4">
              <Monitor className="text-blue-600" size={24} />
              <h2 className="text-lg font-semibold text-slate-900 dark:text-white">Graphics</h2>
            </div>
            <div className="space-y-2">
              {hardware.gpu_info.map((gpu, idx) => (
                <p key={idx} className="text-slate-600 dark:text-slate-400">{gpu}</p>
              ))}
            </div>
          </div>

          <div className="card">
            <div className="flex items-center gap-3 mb-4">
              <HardDrive className="text-green-600" size={24} />
              <h2 className="text-lg font-semibold text-slate-900 dark:text-white">Memory</h2>
            </div>
            <p className="text-slate-600 dark:text-slate-400">{hardware.ram_info}</p>
          </div>

          <div className="card">
            <div className="flex items-center gap-3 mb-4">
              <HardDrive className="text-orange-600" size={24} />
              <h2 className="text-lg font-semibold text-slate-900 dark:text-white">Storage</h2>
            </div>
            <p className="text-slate-600 dark:text-slate-400">{hardware.storage_info}</p>
          </div>
        </div>
      ) : null}
    </div>
  );
}
