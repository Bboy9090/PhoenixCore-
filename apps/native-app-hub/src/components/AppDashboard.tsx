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
    <div className="relative z-10 min-h-screen p-8 md:p-12 lg:p-16 flex flex-col items-center justify-start animate-fade-in">
      <header className="w-full max-w-5xl mb-12 flex flex-col items-center text-center">
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, ease: "easeOut" }}
        >
          <h1 className="text-5xl font-bold tracking-tight mb-4 text-gray-100 drop-shadow-2xl">
            Phoenix <span className="text-gradient">Flagship Suite</span>
          </h1>
          <p className="text-gray-400 text-lg max-w-2xl font-light">
            Zenith Edition • The volumetric flagship layer of the OS.
          </p>
        </motion.div>
      </header>

      <div className="w-full max-w-5xl grid grid-cols-1 gap-12">
        {GROUPS.map((group, groupIdx) => {
          const groupApps = STARTER_APPS.filter(app => app.groupId === group.id);
          
          if (groupApps.length === 0) return null;

          return (
            <motion.section 
              key={group.id}
              initial={{ opacity: 0, y: 30 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: groupIdx * 0.2, duration: 0.6, ease: "easeOut" }}
              className="flex flex-col gap-6"
            >
              <div className="border-b border-primary/20 pb-2">
                <h2 className="text-2xl font-semibold text-gray-100 tracking-wide flex items-center gap-2">
                  <span className="w-2 h-2 rounded-full bg-accent animate-pulse-slow"></span>
                  {group.name}
                </h2>
                <p className="text-sm text-gray-500 mt-1">{group.description}</p>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
                {groupApps.map((app, appIdx) => {
                  const Icon = app.icon;
                  const isActive = activeApp?.id === app.id;

                  return (
                    <motion.div
                      key={app.id}
                      whileHover={{ scale: 1.03, y: -5 }}
                      whileTap={{ scale: 0.97 }}
                      initial={{ opacity: 0, scale: 0.9 }}
                      animate={{ opacity: 1, scale: 1 }}
                      transition={{ delay: (groupIdx * 0.1) + (appIdx * 0.05), type: "spring", stiffness: 300, damping: 20 }}
                      className="glass-panel p-6 rounded-2xl flex flex-col justify-between cursor-pointer group relative overflow-hidden"
                      onClick={() => handleLaunch(app)}
                    >
                      {/* Zenith Volumetric Edge Glow */}
                      <div className="absolute inset-0 bg-gradient-to-br from-primary/0 via-transparent to-accent/0 group-hover:from-primary/20 group-hover:to-accent/20 transition-all duration-700 ease-out" />
                      <div className="absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity duration-700 border-2 border-primary/30 rounded-2xl pointer-events-none" />
                      
                      <div className="relative z-10">
                        <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-white/5 to-white/0 border border-white/10 flex items-center justify-center mb-5 group-hover:border-primary/50 group-hover:shadow-[0_0_20px_rgba(var(--color-primary),0.3)] transition-all duration-500">
                          <Icon className="w-7 h-7 text-gray-300 group-hover:text-primary transition-colors duration-500" />
                        </div>
                        <h3 className="text-xl font-medium text-gray-100 mb-2 group-hover:text-transparent group-hover:bg-clip-text group-hover:bg-gradient-to-r group-hover:from-primary group-hover:to-accent transition-all duration-300">{app.name}</h3>
                        <p className="text-sm text-gray-400 leading-relaxed mb-6 font-light">
                          {app.pitch}
                        </p>
                      </div>

                      <div className="relative z-10 flex items-center justify-between mt-auto">
                        <span className="text-xs font-mono text-primary/70 bg-primary/10 border border-primary/20 px-2 py-1 rounded shadow-inner">
                          {app.command}
                        </span>
                        
                        <AnimatePresence>
                          {isActive && isRunning && (
                            <motion.div 
                              initial={{ opacity: 0, scale: 0.5, rotate: -180 }}
                              animate={{ opacity: 1, scale: 1, rotate: 0 }}
                              exit={{ opacity: 0, scale: 0.5, rotate: 180 }}
                              transition={{ duration: 0.3 }}
                              className="w-5 h-5 rounded-full border-2 border-primary border-t-transparent animate-spin drop-shadow-[0_0_8px_rgba(var(--color-primary),0.8)]"
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
