import React, { useState, useEffect, useRef } from 'react';
import { 
  Cpu, 
  HardDrive, 
  Terminal as TerminalIcon, 
  CheckCircle2, 
  ShieldAlert, 
  RefreshCw, 
  FolderPlus,
  Disc,
  Settings,
  Sparkles
} from 'lucide-react';

// OCLP Releases
const OCLP_VERSIONS = ['v1.5.0 (Latest)', 'v1.4.3', 'v1.3.0', 'v1.2.1'];

// Macbook Target models for BootCamp Windows-on-Mac support
const MACBOOK_MODELS = [
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
  'MacBookAir3,1 (11", Late 2010)',
  'MacBookAir4,2 (13", Mid 2011)',
  'MacBookAir5,2 (13", Mid 2012)',
  'MacBookAir6,2 (13", Mid 2013/Early 2014)',
  'MacBookAir7,2 (13", Early 2015/2017)',
  'MacBook2,1 (White/Black Polycarbonate, Late 2006/Mid 2007 - 32-bit EFI)',
  'MacBook5,2 (White Polycarbonate, Early/Mid 2009)',
  'MacBook7,1 (White Unibody, Mid 2010)',
  'MacBook8,1 (Retina 12", Early 2015)',
  'MacBook9,1 (Retina 12", Early 2016)',
  'MacBook10,1 (Retina 12", Mid 2017)',
  'iMac9,1 (24", Early 2009)',
  'iMac11,1 (27", Late 2009)',
  'iMac12,1 (21.5", Mid 2011)',
  'iMac13,2 (27", Late 2012)',
  'iMac14,2 (27", Late 2013)',
  'iMac15,1 (Retina 5K 27", Late 2014/Mid 2015)',
  'iMac17,1 (Retina 5K 27", Late 2015)',
  'iMac18,3 (Retina 5K 27", Mid 2017)',
  'Macmini3,1 (Late 2009)',
  'Macmini4,1 (Mid 2010)',
  'Macmini5,1 (Mid 2011)',
  'Macmini6,2 (Late 2012)',
  'Macmini7,1 (Late 2014)',
  'Macmini8,1 (Late 2018)',
  'MacPro3,1 (Early 2008)',
  'MacPro4,1 (Early 2009)',
  'MacPro5,1 (Mid 2010/Mid 2012)',
  'MacPro6,1 (Trash Can, Late 2013)'
];

const toNumericSize = (value) => {
  if (typeof value === 'number') return value;
  if (typeof value !== 'string') return 0;

  const trimmed = value.trim();
  const match = trimmed.match(/^([0-9.]+)\s*([KMGT]?)B?$/i);
  if (!match) return Number(trimmed) || 0;

  const amount = Number(match[1]);
  const unit = match[2].toUpperCase();

  if (Number.isNaN(amount)) return 0;
  if (unit === 'T') return amount * 1024;
  if (unit === 'M') return amount / 1024;
  if (unit === 'K') return amount / (1024 * 1024);
  return amount;
};

const formatSize = (value) => {
  if (typeof value === 'number') return `${value} GB`;
  return value || 'Unknown';
};

const getUsedPercent = (drive) => {
  const total = toNumericSize(drive.total_size_gb);
  const free = toNumericSize(drive.free_size_gb);

  if (!total || free > total) return 0;
  return Math.max(0, Math.min(100, ((total - free) / total) * 100));
};

const formatImageSize = (image) => {
  if (!image) return 'Unknown';
  if (image.size_gb && image.size_gb >= 0.01) return `${image.size_gb} GB`;
  return `${image.size_bytes || 0} bytes`;
};

