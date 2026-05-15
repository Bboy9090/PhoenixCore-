import { useState, useEffect } from 'react';

interface ThemeState {
  isDark: boolean;
}

const STORAGE_KEY = 'arcwyre-theme-storage';

const getInitialState = (): ThemeState => {
  const stored = localStorage.getItem(STORAGE_KEY);
  if (stored) {
    try {
      return JSON.parse(stored);
    } catch (e) {
      console.error('Failed to parse theme storage', e);
    }
  }
  return { isDark: window.matchMedia('(prefers-color-scheme: dark)').matches };
};

let globalState = getInitialState();
const listeners = new Set<(state: ThemeState) => void>();

const setState = (partial: Partial<ThemeState>) => {
  globalState = { ...globalState, ...partial };
  localStorage.setItem(STORAGE_KEY, JSON.stringify(globalState));
  listeners.forEach((listener) => listener(globalState));
};

export const useThemeStore = <T>(selector: (state: ThemeState & any) => T): T => {
  const [state, setLocalState] = useState(globalState);

  useEffect(() => {
    const listener = (newState: ThemeState) => setLocalState(newState);
    listeners.add(listener);
    return () => {
      listeners.delete(listener);
    };
  }, []);

  const actions = {
    toggleTheme: () => setState({ isDark: !globalState.isDark }),
    setTheme: (isDark: boolean) => setState({ isDark }),
    initTheme: () => {
      const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
      setState({ isDark: prefersDark });
    },
  };

  return selector({ ...state, ...actions });
};
