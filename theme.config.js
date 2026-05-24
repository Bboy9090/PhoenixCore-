/** @type {const} */
// Phoenix Core — Premium Blue Phoenix & Home Aurelia Color System
// Primary: Electric Blue (#00d2ff), Accent: Gold (#ffd700), Purple (#9d4edd), Cyan (#00ffff)
const themeColors = {
  // Electric Blue — the Phoenix Core signature color
  primary:    { light: '#00b0e6', dark: '#00d2ff' },
  // Deep Space Navy backgrounds
  background: { light: '#f0f4f8', dark: '#050811' },
  // Panel / card surfaces
  surface:    { light: '#ffffff', dark: '#0a0e1a' },
  // Primary text
  foreground: { light: '#0d1117', dark: '#ffffff' },
  // Secondary / muted text
  muted:      { light: '#64748b', dark: '#94a3b8' },
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
