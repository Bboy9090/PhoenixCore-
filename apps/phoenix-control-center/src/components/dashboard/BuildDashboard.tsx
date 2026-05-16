import { useState, useEffect, useRef } from 'react';
import { invoke } from '../../lib/bridge';
import { ScreenContainer } from '@/components/screen-container';
import { ErrorBoundary } from '@/components/ErrorBoundary';
import { ArcwyreLogo } from '@/components/ArcwyreLogo';

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
  initializing: '#31D7FF',
  verifying: '#2F80FF',
  debootstrap: '#C7D0D9',
  installing_packages: '#FFB02E',
  customizing: '#42F59B',
  building_iso: '#31D7FF',
  generating_checksums: '#2F80FF',
  completed: '#42F59B',
  failed: '#FF3B3B',
  cancelled: '#C7D0D9',
};

export default function BuildDashboard() {
  const [buildStatus, setBuildStatus] = useState<BuildStatus | null>(null);
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [buildDir, setBuildDir] = useState('/home/ubuntu/phoenixcore/apps/os');
  const [showLogs, setShowLogs] = useState(true);
  const logsEndRef = useRef<HTMLDivElement>(null);
  const pollIntervalRef = useRef<number | null>(null);

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
      pollIntervalRef.current = window.setInterval(() => {
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

  if (!buildStatus) {
    return (
      <ScreenContainer className="p-6 bg-arc-bg">
        <div className="space-y-6">
          <div className="flex justify-between items-center">
            <h1 className="text-3xl font-bold text-arc-cyan">ARCWYRE Forge Dashboard</h1>
          </div>

          <div className="arc-card p-6">
            <h2 className="text-xl font-semibold text-arc-silver mb-4">ARCWYRE OS ISO Build</h2>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-arc-silver/60 mb-2">Build Workspace</label>
                <input
                  type="text"
                  value={buildDir}
                  onChange={(e) => setBuildDir(e.target.value)}
                  className="w-full px-4 py-2 bg-arc-panel border border-arc-border rounded-lg text-arc-silver focus:outline-none focus:ring-2 focus:ring-arc-cyan"
                  placeholder="/path/to/build"
                />
              </div>

              <button
                onClick={handleStartBuild}
                disabled={isLoading}
                className="arc-btn-primary w-full px-6 py-3 font-semibold rounded-lg hover:opacity-90 disabled:opacity-50 transition-opacity"
              >
                {isLoading ? 'Starting Forge...' : 'Start ARCWYRE Build'}
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
      <ScreenContainer className="p-6 bg-arc-bg">
        <div className="space-y-6">
          {/* Header */}
          <div className="flex justify-between items-center">
            <div className="flex items-center gap-4">
              <ArcwyreLogo size={48} />
              <div>
                <h1 className="text-3xl font-bold text-arc-cyan">ARCWYRE Forge</h1>
                <p className="text-arc-silver/40 text-sm mt-1">Build ID: {buildStatus.build_id}</p>
              </div>
            </div>
            <div className="flex gap-3">
              {buildStatus.is_running && !buildStatus.is_paused && (
                <>
                  <button
                    onClick={handlePauseBuild}
                    className="px-4 py-2 bg-arc-gold text-arc-bg font-semibold rounded-lg hover:opacity-90 transition-opacity"
                  >
                    Pause Forge
                  </button>
                  <button
                    onClick={handleCancelBuild}
                    className="px-4 py-2 bg-arc-danger text-arc-silver font-semibold rounded-lg hover:opacity-90 transition-opacity"
                  >
                    Abort
                  </button>
                </>
              )}
              {buildStatus.is_paused && (
                <button
                  onClick={handleResumeBuild}
                  className="px-4 py-2 bg-arc-success text-arc-bg font-semibold rounded-lg hover:opacity-90 transition-opacity"
                >
                  Resume Forge
                </button>
              )}
            </div>
          </div>

          {/* Progress Section */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {/* Main Progress */}
            <div className="md:col-span-2 arc-card p-6">
              <h2 className="text-lg font-semibold text-arc-silver mb-4 text-arc-cyan">Build Progress</h2>

              {/* Progress Bar */}
              <div className="mb-6">
                <div className="flex justify-between items-center mb-2">
                  <span className="text-sm font-medium text-arc-silver/60">Overall Machine Assembly</span>
                  <span className="text-lg font-bold text-arc-cyan">{buildStatus.progress}%</span>
                </div>
                <div className="w-full bg-arc-bg rounded-full h-3 overflow-hidden border border-arc-border">
                  <div
                    className="h-full bg-gradient-to-r from-arc-cyan to-arc-blue transition-all duration-300"
                    style={{ width: `${buildStatus.progress}%` }}
                  />
                </div>
              </div>

              {/* Stage Indicator */}
              <div className="mb-6">
                <p className="text-sm font-medium text-arc-silver/60 mb-2">Current Active Stage</p>
                <div className="flex items-center gap-3">
                  <div
                    className="w-4 h-4 rounded-full shadow-[0_0_8px_currentColor]"
                    style={{ backgroundColor: getStageColor(buildStatus.stage), color: getStageColor(buildStatus.stage) }}
                  />
                  <span className="text-arc-silver font-semibold capitalize text-lg">
                    {buildStatus.stage.replace(/_/g, ' ')}
                  </span>
                </div>
              </div>

              {/* Stage Progress Chart (Zero-Dependency Replacement) */}
              <div className="mt-6 h-[250px] w-full flex items-end gap-2 border-b border-l border-arc-border p-4 overflow-x-auto">
                {progressData.map((stage, idx) => (
                  <div key={idx} className="flex-1 flex flex-col items-center gap-2 group min-w-[60px]">
                    <div 
                      className="w-full bg-arc-cyan/40 rounded-t transition-all duration-500 hover:bg-arc-cyan"
                      style={{ height: `${stage.progress}%`, opacity: stage.completed ? 1 : 0.3 }}
                    >
                      <div className="text-[10px] text-arc-silver text-center -mt-6 font-mono">{stage.progress}%</div>
                    </div>
                    <div className="text-[8px] text-arc-silver/40 uppercase rotate-45 origin-left whitespace-nowrap mt-2">
                      {stage.name}
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Stats Panel */}
            <div className="arc-card p-6">
              <h2 className="text-lg font-semibold text-arc-silver mb-4 border-b border-arc-border pb-2">Diagnostics</h2>

              <div className="space-y-6">
                <div>
                  <p className="text-xs font-medium text-arc-silver/40 uppercase tracking-widest">Elapsed Time</p>
                  <p className="text-xl font-bold text-arc-cyan font-mono">
                    {formatTime(buildStatus.elapsed_time)}
                  </p>
                </div>

                <div>
                  <p className="text-xs font-medium text-arc-silver/40 uppercase tracking-widest">Est. Remaining</p>
                  <p className="text-xl font-bold text-arc-gold font-mono">
                    {formatTime(buildStatus.estimated_time_remaining)}
                  </p>
                </div>

                <div>
                  <p className="text-xs font-medium text-arc-silver/40 uppercase tracking-widest">Operations</p>
                  <p className="text-xl font-bold text-arc-success font-mono">
                    {buildStatus.current_line} / {buildStatus.total_lines}
                  </p>
                </div>

                {buildStatus.iso_size && (
                  <div>
                    <p className="text-xs font-medium text-arc-silver/40 uppercase tracking-widest">Payload Size</p>
                    <p className="text-xl font-bold text-arc-silver font-mono">
                      {(buildStatus.iso_size / 1024 / 1024 / 1024).toFixed(2)} GB
                    </p>
                  </div>
                )}

                <div className="pt-4 border-t border-arc-border">
                  <p className="text-xs font-medium text-arc-silver/40 uppercase tracking-widest mb-2">Core Status</p>
                  <div className="flex items-center gap-2">
                    <div
                      className={`w-3 h-3 rounded-full ${
                        buildStatus.is_running
                          ? 'bg-arc-cyan animate-pulse shadow-[0_0_8px_rgba(49,215,255,0.6)]'
                          : buildStatus.stage === 'completed'
                            ? 'bg-arc-success'
                            : buildStatus.stage === 'failed'
                              ? 'bg-arc-danger'
                              : 'bg-arc-gold'
                      }`}
                    />
                    <span className="text-sm font-medium text-arc-silver capitalize">
                      {buildStatus.is_paused
                        ? 'System Paused'
                        : buildStatus.is_running
                          ? 'Active Forge'
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
          <div className="arc-card p-6">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-lg font-semibold text-arc-silver">Build Logs</h2>
              <button
                onClick={() => setShowLogs(!showLogs)}
                className="text-sm text-arc-cyan hover:underline"
              >
                {showLogs ? 'Hide' : 'Show'}
              </button>
            </div>

            {showLogs && (
              <div className="bg-arc-bg border border-arc-border rounded-lg p-4 font-mono text-sm max-h-96 overflow-y-auto">
                {logs.length === 0 ? (
                  <p className="text-arc-silver/40">No logs yet...</p>
                ) : (
                  logs.map((log, idx) => (
                    <div
                      key={idx}
                      className={`py-1 ${
                        log.level === 'ERROR'
                          ? 'text-arc-danger'
                          : log.level === 'WARN'
                            ? 'text-arc-gold'
                            : log.level === 'SUCCESS'
                              ? 'text-arc-success'
                              : 'text-arc-silver/60'
                      }`}
                    >
                      <span className="opacity-40">[{log.level}]</span> {log.message}
                    </div>
                  ))
                )}
                <div ref={logsEndRef} />
              </div>
            )}
          </div>

          {/* ISO Output */}
          {buildStatus.iso_path && (
            <div className="bg-arc-success/10 border border-arc-success/40 rounded-lg p-4">
              <p className="text-arc-success font-semibold mb-1">Build Complete!</p>
              <p className="text-arc-success/80 text-sm">ISO: {buildStatus.iso_path}</p>
            </div>
          )}
        </div>
      </ScreenContainer>
    </ErrorBoundary>
  );
}
