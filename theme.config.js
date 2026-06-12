/** @type {const} */
// Arcwyre Control Center Color System (matching Desktop theme.py)
const themeColors = {
  // Arcwyre Cyan
  primary:    { light: '#00B0CC', dark: '#00D0E5' },
  // Arcwyre Window Background
  background: { light: '#f0f4f8', dark: '#1E1E1E' },
  // Arcwyre Elevated Surfaces
  surface:    { light: '#ffffff', dark: '#2C2C2E' },
  // Primary text
  foreground: { light: '#0d1117', dark: '#FFFFFF' },
  // Secondary / muted text
  muted:      { light: '#64748b', dark: '#98989D' },
  // Borders
  border:     { light: '#e2e8f0', dark: 'rgba(255,255,255,0.08)' },
  // Status colors
  success:    { light: '#10b981', dark: '#10b981' },
  warning:    { light: '#ffd700', dark: '#ffd700' },
  error:      { light: '#f43f5e', dark: '#f43f5e' },
  // Phoenix-specific accent tokens (extra, safe to extend)
  gold:       { light: '#cc9900', dark: '#ffd700' },
  purple:     { light: '#7c3aed', dark: '#9d4edd' },
  cyan:       { light: '#00b4cc', dark: '#00ffff' },
  cardBg:     { light: '#f8fafc', dark: '#080c16' },
};

module.exports = { themeColors };
