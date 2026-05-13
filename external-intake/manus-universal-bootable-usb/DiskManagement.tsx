import React, { useEffect, useState } from 'react';
import { HardDrive, AlertTriangle, CheckCircle, RefreshCw, Zap, Lock, Trash2 } from 'lucide-react';
import { SkeletonPartitionList } from '@components/LoadingSkeleton';
import { ErrorDisplay, WarningDisplay, SuccessDisplay } from '@components/ErrorBoundary';
import { systemService } from '@services/systemService';
import { PartitionInfo } from '@types/system';

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
      const result = await systemService.scanDiskErrors(device);
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

  const getUsageBgColor = (usage: number) => {
    if (usage > 90) return 'bg-red-100 dark:bg-red-900';
    if (usage > 75) return 'bg-yellow-100 dark:bg-yellow-900';
    return 'bg-green-100 dark:bg-green-900';
  };

  const formatBytes = (bytes: number) => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i];
  };

  return (
    <div className="p-8 space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-slate-900 dark:text-white">Disk Management</h1>
          <p className="text-slate-600 dark:text-slate-400 mt-2">Manage disks, partitions, and storage</p>
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

      {/* Safety Notice */}
      <WarningDisplay message="System disks are protected from dangerous operations. Only removable media and external drives can be scanned or repaired." />

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
              className={`card cursor-pointer transition-all ${
                selectedPartition === partition.device
                  ? 'ring-2 ring-phoenix-600'
                  : 'hover:shadow-lg'
              }`}
              onClick={() => setSelectedPartition(
                selectedPartition === partition.device ? null : partition.device
              )}
            >
              {/* Header */}
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-3">
                  <HardDrive size={24} className="text-phoenix-600" />
                  <div>
                    <h3 className="font-semibold text-slate-900 dark:text-white">
                      {partition.device}
                    </h3>
                    <p className="text-sm text-slate-600 dark:text-slate-400">
                      {partition.mount_point} • {partition.filesystem}
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  {partition.is_system_disk && (
                    <span className="badge badge-warning">System Disk</span>
                  )}
                  {partition.is_removable && (
                    <span className="badge badge-info">Removable</span>
                  )}
                  {partition.is_read_only && (
                    <span className="badge badge-error">Read-Only</span>
                  )}
                </div>
              </div>

              {/* Usage Bar */}
              <div className="mb-4">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm text-slate-600 dark:text-slate-400">
                    {formatBytes(partition.used_size)} / {formatBytes(partition.total_size)}
                  </span>
                  <span className={`text-sm font-semibold ${
                    partition.usage_percent > 90
                      ? 'text-red-600 dark:text-red-400'
                      : partition.usage_percent > 75
                      ? 'text-yellow-600 dark:text-yellow-400'
                      : 'text-green-600 dark:text-green-400'
                  }`}>
                    {partition.usage_percent.toFixed(1)}%
                  </span>
                </div>
                <div className="w-full bg-slate-200 dark:bg-slate-700 rounded-full h-2">
                  <div
                    className={`h-2 rounded-full transition-all ${getUsageColor(partition.usage_percent)}`}
                    style={{ width: `${Math.min(partition.usage_percent, 100)}%` }}
                  ></div>
                </div>
              </div>

              {/* Details (when selected) */}
              {selectedPartition === partition.device && (
                <div className="space-y-4 pt-4 border-t border-slate-200 dark:border-slate-700">
                  {/* Disk Info Grid */}
                  <div className="grid grid-cols-2 gap-4">
                    <div className={`p-3 rounded-lg ${getUsageBgColor(partition.usage_percent)}`}>
                      <p className="text-xs text-slate-600 dark:text-slate-400 mb-1">Total Size</p>
                      <p className="font-semibold text-slate-900 dark:text-white">
                        {formatBytes(partition.total_size)}
                      </p>
                    </div>
                    <div className="p-3 rounded-lg bg-blue-100 dark:bg-blue-900">
                      <p className="text-xs text-slate-600 dark:text-slate-400 mb-1">Used</p>
                      <p className="font-semibold text-slate-900 dark:text-white">
                        {formatBytes(partition.used_size)}
                      </p>
                    </div>
                    <div className="p-3 rounded-lg bg-green-100 dark:bg-green-900">
                      <p className="text-xs text-slate-600 dark:text-slate-400 mb-1">Available</p>
                      <p className="font-semibold text-slate-900 dark:text-white">
                        {formatBytes(partition.available_size)}
                      </p>
                    </div>
                    <div className="p-3 rounded-lg bg-slate-100 dark:bg-slate-700">
                      <p className="text-xs text-slate-600 dark:text-slate-400 mb-1">Filesystem</p>
                      <p className="font-semibold text-slate-900 dark:text-white">
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
                        className="flex-1 btn-secondary flex items-center justify-center gap-2"
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
                        className="flex-1 btn-danger flex items-center justify-center gap-2"
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
