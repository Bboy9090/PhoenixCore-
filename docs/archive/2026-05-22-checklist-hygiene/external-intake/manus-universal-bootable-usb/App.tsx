import React, { useEffect, useState } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Sidebar from '@components/Sidebar';
import Header from '@components/Header';
import Dashboard from '@pages/Dashboard';
import SystemInfo from '@pages/SystemInfo';
import DiskManagement from '@pages/DiskManagement';
import Recovery from '@pages/Recovery';
import Settings from '@pages/Settings';
import { useThemeStore } from '@stores/themeStore';

export default function App() {
  const { isDark, initTheme } = useThemeStore();
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    initTheme();
    setIsLoading(false);
  }, [initTheme]);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-screen bg-slate-50 dark:bg-slate-900">
        <div className="text-center">
          <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-phoenix-600"></div>
          <p className="mt-4 text-slate-600 dark:text-slate-400">Loading Phoenix Control Center...</p>
        </div>
      </div>
    );
  }

  return (
    <Router>
      <div className={isDark ? 'dark' : ''}>
        <div className="flex h-screen bg-slate-50 dark:bg-slate-900 text-slate-900 dark:text-slate-50">
          <Sidebar />
          <div className="flex-1 flex flex-col overflow-hidden">
            <Header />
            <main className="flex-1 overflow-auto">
              <Routes>
                <Route path="/" element={<Dashboard />} />
                <Route path="/system" element={<SystemInfo />} />
                <Route path="/disk" element={<DiskManagement />} />
                <Route path="/recovery" element={<Recovery />} />
                <Route path="/settings" element={<Settings />} />
              </Routes>
            </main>
          </div>
        </div>
      </div>
    </Router>
  );
}
