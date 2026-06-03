import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Command } from '@tauri-apps/plugin-shell';
import { STARTER_APPS, GROUPS, StarterApp } from '../data/starterApps';

export default function AppDashboard() {
  const [activeApp, setActiveApp] = useState<StarterApp | null>(null);
  const [isRunning, setIsRunning] = useState(false);

  const handleLaunch = async (app: StarterApp) => {
    setActiveApp(app);
    setIsRunning(true);
    
    // Attempt to run the python command using Tauri's shell plugin
    try {
      // Note: In a production environment, you would need to configure tauri.conf.json 
      // to allow these specific commands. For now, this serves as the visual logic.
      const cmdParts = app.command.split(' ');
      if (cmdParts.length > 0) {
        const binary = cmdParts[0]; // e.g., 'python3'
        const args = cmdParts.slice(1);

        const command = Command.create(binary, args);

        command.on('close', data => {
          console.log(`Command finished with code ${data.code}`);
          setIsRunning(false);
          setActiveApp(null);
        });

        command.on('error', error => {
          console.error(`Command error: "${error}"`);
          setIsRunning(false);
          setActiveApp(null);
        });

        command.stdout.on('data', line => console.log(`stdout: ${line}`));
        command.stderr.on('data', line => console.log(`stderr: ${line}`));

        const child = await command.spawn();
        console.log('Spawned PID:', child.pid);
      }
    } catch (e) {
      console.error("Failed to execute command", e);
      setIsRunning(false);
    }
  };

  return (
    <div className="min-h-screen p-8 md:p-12 lg:p-16 flex flex-col items-center justify-start animate-fade-in">
      <header className="w-full max-w-5xl mb-12 flex flex-col items-center text-center">
        <h1 className="text-5xl font-bold tracking-tight mb-4 text-white drop-shadow-lg">
          Phoenix <span className="text-gradient">Flagship Suite</span>
        </h1>
        <p className="text-gray-400 text-lg max-w-2xl">
          These are not random utilities. This is the flagship starter layer of the OS.
        </p>
      </header>

      <div className="w-full max-w-5xl grid grid-cols-1 gap-12">
        {GROUPS.map((group, groupIdx) => {
          const groupApps = STARTER_APPS.filter(app => app.groupId === group.id);
          
          if (groupApps.length === 0) return null;

          return (
            <motion.section 
              key={group.id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: groupIdx * 0.15, duration: 0.5 }}
              className="flex flex-col gap-6"
            >
              <div className="border-b border-white/10 pb-2">
                <h2 className="text-2xl font-semibold text-white tracking-wide">{group.name}</h2>
                <p className="text-sm text-gray-500 mt-1">{group.description}</p>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
                {groupApps.map((app, appIdx) => {
                  const Icon = app.icon;
                  const isActive = activeApp?.id === app.id;

                  return (
                    <motion.div
                      key={app.id}
                      whileHover={{ scale: 1.02, y: -2 }}
                      whileTap={{ scale: 0.98 }}
                      initial={{ opacity: 0, scale: 0.9 }}
                      animate={{ opacity: 1, scale: 1 }}
                      transition={{ delay: (groupIdx * 0.1) + (appIdx * 0.05) }}
                      className="glass-panel p-6 rounded-2xl flex flex-col justify-between cursor-pointer group relative overflow-hidden"
                      onClick={() => handleLaunch(app)}
                    >
                      {/* Glow Effect */}
                      <div className="absolute inset-0 bg-gradient-to-br from-primary/0 to-primary/0 group-hover:from-primary/10 group-hover:to-accent/5 transition-colors duration-500" />
                      
                      <div className="relative z-10">
                        <div className="w-12 h-12 rounded-xl bg-white/5 border border-white/10 flex items-center justify-center mb-4 group-hover:border-primary/50 transition-colors">
                          <Icon className="w-6 h-6 text-gray-300 group-hover:text-primary transition-colors" />
                        </div>
                        <h3 className="text-xl font-medium text-white mb-2">{app.name}</h3>
                        <p className="text-sm text-gray-400 leading-relaxed mb-6">
                          {app.pitch}
                        </p>
                      </div>

                      <div className="relative z-10 flex items-center justify-between mt-auto">
                        <span className="text-xs font-mono text-gray-600 bg-black/30 px-2 py-1 rounded">
                          {app.command}
                        </span>
                        
                        <AnimatePresence>
                          {isActive && isRunning && (
                            <motion.div 
                              initial={{ opacity: 0, scale: 0.8 }}
                              animate={{ opacity: 1, scale: 1 }}
                              exit={{ opacity: 0, scale: 0.8 }}
                              className="w-4 h-4 rounded-full border-2 border-primary border-t-transparent animate-spin"
                            />
                          )}
                        </AnimatePresence>
                      </div>
                    </motion.div>
                  );
                })}
              </div>
            </motion.section>
          );
        })}
      </div>
    </div>
  );
}
