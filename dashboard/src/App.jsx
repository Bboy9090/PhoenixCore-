import React, { useState, useEffect, useRef } from 'react';
import { 
  Cpu, 
  HardDrive, 
  Download, 
  Check, 
  Terminal as TerminalIcon, 
  CheckCircle2, 
  AlertTriangle, 
  ShieldAlert, 
  RefreshCw, 
  FolderPlus, 
  HelpCircle,
  Disc,
  Settings,
  ChevronRight,
  Sparkles
} from 'lucide-react';

// Mock list of drives
const MOCK_DRIVES = [
  { drive: 'D:\\', label: 'SanDisk Extreme', total_size_gb: 64.2, free_size_gb: 63.8, type: 'Removable' },
  { drive: 'E:\\', label: 'Kingston DataTraveler', total_size_gb: 32.0, free_size_gb: 31.9, type: 'Removable' },
  { drive: 'F:\\', label: 'PNY Turbo USB 3.0', total_size_gb: 128.0, free_size_gb: 12.4, type: 'Removable' }
];

// OCLP Releases
const OCLP_VERSIONS = ['v1.5.0 (Latest)', 'v1.4.3', 'v1.3.0', 'v1.2.1'];

// Macbook Target models for BootCamp Windows-on-Mac support
const MACBOOK_MODELS = [
  // MacBook Pro Series
  'MacBookPro5,1 (15", Late 2008)',
  'MacBookPro6,1 (17", Mid 2010)',
  'MacBookPro8,1 (13", Early/Late 2011)',
  'MacBookPro9,1 (15", Mid 2012)',
  'MacBookPro10,1 (Retina 15", Mid 2012/Early 2013)',
  'MacBookPro11,1 (Retina 13", Late 2013/Mid 2014)',
  'MacBookPro11,3 (Retina 15", Late 2013/Mid 2014)',
  'MacBookPro12,1 (Retina 13", Early 2015)',
  'MacBookPro13,3 (Retina 15", Late 2016)',
  'MacBookPro14,1 (Retina 13", Mid 2017)',
  
  // MacBook Air Series
  'MacBookAir3,1 (11", Late 2010)',
  'MacBookAir4,2 (13", Mid 2011)',
  'MacBookAir5,2 (13", Mid 2012)',
  'MacBookAir6,2 (13", Mid 2013/Early 2014)',
  'MacBookAir7,2 (13", Early 2015/2017)',
  
  // MacBook (12" / Polycarbonate) Series
  'MacBook2,1 (White/Black Polycarbonate, Late 2006/Mid 2007 - 32-bit EFI)',
  'MacBook5,2 (White Polycarbonate, Early/Mid 2009)',
  'MacBook7,1 (White Unibody, Mid 2010)',
  'MacBook8,1 (Retina 12", Early 2015)',
  'MacBook9,1 (Retina 12", Early 2016)',
  'MacBook10,1 (Retina 12", Mid 2017)',
  
  // iMac Series
  'iMac9,1 (24", Early 2009)',
  'iMac11,1 (27", Late 2009)',
  'iMac12,1 (21.5", Mid 2011)',
  'iMac13,2 (27", Late 2012)',
  'iMac14,2 (27", Late 2013)',
  'iMac15,1 (Retina 5K 27", Late 2014/Mid 2015)',
  'iMac17,1 (Retina 5K 27", Late 2015)',
  'iMac18,3 (Retina 5K 27", Mid 2017)',
  
  // Mac mini Series
  'Macmini3,1 (Late 2009)',
  'Macmini4,1 (Mid 2010)',
  'Macmini5,1 (Mid 2011)',
  'Macmini6,2 (Late 2012)',
  'Macmini7,1 (Late 2014)',
  'Macmini8,1 (Late 2018)',
  
  // Mac Pro Series
  'MacPro3,1 (Early 2008)',
  'MacPro4,1 (Early 2009)',
  'MacPro5,1 (Mid 2010/Mid 2012)',
  'MacPro6,1 (Trash Can, Late 2013)'
];

