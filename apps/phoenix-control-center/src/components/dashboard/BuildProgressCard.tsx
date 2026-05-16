import { useState, useEffect } from 'react';
import { invoke } from '../../lib/bridge';

interface BuildStatus {
  is_running: boolean;
  is_paused: boolean;
  stage: string;
  progress: number;
  elapsed_time: number;
  estimated_time_remaining: number;
  build_id: string;
}

interface ProgressDataPoint {
  time: number;
  progress: number;
}

export function BuildProgressCard() {
  const [buildStatus, setBuildStatus] = useState<BuildStatus | null>(null);
  const [progressHistory, setProgressHistory] = useState<ProgressDataPoint[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const fetchStatus = async () => {
      try {
        const status = await invoke<BuildStatus>('get_build_status');
        setBuildStatus(status);

        if (status.is_running) {
          setProgressHistory((prev) => [
            ...prev,
            {
              time: Math.floor(Date.now() / 1000),
              progress: status.progress,
            },
          ]);
        }
      } catch (err) {
        console.error('Failed to fetch build status:', err);
      } finally {
        setIsLoading(false);
      }
    };

    fetchStatus();
    const interval = setInterval(fetchStatus, 2000);
    return () => clearInterval(interval);
  }, []);

  if (isLoading || !buildStatus) {
    return (
      <div className="bg-surface rounded-lg p-6 border border-border">
        <div className="animate-pulse space-y-4">
          <div className="h-6 bg-background rounded w-1/3"></div>
          <div className="h-4 bg-background rounded"></div>
          <div className="h-32 bg-background rounded"></div>
        </div>
      </div>
    );
  }

  if (!buildStatus.is_running) {
    return null;
  }

  return (
    <div className="arc-card p-6">
      <div className="flex justify-between items-start mb-4">
        <div>
          <h3 className="text-lg font-semibold text-arc-silver">ARCWYRE Forge Build</h3>
          <p className="text-sm text-arc-silver/40 mt-1">{buildStatus.build_id}</p>
        </div>
        <div className="text-right">
          <div className="text-2xl font-bold text-arc-cyan">{buildStatus.progress}%</div>
          <div className="text-xs text-arc-silver/60 mt-1">
            {buildStatus.is_paused ? 'Paused' : 'Forging...'}
          </div>
        </div>
      </div>

      {/* Progress Bar */}
      <div className="mb-4">
        <div className="w-full bg-arc-bg rounded-full h-2 overflow-hidden border border-arc-border">
          <div
            className="h-full bg-gradient-to-r from-arc-cyan to-arc-blue transition-all duration-300"
            style={{ width: `${buildStatus.progress}%` }}
          />
        </div>
      </div>

      {/* Stage Info */}
      <div className="grid grid-cols-2 gap-4 mb-4 text-sm">
        <div>
          <p className="text-muted text-xs uppercase">Current Stage</p>
          <p className="text-foreground font-semibold capitalize">
            {buildStatus.stage.replace(/_/g, ' ')}
          </p>
        </div>
        <div>
          <p className="text-muted text-xs uppercase">Elapsed Time</p>
          <p className="text-foreground font-semibold">
            {Math.floor(buildStatus.elapsed_time / 60)}m {buildStatus.elapsed_time % 60}s
          </p>
        </div>
      </div>

      {/* Progress Chart (Zero-Dependency SVG Replacement) */}
      {progressHistory.length > 1 && (
        <div className="mt-4 pt-4 border-t border-arc-border h-32 relative">
          <svg className="w-full h-full" viewBox="0 0 100 100" preserveAspectRatio="none">
            <path
              d={`M ${progressHistory.map((p, i) => `${(i / (progressHistory.length - 1)) * 100},${100 - p.progress}`).join(' L ')}`}
              fill="none"
              stroke="var(--arc-cyan)"
              strokeWidth="2"
              className="transition-all duration-500"
            />
          </svg>
          <div className="absolute bottom-0 left-0 text-[8px] text-arc-silver/20 font-mono">0%</div>
          <div className="absolute top-0 left-0 text-[8px] text-arc-silver/20 font-mono">100%</div>
        </div>
      )}
    </div>
  );
}
