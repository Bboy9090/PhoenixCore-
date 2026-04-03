import React, { useState, useEffect } from 'react';

// ─── Components ──────────────────────────────────────────────────────────────

const SplashScreen: React.FC<{ onComplete: () => void }> = ({ onComplete }) => {
  useEffect(() => {
    const timer = setTimeout(onComplete, 3000);
    return () => clearTimeout(timer);
  }, [onComplete]);

  return (
    <div className="fixed inset-0 flex flex-col items-center justify-center bg-black z-50">
      <div className="relative">
        <div className="absolute inset-0 bg-accent-primary animate-phoenix-glow rounded-full"></div>
        <div className="relative text-accent-primary text-9xl font-bold tracking-tighter">
          PHX
        </div>
      </div>
      <div className="mt-12 text-accent-primary/60 font-mono tracking-widest uppercase">
        Initializing Phoenix Recovery Environment
      </div>
      <div className="mt-4 flex gap-1">
        {[0, 1, 2].map((i) => (
          <div key={i} className="w-1 h-1 bg-accent-primary rounded-full animate-bounce" style={{ animationDelay: `${i * 0.2}s` }}></div>
        ))}
      </div>
    </div>
  );
};

const Dashboard: React.FC = () => {
  const [metrics, setMetrics] = useState({ cpu: 0, ram: 0, temp: 0 });

  useEffect(() => {
    const interval = setInterval(() => {
      setMetrics({
        cpu: Math.floor(Math.random() * 20) + 10,
        ram: Math.floor(Math.random() * 15) + 30,
        temp: Math.floor(Math.random() * 10) + 40,
      });
    }, 2000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="min-h-screen p-8 flex flex-col">
      <header className="flex justify-between items-center mb-12">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-accent-primary rounded-lg flex items-center justify-center text-black font-bold">P</div>
          <h1 className="text-2xl font-bold tracking-tight">Phoenix Core <span className="text-accent-primary">RE</span></h1>
        </div>
        <div className="flex items-center gap-4 text-xs font-mono text-white/40 uppercase">
          <span>Session: PRE-ALPHA-01</span>
          <span>•</span>
          <span className="text-accent-primary">Online</span>
        </div>
      </header>

      <main className="grid grid-cols-12 gap-6 flex-1">
        {/* Left Column - Diagnostics */}
        <div className="col-span-4 flex flex-col gap-6">
          <div className="glass-card p-6 flex-1">
            <h3 className="text-sm font-mono text-white/60 mb-6 uppercase tracking-wider">System Metrics</h3>
            <div className="space-y-8">
              <MetricBar label="CPU LOAD" value={metrics.cpu} color="accent-primary" />
              <MetricBar label="MEM USAGE" value={metrics.ram} color="accent-primary" />
              <MetricBar label="TEMPERATURE" value={metrics.temp} unit="°C" color={metrics.temp > 50 ? 'red-500' : 'accent-primary'} />
            </div>
          </div>
          
          <div className="glass-card p-6 h-48">
            <h3 className="text-sm font-mono text-white/60 mb-4 uppercase tracking-wider">Hardware Profile</h3>
            <div className="text-xs space-y-2 font-mono text-white/40">
              <div className="flex justify-between"><span>Processor</span> <span className="text-white">x86_64 Generic</span></div>
              <div className="flex justify-between"><span>Platform</span> <span className="text-white">Phoenix LiveOS</span></div>
              <div className="flex justify-between"><span>Boot Mode</span> <span className="text-white">UEFI (Secure)</span></div>
            </div>
          </div>
        </div>

        {/* Right Column - Main Wizard */}
        <div className="col-span-8 glass-card p-12 flex flex-col items-center justify-center relative overflow-hidden">
          <div className="absolute top-0 right-0 p-8">
            <div className="text-7xl font-bold text-white/[0.03] select-none">RECOVERY</div>
          </div>
          
          <div className="max-w-md w-full text-center">
            <div className="w-20 h-20 bg-accent-primary/10 rounded-full flex items-center justify-center mx-auto mb-8 accent-glow">
              <span className="text-3xl">🛠️</span>
            </div>
            <h2 className="text-4xl font-bold mb-4">Phoenix Recovery Suite</h2>
            <p className="text-white/60 mb-12">Automated system diagnostics and OS deployment for all Phoenix Core supported platforms.</p>
            
            <div className="grid grid-cols-2 gap-4">
              <button className="phoenix-button w-full">Start Setup Wizard</button>
              <button className="bg-white/5 border border-white/10 text-white font-bold py-3 px-6 rounded-xl hover:bg-white/10 transition-all">Launch Shell</button>
            </div>
          </div>
        </div>
      </main>

      <footer className="mt-12 flex justify-between items-center text-[10px] font-mono text-white/20 uppercase tracking-widest">
        <div>Proprietary Build © 2026 Phoenix Core Project</div>
        <div className="flex gap-6">
          <span>Logs</span>
          <span>Security</span>
          <span>Support</span>
        </div>
      </footer>
    </div>
  );
};

const MetricBar: React.FC<{ label: string, value: number, unit?: string, color: string }> = ({ label, value, unit = '%', color }) => (
  <div>
    <div className="flex justify-between text-[10px] font-mono mb-2 opacity-60">
      <span>{label}</span>
      <span>{value}{unit}</span>
    </div>
    <div className="h-1 bg-white/5 rounded-full overflow-hidden">
      <div 
        className={`h-full bg-${color} transition-all duration-1000`} 
        style={{ width: `${value}%`, filter: 'drop-shadow(0 0 4px currentColor)' }}
      ></div>
    </div>
  </div>
);

// ─── App ───────────────────────────────────────────────────────────────────

function App() {
  const [loading, setLoading] = useState(true);

  return (
    <>
      {loading ? (
        <SplashScreen onComplete={() => setLoading(false)} />
      ) : (
        <Dashboard />
      )}
    </>
  );
}

export default App;
