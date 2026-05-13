import React, { useEffect, useState } from 'react';
import { Bell, User, Clock } from 'lucide-react';
import { systemService } from '@services/systemService';

export default function Header() {
  const [time, setTime] = useState(new Date());
  const [systemUptime, setSystemUptime] = useState('Loading...');

  useEffect(() => {
    // Update time every second
    const timer = setInterval(() => setTime(new Date()), 1000);
    return () => clearInterval(timer);
  }, []);

  useEffect(() => {
    // Fetch system uptime
    const fetchUptime = async () => {
      try {
        const info = await systemService.getSystemInfo();
        const hours = Math.floor(info.uptime / 3600);
        const minutes = Math.floor((info.uptime % 3600) / 60);
        setSystemUptime(`${hours}h ${minutes}m`);
      } catch (error) {
        console.error('Failed to fetch uptime:', error);
      }
    };

    fetchUptime();
    const interval = setInterval(fetchUptime, 60000); // Update every minute
    return () => clearInterval(interval);
  }, []);

  return (
    <header className="bg-white dark:bg-slate-800 border-b border-slate-200 dark:border-slate-700 px-8 py-4 flex items-center justify-between">
      <div className="flex items-center gap-4">
        <Clock size={20} className="text-slate-500 dark:text-slate-400" />
        <div>
          <p className="text-sm text-slate-500 dark:text-slate-400">System Uptime</p>
          <p className="font-semibold text-slate-900 dark:text-white">{systemUptime}</p>
        </div>
      </div>

      <div className="flex items-center gap-6">
        <div className="text-right">
          <p className="text-sm text-slate-500 dark:text-slate-400">Current Time</p>
          <p className="font-semibold text-slate-900 dark:text-white">
            {time.toLocaleTimeString()}
          </p>
        </div>

        <button className="relative p-2 text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-700 rounded-lg transition-colors">
          <Bell size={20} />
          <span className="absolute top-1 right-1 w-2 h-2 bg-red-500 rounded-full"></span>
        </button>

        <button className="p-2 text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-700 rounded-lg transition-colors">
          <User size={20} />
        </button>
      </div>
    </header>
  );
}
