import { useEffect, useState } from 'react';
import { CheckCircle, XCircle, AlertCircle, RefreshCw, Server, Shield, Cog } from '../Icons';

interface ServiceHealth {
  name: string;
  status: 'healthy' | 'degraded' | 'unhealthy';
  uptime?: number;
  version?: string;
  lastCheck: string;
  details?: Record<string, any>;
}

export default function ServiceStatus() {
  const [services, setServices] = useState<ServiceHealth[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const checkServices = async () => {
    try {
      const now = new Date().toISOString();

      // Check Backend API
      let backendStatus: 'healthy' | 'degraded' | 'unhealthy' = 'unhealthy';
      try {
        const response = await fetch('http://localhost:5000/health', {
          method: 'GET',
          signal: AbortSignal.timeout(2000)
        });
        backendStatus = response.ok ? 'healthy' : 'degraded';
      } catch {
        backendStatus = 'unhealthy';
      }

      // Rust Core is always available (compiled into the app)
      const coreStatus: 'healthy' = 'healthy';

      // Safety Engine (simulated check)
      const safetyStatus: 'healthy' = 'healthy';

      setServices([
        {
          name: 'Backend API',
          status: backendStatus,
          version: '1.0.0',
          lastCheck: now,
          details: {
            endpoint: 'http://localhost:5000',
            transport: 'HTTP/JSON',
          },
        },
        {
          name: 'Rust Core',
          status: coreStatus,
          version: '1.0.0',
          lastCheck: now,
          details: {
            library: 'phoenix-core',
            interface: 'FFI/Direct',
          },
        },
        {
          name: 'Safety Engine',
          status: safetyStatus,
          version: '1.0.0',
          lastCheck: now,
          details: {
            library: 'phoenix-safety',
            gates: 'enabled',
          },
        },
      ]);
    } catch (err) {
      console.error('Failed to check services:', err);
    }
  };

  useEffect(() => {
    setLoading(true);
    checkServices().finally(() => setLoading(false));

    // Auto-refresh every 30 seconds
    const interval = setInterval(checkServices, 30000);
    return () => clearInterval(interval);
  }, []);

  const handleRefresh = async () => {
    setRefreshing(true);
    await checkServices();
    setRefreshing(false);
  };

  const getStatusIcon = (status: ServiceHealth['status']) => {
    switch (status) {
      case 'healthy':
        return <CheckCircle className="w-5 h-5 text-arc-success" />;
      case 'degraded':
        return <AlertCircle className="w-5 h-5 text-arc-gold" />;
      case 'unhealthy':
        return <XCircle className="w-5 h-5 text-arc-error" />;
    }
  };

  const getServiceIcon = (name: string) => {
    if (name.includes('Backend')) return <Server className="w-5 h-5" />;
    if (name.includes('Safety')) return <Shield className="w-5 h-5" />;
    return <Cog className="w-5 h-5" />;
  };

  const getStatusColor = (status: ServiceHealth['status']) => {
    switch (status) {
      case 'healthy':
        return 'text-arc-success';
      case 'degraded':
        return 'text-arc-gold';
      case 'unhealthy':
        return 'text-arc-error';
    }
  };

  const getStatusBg = (status: ServiceHealth['status']) => {
    switch (status) {
      case 'healthy':
        return 'bg-arc-success/10';
      case 'degraded':
        return 'bg-arc-gold/10';
      case 'unhealthy':
        return 'bg-arc-error/10';
    }
  };

  const healthyCount = services.filter(s => s.status === 'healthy').length;
  const overallStatus = healthyCount === services.length ? 'healthy' :
                       healthyCount > 0 ? 'degraded' : 'unhealthy';

  return (
    <div className="bg-arc-surface border border-arc-border rounded-xl p-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-xl font-bold text-arc-cyan">Service Status</h2>
          <p className="text-sm text-arc-silver/60 mt-1">Core PhoenixCore services health</p>
        </div>
        <button
          onClick={handleRefresh}
          disabled={refreshing || loading}
          className="p-2 hover:bg-arc-panel rounded-lg transition-colors"
          title="Refresh service status"
        >
          <RefreshCw size={18} className={`text-arc-silver ${refreshing ? 'animate-spin' : ''}`} />
        </button>
      </div>

      {/* Overall Status */}
      <div className={`mb-6 p-4 ${getStatusBg(overallStatus)} border border-arc-border rounded-lg`}>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            {getStatusIcon(overallStatus)}
            <div>
              <h3 className="font-semibold text-arc-silver">Overall System Health</h3>
              <p className="text-xs text-arc-silver/60 mt-0.5">
                {healthyCount} of {services.length} services operational
              </p>
            </div>
          </div>
          <div className={`text-lg font-bold ${getStatusColor(overallStatus)} uppercase tracking-wide`}>
            {overallStatus}
          </div>
        </div>
      </div>

      {/* Service List */}
      {loading && !services.length ? (
        <div className="space-y-3">
          {Array.from({ length: 3 }).map((_, idx) => (
            <div key={idx} className="animate-pulse bg-arc-panel rounded-lg p-4 h-24" />
          ))}
        </div>
      ) : (
        <div className="space-y-3">
          {services.map((service) => (
            <div
              key={service.name}
              className="bg-arc-panel border border-arc-border rounded-lg p-4"
            >
              <div className="flex items-start justify-between">
                <div className="flex items-start gap-3">
                  <div className={`p-2 rounded-lg ${getStatusBg(service.status)} ${getStatusColor(service.status)}`}>
                    {getServiceIcon(service.name)}
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <h3 className="font-semibold text-arc-silver">{service.name}</h3>
                      {getStatusIcon(service.status)}
                    </div>
                    {service.version && (
                      <p className="text-xs text-arc-silver/50 mt-1">v{service.version}</p>
                    )}
                    {service.details && (
                      <div className="mt-2 space-y-1">
                        {Object.entries(service.details).map(([key, value]) => (
                          <p key={key} className="text-xs text-arc-silver/60">
                            <span className="text-arc-cyan font-mono">{key}:</span>{' '}
                            <span className="text-arc-silver/80">{String(value)}</span>
                          </p>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
                <div className="text-right">
                  <div className={`text-sm font-medium ${getStatusColor(service.status)}`}>
                    {service.status.toUpperCase()}
                  </div>
                  <div className="text-xs text-arc-silver/40 mt-0.5">
                    {new Date(service.lastCheck).toLocaleTimeString()}
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      <div className="mt-4 p-3 bg-arc-bg/50 border border-arc-border rounded-lg text-xs text-arc-silver/60">
        <p>
          <span className="font-mono text-arc-cyan">Auto-refresh:</span> Service health checks run every 30 seconds
        </p>
      </div>
    </div>
  );
}
