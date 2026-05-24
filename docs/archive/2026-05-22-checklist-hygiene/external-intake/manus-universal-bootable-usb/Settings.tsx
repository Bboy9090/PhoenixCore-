import React from 'react';
import { Settings as SettingsIcon } from 'lucide-react';

export default function Settings() {
  return (
    <div className="p-8 space-y-8">
      <div>
        <h1 className="text-3xl font-bold text-slate-900 dark:text-white">Settings</h1>
        <p className="text-slate-600 dark:text-slate-400 mt-2">Configure Phoenix Control Center</p>
      </div>

      <div className="card flex items-center justify-center py-12">
        <div className="text-center">
          <SettingsIcon size={48} className="mx-auto text-slate-400 mb-4" />
          <p className="text-slate-600 dark:text-slate-400">Settings coming soon...</p>
        </div>
      </div>
    </div>
  );
}