export default function App() {
  const [drives, setDrives] = useState(MOCK_DRIVES);
  const [selectedDrive, setSelectedDrive] = useState('');
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [selectedOclp, setSelectedOclp] = useState(OCLP_VERSIONS[0]);
  const [targetMacModel, setTargetMacModel] = useState(MACBOOK_MODELS[0]);
  
  // Selection check states
  const [includeOclp, setIncludeOclp] = useState(true);
  const [includeBootcamp, setIncludeBootcamp] = useState(true);
  const [includeRescueTools, setIncludeRescueTools] = useState(true);
  
  // Status & Progress states
  const [status, setStatus] = useState('idle'); // idle, working, success, error
  const [progress, setProgress] = useState(0);
  const [terminalLogs, setTerminalLogs] = useState([
    { type: 'info', text: 'PhoenixCore & BootForge Engine v2.5.0 Initialized.' },
    { type: 'info', text: 'Select a target USB drive and tools to compile the rescue system.' }
  ]);
  
  const terminalEndRef = useRef(null);

  // Scroll to bottom of terminal when logs update
  useEffect(() => {
    if (terminalEndRef.current) {
      terminalEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [terminalLogs]);

  // Refresh drive list simulation
  const refreshDrives = () => {
    setIsRefreshing(true);
    addLog('info', 'Scanning system logical drives...');
    setTimeout(() => {
      // Simulate reading drives
      setDrives(MOCK_DRIVES);
      setIsRefreshing(false);
      addLog('success', `Scan complete. Found ${MOCK_DRIVES.length} removable USB drives.`);
    }, 1200);
  };

  const addLog = (type, text) => {
    const timestamp = new Date().toLocaleTimeString();
    setTerminalLogs(prev => [...prev, { type, text: `[${timestamp}] ${text}` }]);
  };

  // Run USB Creation simulation
  const handleCreate = () => {
    if (!selectedDrive) {
      addLog('error', 'No target USB drive selected!');
      return;
    }
    
    setStatus('working');
    setProgress(0);
    setTerminalLogs([]);
    
    addLog('info', `PHOENIXCORE ENGINE: Launching Rescue USB Creator on target ${selectedDrive}...`);
    
    const steps = [
      { 
        percent: 10, 
        log: `Locking volume ${selectedDrive} for exclusive partition access...`,
        type: 'info'
      },
      { 
        percent: 20, 
        log: `Writing standard GUID Partition Table (GPT) to drive layout...`,
        type: 'info'
      },
      { 
        percent: 30, 
        log: `Formatting partition as FAT32 Rescue System (Volume Name: PHOENIX)...`,
        type: 'success'
      },
      { 
        percent: 45, 
        log: includeOclp 
          ? `Fetching Dortania OpenCore Legacy Patcher API releases (${selectedOclp})...` 
          : 'Skipping OpenCore Legacy Patcher packaging...',
        type: 'info'
      },
      { 
        percent: 55, 
        log: includeOclp 
          ? `Successfully downloaded and extracted OpenCore-Patcher-GUI to ${selectedDrive}OCLP_Patcher\\` 
          : '',
        type: includeOclp ? 'success' : ''
      },
      { 
        percent: 65, 
        log: includeBootcamp 
          ? `Requesting Apple System Recovery servers for ${targetMacModel} BootCamp Windows-on-Mac support drivers...` 
          : 'Skipping BootCamp hardware drivers...',
        type: 'info'
      },
      { 
        percent: 75, 
        log: includeBootcamp 
          ? `Downloaded and unpacked Windows Support Software (BootCamp v6.0) for running Windows natively on Apple Mac hardware to ${selectedDrive}BootCamp_Drivers\\` 
          : '',
        type: includeBootcamp ? 'success' : ''
      },
      { 
        percent: 85, 
        log: includeRescueTools 
          ? `Bundling default Rescue Utilities: rufus-4.14.exe, void-live.iso, palen1x...` 
          : 'Skipping third-party rescue utilities...',
        type: 'info'
      },
      { 
        percent: 92, 
        log: `Generating index metadata and README instructions in ${selectedDrive}README.txt...`,
        type: 'info'
      },
      { 
        percent: 100, 
        log: `SUCCESS: PhoenixCore USB Rescue drive initialized successfully! Safe to eject.`,
        type: 'success'
      }
    ];

    let currentStep = 0;
    
    const interval = setInterval(() => {
      if (currentStep < steps.length) {
        const step = steps[currentStep];
        setProgress(step.percent);
        if (step.log) {
          addLog(step.type, step.log);
        }
        currentStep++;
      } else {
        clearInterval(interval);
        setStatus('success');
      }
    }, 1500);
  };

  const selectedDriveDetails = drives.find(d => d.drive === selectedDrive);

  // SVG calculations for progress ring
  const radius = 70;
  const stroke = 12;
  const normalizedRadius = radius - stroke * 2;
  const circumference = normalizedRadius * 2 * Math.PI;
  const strokeDashoffset = circumference - (progress / 100) * circumference;

  return (
    <div className="container">
      {/* Header section */}
      <header>
        <div className="logo-container">
          <div className="logo-text">
            <Cpu size={36} className="glow-text-primary" />
            <span>PHOENIXCORE</span>
          </div>
          <span className="badge">BOOTFORGE v2.5</span>
        </div>
        
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <div className={`status-badge ${status === 'working' ? 'active' : status === 'success' ? 'success' : 'idle'}`}>
            <span className="status-dot"></span>
            {status === 'idle' && 'System Idle'}
            {status === 'working' && 'Burning USB...'}
            {status === 'success' && 'Build Completed'}
          </div>
          <button 
            onClick={refreshDrives} 
            disabled={status === 'working' || isRefreshing}
            className="glass-panel" 
            style={{ 
              padding: '10px', 
              borderRadius: '10px', 
              cursor: 'pointer', 
              color: '#fff', 
              display: 'flex', 
              alignItems: 'center', 
              gap: '6px',
              border: '1px solid var(--border-glass)'
            }}
          >
            <RefreshCw size={16} className={isRefreshing ? 'spin-anim' : ''} />
            Scan USBs
          </button>
        </div>
      </header>

      {/* Main Grid */}
      <div className="dashboard-grid">
        
        {/* Left Hand: Controls & Selections */}
        <div className="glass-panel" style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
          <h2>
            <Settings size={20} className="glow-text-primary" />
            <span>Rescue Creator Configuration</span>
          </h2>

          {/* Form Group 1: Target Drive */}
          <div className="form-group">
            <label className="form-label">1. Select Target USB Recovery Drive</label>
            <div className="drive-list">
              {drives.map(item => {
                const usedPercent = ((item.total_size_gb - item.free_size_gb) / item.total_size_gb) * 100;
                return (
                  <div 
                    key={item.drive} 
                    onClick={() => status !== 'working' && setSelectedDrive(item.drive)}
                    className={`drive-card ${selectedDrive === item.drive ? 'selected' : ''}`}
                  >
                    <div className="drive-info">
                      <div className="drive-icon-wrapper">
                        <HardDrive size={22} />
                      </div>
                      <div className="drive-details">
                        <h3>{item.label} ({item.drive})</h3>
                        <p>{item.type} Drive • GPT Layout</p>
                      </div>
                    </div>
                    <div className="drive-capacity">
                      <span style={{ fontSize: '0.9rem', fontWeight: 600 }}>
                        {item.free_size_gb} GB free of {item.total_size_gb} GB
                      </span>
                      <div className="drive-capacity-bar">
                        <div 
                          className="drive-capacity-fill" 
                          style={{ width: `${usedPercent}%` }}
                        ></div>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Form Group 2: Recovery Utility Pack */}
          <div className="form-group">
            <label className="form-label">2. Select Rescue Utilities & Systems</label>
            <div className="utility-grid">
              
              {/* OCLP Patcher Card */}
              <div 
                className={`utility-card ${includeOclp ? 'selected' : ''}`}
                onClick={() => status !== 'working' && setIncludeOclp(!includeOclp)}
              >
                <div className="utility-header">
                  <span className="utility-icon"><Cpu size={18} /></span>
                  {includeOclp && <CheckCircle2 size={16} style={{ color: 'var(--accent)' }} />}
                </div>
                <h3>OpenCore OCLP</h3>
                <p>Install OpenCore bootloader & EFI patches for legacy Macs.</p>
              </div>

              {/* BootCamp Drivers Card */}
              <div 
                className={`utility-card ${includeBootcamp ? 'selected' : ''}`}
                onClick={() => status !== 'working' && setIncludeBootcamp(!includeBootcamp)}
              >
                <div className="utility-header">
                  <span className="utility-icon"><Disc size={18} /></span>
                  {includeBootcamp && <CheckCircle2 size={16} style={{ color: 'var(--accent)' }} />}
                </div>
                <h3>BootCamp Drivers</h3>
                <p>Windows support software & drivers for running Windows natively on Mac hardware.</p>
              </div>

              {/* Rescue Tools Card */}
              <div 
                className={`utility-card ${includeRescueTools ? 'selected' : ''}`}
                onClick={() => status !== 'working' && setIncludeRescueTools(!includeRescueTools)}
              >
                <div className="utility-header">
                  <span className="utility-icon"><FolderPlus size={18} /></span>
                  {includeRescueTools && <CheckCircle2 size={16} style={{ color: 'var(--accent)' }} />}
                </div>
                <h3>Rescue Tools Suite</h3>
                <p>Includes Rufus-4.14, void-live.iso, and disk restoration ISOs.</p>
              </div>
            </div>
          </div>

          {/* Form Group 3: Specific Configuration Details */}
          {(includeOclp || includeBootcamp) && (
            <div className="glass-panel" style={{ padding: '16px', background: 'rgba(255, 255, 255, 0.01)', borderStyle: 'dashed' }}>
              <h3 style={{ fontSize: '0.95rem', fontFamily: 'var(--font-tech)', marginBottom: '12px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Sparkles size={14} style={{ color: 'var(--primary)' }} />
                <span>Extended Rescue Parameters</span>
              </h3>
              
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
                {includeOclp && (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                    <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>OCLP Target Patcher</span>
                    <select 
                      disabled={status === 'working'}
                      value={selectedOclp}
                      onChange={(e) => setSelectedOclp(e.target.value)}
                      style={{ padding: '8px', background: 'rgba(0,0,0,0.3)', border: '1px solid var(--border-glass)', borderRadius: '6px', color: '#fff', outline: 'none' }}
                    >
                      {OCLP_VERSIONS.map(v => <option key={v} value={v}>{v}</option>)}
                    </select>
                  </div>
                )}
                {includeBootcamp && (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '6px', gridColumn: includeOclp ? 'auto' : 'span 2' }}>
                    <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Apple Target MacBook Model</span>
                    <select 
                      disabled={status === 'working'}
                      value={targetMacModel}
                      onChange={(e) => setTargetMacModel(e.target.value)}
                      style={{ padding: '8px', background: 'rgba(0,0,0,0.3)', border: '1px solid var(--border-glass)', borderRadius: '6px', color: '#fff', outline: 'none' }}
                    >
                      {MACBOOK_MODELS.map(m => <option key={m} value={m}>{m}</option>)}
                    </select>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Creation Button */}
          <button 
            className="btn-primary" 
            onClick={handleCreate} 
            disabled={!selectedDrive || status === 'working'}
          >
            <Cpu size={20} />
            <span>INITIALIZE RECOVERY USB</span>
          </button>
        </div>

        {/* Right Hand: Terminal & Live Status */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '32px' }}>
          
          {/* Status Progress Ring */}
          <div className="glass-panel" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <div className="progress-ring-container">
              <div className="progress-circle">
                <svg className="progress-circle-svg">
                  <defs>
                    <linearGradient id="progressGradient" x1="0%" y1="0%" x2="100%" y2="100%">
                      <stop offset="0%" stopColor="var(--primary)" />
                      <stop offset="100%" stopColor="var(--accent)" />
                    </linearGradient>
                  </defs>
                  <circle className="progress-circle-bg" cx="90" cy="90" r={radius} />
                  <circle 
                    className="progress-circle-fill" 
                    cx="90" 
                    cy="90" 
                    r={radius} 
                    strokeDasharray={circumference}
                    strokeDashoffset={strokeDashoffset}
                  />
                </svg>
                <div className="progress-value">
                  {progress}%
                </div>
              </div>
              
              <div style={{ textAlign: 'center' }}>
                <h3 style={{ fontFamily: 'var(--font-tech)', fontSize: '1.2rem', marginBottom: '4px' }}>
                  {status === 'idle' && 'PhoenixCore Standby'}
                  {status === 'working' && 'Burning Bootable Image...'}
                  {status === 'success' && 'Phoenix Rescue USB Complete!'}
                </h3>
                <p style={{ fontSize: '0.9rem', color: 'var(--text-muted)' }}>
                  {status === 'idle' && 'Select options and click Initialize above.'}
                  {status === 'working' && 'DO NOT eject the USB drive during installation.'}
                  {status === 'success' && `Drive ${selectedDrive} is ready to revive your legacy Macbook.`}
                </p>
              </div>
            </div>
          </div>

          {/* Terminal Console */}
          <div className="terminal-container">
            <div className="terminal-header">
              <div className="terminal-dot-group">
                <span className="terminal-dot red"></span>
                <span className="terminal-dot yellow"></span>
                <span className="terminal-dot green"></span>
              </div>
              <div className="terminal-title">PHOENIX_RESCUE_CONSOLE</div>
              <TerminalIcon size={14} style={{ color: 'var(--text-muted)' }} />
            </div>
            
            <div className="terminal-body">
              {terminalLogs.map((log, idx) => (
                <div className="terminal-line" key={idx}>
                  <span className="terminal-prompt">&gt;</span>
                  <span className={`terminal-text ${log.type}`}>
                    {log.text}
                  </span>
                </div>
              ))}
              {status === 'working' && (
                <div className="terminal-line">
                  <span className="terminal-prompt">&gt;</span>
                  <span className="terminal-text info blink">_</span>
                </div>
              )}
              <div ref={terminalEndRef} />
            </div>
          </div>

        </div>

      </div>

      {/* Embedded style tweaks for small animations */}
      <style>{`
        @keyframes spin {
          0% { transform: rotate(0deg); }
          100% { transform: rotate(360deg); }
        }
        .spin-anim {
          animation: spin 1s linear infinite;
        }
        @keyframes blink {
          0%, 100% { opacity: 1; }
          50% { opacity: 0; }
        }
        .blink {
          animation: blink 1s infinite;
        }
        .status-dot {
          width: 8px;
          height: 8px;
          border-radius: 50%;
          background: #94a3b8;
          display: inline-block;
        }
        .status-badge.active .status-dot {
          background: var(--primary);
          box-shadow: 0 0 8px var(--primary);
          animation: blink 1s infinite;
        }
        .status-badge.success .status-dot {
          background: var(--success);
          box-shadow: 0 0 8px var(--success);
        }
      `}</style>
    </div>
  );
}
