import { useEffect, useState } from 'react';
import { systemService } from '../../systemService';
import { HardwareInfo } from '../../system';
import { Cpu, HardDrive, Monitor, RefreshCw, Zap } from '../Icons';
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
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {Array.from({ length: 4 }).map((_, idx) => (
            <SkeletonHardwareCard key={idx} />
          ))}
        </div>
      ) : hardware ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {/* CPU */}
          <div className="bg-arc-surface border border-arc-border p-4 rounded-lg flex items-center space-x-4">
            <div className="bg-arc-cyan/10 p-3 rounded-lg">
              <Cpu className="w-6 h-6 text-arc-cyan" />
            </div>
            <div>
              <p className="text-xs text-arc-silver/50 uppercase tracking-wider">Processor</p>
              <p className="text-arc-silver/80">{hardware.cpuInfo}</p>
            </div>
          </div>

          {/* GPU */}
          <div className="bg-arc-surface border border-arc-border p-4 rounded-lg flex items-center space-x-4">
            <div className="bg-arc-blue/10 p-3 rounded-lg">
              <Monitor className="w-6 h-6 text-arc-blue" />
            </div>
            <div>
              <p className="text-xs text-arc-silver/50 uppercase tracking-wider">Graphics</p>
              <div className="flex flex-col">
                {hardware.gpuInfo.map((gpu: string, idx: number) => (
                  <p key={idx} className="text-arc-silver/80">{gpu}</p>
                ))}
              </div>
            </div>
          </div>

          {/* RAM */}
          <div className="bg-arc-surface border border-arc-border p-4 rounded-lg flex items-center space-x-4">
            <div className="bg-arc-gold/10 p-3 rounded-lg">
              <Zap className="w-6 h-6 text-arc-gold" />
            </div>
            <div>
              <p className="text-xs text-arc-silver/50 uppercase tracking-wider">Memory</p>
              <p className="text-arc-silver/80">{hardware.ramInfo}</p>
            </div>
          </div>

          {/* Storage */}
          <div className="bg-arc-surface border border-arc-border p-4 rounded-lg flex items-center space-x-4">
            <div className="bg-arc-cyan/10 p-3 rounded-lg">
              <HardDrive className="w-6 h-6 text-arc-cyan" />
            </div>
            <div>
              <p className="text-xs text-arc-silver/50 uppercase tracking-wider">Storage</p>
              <p className="text-arc-silver/80">{hardware.storageInfo}</p>
            </div>
          </div>
        </div>
      ) : null}
    </div>
  );
}
