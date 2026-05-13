import React from 'react';
import { RotateCcw } from 'lucide-react';

export default function Recovery() {
  return (
    <div className="p-8 space-y-8">
      <div>
        <h1 className="text-3xl font-bold text-slate-900 dark:text-white">System Recovery</h1>
        <p className="text-slate-600 dark:text-slate-400 mt-2">Create and restore system recovery points</p>
      </div>

      <div className="card flex items-center justify-center py-12">
        <div className="text-center">
          <RotateCcw size={48} className="mx-auto text-slate-400 mb-4" />
          <p className="text-slate-600 dark:text-slate-400">Recovery features coming soon...</p>
        </div>
      </div>
    </div>
  );
}
