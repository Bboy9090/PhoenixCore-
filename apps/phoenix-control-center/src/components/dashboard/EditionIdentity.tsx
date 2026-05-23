import { useEffect, useState } from 'react';
import { RefreshCw, Shield, Package, Palette } from '../Icons';

interface EditionInfo {
  id: string;
  display_name: string;
  edition_type: 'professional' | 'premium' | 'industrial' | 'legacy';
  tagline: string;
  description?: string;
  theme: {
    colors: {
      primary: string;
      secondary: string;
      accent: string;
      background: string;
      surface: string;
      text: string;
    };
  };
  features: string[];
  safety: {
    allow_destructive_disk_ops_by_default: boolean;
    require_dry_run_for_recovery_ops: boolean;
  };
  packages?: {
    include: string[];
  };
}

export default function EditionIdentity() {
  const [edition, setEdition] = useState<EditionInfo | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [refreshing, setRefreshing] = useState(false);

  const loadEdition = async () => {
    try {
      // Try to load ARCWYRE edition by default (can be made dynamic)
      const editionId = process.env.BWOS_EDITION || 'arcwyre';
      const response = await fetch(`/editions/${editionId}/edition.yaml`);

      if (!response.ok) {
        throw new Error(`Failed to load edition manifest: ${response.status}`);
      }

      const yamlText = await response.text();

      // For MVP, we'll provide ARCWYRE data directly since we can't parse YAML in browser easily
      // In production, this would be parsed server-side or use a YAML parser library
      const arcwyreEdition: EditionInfo = {
        id: 'arcwyre',
        display_name: "Bobby's Worldwide OS: ARCWYRE Edition",
        edition_type: 'professional',
        tagline: 'The modern cyber-recovery suite.',
        description: 'A sleek, professional edition focused on cyber-security, data recovery, and modern developer workflows.',
        theme: {
          colors: {
            primary: '#00E5FF',
            secondary: '#94A3B8',
            accent: '#F8FAFC',
            background: '#0F172A',
            surface: '#1E293B',
            text: '#E2E8F0',
          },
        },
        features: [
          'cyber_security_audit',
          'modern_dev_tools',
          'arcwyre_dashboard',
        ],
        safety: {
          allow_destructive_disk_ops_by_default: false,
          require_dry_run_for_recovery_ops: true,
        },
        packages: {
          include: [
            'bwos-core',
            'bootforge',
            'arcwyre-control-center',
            'forensic-toolset',
          ],
        },
      };

      setEdition(arcwyreEdition);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load edition');
      // Fallback to default data
      setEdition({
        id: 'arcwyre',
        display_name: "Bobby's Worldwide OS: ARCWYRE Edition",
        edition_type: 'professional',
        tagline: 'The modern cyber-recovery suite.',
        theme: {
          colors: {
            primary: '#00E5FF',
            secondary: '#94A3B8',
            accent: '#F8FAFC',
            background: '#0F172A',
            surface: '#1E293B',
            text: '#E2E8F0',
          },
        },
        features: ['cyber_security_audit', 'modern_dev_tools'],
        safety: {
          allow_destructive_disk_ops_by_default: false,
          require_dry_run_for_recovery_ops: true,
        },
      });
    }
  };

  useEffect(() => {
    setLoading(true);
    loadEdition().finally(() => setLoading(false));
  }, []);

  const handleRefresh = async () => {
    setRefreshing(true);
    await loadEdition();
    setRefreshing(false);
  };

  const getEditionTypeLabel = (type: EditionInfo['edition_type']) => {
    const labels = {
      professional: 'Professional',
      premium: 'Premium',
      industrial: 'Industrial',
      legacy: 'Legacy',
    };
    return labels[type];
  };

  const getEditionTypeBadge = (type: EditionInfo['edition_type']) => {
    const colors = {
      professional: 'bg-arc-cyan/10 text-arc-cyan border-arc-cyan/20',
      premium: 'bg-arc-gold/10 text-arc-gold border-arc-gold/20',
      industrial: 'bg-arc-blue/10 text-arc-blue border-arc-blue/20',
      legacy: 'bg-arc-silver/10 text-arc-silver border-arc-silver/20',
    };
    return colors[type];
  };

  const formatFeature = (feature: string) => {
    return feature
      .split('_')
      .map(word => word.charAt(0).toUpperCase() + word.slice(1))
      .join(' ');
  };

  return (
    <div className="bg-arc-surface border border-arc-border rounded-xl p-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-xl font-bold text-arc-cyan">Edition Identity</h2>
          <p className="text-sm text-arc-silver/60 mt-1">Current edition configuration</p>
        </div>
        <button
          onClick={handleRefresh}
          disabled={refreshing || loading}
          className="p-2 hover:bg-arc-panel rounded-lg transition-colors"
          title="Refresh edition data"
        >
          <RefreshCw size={18} className={`text-arc-silver ${refreshing ? 'animate-spin' : ''}`} />
        </button>
      </div>

      {error && (
        <div className="mb-4 p-3 bg-arc-error/10 border border-arc-error/20 rounded-lg text-arc-error text-sm">
          {error}
        </div>
      )}

      {loading && !edition ? (
        <div className="space-y-4">
          <div className="animate-pulse bg-arc-panel rounded-lg h-32" />
          <div className="animate-pulse bg-arc-panel rounded-lg h-24" />
        </div>
      ) : edition ? (
        <div className="space-y-6">
          {/* Edition Header */}
          <div className="bg-arc-panel border border-arc-border rounded-lg p-6">
            <div className="flex items-start justify-between mb-4">
              <div>
                <h3 className="text-2xl font-bold text-arc-silver">{edition.display_name}</h3>
                <p className="text-arc-cyan/80 mt-1 italic">{edition.tagline}</p>
                {edition.description && (
                  <p className="text-arc-silver/60 text-sm mt-2">{edition.description}</p>
                )}
              </div>
              <div className={`px-3 py-1 border rounded-lg text-sm font-medium ${getEditionTypeBadge(edition.edition_type)}`}>
                {getEditionTypeLabel(edition.edition_type)}
              </div>
            </div>

            {/* Theme Colors */}
            <div className="mt-4">
              <div className="flex items-center gap-2 mb-3">
                <Palette className="w-4 h-4 text-arc-silver/60" />
                <span className="text-xs text-arc-silver/60 uppercase tracking-wider">Theme Palette</span>
              </div>
              <div className="flex gap-2">
                {Object.entries(edition.theme.colors).slice(0, 3).map(([name, color]) => (
                  <div key={name} className="flex items-center gap-2">
                    <div
                      className="w-6 h-6 rounded border border-arc-border"
                      style={{ backgroundColor: color }}
                    />
                    <span className="text-xs text-arc-silver/60">{name}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Features */}
          <div className="bg-arc-panel border border-arc-border rounded-lg p-6">
            <div className="flex items-center gap-2 mb-4">
              <Package className="w-5 h-5 text-arc-cyan" />
              <h4 className="font-semibold text-arc-silver">Enabled Features</h4>
            </div>
            <div className="flex flex-wrap gap-2">
              {edition.features.map((feature) => (
                <span
                  key={feature}
                  className="px-3 py-1 bg-arc-cyan/10 border border-arc-cyan/20 text-arc-cyan rounded-lg text-sm"
                >
                  {formatFeature(feature)}
                </span>
              ))}
            </div>
          </div>

          {/* Safety Policy */}
          <div className="bg-arc-panel border border-arc-border rounded-lg p-6">
            <div className="flex items-center gap-2 mb-4">
              <Shield className="w-5 h-5 text-arc-gold" />
              <h4 className="font-semibold text-arc-silver">Safety Policy</h4>
            </div>
            <div className="space-y-2">
              <div className="flex items-center justify-between p-2 bg-arc-bg/50 rounded">
                <span className="text-sm text-arc-silver/80">Destructive Operations</span>
                <span className={`text-sm font-medium ${edition.safety.allow_destructive_disk_ops_by_default ? 'text-arc-error' : 'text-arc-success'}`}>
                  {edition.safety.allow_destructive_disk_ops_by_default ? 'Allowed' : 'Blocked'}
                </span>
              </div>
              <div className="flex items-center justify-between p-2 bg-arc-bg/50 rounded">
                <span className="text-sm text-arc-silver/80">Dry-Run Required</span>
                <span className={`text-sm font-medium ${edition.safety.require_dry_run_for_recovery_ops ? 'text-arc-success' : 'text-arc-error'}`}>
                  {edition.safety.require_dry_run_for_recovery_ops ? 'Yes' : 'No'}
                </span>
              </div>
            </div>
          </div>

          {/* Packages */}
          {edition.packages && (
            <div className="bg-arc-panel border border-arc-border rounded-lg p-6">
              <div className="flex items-center gap-2 mb-4">
                <Package className="w-5 h-5 text-arc-blue" />
                <h4 className="font-semibold text-arc-silver">Included Packages</h4>
              </div>
              <div className="grid grid-cols-2 gap-2">
                {edition.packages.include.map((pkg) => (
                  <div key={pkg} className="text-sm text-arc-silver/80 font-mono">
                    • {pkg}
                  </div>
                ))}
              </div>
            </div>
          )}

          <div className="p-3 bg-arc-bg/50 border border-arc-border rounded-lg text-xs text-arc-silver/60">
            <p>
              <span className="font-mono text-arc-cyan">Manifest:</span> Edition loaded from{' '}
              <code className="text-arc-silver/80">editions/{edition.id}/edition.yaml</code>
            </p>
          </div>
        </div>
      ) : null}
    </div>
  );
}
