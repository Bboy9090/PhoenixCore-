import React, { useState, useEffect, useRef } from 'react';
import { invoke } from '@tauri-apps/api/tauri';
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';
import { ScreenContainer } from '@/components/screen-container';
import { LoadingSkeleton } from '@/components/LoadingSkeleton';
import { ErrorBoundary } from '@/components/ErrorBoundary';

interface BuildStatus {
  is_running: boolean;
  is_paused: boolean;
  stage: string;
  progress: number;
  total_lines: number;
  current_line: number;
  elapsed_time: number;
  estimated_time_remaining: number;
  iso_path: string | null;
  iso_size: number | null;
  error_message: string | null;
  start_time: number;
  end_time: number | null;
  build_id: string;
}

interface LogEntry {
  timestamp: number;
  level: string;
  message: string;
  stage: string;
}

const BUILD_STAGES = [
  { name: 'Initializing', value: 5 },
  { name: 'Verifying', value: 10 },
  { name: 'Debootstrap', value: 25 },
  { name: 'Installing Packages', value: 45 },
  { name: 'Customizing', value: 65 },
  { name: 'Building ISO', value: 80 },
  { name: 'Generating Checksums', value: 95 },
  { name: 'Completed', value: 100 },
];

const STAGE_COLORS = {
  initializing: '#3b82f6',
  verifying: '#8b5cf6',
  debootstrap: '#ec4899',
  installing_packages: '#f59e0b',
  customizing: '#10b981',
  building_iso: '#06b6d4',
  generating_checksums: '#6366f1',
  completed: '#22c55e',
  failed: '#ef4444',
  cancelled: '#6b7280',
};

