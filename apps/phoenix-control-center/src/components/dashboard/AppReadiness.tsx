import { useEffect, useState } from 'react';
import { CheckCircle, XCircle, AlertCircle, RefreshCw } from '../Icons';

interface AppStatus {
  packageId: string;
  name: string;
  version: string;
  status: 'healthy' | 'degraded' | 'unavailable';
  lastCheck: string;
}

export default function AppReadiness() {
  const [apps, setApps] = useState<AppStatus[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [refreshing, setRefreshing] = useState(false);

  const fetchAppRegistry = async () => {
    try {
      // Read app.metadata.json for now (in production this would query a registry)
      const response = await fetch('/app.metadata.json');
      const metadata = await response.json();

      // Simulate app registry with the Command app itself
      const commandApp: AppStatus = {
        packageId: metadata.packageId,
        name: metadata.displayName,
        version: metadata.version,
        status: 'healthy',
        lastCheck: new Date().toISOString(),
      };

      setApps([commandApp]);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch app registry');
      // Fallback data for demo
      setApps([{
        packageId: 'com.bobbysworld.command',
        name: 'Command Control Center',
        version: '1.0.0',
        status: 'healthy',
        lastCheck: new Date().toISOString(),
      }]);
    }
  };

  useEffect(() => {
    setLoading(true);
    fetchAppRegistry().finally(() => setLoading(false));
  }, []);

  const handleRefresh = async () => {
    setRefreshing(true);
    await fetchAppRegistry();
    setRefreshing(false);
  };

  const getStatusIcon = (status: AppStatus['status']) => {
    switch (status) {
      case 'healthy':
        return <CheckCircle className="w-5 h-5 text-arc-success" />;
      case 'degraded':
        return <AlertCircle className="w-5 h-5 text-arc-gold" />;
      case 'unavailable':
        return <XCircle className="w-5 h-5 text-arc-error" />;
    }
  };

  const getStatusText = (status: AppStatus['status']) => {
    switch (status) {
      case 'healthy':
        return 'Healthy';
      case 'degraded':
        return 'Degraded';
      case 'unavailable':
        return 'Unavailable';
    }
  };

  const getStatusColor = (status: AppStatus['status']) => {
    switch (status) {
      case 'healthy':
        return 'text-arc-success';
      case 'degraded':
        return 'text-arc-gold';
      case 'unavailable':
        return 'text-arc-error';
    }
  };

  return (
    <div className="bg-arc-surface border border-arc-border rounded-xl p-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-xl font-bold text-arc-cyan">App Readiness</h2>
          <p className="text-sm text-arc-silver/60 mt-1">Installed applications and health status</p>
        </div>
        <button
          onClick={handleRefresh}
          disabled={refreshing || loading}
          className="p-2 hover:bg-arc-panel rounded-lg transition-colors"
          title="Refresh app registry"
        >
          <RefreshCw size={18} className={`text-arc-silver ${refreshing ? 'animate-spin' : ''}`} />
        </button>
      </div>

      {error && (
        <div className="mb-4 p-3 bg-arc-error/10 border border-arc-error/20 rounded-lg text-arc-error text-sm">
          {error}
        </div>
      )}

      {loading && !apps.length ? (
        <div className="space-y-3">
          {Array.from({ length: 2 }).map((_, idx) => (
            <div key={idx} className="animate-pulse bg-arc-panel rounded-lg p-4 h-20" />
          ))}
        </div>
      ) : (
        <div className="space-y-3">
          {apps.map((app) => (
            <div
              key={app.packageId}
              className="bg-arc-panel border border-arc-border rounded-lg p-4 hover:border-arc-cyan/30 transition-colors"
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  {getStatusIcon(app.status)}
                  <div>
                    <h3 className="font-semibold text-arc-silver">{app.name}</h3>
                    <p className="text-xs text-arc-silver/50 mt-0.5">
                      {app.packageId} • v{app.version}
                    </p>
                  </div>
                </div>
                <div className="text-right">
                  <div className={`text-sm font-medium ${getStatusColor(app.status)}`}>
                    {getStatusText(app.status)}
                  </div>
                  <div className="text-xs text-arc-silver/40 mt-0.5">
                    {new Date(app.lastCheck).toLocaleTimeString()}
                  </div>
                </div>
              </div>
            </div>
          ))}

          {apps.length === 0 && !loading && (
            <div className="text-center py-8 text-arc-silver/50">
              <p>No applications registered</p>
            </div>
          )}

          <div className="mt-4 p-3 bg-arc-bg/50 border border-arc-border rounded-lg text-xs text-arc-silver/60">
            <p>
              <span className="font-mono text-arc-cyan">Registry:</span> Apps are discovered via{' '}
              <code className="text-arc-silver/80">app.metadata.json</code> manifests
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
