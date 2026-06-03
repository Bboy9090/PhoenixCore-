import { useEffect, useState } from 'react';
import { HardDrive, AlertTriangle, RefreshCw, Zap, Lock, Trash2 } from '../Icons';
import { SkeletonPartitionList } from '../LoadingSkeleton';
import { ErrorDisplay, WarningDisplay, SuccessDisplay } from '../ErrorBoundary';
import { systemService } from '../../systemService';
import { PartitionInfo } from '../../system';

export default function DiskManagement() {
  const [partitions, setPartitions] = useState<PartitionInfo[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [refreshing, setRefreshing] = useState(false);
  const [selectedPartition, setSelectedPartition] = useState<string | null>(null);
  const [scanning, setScanningDevice] = useState<string | null>(null);
  const [repairing, setRepairingDevice] = useState<string | null>(null);

  const fetchPartitions = async () => {
    try {
      const data = await systemService.getDiskInfo();
      setPartitions(data as unknown as PartitionInfo[]);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch disk information');
    }
  };

  useEffect(() => {
    setLoading(true);
    fetchPartitions().finally(() => setLoading(false));
  }, []);

  const handleRefresh = async () => {
    setRefreshing(true);
    await fetchPartitions();
    setRefreshing(false);
  };

  const handleScanDisk = async (device: string) => {
    // Safety check
    const partition = partitions.find((p) => p.device === device);
    if (partition?.is_system_disk) {
      setError('Cannot scan system disk for safety reasons');
      return;
    }

    setScanningDevice(device);
    try {
      await systemService.scanDiskErrors(device);
      setSuccess(`Disk scan started for ${device}`);
      setTimeout(() => setSuccess(null), 3000);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to scan disk');
    } finally {
      setScanningDevice(null);
    }
  };

  const handleRepairDisk = async (device: string) => {
    // Safety check
    const partition = partitions.find((p) => p.device === device);
    if (partition?.is_system_disk) {
      setError('Cannot repair system disk for safety reasons');
      return;
    }

    if (!window.confirm(`Are you sure you want to repair ${device}? This may take several minutes.`)) {
      return;
    }

    setRepairingDevice(device);
    try {
      const result = await systemService.repairDisk(device);
      if (result.success) {
        setSuccess(`Disk repair completed for ${device}`);
      } else {
        setError(result.message);
      }
      setTimeout(() => setSuccess(null), 3000);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to repair disk');
    } finally {
      setRepairingDevice(null);
    }
  };

  const getUsageColor = (usage: number) => {
    if (usage > 90) return 'bg-red-500';
    if (usage > 75) return 'bg-yellow-500';
    return 'bg-green-500';
  };

  const formatBytes = (bytes: number) => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i];
  };

  return (
    <div className="p-8 space-y-8 bg-arc-bg text-arc-silver">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-arc-cyan">ARCWYRE Disk Management</h1>
          <p className="text-arc-silver/60 mt-2">Manage disks, partitions, and storage clusters</p>
        </div>
        <button
          onClick={handleRefresh}
          disabled={refreshing || loading}
          className="arc-btn-secondary flex items-center gap-2 px-4 py-2 rounded-lg"
        >
          <RefreshCw size={18} className={refreshing ? 'animate-spin' : ''} />
          Refresh Registry
        </button>
      </div>

      {/* Safety Notice */}
      <WarningDisplay message="Safety Protocols Active: System disks are protected from dangerous operations. Only removable media and external drives can be scanned or repaired." />

      {/* Messages */}
      {error && (
        <ErrorDisplay
          error={error}
          onDismiss={() => setError(null)}
        />
      )}
      {success && (
        <SuccessDisplay
          message={success}
          onDismiss={() => setSuccess(null)}
        />
      )}

      {/* Partitions List */}
      {loading && !partitions.length ? (
        <SkeletonPartitionList count={3} />
      ) : partitions.length > 0 ? (
        <div className="space-y-4">
          {partitions.map((partition) => (
              <div
                key={partition.device}
                className={`arc-card cursor-pointer transition-all p-6 ${
                  selectedPartition === partition.device
                    ? 'ring-2 ring-arc-cyan shadow-[0_0_15px_rgba(49,215,255,0.3)]'
                    : 'hover:border-arc-cyan/30'
                }`}
                onClick={() => setSelectedPartition(
                  selectedPartition === partition.device ? null : partition.device
                )}
              >
                {/* Header */}
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center gap-3">
                    <HardDrive size={24} className="text-arc-cyan" />
                    <div>
                      <h3 className="font-semibold text-arc-silver">
                        {partition.device}
                      </h3>
                      <p className="text-sm text-arc-silver/40">
                        {partition.mount_point} • {partition.filesystem}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    {partition.is_system_disk && (
                      <span className="px-2 py-0.5 text-[10px] uppercase font-bold bg-arc-gold/10 text-arc-gold border border-arc-gold/20 rounded">System Disk</span>
                    )}
                    {partition.is_removable && (
                      <span className="px-2 py-0.5 text-[10px] uppercase font-bold bg-arc-blue/10 text-arc-blue border border-arc-blue/20 rounded">Removable</span>
                    )}
                    {partition.is_read_only && (
                      <span className="px-2 py-0.5 text-[10px] uppercase font-bold bg-arc-danger/10 text-arc-danger border border-arc-danger/20 rounded">Read-Only</span>
                    )}
                  </div>
                </div>

              {/* Usage Bar */}
              <div className="mb-4">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm text-arc-silver/60">
                    {formatBytes(partition.used_size)} / {formatBytes(partition.total_size)}
                  </span>
                  <span className={`text-sm font-semibold ${
                    partition.usage_percent > 90
                      ? 'text-arc-danger'
                      : partition.usage_percent > 75
                      ? 'text-arc-gold'
                      : 'text-arc-success'
                  }`}>
                    {partition.usage_percent.toFixed(1)}%
                  </span>
                </div>
                <div className="w-full bg-arc-panel rounded-full h-2 border border-arc-border">
                  <div
                    className={`h-2 rounded-full transition-all ${getUsageColor(partition.usage_percent)}`}
                    style={{ width: `${Math.min(partition.usage_percent, 100)}%` }}
                  ></div>
                </div>
              </div>

              {/* Details (when selected) */}
              {selectedPartition === partition.device && (
                <div className="space-y-4 pt-4 border-t border-arc-border">
                  {/* Disk Info Grid */}
                  <div className="grid grid-cols-2 gap-4">
                    <div className="p-3 rounded-lg bg-arc-panel/50 border border-arc-border">
                      <p className="text-xs text-arc-silver/40 mb-1">Total Size</p>
                      <p className="font-semibold text-arc-silver">
                        {formatBytes(partition.total_size)}
                      </p>
                    </div>
                    <div className="p-3 rounded-lg bg-arc-blue/10 border border-arc-blue/20">
                      <p className="text-xs text-arc-blue/60 mb-1">Used</p>
                      <p className="font-semibold text-arc-blue">
                        {formatBytes(partition.used_size)}
                      </p>
                    </div>
                    <div className="p-3 rounded-lg bg-arc-success/10 border border-arc-success/20">
                      <p className="text-xs text-arc-success/60 mb-1">Available</p>
                      <p className="font-semibold text-arc-success">
                        {formatBytes(partition.available_size)}
                      </p>
                    </div>
                    <div className="p-3 rounded-lg bg-arc-panel">
                      <p className="text-xs text-arc-silver/40 mb-1">Filesystem</p>
                      <p className="font-semibold text-arc-silver">
                        {partition.filesystem}
                      </p>
                    </div>
                  </div>

                  {/* Safety Warnings */}
                  {partition.usage_percent > 90 && (
                    <div className="p-3 rounded-lg bg-red-50 dark:bg-red-900 border border-red-200 dark:border-red-700 flex gap-2">
                      <AlertTriangle size={16} className="text-red-600 dark:text-red-400 flex-shrink-0 mt-0.5" />
                      <p className="text-sm text-red-800 dark:text-red-200">
                        Disk is almost full. Consider freeing up space.
                      </p>
                    </div>
                  )}

                  {partition.is_system_disk && (
                    <div className="p-3 rounded-lg bg-yellow-50 dark:bg-yellow-900 border border-yellow-200 dark:border-yellow-700 flex gap-2">
                      <Lock size={16} className="text-yellow-600 dark:text-yellow-400 flex-shrink-0 mt-0.5" />
                      <p className="text-sm text-yellow-800 dark:text-yellow-200">
                        System disk is protected from dangerous operations.
                      </p>
                    </div>
                  )}

                  {/* Action Buttons */}
                  {!partition.is_system_disk && (
                    <div className="flex gap-3 pt-2">
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          handleScanDisk(partition.device);
                        }}
                        disabled={scanning === partition.device}
                        className="flex-1 arc-btn-secondary flex items-center justify-center gap-2 p-2 rounded-lg"
                      >
                        <Zap size={16} className={scanning === partition.device ? 'animate-spin' : ''} />
                        {scanning === partition.device ? 'Scanning...' : 'Scan for Errors'}
                      </button>
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          handleRepairDisk(partition.device);
                        }}
                        disabled={repairing === partition.device}
                        className="flex-1 bg-arc-danger/20 border border-arc-danger/40 text-arc-danger hover:bg-arc-danger/30 flex items-center justify-center gap-2 p-2 rounded-lg"
                      >
                        <Trash2 size={16} className={repairing === partition.device ? 'animate-spin' : ''} />
                        {repairing === partition.device ? 'Repairing...' : 'Repair Disk'}
                      </button>
                    </div>
                  )}
                </div>
              )}
            </div>
          ))}
        </div>
      ) : (
        <div className="card flex items-center justify-center py-12">
          <div className="text-center">
            <HardDrive size={48} className="mx-auto text-slate-400 mb-4" />
            <p className="text-slate-600 dark:text-slate-400">No disk partitions found</p>
          </div>
        </div>
      )}

      {/* Information */}
      <div className="card bg-blue-50 dark:bg-blue-900 border-blue-200 dark:border-blue-700">
        <h3 className="font-semibold text-blue-900 dark:text-blue-100 mb-2">💡 About Disk Management</h3>
        <ul className="text-sm text-blue-800 dark:text-blue-200 space-y-1">
          <li>• System disks (/, /boot, /home) are protected from dangerous operations</li>
          <li>• Only removable media and external drives can be scanned or repaired</li>
          <li>• Disk scans and repairs may take several minutes to complete</li>
          <li>• Always backup important data before performing disk operations</li>
          <li>• Requires administrator privileges for repair operations</li>
        </ul>
      </div>
    </div>
  );
}
