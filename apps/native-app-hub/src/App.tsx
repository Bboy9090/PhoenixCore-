import { useState, useEffect } from 'react';
import AppDashboard from './components/AppDashboard';

const THEMES = [
  { id: 'native', name: 'Native' },
  { id: 'aurelia', name: 'Aurelia' },
  { id: 'arcwyre', name: 'Arcwyre' },
  { id: 'thundergod', name: 'Thundergod' }
];

function App() {
  const [theme, setTheme] = useState('native');

  useEffect(() => {
    document.body.setAttribute('data-theme', theme);
  }, [theme]);

  return (
    <main className="relative w-full min-h-screen bg-background overflow-hidden transition-colors duration-700">
      {/* Zenith Volumetric Orbs */}
      <div className="absolute top-[-10%] left-[-10%] w-[50vw] h-[50vw] bg-primary/20 rounded-full blur-[120px] mix-blend-screen animate-pulse-slow pointer-events-none" />
      <div className="absolute bottom-[-10%] right-[-10%] w-[40vw] h-[40vw] bg-accent/20 rounded-full blur-[100px] mix-blend-screen animate-pulse-slow pointer-events-none" style={{ animationDelay: '1.5s' }} />

      {/* Theme Switcher (for demonstration/build config) */}
      <div className="absolute top-4 right-4 z-50 flex gap-2 glass-panel px-4 py-2 rounded-full">
        {THEMES.map(t => (
          <button
            key={t.id}
            onClick={() => setTheme(t.id)}
            className={`text-xs font-semibold px-3 py-1 rounded-full transition-all ${
              theme === t.id 
                ? 'bg-gradient-to-r from-primary to-accent text-white shadow-lg' 
                : 'text-gray-400 hover:text-white hover:bg-white/10'
            }`}
          >
            {t.name}
          </button>
        ))}
      </div>

      <AppDashboard />
    </main>
  );
}

export default App;
