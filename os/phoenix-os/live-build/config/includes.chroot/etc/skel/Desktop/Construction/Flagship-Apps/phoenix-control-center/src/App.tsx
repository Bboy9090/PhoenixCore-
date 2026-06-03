import BuildDashboard from './components/dashboard/BuildDashboard';
import SystemInfo from './components/dashboard/SystemInfo';
import DiskManagement from './components/dashboard/DiskManagement';
import { ArcwyreLogo } from './components/ArcwyreLogo';

function App() {
  return (
    <div className="min-h-screen bg-arc-bg text-arc-silver font-sans">
      {/* Sidebar / Navigation Placeholder */}
      <div className="flex">
        <aside className="w-72 border-r border-arc-border min-h-screen p-8 bg-arc-surface flex flex-col">
          <div className="flex items-center gap-4 mb-16">
            <ArcwyreLogo size={40} className="drop-shadow-[0_0_10px_rgba(49,215,255,0.4)]" />
            <div className="flex flex-col">
              <span className="font-bold text-2xl tracking-tighter text-arc-cyan leading-none">ARCWYRE</span>
              <span className="text-[10px] uppercase tracking-[0.2em] text-arc-silver/40 font-mono mt-1">Machine Registry</span>
            </div>
          </div>
          
          <nav className="space-y-2 flex-1">
            <div className="text-arc-cyan font-semibold px-4 py-3 bg-arc-panel/50 border border-arc-cyan/20 rounded-lg cursor-pointer flex items-center gap-3">
              <div className="w-1.5 h-1.5 bg-arc-cyan rounded-full animate-pulse" />
              Forge Dashboard
            </div>
            <div className="text-arc-silver/50 px-4 py-3 hover:bg-arc-panel hover:text-arc-silver rounded-lg cursor-pointer transition-all duration-300 flex items-center gap-3">
              <div className="w-1.5 h-1.5 bg-arc-silver/20 rounded-full" />
              Disk Logistics
            </div>
            <div className="text-arc-silver/50 px-4 py-3 hover:bg-arc-panel hover:text-arc-silver rounded-lg cursor-pointer transition-all duration-300 flex items-center gap-3">
              <div className="w-1.5 h-1.5 bg-arc-silver/20 rounded-full" />
              Core Diagnostics
            </div>
          </nav>

          <div className="mt-auto pt-8 border-t border-arc-border">
            <div className="bg-arc-panel p-4 rounded-xl border border-arc-border">
              <div className="text-[10px] uppercase text-arc-silver/40 font-mono mb-2">Machine Status</div>
              <div className="text-arc-success font-mono text-sm flex items-center gap-2">
                <span className="w-2 h-2 bg-arc-success rounded-full" />
                CRYSTAL_CLEAN
              </div>
            </div>
          </div>
        </aside>

        <main className="flex-1 overflow-y-auto">
          <BuildDashboard />
          <div className="grid grid-cols-1 xl:grid-cols-2 gap-8 p-6">
            <SystemInfo />
            <DiskManagement />
          </div>
        </main>
      </div>
    </div>
  );
}

export default App;
