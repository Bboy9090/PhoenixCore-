import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Home, HardDrive, RotateCcw, Settings, Zap } from 'lucide-react';
import { useThemeStore } from '@stores/themeStore';

const menuItems = [
  { path: '/', label: 'Dashboard', icon: Home },
  { path: '/system', label: 'System Info', icon: Zap },
  { path: '/disk', label: 'Disk Management', icon: HardDrive },
  { path: '/recovery', label: 'Recovery', icon: RotateCcw },
  { path: '/settings', label: 'Settings', icon: Settings },
];

export default function Sidebar() {
  const location = useLocation();
  const { isDark, toggleTheme } = useThemeStore();

  return (
    <aside className="w-64 bg-white dark:bg-slate-800 border-r border-slate-200 dark:border-slate-700 flex flex-col">
      {/* Logo */}
      <div className="p-6 border-b border-slate-200 dark:border-slate-700">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-phoenix-600 rounded-lg flex items-center justify-center">
            <span className="text-white font-bold text-lg">P</span>
          </div>
          <div>
            <h1 className="font-bold text-slate-900 dark:text-white">Phoenix</h1>
            <p className="text-xs text-slate-500 dark:text-slate-400">Control Center</p>
          </div>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-4 py-6 space-y-2">
        {menuItems.map((item) => {
          const Icon = item.icon;
          const isActive = location.pathname === item.path;

          return (
            <Link
              key={item.path}
              to={item.path}
              className={`flex items-center gap-3 px-4 py-3 rounded-lg transition-colors ${
                isActive
                  ? 'bg-phoenix-100 dark:bg-phoenix-900 text-phoenix-600 dark:text-phoenix-400'
                  : 'text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-700'
              }`}
            >
              <Icon size={20} />
              <span className="font-medium">{item.label}</span>
            </Link>
          );
        })}
      </nav>

      {/* Footer */}
      <div className="p-4 border-t border-slate-200 dark:border-slate-700 space-y-3">
        <button
          onClick={toggleTheme}
          className="w-full flex items-center justify-center gap-2 px-4 py-2 rounded-lg bg-slate-100 dark:bg-slate-700 text-slate-900 dark:text-slate-50 hover:bg-slate-200 dark:hover:bg-slate-600 transition-colors"
        >
          {isDark ? '☀️' : '🌙'}
          <span className="text-sm font-medium">{isDark ? 'Light' : 'Dark'}</span>
        </button>
        <p className="text-xs text-slate-500 dark:text-slate-400 text-center">
          Phoenix OS v2.0.0
        </p>
      </div>
    </aside>
  );
}