export default function BuildDashboard() {
  const [buildStatus, setBuildStatus] = useState<BuildStatus | null>(null);
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [buildDir, setBuildDir] = useState('/home/ubuntu/phoenixcore/apps/os');
  const [showLogs, setShowLogs] = useState(true);
  const logsEndRef = useRef<HTMLDivElement>(null);
  const pollIntervalRef = useRef<NodeJS.Timeout | null>(null);

  // Auto-scroll logs to bottom
  const scrollLogsToBottom = () => {
    logsEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollLogsToBottom();
  }, [logs]);

  // Fetch build status
  const fetchBuildStatus = async () => {
    try {
      const status = await invoke<BuildStatus>('get_build_status');
      setBuildStatus(status);

      if (status.is_running) {
        const buildLogs = await invoke<LogEntry[]>('get_build_logs');
        setLogs(buildLogs);
      }
    } catch (err) {
      setError(`Failed to fetch build status: ${err}`);
    }
  };

  // Start build
  const handleStartBuild = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const status = await invoke<BuildStatus>('start_phoenix_build', { buildDir });
      setBuildStatus(status);

      // Start polling for updates
      if (pollIntervalRef.current) clearInterval(pollIntervalRef.current);
      pollIntervalRef.current = setInterval(() => {
        fetchBuildStatus();
      }, 1000);
    } catch (err) {
      setError(`Failed to start build: ${err}`);
    } finally {
      setIsLoading(false);
    }
  };

  // Pause build
  const handlePauseBuild = async () => {
    try {
      await invoke('pause_build');
      await fetchBuildStatus();
    } catch (err) {
      setError(`Failed to pause build: ${err}`);
    }
  };

  // Resume build
  const handleResumeBuild = async () => {
    try {
      await invoke('resume_build');
      await fetchBuildStatus();
    } catch (err) {
      setError(`Failed to resume build: ${err}`);
    }
  };

  // Cancel build
  const handleCancelBuild = async () => {
    if (window.confirm('Are you sure you want to cancel the build?')) {
      try {
        await invoke('cancel_build');
        await fetchBuildStatus();
        if (pollIntervalRef.current) clearInterval(pollIntervalRef.current);
      } catch (err) {
        setError(`Failed to cancel build: ${err}`);
      }
    }
  };

  // Stop polling when build completes
  useEffect(() => {
    if (buildStatus && !buildStatus.is_running && pollIntervalRef.current) {
      clearInterval(pollIntervalRef.current);
    }
  }, [buildStatus?.is_running]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (pollIntervalRef.current) clearInterval(pollIntervalRef.current);
    };
  }, []);

  // Format time
  const formatTime = (seconds: number): string => {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;
    return `${hours}h ${minutes}m ${secs}s`;
  };

  // Get stage color
  const getStageColor = (stage: string): string => {
    return STAGE_COLORS[stage as keyof typeof STAGE_COLORS] || '#6b7280';
  };

  // Prepare chart data
  const progressData = BUILD_STAGES.map((stage) => ({
    name: stage.name,
    progress: stage.value,
    completed: buildStatus && buildStatus.progress >= stage.value,
  }));

  const timelineData = logs
    .filter((log) => log.level === 'SUCCESS' || log.level === 'ERROR')
    .slice(-10)
    .map((log, idx) => ({
      index: idx,
      level: log.level,
      timestamp: new Date(log.timestamp * 1000).toLocaleTimeString(),
    }));

  if (!buildStatus) {
    return (
      <ScreenContainer className="p-6">
        <div className="space-y-6">
          <div className="flex justify-between items-center">
            <h1 className="text-3xl font-bold text-foreground">Build Dashboard</h1>
          </div>

          <div className="bg-surface rounded-lg p-6 border border-border">
            <h2 className="text-xl font-semibold text-foreground mb-4">Phoenix OS ISO Build</h2>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-muted mb-2">Build Directory</label>
                <input
                  type="text"
                  value={buildDir}
                  onChange={(e) => setBuildDir(e.target.value)}
                  className="w-full px-4 py-2 bg-background border border-border rounded-lg text-foreground focus:outline-none focus:ring-2 focus:ring-primary"
                  placeholder="/path/to/build"
                />
              </div>

              <button
                onClick={handleStartBuild}
                disabled={isLoading}
                className="w-full px-6 py-3 bg-primary text-background font-semibold rounded-lg hover:opacity-90 disabled:opacity-50 transition-opacity"
              >
                {isLoading ? 'Starting...' : 'Start Build'}
              </button>
            </div>
          </div>

          {error && (
            <div className="bg-error/20 border border-error rounded-lg p-4">
              <p className="text-error font-semibold">{error}</p>
            </div>
          )}
        </div>
      </ScreenContainer>
    );
  }

  return (
    <ErrorBoundary>
      <ScreenContainer className="p-6">
        <div className="space-y-6">
          {/* Header */}
          <div className="flex justify-between items-center">
            <div>
              <h1 className="text-3xl font-bold text-foreground">Build Dashboard</h1>
              <p className="text-muted text-sm mt-1">Build ID: {buildStatus.build_id}</p>
            </div>
            <div className="flex gap-2">
              {buildStatus.is_running && !buildStatus.is_paused && (
                <>
                  <button
                    onClick={handlePauseBuild}
                    className="px-4 py-2 bg-warning text-background font-semibold rounded-lg hover:opacity-90 transition-opacity"
                  >
                    Pause
                  </button>
                  <button
                    onClick={handleCancelBuild}
                    className="px-4 py-2 bg-error text-background font-semibold rounded-lg hover:opacity-90 transition-opacity"
                  >
                    Cancel
                  </button>
                </>
              )}
              {buildStatus.is_paused && (
                <button
                  onClick={handleResumeBuild}
                  className="px-4 py-2 bg-success text-background font-semibold rounded-lg hover:opacity-90 transition-opacity"
                >
                  Resume
                </button>
              )}
            </div>
          </div>

          {/* Progress Section */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* Main Progress */}
            <div className="md:col-span-2 bg-surface rounded-lg p-6 border border-border">
              <h2 className="text-lg font-semibold text-foreground mb-4">Build Progress</h2>

              {/* Progress Bar */}
              <div className="mb-6">
                <div className="flex justify-between items-center mb-2">
                  <span className="text-sm font-medium text-muted">Overall Progress</span>
                  <span className="text-lg font-bold text-primary">{buildStatus.progress}%</span>
                </div>
                <div className="w-full bg-background rounded-full h-3 overflow-hidden">
                  <div
                    className="h-full bg-gradient-to-r from-primary to-success transition-all duration-300"
                    style={{ width: `${buildStatus.progress}%` }}
                  />
                </div>
              </div>

              {/* Stage Indicator */}
              <div className="mb-6">
                <p className="text-sm font-medium text-muted mb-2">Current Stage</p>
                <div className="flex items-center gap-3">
                  <div
                    className="w-4 h-4 rounded-full"
                    style={{ backgroundColor: getStageColor(buildStatus.stage) }}
                  />
                  <span className="text-foreground font-semibold capitalize">
                    {buildStatus.stage.replace(/_/g, ' ')}
                  </span>
                </div>
              </div>

              {/* Stage Progress Chart */}
              <div className="mt-6">
                <ResponsiveContainer width="100%" height={250}>
                  <BarChart data={progressData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                    <XAxis dataKey="name" tick={{ fill: '#9BA1A6', fontSize: 12 }} />
                    <YAxis tick={{ fill: '#9BA1A6', fontSize: 12 }} />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: '#1e2022',
                        border: '1px solid #334155',
                        borderRadius: '8px',
                      }}
                      formatter={(value) => `${value}%`}
                    />
                    <Bar dataKey="progress" fill="#0a7ea4" radius={[8, 8, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>

            {/* Stats Panel */}
            <div className="bg-surface rounded-lg p-6 border border-border">
              <h2 className="text-lg font-semibold text-foreground mb-4">Statistics</h2>

              <div className="space-y-4">
                <div>
                  <p className="text-xs font-medium text-muted uppercase">Elapsed Time</p>
                  <p className="text-xl font-bold text-primary">
                    {formatTime(buildStatus.elapsed_time)}
                  </p>
                </div>

                <div>
                  <p className="text-xs font-medium text-muted uppercase">Estimated Remaining</p>
                  <p className="text-xl font-bold text-warning">
                    {formatTime(buildStatus.estimated_time_remaining)}
                  </p>
                </div>

                <div>
                  <p className="text-xs font-medium text-muted uppercase">Lines Processed</p>
                  <p className="text-xl font-bold text-success">
                    {buildStatus.current_line} / {buildStatus.total_lines}
                  </p>
                </div>

                {buildStatus.iso_size && (
                  <div>
                    <p className="text-xs font-medium text-muted uppercase">ISO Size</p>
                    <p className="text-xl font-bold text-foreground">
                      {(buildStatus.iso_size / 1024 / 1024 / 1024).toFixed(2)} GB
                    </p>
                  </div>
                )}

                <div>
                  <p className="text-xs font-medium text-muted uppercase">Status</p>
                  <div className="flex items-center gap-2 mt-1">
                    <div
                      className={`w-3 h-3 rounded-full ${
                        buildStatus.is_running
                          ? 'bg-success animate-pulse'
                          : buildStatus.stage === 'completed'
                            ? 'bg-success'
                            : buildStatus.stage === 'failed'
                              ? 'bg-error'
                              : 'bg-warning'
                      }`}
                    />
                    <span className="text-sm font-medium text-foreground capitalize">
                      {buildStatus.is_paused
                        ? 'Paused'
                        : buildStatus.is_running
                          ? 'Running'
                          : buildStatus.stage}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Error Message */}
          {buildStatus.error_message && (
            <div className="bg-error/20 border border-error rounded-lg p-4">
              <p className="text-error font-semibold mb-1">Build Error</p>
              <p className="text-error/80 text-sm">{buildStatus.error_message}</p>
            </div>
          )}

          {/* Logs Section */}
          <div className="bg-surface rounded-lg p-6 border border-border">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-lg font-semibold text-foreground">Build Logs</h2>
              <button
                onClick={() => setShowLogs(!showLogs)}
                className="text-sm text-primary hover:underline"
              >
                {showLogs ? 'Hide' : 'Show'}
              </button>
            </div>

            {showLogs && (
              <div className="bg-background rounded-lg p-4 font-mono text-sm max-h-96 overflow-y-auto">
                {logs.length === 0 ? (
                  <p className="text-muted">No logs yet...</p>
                ) : (
                  logs.map((log, idx) => (
                    <div
                      key={idx}
                      className={`py-1 ${
                        log.level === 'ERROR'
                          ? 'text-error'
                          : log.level === 'WARN'
                            ? 'text-warning'
                            : log.level === 'SUCCESS'
                              ? 'text-success'
                              : 'text-muted'
                      }`}
                    >
                      <span className="text-muted">[{log.level}]</span> {log.message}
                    </div>
                  ))
                )}
                <div ref={logsEndRef} />
              </div>
            )}
          </div>

          {/* ISO Output */}
          {buildStatus.iso_path && (
            <div className="bg-success/20 border border-success rounded-lg p-4">
              <p className="text-success font-semibold mb-1">Build Complete!</p>
              <p className="text-success/80 text-sm">ISO: {buildStatus.iso_path}</p>
            </div>
          )}
        </div>
      </ScreenContainer>
    </ErrorBoundary>
  );
}
