/**
 * Phoenix Core Design System
 * Dark theme with phoenix blue accent colors
 */

export const Colors = {
  // Background layers
  bg: {
    primary: '#0a0a0f',
    secondary: '#12121a',
    tertiary: '#1a1a26',
    card: '#16161f',
    elevated: '#1e1e2e',
    overlay: 'rgba(0, 0, 0, 0.7)',
  },

  // Phoenix accent colors
  accent: {
    primary: '#00d4ff',
    secondary: '#0099cc',
    tertiary: '#006699',
    glow: 'rgba(0, 212, 255, 0.15)',
    glowStrong: 'rgba(0, 212, 255, 0.3)',
  },

  // Status colors
  status: {
    success: '#28a745',
    successBg: 'rgba(40, 167, 69, 0.15)',
    warning: '#ffc107',
    warningBg: 'rgba(255, 193, 7, 0.15)',
    error: '#dc3545',
    errorBg: 'rgba(220, 53, 69, 0.15)',
    info: '#17a2b8',
    infoBg: 'rgba(23, 162, 184, 0.15)',
  },

  // Risk level colors
  risk: {
    low: '#28a745',
    medium: '#ffc107',
    high: '#fd7e14',
    critical: '#dc3545',
  },

  // Text
  text: {
    primary: '#ffffff',
    secondary: '#cccccc',
    tertiary: '#888888',
    muted: '#555566',
    accent: '#00d4ff',
  },

  // Borders
  border: {
    default: 'rgba(255, 255, 255, 0.1)',
    accent: 'rgba(0, 212, 255, 0.3)',
    strong: 'rgba(255, 255, 255, 0.2)',
  },

  // OS type colors
  os: {
    macos: '#a8b5c8',
    windows: '#0078d4',
    linux: '#f7c948',
    custom: '#9b59b6',
  },
};

export const Typography = {
  fontFamily: {
    regular: 'System',
    mono: 'Courier',
  },
  size: {
    xs: 10,
    sm: 12,
    base: 14,
    md: 16,
    lg: 18,
    xl: 22,
    '2xl': 26,
    '3xl': 32,
    '4xl': 40,
  },
  weight: {
    regular: '400' as const,
    medium: '500' as const,
    semibold: '600' as const,
    bold: '700' as const,
    extrabold: '800' as const,
  },
};

export const Spacing = {
  xs: 4,
  sm: 8,
  md: 12,
  base: 16,
  lg: 20,
  xl: 24,
  '2xl': 32,
  '3xl': 40,
  '4xl': 48,
};

export const BorderRadius = {
  sm: 6,
  md: 10,
  lg: 14,
  xl: 18,
  '2xl': 24,
  full: 9999,
};

export const Shadows = {
  sm: {
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.3,
    shadowRadius: 4,
    elevation: 3,
  },
  md: {
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.4,
    shadowRadius: 8,
    elevation: 6,
  },
  accent: {
    shadowColor: '#00d4ff',
    shadowOffset: { width: 0, height: 0 },
    shadowOpacity: 0.4,
    shadowRadius: 12,
    elevation: 8,
  },
};

export const getRiskColor = (risk: string): string => {
  switch (risk) {
    case 'low': return Colors.risk.low;
    case 'medium': return Colors.risk.medium;
    case 'high': return Colors.risk.high;
    case 'critical': return Colors.risk.critical;
    default: return Colors.text.tertiary;
  }
};

export const getOSColor = (osType: string): string => {
  switch (osType) {
    case 'macos': return Colors.os.macos;
    case 'windows': return Colors.os.windows;
    case 'linux': return Colors.os.linux;
    default: return Colors.os.custom;
  }
};

export const getOSIcon = (osType: string): string => {
  switch (osType) {
    case 'macos': return '🍎';
    case 'windows': return '🪟';
    case 'linux': return '🐧';
    default: return '💾';
  }
};

export const getStatusColor = (status: string): string => {
  switch (status) {
    case 'complete': return Colors.status.success;
    case 'failed': return Colors.status.error;
    case 'cancelled': return Colors.text.tertiary;
    case 'writing':
    case 'formatting':
    case 'verifying':
    case 'patching':
    case 'preparing': return Colors.accent.primary;
    default: return Colors.text.secondary;
  }
};
