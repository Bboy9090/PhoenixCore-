import React, { useEffect, useState } from 'react';
import { systemService } from '../../systemService';
import { HardwareInfo } from '../../system';
import { Cpu, HardDrive, Monitor, RefreshCw } from '../Icons';
import { SkeletonHardwareCard } from '../LoadingSkeleton';
import { ErrorDisplay } from '../ErrorBoundary';

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
    <div className="p-8 space-y-8 bg-arc-bg text-arc-silver">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-arc-cyan">ARCWYRE System Information</h1>
          <p className="text-arc-silver/60 mt-2">Detailed hardware and machine diagnostics</p>
        </div>
        <button
          onClick={handleRefresh}
          disabled={refreshing || loading}
          className="arc-btn-secondary flex items-center gap-2 px-4 py-2 rounded-lg"
        >
          <RefreshCw size={18} className={refreshing ? 'animate-spin' : ''} />
          Refresh Core
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
          <div className="arc-card p-6">
            <div className="flex items-center gap-3 mb-4">
              <Cpu className="text-arc-cyan" size={24} />
              <h2 className="text-lg font-semibold text-arc-silver">Processor</h2>
            </div>
            <p className="text-arc-silver/80">{hardware.cpu_info}</p>
          </div>

          <div className="arc-card p-6">
            <div className="flex items-center gap-3 mb-4">
              <Monitor className="text-arc-blue" size={24} />
              <h2 className="text-lg font-semibold text-arc-silver">Graphics</h2>
            </div>
            <div className="space-y-2">
              {hardware.gpu_info.map((gpu, idx) => (
                <p key={idx} className="text-arc-silver/80">{gpu}</p>
              ))}
            </div>
          </div>

          <div className="arc-card p-6">
            <div className="flex items-center gap-3 mb-4">
              <HardDrive className="text-arc-success" size={24} />
              <h2 className="text-lg font-semibold text-arc-silver">Memory</h2>
            </div>
            <p className="text-arc-silver/80">{hardware.ram_info}</p>
          </div>

          <div className="arc-card p-6">
            <div className="flex items-center gap-3 mb-4">
              <HardDrive className="text-arc-gold" size={24} />
              <h2 className="text-lg font-semibold text-arc-silver">Storage</h2>
            </div>
            <p className="text-arc-silver/80">{hardware.storage_info}</p>
          </div>
        </div>
      ) : null}
    </div>
  );
}
