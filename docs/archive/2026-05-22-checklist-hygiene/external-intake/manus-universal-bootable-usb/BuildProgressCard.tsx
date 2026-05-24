import React, { useState, useEffect } from 'react';
import { invoke } from '@tauri-apps/api/tauri';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

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
    <div className="bg-surface rounded-lg p-6 border border-border">
      <div className="flex justify-between items-start mb-4">
        <div>
          <h3 className="text-lg font-semibold text-foreground">Phoenix OS Build</h3>
          <p className="text-sm text-muted mt-1">{buildStatus.build_id}</p>
        </div>
        <div className="text-right">
          <div className="text-2xl font-bold text-primary">{buildStatus.progress}%</div>
          <div className="text-xs text-muted mt-1">
            {buildStatus.is_paused ? 'Paused' : 'Running'}
          </div>
        </div>
      </div>

      {/* Progress Bar */}
      <div className="mb-4">
        <div className="w-full bg-background rounded-full h-2 overflow-hidden">
          <div
            className="h-full bg-gradient-to-r from-primary to-success transition-all duration-300"
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

      {/* Progress Chart */}
      {progressHistory.length > 1 && (
        <div className="mt-4">
          <ResponsiveContainer width="100%" height={150}>
            <LineChart data={progressHistory}>
              <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
              <XAxis dataKey="time" tick={{ fill: '#9BA1A6', fontSize: 10 }} />
              <YAxis tick={{ fill: '#9BA1A6', fontSize: 10 }} domain={[0, 100]} />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#1e2022',
                  border: '1px solid #334155',
                  borderRadius: '4px',
                }}
                formatter={(value) => `${value}%`}
              />
              <Line
                type="monotone"
                dataKey="progress"
                stroke="#0a7ea4"
                dot={false}
                isAnimationActive={false}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  );
}
