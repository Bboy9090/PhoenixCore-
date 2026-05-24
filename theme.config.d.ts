export const themeColors: {
  primary:    { light: string; dark: string };
  background: { light: string; dark: string };
  surface:    { light: string; dark: string };
  foreground: { light: string; dark: string };
  muted:      { light: string; dark: string };
  border:     { light: string; dark: string };
  success:    { light: string; dark: string };
  warning:    { light: string; dark: string };
  error:      { light: string; dark: string };
  // Phoenix Core extended palette
  gold:       { light: string; dark: string };
  purple:     { light: string; dark: string };
  cyan:       { light: string; dark: string };
  cardBg:     { light: string; dark: string };
};

declare const themeConfig: {
  themeColors: typeof themeColors;
};

export default themeConfig;