export default function App() {
  const [drives, setDrives] = useState([]);
  const [selectedDrive, setSelectedDrive] = useState('');
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [selectedOclp, setSelectedOclp] = useState(OCLP_VERSIONS[0]);
  const [targetMacModel, setTargetMacModel] = useState(MACBOOK_MODELS[0]);
  const [imagePath, setImagePath] = useState('');
  const [inspectedImage, setInspectedImage] = useState(null);
  const [isInspectingImage, setIsInspectingImage] = useState(false);
  
  // Selection check states
  const [includeOclp, setIncludeOclp] = useState(true);
  const [includeBootcamp, setIncludeBootcamp] = useState(true);
  const [includeRescueTools, setIncludeRescueTools] = useState(true);
  
  // Status & Progress states
  const [status, setStatus] = useState('idle'); // idle, working, success, error
  const [progress, setProgress] = useState(0);
  const [terminalLogs, setTerminalLogs] = useState([
    { type: 'info', text: 'PhoenixCore & BootForge Engine v2.5.0 Initialized.' },
    { type: 'warning', text: 'Foundation Lock active: real USB scanning and image inspection only. Write, format, partition, and burn actions are disabled.' },
    { type: 'info', text: 'Click Scan USBs or inspect an ISO/IMG path through the read-only Python bridge.' }
  ]);
  
  const terminalEndRef = useRef(null);

  // Scroll to bottom of terminal when logs update
  useEffect(() => {
    if (terminalEndRef.current) {
      terminalEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [terminalLogs]);

  const addLog = (type, text) => {
    const timestamp = new Date().toLocaleTimeString();
    setTerminalLogs(prev => [...prev, { type, text: `[${timestamp}] ${text}` }]);
  };

  // Refresh drive list through the safe Vite dev bridge.
  const refreshDrives = async () => {
    setIsRefreshing(true);
    setSelectedDrive('');
    addLog('info', 'Scanning removable drives through read-only Python bridge...');

    try {
      const response = await fetch('/api/usb/scan', {
        method: 'GET',
        headers: { Accept: 'application/json' }
      });

      const payload = await response.json();

      if (!response.ok) {
        throw new Error(payload.error || `USB scan failed with HTTP ${response.status}`);
      }

      if (payload.destructive !== false || payload.operation !== 'read_only_drive_scan') {
        throw new Error('USB scan bridge failed safety validation. Refusing to trust payload.');
      }

      const nextDrives = Array.isArray(payload.drives) ? payload.drives : [];
      setDrives(nextDrives);
      setStatus('success');

      if (nextDrives.length === 0) {
        addLog('warning', `Scan complete on ${payload.platform}. No removable USB drives detected.`);
      } else {
        addLog('success', `Scan complete on ${payload.platform}. Found ${nextDrives.length} removable USB drive(s).`);
      }
    } catch (error) {
      setDrives([]);
      setStatus('error');
      addLog('error', `USB scan bridge error: ${error.message}`);
    } finally {
      setIsRefreshing(false);
    }
  };

  const inspectImage = async () => {
    const trimmedPath = imagePath.trim();
    if (!trimmedPath) {
      addLog('error', 'No image path entered for inspection.');
      return;
    }

    setIsInspectingImage(true);
    setInspectedImage(null);
    addLog('info', `Inspecting image through read-only bridge: ${trimmedPath}`);

    try {
      const response = await fetch(`/api/image/inspect?path=${encodeURIComponent(trimmedPath)}`, {
        method: 'GET',
        headers: { Accept: 'application/json' }
      });

      const payload = await response.json();

      if (!response.ok) {
        throw new Error(payload.error || `Image inspection failed with HTTP ${response.status}`);
      }

      if (payload.destructive !== false || payload.operation !== 'read_only_image_inspection') {
        throw new Error('Image inspection bridge failed safety validation. Refusing to trust payload.');
      }

      setInspectedImage(payload.image);
      setStatus(payload.error ? 'error' : 'success');

      if (payload.error) {
        addLog('error', `Image inspection returned error: ${payload.error}`);
      } else {
        addLog('success', `Image inspected: ${payload.image.filename} | ${formatImageSize(payload.image)} | SHA256 ready.`);
      }
    } catch (error) {
      setInspectedImage(null);
      setStatus('error');
      addLog('error', `Image inspection bridge error: ${error.message}`);
    } finally {
      setIsInspectingImage(false);
    }
  };

  // Phase 1/2A safety lock: no writer exists yet, so do not simulate destructive work.
  const handleCreate = () => {
    addLog('warning', 'Creation is disabled in Phase 2A. Image inspection is read-only; USB write, format, partition, and burn operations remain locked.');
    setProgress(0);
  };

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
          <div className={`status-badge ${status === 'working' ? 'active' : status === 'success' ? 'success' : status === 'error' ? 'error' : 'idle'}`}>
            <span className="status-dot"></span>
            {status === 'idle' && 'Read-Only Idle'}
            {status === 'working' && 'Bridge Working...'}
            {status === 'success' && 'Read-Only Pass'}
            {status === 'error' && 'Bridge Error'}
          </div>
          <button 
            onClick={refreshDrives} 
            disabled={isRefreshing || isInspectingImage}
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

          <div className="glass-panel" style={{ padding: '14px', borderColor: 'rgba(250, 204, 21, 0.35)' }}>
            <h3 style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '6px' }}>
              <ShieldAlert size={18} />
              <span>Phase 2A Read-Only Lock</span>
            </h3>
            <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', lineHeight: 1.5 }}>
              This dashboard can scan USB drives and inspect ISO/IMG/DMG files only. Writing, formatting, partitioning,
              mounting, unmounting, and burn actions remain disabled until the safety model is complete.
            </p>
          </div>

          {/* Form Group 1: Target Drive */}
          <div className="form-group">
            <label className="form-label">1. Select Target USB Recovery Drive</label>
            <div className="drive-list">
              {drives.length === 0 && (
                <div className="drive-card" style={{ cursor: 'default', opacity: 0.78 }}>
                  <div className="drive-info">
                    <div className="drive-icon-wrapper">
                      <HardDrive size={22} />
                    </div>
                    <div className="drive-details">
                      <h3>No removable USB drives detected</h3>
                      <p>Plug in a USB drive and click Scan USBs.</p>
                    </div>
                  </div>
                </div>
              )}

              {drives.map(item => {
                const usedPercent = getUsedPercent(item);
                const key = item.drive || `${item.label}-${item.total_size_gb}`;
                return (
                  <div 
                    key={key} 
                    onClick={() => setSelectedDrive(item.drive)}
                    className={`drive-card ${selectedDrive === item.drive ? 'selected' : ''}`}
                  >
                    <div className="drive-info">
                      <div className="drive-icon-wrapper">
                        <HardDrive size={22} />
                      </div>
                      <div className="drive-details">
                        <h3>{item.label || 'Removable Drive'} ({item.drive || 'Unknown path'})</h3>
                        <p>{item.type || 'USB'} Drive • Read-only scan result</p>
                      </div>
                    </div>
                    <div className="drive-capacity">
                      <span style={{ fontSize: '0.9rem', fontWeight: 600 }}>
                        {formatSize(item.free_size_gb)} free of {formatSize(item.total_size_gb)}
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

          {/* Form Group 2: Image Inspection */}
          <div className="form-group">
            <label className="form-label">2. Select / Inspect OS Image</label>
            <div className="glass-panel" style={{ padding: '16px', display: 'flex', flexDirection: 'column', gap: '12px' }}>
              <input
                type="text"
                value={imagePath}
                onChange={(e) => setImagePath(e.target.value)}
                placeholder={'Example: C:\\Users\\Bobby\\Downloads\\debian.iso'}
                disabled={isRefreshing || isInspectingImage}
                style={{
                  padding: '10px',
                  background: 'rgba(0,0,0,0.3)',
                  border: '1px solid var(--border-glass)',
                  borderRadius: '8px',
                  color: '#fff',
                  outline: 'none',
                  width: '100%'
                }}
              />
              <button
                className="glass-panel"
                onClick={inspectImage}
                disabled={isRefreshing || isInspectingImage || !imagePath.trim()}
                style={{
                  padding: '10px',
                  borderRadius: '10px',
                  cursor: imagePath.trim() ? 'pointer' : 'not-allowed',
                  color: '#fff',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: '8px',
                  border: '1px solid var(--border-glass)'
                }}
              >
                <RefreshCw size={16} className={isInspectingImage ? 'spin-anim' : ''} />
                Inspect Image Read-Only
              </button>

              {inspectedImage && (
                <div className="drive-card" style={{ cursor: 'default' }}>
                  <div className="drive-info">
                    <div className="drive-icon-wrapper">
                      <Disc size={22} />
                    </div>
                    <div className="drive-details">
                      <h3>{inspectedImage.filename || 'Image File'}</h3>
                      <p>{inspectedImage.supported ? 'Supported image type' : 'Unsupported image type'} • {inspectedImage.extension || 'no extension'}</p>
                    </div>
                  </div>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', fontSize: '0.82rem', color: 'var(--text-muted)', wordBreak: 'break-all' }}>
                    <span><strong>Path:</strong> {inspectedImage.path}</span>
                    <span><strong>Size:</strong> {formatImageSize(inspectedImage)}</span>
                    <span><strong>SHA256:</strong> {inspectedImage.sha256 || 'Unavailable'}</span>
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Form Group 3: Recovery Utility Pack */}
          <div className="form-group">
            <label className="form-label">3. Select Rescue Utilities & Systems</label>
            <div className="utility-grid">
              
              {/* OCLP Patcher Card */}
              <div 
                className={`utility-card ${includeOclp ? 'selected' : ''}`}
                onClick={() => setIncludeOclp(!includeOclp)}
              >
                <div className="utility-header">
                  <span className="utility-icon"><Cpu size={18} /></span>
                  {includeOclp && <CheckCircle2 size={16} style={{ color: 'var(--accent)' }} />}
                </div>
                <h3>OpenCore OCLP</h3>
                <p>Future packaging slot. Disabled from writing during Phase 2A.</p>
              </div>

              {/* BootCamp Drivers Card */}
              <div 
                className={`utility-card ${includeBootcamp ? 'selected' : ''}`}
                onClick={() => setIncludeBootcamp(!includeBootcamp)}
              >
                <div className="utility-header">
                  <span className="utility-icon"><Disc size={18} /></span>
                  {includeBootcamp && <CheckCircle2 size={16} style={{ color: 'var(--accent)' }} />}
                </div>
                <h3>BootCamp Drivers</h3>
                <p>Future driver bundle slot. Disabled from writing during Phase 2A.</p>
              </div>

              {/* Rescue Tools Card */}
              <div 
                className={`utility-card ${includeRescueTools ? 'selected' : ''}`}
                onClick={() => setIncludeRescueTools(!includeRescueTools)}
              >
                <div className="utility-header">
                  <span className="utility-icon"><FolderPlus size={18} /></span>
                  {includeRescueTools && <CheckCircle2 size={16} style={{ color: 'var(--accent)' }} />}
                </div>
                <h3>Rescue Tools Suite</h3>
                <p>Future bundle slot. Disabled from writing during Phase 2A.</p>
              </div>
            </div>
          </div>

          {/* Form Group 4: Specific Configuration Details */}
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
            style={{ opacity: 0.75 }}
          >
            <ShieldAlert size={20} />
            <span>PHASE 2A READ-ONLY LOCK ACTIVE</span>
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
                  {status === 'working' && 'Read-Only Bridge Running...'}
                  {status === 'success' && 'Read-Only Operation Complete'}
                  {status === 'error' && 'Bridge Error'}
                </h3>
                <p style={{ fontSize: '0.9rem', color: 'var(--text-muted)' }}>
                  {status === 'idle' && 'Scan USBs or inspect an OS image. No writes are available.'}
                  {status === 'working' && 'Read-only bridge is running.'}
                  {status === 'success' && 'Read-only validation completed. Creation remains disabled.'}
                  {status === 'error' && 'The dashboard could not reach or parse a bridge response.'}
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
              {(isRefreshing || isInspectingImage) && (
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
        .status-badge.error .status-dot {
          background: var(--danger, #ef4444);
          box-shadow: 0 0 8px var(--danger, #ef4444);
        }
      `}</style>
    </div>
  );
}
