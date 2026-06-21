import React, { useState, useEffect, useRef } from 'react';
import { 
  Cpu, 
  HardDrive, 
  Terminal as TerminalIcon, 
  CheckCircle2, 
  ShieldAlert, 
  ShieldCheck,
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
  const [safetyData, setSafetyData] = useState(null);
  const [isCheckingSafety, setIsCheckingSafety] = useState(false);
  const [safetyError, setSafetyError] = useState(null);
  
  // Write Plan States
  const [writePlanData, setWritePlanData] = useState(null);
  const [isPlanningWrite, setIsPlanningWrite] = useState(false);
  const [planningError, setPlanningError] = useState(null);

  // Safety Audit States (Phase 3B)
  const [auditData, setAuditData] = useState(null);
  const [isAuditingPlan, setIsAuditingPlan] = useState(false);
  const [auditError, setAuditError] = useState(null);

  // Safety Audit Export States (Phase 3C)
  const [exportPath, setExportPath] = useState('');
  const [isExporting, setIsExporting] = useState(false);
  const [exportStatus, setExportStatus] = useState(null);

  // Mock Writer Simulator States (Phase 4A-2B)
  const [mockWriterData, setMockWriterData] = useState(null);
  const [isSimulatingWrite, setIsSimulatingWrite] = useState(false);
  const [mockWriterError, setMockWriterError] = useState(null);
  const [mockFailAtChunk, setMockFailAtChunk] = useState('');
  const [mockCancelAtChunk, setMockCancelAtChunk] = useState('');

  // Writer Safety Contract Preview States (Phase 4C-2)
  const [contractData, setContractData] = useState(null);
  const [isPreviewingContract, setIsPreviewingContract] = useState(false);
  const [contractError, setContractError] = useState(null);
  // Contract Export States (Phase 4C-3)
  const [contractExportPath, setContractExportPath] = useState('');
  const [contractExportType, setContractExportType] = useState('json');
  const [isExportingContract, setIsExportingContract] = useState(false);
  const [contractExportResult, setContractExportResult] = useState(null);
  // Ledger History States (Phase 4C-4)
  const [contractLedgerPath, setContractLedgerPath] = useState('');
  const [isAppendingLedger, setIsAppendingLedger] = useState(false);
  const [ledgerAppendResult, setLedgerAppendResult] = useState(null);

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

  const checkDriveSafety = async (drivePath) => {
    if (!drivePath) {
      setSafetyData(null);
      return;
    }
    setIsCheckingSafety(true);
    setSafetyError(null);
    addLog('info', `Checking safety for drive path: ${drivePath}`);
    try {
      const response = await fetch(`/api/usb/safety?path=${encodeURIComponent(drivePath)}`, {
        method: 'GET',
        headers: { Accept: 'application/json' }
      });
      const payload = await response.json();
      if (!response.ok) {
        throw new Error(payload.error || `Drive safety check failed with HTTP ${response.status}`);
      }
      if (payload.destructive !== false || payload.operation !== 'read_only_drive_safety_check') {
        throw new Error('Drive safety check bridge failed safety validation.');
      }
      if (payload.error) {
        setSafetyError(payload.error);
        addLog('error', `Drive safety check returned error: ${payload.error}`);
      } else {
        setSafetyData(payload.drive);
        const eligibilityStr = payload.drive.eligible_for_future_write 
          ? 'Eligible for Future Write Candidate' 
          : 'Write Blocked';
        addLog('success', `Drive safety check complete: ${payload.drive.label} is ${eligibilityStr} (Risk: ${payload.drive.risk_level.toUpperCase()}).`);
      }
    } catch (error) {
      setSafetyData(null);
      setSafetyError(error.message);
      addLog('error', `Drive safety bridge error: ${error.message}`);
    } finally {
      setIsCheckingSafety(false);
    }
  };

  const generateWritePlan = async (drivePath, imgPath) => {
    const trimmedDrive = drivePath ? drivePath.trim() : '';
    const trimmedImg = imgPath ? imgPath.trim() : '';
    if (!trimmedDrive || !trimmedImg) {
      addLog('error', 'Both a target drive and OS image path are required to generate a write plan.');
      return;
    }

    setIsPlanningWrite(true);
    setPlanningError(null);
    setWritePlanData(null);
    setAuditData(null);
    setAuditError(null);
    addLog('info', `Generating dry-run write execution plan for ${trimmedDrive} with ${trimmedImg}...`);

    try {
      const response = await fetch(`/api/write/plan?drive=${encodeURIComponent(trimmedDrive)}&image=${encodeURIComponent(trimmedImg)}`, {
        method: 'GET',
        headers: { Accept: 'application/json' }
      });
      const payload = await response.json();

      if (!response.ok) {
        throw new Error(payload.error || `Write plan generation failed with HTTP ${response.status}`);
      }

      if (payload.destructive !== false || payload.operation !== 'dry_run_write_plan') {
        throw new Error('Write plan bridge failed safety validation.');
      }

      setWritePlanData(payload);
      setStatus(payload.error ? 'error' : 'success');

      if (payload.error) {
        setPlanningError(payload.error);
        addLog('error', `Write plan returned error: ${payload.error}`);
      } else {
        if (payload.blocked) {
          addLog('warning', `Dry-run plan generated but BLOCKED. Reasons: ${payload.block_reasons.join('; ')}`);
        } else {
          addLog('success', `Dry-run write plan generated successfully! Drive is ready for simulation.`);
        }
        // Automatically trigger safety audit trail validation
        runPlanAudit(trimmedDrive, trimmedImg);
      }
    } catch (error) {
      setWritePlanData(null);
      setPlanningError(error.message);
      addLog('error', `Write plan bridge error: ${error.message}`);
    } finally {
      setIsPlanningWrite(false);
    }
  };

  const runPlanAudit = async (drivePath, imgPath) => {
    const trimmedDrive = drivePath ? drivePath.trim() : '';
    const trimmedImg = imgPath ? imgPath.trim() : '';
    if (!trimmedDrive || !trimmedImg) return;

    setIsAuditingPlan(true);
    setAuditError(null);
    setAuditData(null);
    addLog('info', 'Running paranoid dry-run safety validation audit...');

    try {
      const response = await fetch(`/api/write/audit?drive=${encodeURIComponent(trimmedDrive)}&image=${encodeURIComponent(trimmedImg)}`, {
        method: 'GET',
        headers: { Accept: 'application/json' }
      });
      const payload = await response.json();

      if (!response.ok) {
        throw new Error(payload.error || `Safety audit failed with HTTP ${response.status}`);
      }

      if (payload.destructive !== false || payload.operation !== 'dry_run_write_plan_audit') {
        throw new Error('Safety audit bridge failed schema validation.');
      }

      setAuditData(payload);

      if (payload.error) {
        setAuditError(payload.error);
        addLog('error', `Safety audit returned error: ${payload.error}`);
      } else if (payload.validation_status === 'failed') {
        addLog('warning', `Safety audit FAILED! Gate failure reasons: ${payload.block_reasons.join('; ')}`);
      } else {
        addLog('success', `Safety audit PASSED! Canonical Plan ID: ${payload.plan_id}`);
      }
    } catch (error) {
      setAuditData(null);
      setAuditError(error.message);
      addLog('error', `Safety audit bridge error: ${error.message}`);
    } finally {
      setIsAuditingPlan(false);
    }
  };

  const exportAuditToHost = async (format) => {
    const trimmedPath = exportPath.trim();
    if (!trimmedPath) {
      setExportStatus({ status: 'error', message: 'Please specify a local host save path.' });
      return;
    }
    if (!selectedDrive || !imagePath) {
      setExportStatus({ status: 'error', message: 'Target drive and OS image path are required to export.' });
      return;
    }

    setIsExporting(true);
    setExportStatus(null);
    addLog('info', `Saving ${format.toUpperCase()} audit summary to host at ${trimmedPath}...`);

    try {
      const response = await fetch('/api/write/export', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          drive: selectedDrive,
          image: imagePath,
          format: format,
          path: trimmedPath
        })
      });

      const payload = await response.json();

      if (!response.ok) {
        throw new Error(payload.error || `Export failed with HTTP ${response.status}`);
      }

      if (payload.status === 'success') {
        setExportStatus({ status: 'success', message: `Successfully exported ${format.toUpperCase()} report to ${trimmedPath}.` });
        addLog('success', `Export complete: ${trimmedPath}`);
      } else {
        throw new Error(payload.error || 'Unknown error occurred during export.');
      }
    } catch (error) {
      setExportStatus({ status: 'error', message: error.message });
      addLog('error', `Export error: ${error.message}`);
    } finally {
      setIsExporting(false);
    }
  };

  const generateBrowserMarkdown = (data) => {
    const plan = data.write_plan || {};
    const drive = (plan.drive_safety && plan.drive_safety.drive) || {};
    const image = (plan.image_inspection && plan.image_inspection.image) || {};
    
    const statusEmoji = data.validation_status === 'passed' ? '✅ PASSED' : '❌ FAILED';
    
    const checksStr = (data.checks || []).map(c => {
      const mark = c.passed ? '[PASS]' : '[FAIL]';
      return `- ${mark} ${c.label}`;
    }).join('\n');
    
    const reasonsStr = (data.block_reasons || []).length > 0
      ? (data.block_reasons || []).map(r => `- ${r}`).join('\n')
      : 'None';
      
    const warningsStr = (data.warnings || []).length > 0
      ? (data.warnings || []).map(w => `- ${w}`).join('\n')
      : 'None';
      
    const driveStr = drive.requested_path 
      ? `- **Requested Path**: ${drive.requested_path}
- **Root Mount**: ${drive.root || 'N/A'}
- **Label**: ${drive.label || 'N/A'}
- **Type**: ${drive.type || 'N/A'}
- **Filesystem**: ${drive.filesystem || 'N/A'}
- **Total Capacity**: ${drive.total_size_gb || 0} GB
- **Free Space**: ${drive.free_size_gb || 0} GB
- **System Drive**: ${drive.is_system_drive ? 'Yes' : 'No'}
- **Risk Level**: ${String(drive.risk_level).toUpperCase()}
- **Eligible**: ${drive.eligible_for_future_write ? 'Yes' : 'No'}`
      : 'N/A';
      
    const imgSizeStr = image.size_gb >= 0.01 
      ? `${image.size_gb} GB` 
      : `${image.size_bytes || 0} bytes`;
      
    const imageStr = image.path
      ? `- **Filename**: ${image.filename}
- **Path**: ${image.path}
- **Extension**: ${image.extension}
- **Exists**: ${image.exists ? 'Yes' : 'No'}
- **Supported**: ${image.supported ? 'Yes' : 'No'}
- **Size**: ${imgSizeStr}
- **Calculated SHA256**: ${image.sha256 || 'N/A'}`
      : 'N/A';
      
    return `# PhoenixCore / BootForge Audit Evidence Report

## General Info
- **Plan ID**: ${data.plan_id}
- **Plan Hash**: ${data.plan_hash}
- **Validation Status**: ${statusEmoji}
- **Generated At**: ${data.generated_at}
- **Platform**: ${data.platform}
- **Target Drive**: ${plan.target_drive || 'N/A'}
- **Image Path**: ${plan.image_path || 'N/A'}
- **Eligibility**: ${data.eligible ? 'Yes' : 'No'}
- **Blocked**: ${data.blocked ? 'Yes' : 'No'}

---

## Safety Checks Checklist
${checksStr}

---

## Drive Safety Summary
${driveStr}

---

## Image Inspection Summary
${imageStr}

---

## Block Reasons
${reasonsStr}

---

## Warnings
${warningsStr}

---

## Read-Only Safety Statement
> [!IMPORTANT]
> **This report is evidence of a dry-run audit only. It does not indicate that a write, format, partition, or mount operation was performed.**
> All actual destructive writing engines remain completely locked and dry-run safe.

---
*Prepared by PhoenixCore BootForge Supply-Chain Safety Engine.*
`;
  };

  const downloadAuditInBrowser = (format) => {
    if (!auditData) return;
    
    let content = '';
    let filename = '';
    let mimeType = '';
    
    if (format === 'json') {
      content = JSON.stringify(auditData, null, 2);
      filename = `audit_${auditData.plan_id || 'plan'}.json`;
      mimeType = 'application/json';
    } else {
      content = generateBrowserMarkdown(auditData);
      filename = `audit_${auditData.plan_id || 'plan'}.md`;
      mimeType = 'text/markdown';
    }
    
    const blob = new Blob([content], { type: mimeType });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
    
    addLog('success', `Browser download triggered for ${filename}`);
  };

  const runMockWriterSimulation = async (drivePath, imgPath) => {
    const trimmedDrive = drivePath ? drivePath.trim() : '';
    const trimmedImg = imgPath ? imgPath.trim() : '';
    if (!trimmedDrive || !trimmedImg) {
      setMockWriterError('Both target drive and image path are required.');
      return;
    }

    setIsSimulatingWrite(true);
    setMockWriterError(null);
    setMockWriterData(null);
    setProgress(0);

    addLog('info', 'Initializing mock writer simulation (Phase 4A)...');

    try {
      let url = `/api/write/simulate?drive=${encodeURIComponent(trimmedDrive)}&image=${encodeURIComponent(trimmedImg)}`;
      if (mockFailAtChunk) {
        url += `&failAtChunk=${encodeURIComponent(mockFailAtChunk)}`;
      }
      if (mockCancelAtChunk) {
        url += `&cancelAtChunk=${encodeURIComponent(mockCancelAtChunk)}`;
      }

      const response = await fetch(url, {
        method: 'GET',
        headers: { Accept: 'application/json' }
      });

      const payload = await response.json();

      if (!response.ok) {
        throw new Error(payload.error || `Simulation failed with HTTP ${response.status}`);
      }

      // Paranoid Security Validation
      if (
        payload.destructive !== false ||
        payload.operation !== 'mock_writer_simulation' ||
        payload.actual_write_enabled !== false ||
        payload.target_type !== 'null_device'
      ) {
        throw new Error('Simulation payload failed paranoid safety verification check.');
      }

      if (payload.status === 'blocked' || payload.blocked) {
        setMockWriterData(payload);
        const blockReason = payload.block_reasons?.join('; ') || 'Simulation blocked';
        addLog('warning', `Mock writer simulation BLOCKED: ${blockReason}`);
        setProgress(0);
        return;
      }

      const events = payload.events || [];

      for (let i = 0; i < events.length; i++) {
        const event = events[i];

        // Wait for a short duration to simulate live updates
        await new Promise(resolve => setTimeout(resolve, 150));

        // Update progress ring from event progress
        setProgress(event.progress);

        if (event.type === 'simulation_started') {
          addLog('info', 'Mock writer simulation started. Target type: null_device.');
        } else if (event.type === 'chunk_simulated') {
          addLog('info', `[Simulator] Chunk ${event.chunk_index}/${event.chunks_total} completed (${event.progress}%)`);
        } else if (event.type === 'simulation_completed') {
          addLog('success', 'Mock writer simulation completed successfully.');
        } else if (event.type === 'simulation_failed') {
          addLog('error', `Mock writer simulation failed: ${event.message || 'Error'}`);
        } else if (event.type === 'simulation_cancelled') {
          addLog('warning', `Mock writer simulation cancelled at chunk ${event.chunk_index}/${event.chunks_total}.`);
        } else if (event.type === 'simulation_blocked') {
          addLog('warning', 'Mock writer simulation blocked.');
        }

        const partialData = {
          ...payload,
          events: events.slice(0, i + 1),
          chunks_completed: events.slice(0, i + 1).filter(e => e.type === 'chunk_simulated').length,
          bytes_simulated: event.bytes_simulated || 0,
          status: (event.type === 'simulation_completed') ? 'completed' :
                  (event.type === 'simulation_failed') ? 'failed' :
                  (event.type === 'simulation_cancelled') ? 'cancelled' : 'running'
        };
        setMockWriterData(partialData);
      }

    } catch (err) {
      setMockWriterData(null);
      setMockWriterError(err.message);
      addLog('error', `Mock writer simulation error: ${err.message}`);
    } finally {
      setIsSimulatingWrite(false);
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

  // ----- Writer Safety Contract Preview (Phase 4C-2) -----
  // Calls GET /api/write/contract — read-only, no drive mutation.
  // Never writes, formats, partitions, mounts, unmounts, or accesses any drive.
  const fetchContractPreview = async () => {
    setIsPreviewingContract(true);
    setContractError(null);
    setContractData(null);
    try {
      const params = new URLSearchParams();
      if (selectedDrive) params.set('drive', selectedDrive);
      if (imagePath)     params.set('image', imagePath);
      if (auditData?.validation_status === 'passed') params.set('auditPassed', 'true');
      if (mockWriterData?.status === 'completed')    params.set('simulationPassed', 'true');
      const response = await fetch(`/api/write/contract?${params.toString()}`, {
        method: 'GET',
        headers: { Accept: 'application/json' },
      });
      const data = await response.json();
      if (!data || data.schema !== 'bootforge.writer_safety_contract.v1') {
        throw new Error('Unexpected response schema from contract preview endpoint');
      }
      setContractData(data);
    } catch (err) {
      setContractError(err.message || 'Contract preview request failed');
    } finally {
      setIsPreviewingContract(false);
    }
  };

  // Expose Contract Export POST Endpoint
  const exportContractEvidence = async () => {
    const trimmedPath = contractExportPath.trim();
    if (!trimmedPath) {
      setContractExportResult({ status: 'failed', error: 'Please specify a local host export path.' });
      return;
    }

    setIsExportingContract(true);
    setContractExportResult(null);
    addLog('info', `Exporting writer safety contract evidence (${contractExportType.toUpperCase()}) to ${trimmedPath}...`);

    try {
      const response = await fetch('/api/write/contract/export', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          drive: selectedDrive || null,
          image: imagePath || null,
          auditPassed: auditData?.validation_status === 'passed',
          simulationPassed: mockWriterData?.status === 'completed',
          exportPath: trimmedPath,
          exportType: contractExportType
        })
      });

      const payload = await response.json();
      if (!response.ok) {
        throw new Error(payload.error || `Contract export failed with HTTP ${response.status}`);
      }

      setContractExportResult(payload);
      if (payload.status === 'success') {
        addLog('success', `Contract export succeeded: evidence file created at ${trimmedPath}`);
      } else {
        addLog('error', `Contract export blocked: ${payload.error}`);
      }
    } catch (err) {
      setContractExportResult({ status: 'failed', error: err.message });
      addLog('error', `Contract export error: ${err.message}`);
    } finally {
      setIsExportingContract(false);
    }
  };

  // Expose Ledger History Append POST Endpoint (Phase 4C-4)
  const appendContractLedger = async () => {
    const trimmedPath = contractLedgerPath.trim();
    if (!trimmedPath) {
      setLedgerAppendResult({ status: 'failed', error: 'Please specify a local host ledger path.' });
      return;
    }

    setIsAppendingLedger(true);
    setLedgerAppendResult(null);
    addLog('info', `Appending contract session ledger entry to ${trimmedPath}...`);

    try {
      const response = await fetch('/api/write/contract/ledger', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          drive: selectedDrive || null,
          image: imagePath || null,
          auditPassed: auditData?.validation_status === 'passed',
          simulationPassed: mockWriterData?.status === 'completed',
          ledgerPath: trimmedPath,
          eventType: 'dashboard_preview_action'
        })
      });

      const payload = await response.json();
      if (!response.ok) {
        throw new Error(payload.error || `Ledger append failed with HTTP ${response.status}`);
      }

      setLedgerAppendResult(payload);
      if (payload.status === 'success') {
        addLog('success', `Ledger append succeeded: record ${payload.ledger_record_id} appended to ${trimmedPath}`);
      } else {
        addLog('error', `Ledger append blocked: ${payload.error}`);
      }
    } catch (err) {
      setLedgerAppendResult({ status: 'failed', error: err.message });
      addLog('error', `Ledger append error: ${err.message}`);
    } finally {
      setIsAppendingLedger(false);
    }
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
                    onClick={() => {
                      setSelectedDrive(item.drive);
                      checkDriveSafety(item.drive);
                    }}
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

            <div className="glass-panel" style={{ padding: '16px', display: 'flex', flexDirection: 'column', gap: '12px', marginTop: '16px' }}>
              <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>Or Enter Path Manually to Inspect:</span>
              <div style={{ display: 'flex', gap: '10px' }}>
                <input
                  type="text"
                  value={selectedDrive}
                  onChange={(e) => {
                    setSelectedDrive(e.target.value);
                    setSafetyData(null);
                  }}
                  placeholder={'Example: E:\\'}
                  disabled={isRefreshing || isCheckingSafety}
                  style={{
                    padding: '10px',
                    background: 'rgba(0,0,0,0.3)',
                    border: '1px solid var(--border-glass)',
                    borderRadius: '8px',
                    color: '#fff',
                    outline: 'none',
                    flex: 1
                  }}
                />
                <button
                  className="glass-panel"
                  onClick={() => checkDriveSafety(selectedDrive)}
                  disabled={isRefreshing || isCheckingSafety || !selectedDrive.trim()}
                  style={{
                    padding: '10px 16px',
                    borderRadius: '10px',
                    cursor: selectedDrive.trim() ? 'pointer' : 'not-allowed',
                    color: '#fff',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    gap: '8px',
                    border: '1px solid var(--border-glass)'
                  }}
                >
                  <RefreshCw size={16} className={isCheckingSafety ? 'spin-anim' : ''} />
                  Verify Drive
                </button>
              </div>

              {safetyError && (
                <div style={{ color: '#ef4444', fontSize: '0.88rem', marginTop: '4px' }}>
                  <strong>Error:</strong> {safetyError}
                </div>
              )}

              {safetyData && (
                <div className="drive-card" style={{ cursor: 'default', flexDirection: 'column', gap: '12px', background: 'rgba(255, 255, 255, 0.02)', marginTop: '8px', width: '100%', border: '1px solid var(--border-glass)' }}>
                  
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '10px', width: '100%' }}>
                    <div style={{ 
                      padding: '6px 12px', 
                      borderRadius: '20px', 
                      fontSize: '0.82rem', 
                      fontWeight: 600,
                      display: 'flex', 
                      alignItems: 'center', 
                      gap: '6px',
                      background: safetyData.eligible_for_future_write ? 'rgba(16, 185, 129, 0.15)' : 'rgba(239, 68, 68, 0.15)',
                      color: safetyData.eligible_for_future_write ? '#10b981' : '#ef4444',
                      border: `1px solid ${safetyData.eligible_for_future_write ? 'rgba(16, 185, 129, 0.3)' : 'rgba(239, 68, 68, 0.3)'}`
                    }}>
                      <CheckCircle2 size={14} />
                      {safetyData.eligible_for_future_write ? 'Eligible for Future Write Candidate' : 'Write Blocked'}
                    </div>

                    <div style={{ 
                      padding: '6px 12px', 
                      borderRadius: '20px', 
                      fontSize: '0.82rem', 
                      fontWeight: 600,
                      background: safetyData.risk_level === 'low' ? 'rgba(16, 185, 129, 0.15)' : safetyData.risk_level === 'medium' ? 'rgba(245, 158, 11, 0.15)' : 'rgba(239, 68, 68, 0.15)',
                      color: safetyData.risk_level === 'low' ? '#10b981' : safetyData.risk_level === 'medium' ? '#f59e0b' : '#ef4444',
                      border: `1px solid ${safetyData.risk_level === 'low' ? 'rgba(16, 185, 129, 0.3)' : safetyData.risk_level === 'medium' ? 'rgba(245, 158, 11, 0.3)' : 'rgba(239, 68, 68, 0.3)'}`
                    }}>
                      Risk Level: {safetyData.risk_level.toUpperCase()}
                    </div>
                  </div>

                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px 16px', fontSize: '0.85rem', borderTop: '1px solid var(--border-glass)', paddingTop: '10px', marginTop: '4px', width: '100%' }}>
                    <div><span style={{ color: 'var(--text-muted)' }}>Root Path:</span> <code style={{ color: 'var(--accent)' }}>{safetyData.root}</code></div>
                    <div><span style={{ color: 'var(--text-muted)' }}>Label:</span> <strong>{safetyData.label}</strong></div>
                    <div><span style={{ color: 'var(--text-muted)' }}>Filesystem:</span> <strong>{safetyData.filesystem}</strong></div>
                    <div><span style={{ color: 'var(--text-muted)' }}>Drive Type:</span> <strong>{safetyData.type}</strong></div>
                    <div><span style={{ color: 'var(--text-muted)' }}>Total Space:</span> <strong>{safetyData.total_size_gb} GB</strong></div>
                    <div><span style={{ color: 'var(--text-muted)' }}>Free Space:</span> <strong>{safetyData.free_size_gb} GB</strong></div>
                  </div>

                  {safetyData.warnings.length > 0 && (
                    <div style={{ borderTop: '1px solid var(--border-glass)', paddingTop: '10px', marginTop: '4px', width: '100%' }}>
                      <span style={{ fontSize: '0.85rem', fontWeight: 600, color: '#f59e0b', display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '6px' }}>
                        <ShieldAlert size={14} />
                        Safety Warnings ({safetyData.warnings.length})
                      </span>
                      <ul style={{ paddingLeft: '18px', margin: 0, fontSize: '0.82rem', display: 'flex', flexDirection: 'column', gap: '4px' }}>
                        {safetyData.warnings.map((w, idx) => (
                          <li key={idx} style={{ color: '#f87171' }}>{w}</li>
                        ))}
                      </ul>
                    </div>
                  )}

                </div>
              )}
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

          {/* Write Plan Button */}
          <button 
            className="btn-primary" 
            onClick={() => generateWritePlan(selectedDrive, imagePath)}
            disabled={isPlanningWrite || !selectedDrive || !imagePath}
            style={{ 
              opacity: (selectedDrive && imagePath) ? 1 : 0.5,
              cursor: (selectedDrive && imagePath) ? 'pointer' : 'not-allowed',
              background: 'linear-gradient(135deg, var(--primary) 0%, var(--accent) 100%)'
            }}
          >
            <RefreshCw size={20} className={isPlanningWrite ? 'spin-anim' : ''} />
            <span>Generate Dry-Run Write Plan</span>
          </button>

          {/* Simulation Inject Settings */}
          <div className="glass-panel" style={{ marginTop: '20px', padding: '16px', borderStyle: 'dashed', background: 'rgba(255, 255, 255, 0.01)', border: '1px dashed var(--border-glass)' }}>
            <h3 style={{ fontSize: '0.9rem', fontFamily: 'var(--font-tech)', marginBottom: '12px', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Settings size={14} style={{ color: 'var(--accent)' }} />
              <span>Simulation Controls (Optional)</span>
            </h3>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Fail at Chunk #</span>
                <input
                  type="number"
                  min="1"
                  value={mockFailAtChunk}
                  onChange={(e) => setMockFailAtChunk(e.target.value)}
                  placeholder="e.g. 5"
                  style={{
                    padding: '8px',
                    background: 'rgba(0,0,0,0.3)',
                    border: '1px solid var(--border-glass)',
                    borderRadius: '6px',
                    color: '#fff',
                    outline: 'none',
                    fontSize: '0.85rem'
                  }}
                />
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Cancel at Chunk #</span>
                <input
                  type="number"
                  min="1"
                  value={mockCancelAtChunk}
                  onChange={(e) => setMockCancelAtChunk(e.target.value)}
                  placeholder="e.g. 8"
                  style={{
                    padding: '8px',
                    background: 'rgba(0,0,0,0.3)',
                    border: '1px solid var(--border-glass)',
                    borderRadius: '6px',
                    color: '#fff',
                    outline: 'none',
                    fontSize: '0.85rem'
                  }}
                />
              </div>
            </div>
          </div>

          {/* Run Mock Writer Simulation Button */}
          <button 
            className="btn-primary" 
            onClick={() => runMockWriterSimulation(selectedDrive, imagePath)}
            disabled={isSimulatingWrite || !selectedDrive || !imagePath}
            style={{ 
              opacity: (selectedDrive && imagePath) ? 1 : 0.5,
              cursor: (selectedDrive && imagePath) ? 'pointer' : 'not-allowed',
              background: 'linear-gradient(135deg, #7c3aed 0%, #c084fc 100%)',
              marginTop: '12px'
            }}
          >
            <Cpu size={20} className={isSimulatingWrite ? 'spin-anim' : ''} />
            <span>Run Mock Writer Simulation</span>
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

          {writePlanData && (
            <div className="glass-panel" style={{ display: 'flex', flexDirection: 'column', gap: '16px', border: '1px solid var(--border-glass)' }}>
              <h2 style={{ fontSize: '1.1rem', display: 'flex', alignItems: 'center', gap: '8px', borderBottom: '1px solid var(--border-glass)', paddingBottom: '8px', marginBottom: '4px' }}>
                <Cpu size={18} className="glow-text-primary" />
                <span>Dry-Run Execution Plan (Phase 3A)</span>
              </h2>

              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '10px' }}>
                <div style={{ 
                  padding: '6px 12px', 
                  borderRadius: '20px', 
                  fontSize: '0.82rem', 
                  fontWeight: 600,
                  display: 'flex', 
                  alignItems: 'center', 
                  gap: '6px',
                  background: writePlanData.eligible ? 'rgba(16, 185, 129, 0.15)' : 'rgba(239, 68, 68, 0.15)',
                  color: writePlanData.eligible ? '#10b981' : '#ef4444',
                  border: `1px solid ${writePlanData.eligible ? 'rgba(16, 185, 129, 0.3)' : 'rgba(239, 68, 68, 0.3)'}`
                }}>
                  <CheckCircle2 size={14} />
                  {writePlanData.eligible ? 'Eligible for Future Write Candidate' : 'Write Blocked'}
                </div>

                <div style={{ fontSize: '0.82rem', color: 'var(--text-muted)' }}>
                  Safe Mode: <strong style={{ color: '#10b981' }}>ON (Read-Only)</strong>
                </div>
              </div>

              {writePlanData.blocked && (
                <div style={{ padding: '12px', background: 'rgba(239, 68, 68, 0.08)', border: '1px solid rgba(239, 68, 68, 0.2)', borderRadius: '8px', fontSize: '0.88rem', color: '#f87171' }}>
                  <div style={{ fontWeight: 600, display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '4px' }}>
                    <ShieldAlert size={16} />
                    Plan Blocked
                  </div>
                  {writePlanData.block_reasons.map((r, i) => (
                    <div key={i} style={{ paddingLeft: '22px' }}>• {r}</div>
                  ))}
                </div>
              )}

              {/* Execution Steps Sequence */}
              <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                <h3 style={{ fontSize: '0.9rem', color: 'var(--text-muted)', fontFamily: 'var(--font-tech)' }}>Simulated Preflight Checklist:</h3>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                  {writePlanData.steps.map((step) => (
                    <div key={step.id} style={{ 
                      display: 'flex', 
                      alignItems: 'center', 
                      justifyContent: 'space-between', 
                      padding: '10px 14px', 
                      background: 'rgba(0,0,0,0.2)', 
                      borderRadius: '8px',
                      border: '1px solid var(--border-glass)',
                      fontSize: '0.86rem'
                    }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                        <span style={{ 
                          width: '8px', 
                          height: '8px', 
                          borderRadius: '50%', 
                          background: writePlanData.eligible ? 'var(--primary)' : 'rgba(255,255,255,0.2)',
                          boxShadow: writePlanData.eligible ? '0 0 6px var(--primary)' : 'none'
                        }}></span>
                        <span style={{ color: writePlanData.eligible ? '#fff' : 'var(--text-muted)' }}>{step.label}</span>
                      </div>
                      <span style={{ 
                        fontSize: '0.75rem', 
                        fontFamily: 'var(--font-tech)',
                        color: writePlanData.eligible ? 'var(--accent)' : 'var(--text-muted)'
                      }}>
                        {step.status.toUpperCase()}
                      </span>
                    </div>
                  ))}
                </div>
              </div>

              <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', borderTop: '1px solid var(--border-glass)', paddingTop: '10px', display: 'flex', alignItems: 'center', gap: '6px' }}>
                <ShieldAlert size={12} style={{ color: 'var(--accent)' }} />
                <span>Actual write operations are locked. Planning only.</span>
              </div>
            </div>
          )}

          {isAuditingPlan && (
            <div className="glass-panel" style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: '30px', gap: '16px', border: '1px solid rgba(255, 255, 255, 0.1)', background: 'rgba(255,255,255,0.02)' }}>
              <RefreshCw size={24} className="spin-anim" style={{ color: 'var(--primary)' }} />
              <div style={{ fontFamily: 'var(--font-tech)', fontSize: '1rem', color: '#fff', letterSpacing: '0.05em' }}>RUNNING PARANOID SAFETY AUDIT...</div>
              <div style={{ fontSize: '0.82rem', color: 'var(--text-muted)' }}>Verifying write plan schema and checking safety gates</div>
            </div>
          )}

          {auditError && (
            <div className="glass-panel" style={{ padding: '20px', border: '1px solid rgba(239, 68, 68, 0.3)', background: 'rgba(239, 68, 68, 0.05)', display: 'flex', flexDirection: 'column', gap: '10px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#ef4444', fontWeight: 600, fontSize: '1rem' }}>
                <ShieldAlert size={20} />
                <span>Plan Audit Failure</span>
              </div>
              <div style={{ fontSize: '0.88rem', color: '#f87171' }}>{auditError}</div>
            </div>
          )}

          {auditData && (
            <div className="glass-panel animate-fade-in" style={{ display: 'flex', flexDirection: 'column', gap: '18px', border: '1px solid var(--border-glass)' }}>
              <h2 style={{ fontSize: '1.1rem', display: 'flex', alignItems: 'center', gap: '8px', borderBottom: '1px solid var(--border-glass)', paddingBottom: '8px', marginBottom: '4px' }}>
                <ShieldCheck size={20} style={{ color: auditData.validation_status === 'passed' ? '#10b981' : '#ef4444' }} />
                <span>Dry-Run Safety Audit Trail (Phase 3B)</span>
              </h2>

              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '10px' }}>
                <div style={{ 
                  padding: '6px 12px', 
                  borderRadius: '20px', 
                  fontSize: '0.82rem', 
                  fontWeight: 600,
                  display: 'flex', 
                  alignItems: 'center', 
                  gap: '6px',
                  background: auditData.validation_status === 'passed' ? 'rgba(16, 185, 129, 0.15)' : 'rgba(239, 68, 68, 0.15)',
                  color: auditData.validation_status === 'passed' ? '#10b981' : '#ef4444',
                  border: `1px solid ${auditData.validation_status === 'passed' ? 'rgba(16, 185, 129, 0.3)' : 'rgba(239, 68, 68, 0.3)'}`
                }}>
                  {auditData.validation_status === 'passed' ? <CheckCircle2 size={14} /> : <ShieldAlert size={14} />}
                  AUDIT: {auditData.validation_status.toUpperCase()}
                </div>

                <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                  Platform: <strong>{auditData.platform}</strong>
                </div>
              </div>

              {/* Identity & Hashes Box */}
              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', background: 'rgba(0,0,0,0.3)', padding: '12px', borderRadius: '8px', border: '1px solid rgba(255,255,255,0.05)', fontSize: '0.82rem' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid rgba(255,255,255,0.05)', paddingBottom: '6px', marginBottom: '2px' }}>
                  <span style={{ color: 'var(--text-muted)' }}>Audit Identity (Deterministic plan_id):</span>
                  <code style={{ color: 'var(--accent)', fontWeight: 600 }}>{auditData.plan_id || 'N/A'}</code>
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                  <span style={{ color: 'var(--text-muted)' }}>Canonical Plan Hash (SHA256):</span>
                  <code style={{ color: '#94a3b8', fontSize: '0.76rem', wordBreak: 'break-all' }}>{auditData.plan_hash || 'N/A'}</code>
                </div>
              </div>

              {/* Safety Gate Checklist */}
              <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                <h3 style={{ fontSize: '0.9rem', color: 'var(--text-muted)', fontFamily: 'var(--font-tech)' }}>Safety Gate Verification Checklist:</h3>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                  {auditData.checks.map((check) => (
                    <div key={check.id} style={{ 
                      display: 'flex', 
                      alignItems: 'center', 
                      justifyContent: 'space-between', 
                      padding: '10px 14px', 
                      background: check.passed ? 'rgba(16, 185, 129, 0.03)' : 'rgba(239, 68, 68, 0.03)', 
                      borderRadius: '8px',
                      border: `1px solid ${check.passed ? 'rgba(16, 185, 129, 0.15)' : 'rgba(239, 68, 68, 0.15)'}`,
                      fontSize: '0.86rem'
                    }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                        {check.passed ? (
                          <CheckCircle2 size={16} style={{ color: '#10b981' }} />
                        ) : (
                          <ShieldAlert size={16} style={{ color: '#ef4444' }} />
                        )}
                        <span style={{ color: check.passed ? '#fff' : '#f87171', fontWeight: check.passed ? 500 : 600 }}>{check.label}</span>
                      </div>
                      <span style={{ 
                        fontSize: '0.75rem', 
                        fontFamily: 'var(--font-tech)',
                        fontWeight: 600,
                        color: check.passed ? '#10b981' : '#ef4444'
                      }}>
                        {check.passed ? 'PASSED' : 'BLOCKED'}
                      </span>
                    </div>
                  ))}
                </div>
              </div>

              {auditData.blocked && auditData.block_reasons.length > 0 && (
                <div style={{ padding: '12px', background: 'rgba(239, 68, 68, 0.06)', border: '1px solid rgba(239, 68, 68, 0.18)', borderRadius: '8px', fontSize: '0.85rem', color: '#f87171' }}>
                  <div style={{ fontWeight: 600, display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '6px' }}>
                    <ShieldAlert size={15} />
                    Audit Block Reasons
                  </div>
                  <ul style={{ paddingLeft: '18px', margin: 0, display: 'flex', flexDirection: 'column', gap: '4px' }}>
                    {auditData.block_reasons.map((r, i) => (
                      <li key={i}>{r}</li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Evidence Export Center */}
              <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', borderTop: '1px solid var(--border-glass)', paddingTop: '16px' }}>
                <h3 style={{ fontSize: '0.9rem', color: 'var(--text-muted)', fontFamily: 'var(--font-tech)', display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <Settings size={14} style={{ color: 'var(--primary)' }} />
                  <span>Evidence Export Center</span>
                </h3>
                
                {/* Local Host Save Input */}
                <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                  <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Option A: Export to Local Host File Path (No Target USB path)</span>
                  <div style={{ display: 'flex', gap: '10px' }}>
                    <input
                      type="text"
                      value={exportPath}
                      onChange={(e) => {
                        setExportPath(e.target.value);
                        setExportStatus(null);
                      }}
                      placeholder="Example: C:\Users\Bobby\Documents\audit.md (or .json)"
                      disabled={isExporting}
                      style={{
                        padding: '10px',
                        background: 'rgba(0,0,0,0.3)',
                        border: '1px solid var(--border-glass)',
                        borderRadius: '8px',
                        color: '#fff',
                        outline: 'none',
                        flex: 1,
                        fontSize: '0.85rem'
                      }}
                    />
                  </div>
                  <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
                    <button
                      className="glass-panel"
                      onClick={() => exportAuditToHost('json')}
                      disabled={isExporting || !exportPath.trim()}
                      style={{
                        padding: '8px 14px',
                        borderRadius: '8px',
                        cursor: exportPath.trim() ? 'pointer' : 'not-allowed',
                        color: '#fff',
                        fontSize: '0.8rem',
                        border: '1px solid var(--border-glass)',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '6px'
                      }}
                    >
                      <RefreshCw size={12} className={isExporting ? 'spin-anim' : ''} />
                      Save JSON to Host
                    </button>
                    <button
                      className="glass-panel"
                      onClick={() => exportAuditToHost('markdown')}
                      disabled={isExporting || !exportPath.trim()}
                      style={{
                        padding: '8px 14px',
                        borderRadius: '8px',
                        cursor: exportPath.trim() ? 'pointer' : 'not-allowed',
                        color: '#fff',
                        fontSize: '0.8rem',
                        border: '1px solid var(--border-glass)',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '6px'
                      }}
                    >
                      <RefreshCw size={12} className={isExporting ? 'spin-anim' : ''} />
                      Save Markdown to Host
                    </button>
                  </div>
                </div>

                {/* Direct Browser Download */}
                <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', marginTop: '4px' }}>
                  <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Option B: Direct Browser Download (In-Memory)</span>
                  <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
                    <button
                      className="glass-panel"
                      onClick={() => downloadAuditInBrowser('json')}
                      style={{
                        padding: '8px 14px',
                        borderRadius: '8px',
                        cursor: 'pointer',
                        color: '#fff',
                        fontSize: '0.8rem',
                        border: '1px solid var(--border-glass)',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '6px'
                      }}
                    >
                      <FolderPlus size={12} />
                      Download JSON (Browser)
                    </button>
                    <button
                      className="glass-panel"
                      onClick={() => downloadAuditInBrowser('markdown')}
                      style={{
                        padding: '8px 14px',
                        borderRadius: '8px',
                        cursor: 'pointer',
                        color: '#fff',
                        fontSize: '0.8rem',
                        border: '1px solid var(--border-glass)',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '6px'
                      }}
                    >
                      <FolderPlus size={12} />
                      Download Markdown (Browser)
                    </button>
                  </div>
                </div>

                {/* Status Message */}
                {exportStatus && (
                  <div style={{ 
                    fontSize: '0.85rem', 
                    padding: '8px 12px', 
                    borderRadius: '6px', 
                    background: exportStatus.status === 'success' ? 'rgba(16, 185, 129, 0.1)' : 'rgba(239, 68, 68, 0.1)',
                    color: exportStatus.status === 'success' ? '#10b981' : '#f87171',
                    border: `1px solid ${exportStatus.status === 'success' ? 'rgba(16, 185, 129, 0.2)' : 'rgba(239, 68, 68, 0.2)'}`,
                    marginTop: '4px'
                  }}>
                    {exportStatus.message}
                  </div>
                )}
              </div>

              <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', borderTop: '1px solid var(--border-glass)', paddingTop: '10px', display: 'flex', alignItems: 'center', gap: '6px' }}>
                <ShieldAlert size={12} style={{ color: auditData.validation_status === 'passed' ? '#10b981' : '#ef4444' }} />
                <span>
                  This report is evidence of a dry-run audit only. It does not indicate that a write, format, partition, or mount operation was performed.
                </span>
              </div>
            </div>
          )}

          {(mockWriterData || isSimulatingWrite) && (
            <div className="glass-panel animate-fade-in" style={{ display: 'flex', flexDirection: 'column', gap: '18px', border: '1px solid var(--border-glass)' }}>
              <h2 style={{ fontSize: '1.1rem', display: 'flex', alignItems: 'center', gap: '8px', borderBottom: '1px solid var(--border-glass)', paddingBottom: '8px', marginBottom: '4px' }}>
                <Cpu size={20} style={{ color: 'var(--accent)' }} />
                <span>Mock Writer Simulation Panel (Phase 4A-2B)</span>
              </h2>

              {/* Status & Basic Metadata Grid */}
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', fontSize: '0.85rem' }}>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '4px', background: 'rgba(0,0,0,0.2)', padding: '10px', borderRadius: '8px' }}>
                  <span style={{ color: 'var(--text-muted)' }}>Status</span>
                  <strong style={{ 
                    color: mockWriterData?.status === 'completed' ? '#10b981' : 
                           mockWriterData?.status === 'failed' ? '#ef4444' : 
                           mockWriterData?.status === 'cancelled' ? '#f59e0b' : 
                           mockWriterData?.status === 'blocked' ? '#f87171' : '#60a5fa',
                    textTransform: 'uppercase'
                  }}>
                    {isSimulatingWrite ? 'SIMULATING...' : (mockWriterData?.status || 'UNKNOWN')}
                  </strong>
                </div>

                <div style={{ display: 'flex', flexDirection: 'column', gap: '4px', background: 'rgba(0,0,0,0.2)', padding: '10px', borderRadius: '8px' }}>
                  <span style={{ color: 'var(--text-muted)' }}>Target Type</span>
                  <strong style={{ color: '#fff' }}>
                    {mockWriterData?.target_type || 'N/A'}
                  </strong>
                </div>

                <div style={{ display: 'flex', flexDirection: 'column', gap: '4px', background: 'rgba(0,0,0,0.2)', padding: '10px', borderRadius: '8px' }}>
                  <span style={{ color: 'var(--text-muted)' }}>Plan ID</span>
                  <code style={{ color: 'var(--accent)', fontSize: '0.8rem' }}>
                    {mockWriterData?.plan_id || 'N/A'}
                  </code>
                </div>

                <div style={{ display: 'flex', flexDirection: 'column', gap: '4px', background: 'rgba(0,0,0,0.2)', padding: '10px', borderRadius: '8px' }}>
                  <span style={{ color: 'var(--text-muted)' }}>Actual Write Enabled</span>
                  <strong style={{ color: mockWriterData?.actual_write_enabled ? '#ef4444' : '#10b981' }}>
                    {mockWriterData?.actual_write_enabled ? 'TRUE' : 'FALSE'}
                  </strong>
                </div>
              </div>

              {/* Progress & Bytes Info */}
              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', background: 'rgba(0,0,0,0.2)', padding: '12px', borderRadius: '8px' }}>
                <div style={{ display: 'flex', width: '100%', justifyContent: 'space-between', fontSize: '0.85rem' }}>
                  <span style={{ color: 'var(--text-muted)' }}>Chunks Progress</span>
                  <strong>
                    {mockWriterData?.chunks_completed || 0} / {mockWriterData?.chunks_total || 0}
                  </strong>
                </div>
                <div style={{ display: 'flex', width: '100%', justifyContent: 'space-between', fontSize: '0.85rem' }}>
                  <span style={{ color: 'var(--text-muted)' }}>Bytes Simulated</span>
                  <strong>
                    {mockWriterData?.bytes_simulated?.toLocaleString() || 0} bytes
                  </strong>
                </div>
              </div>

              {/* Block Reasons if Blocked */}
              {mockWriterData?.blocked && mockWriterData.block_reasons && mockWriterData.block_reasons.length > 0 && (
                <div style={{ padding: '12px', background: 'rgba(239, 68, 68, 0.08)', border: '1px solid rgba(239, 68, 68, 0.2)', borderRadius: '8px', fontSize: '0.88rem', color: '#f87171' }}>
                  <div style={{ fontWeight: 600, display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '4px' }}>
                    <ShieldAlert size={16} />
                    Block Reasons
                  </div>
                  {mockWriterData.block_reasons.map((r, i) => (
                    <div key={i} style={{ paddingLeft: '22px' }}>• {r}</div>
                  ))}
                </div>
              )}

              {/* Event Stream List */}
              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                <h3 style={{ fontSize: '0.9rem', color: 'var(--text-muted)', fontFamily: 'var(--font-tech)' }}>Event Stream Log:</h3>
                <div style={{ 
                  maxHeight: '200px', 
                  overflowY: 'auto', 
                  display: 'flex', 
                  flexDirection: 'column', 
                  gap: '6px',
                  background: 'rgba(0,0,0,0.3)',
                  padding: '10px',
                  borderRadius: '8px',
                  border: '1px solid rgba(255,255,255,0.05)'
                }}>
                  {mockWriterData?.events && mockWriterData.events.length > 0 ? (
                    mockWriterData.events.map((e, idx) => (
                      <div key={idx} style={{ 
                        display: 'flex', 
                        justifyContent: 'space-between', 
                        fontSize: '0.82rem',
                        padding: '4px 6px',
                        borderRadius: '4px',
                        background: e.type === 'simulation_completed' ? 'rgba(16, 185, 129, 0.08)' :
                                    e.type === 'simulation_failed' ? 'rgba(239, 68, 68, 0.08)' : 'transparent'
                      }}>
                        <span style={{ 
                          color: e.type === 'simulation_completed' ? '#10b981' : 
                                 e.type === 'simulation_failed' ? '#ef4444' : 
                                 e.type === 'simulation_cancelled' ? '#f59e0b' : '#e2e8f0'
                        }}>
                          {e.type}
                        </span>
                        <span style={{ color: 'var(--text-muted)' }}>{e.progress}%</span>
                      </div>
                    ))
                  ) : (
                    <div style={{ color: 'var(--text-muted)', fontSize: '0.8rem', textAlign: 'center', padding: '10px' }}>
                      Waiting for stream events...
                    </div>
                  )}
                </div>
              </div>

              {/* Error display */}
              {mockWriterError && (
                <div style={{ padding: '10px', background: 'rgba(239, 68, 68, 0.1)', border: '1px solid rgba(239, 68, 68, 0.3)', borderRadius: '6px', color: '#f87171', fontSize: '0.85rem' }}>
                  {mockWriterError}
                </div>
              )}

              {/* Safety Copy */}
              <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', borderTop: '1px solid var(--border-glass)', paddingTop: '10px', display: 'flex', alignItems: 'center', gap: '6px' }}>
                <ShieldAlert size={14} style={{ color: 'var(--accent)', flexShrink: 0 }} />
                <span>
                  Null-device simulation only. No USB write, format, partition, mount, unmount, or raw disk access is performed.
                </span>
              </div>
            </div>
          )}

          {/* --------------------------------------------------------- */}
          {/* Writer Safety Contract Preview Panel (Phase 4C-2)          */}
          {/* Read-only. No writes. No formatting. No drive mutation.    */}
          {/* --------------------------------------------------------- */}
          <div
            id="writer-safety-contract-preview-panel"
            className="glass-panel animate-fade-in"
            style={{
              display: 'flex',
              flexDirection: 'column',
              gap: '16px',
              border: '1px solid rgba(139, 92, 246, 0.35)',
              background: 'rgba(139, 92, 246, 0.04)',
            }}
          >
            {/* Panel Header */}
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '12px', borderBottom: '1px solid rgba(139,92,246,0.2)', paddingBottom: '10px' }}>
              <h2 style={{ fontSize: '1.05rem', display: 'flex', alignItems: 'center', gap: '8px', margin: 0 }}>
                <ShieldCheck size={18} style={{ color: '#8b5cf6' }} />
                <span style={{ fontFamily: 'var(--font-tech)', letterSpacing: '0.04em' }}>Writer Safety Contract Preview</span>
              </h2>
              <button
                id="btn-preview-writer-safety-contract"
                className="btn-primary"
                onClick={fetchContractPreview}
                disabled={isPreviewingContract}
                style={{
                  background: 'linear-gradient(135deg, #6d28d9 0%, #8b5cf6 100%)',
                  padding: '8px 16px',
                  fontSize: '0.85rem',
                  opacity: isPreviewingContract ? 0.6 : 1,
                  cursor: isPreviewingContract ? 'not-allowed' : 'pointer',
                }}
              >
                {isPreviewingContract
                  ? <><RefreshCw size={14} className="spin-anim" /> Previewing…</>
                  : <><ShieldCheck size={14} /> Preview Writer Safety Contract</>}
              </button>
            </div>

            {/* Safety Copy — always visible */}
            <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)', display: 'flex', alignItems: 'flex-start', gap: '6px', background: 'rgba(0,0,0,0.15)', padding: '8px 10px', borderRadius: '6px', lineHeight: 1.5 }}>
              <ShieldAlert size={13} style={{ color: '#8b5cf6', flexShrink: 0, marginTop: '1px' }} />
              <span>Read-only safety contract preview. No USB write, format, partition, mount, unmount, raw disk access, or destructive operation is available.</span>
            </div>

            {/* Loading state */}
            {isPreviewingContract && (
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px', padding: '12px', color: 'var(--text-muted)', fontSize: '0.88rem' }}>
                <RefreshCw size={16} className="spin-anim" style={{ color: '#8b5cf6' }} />
                <span>Fetching safety contract from backend…</span>
              </div>
            )}

            {/* Error state */}
            {contractError && (
              <div style={{ padding: '12px', background: 'rgba(239,68,68,0.08)', border: '1px solid rgba(239,68,68,0.25)', borderRadius: '8px', color: '#f87171', fontSize: '0.85rem', display: 'flex', alignItems: 'center', gap: '8px' }}>
                <ShieldAlert size={16} />
                <span>{contractError}</span>
              </div>
            )}

            {/* Contract data */}
            {contractData && (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>

                {/* Schema + IDs row */}
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
                  <span style={{ fontFamily: 'var(--font-tech)', fontSize: '0.75rem', padding: '3px 10px', borderRadius: '20px', background: 'rgba(139,92,246,0.15)', color: '#a78bfa', border: '1px solid rgba(139,92,246,0.3)' }}>
                    {contractData.schema}
                  </span>
                  <span style={{ fontFamily: 'var(--font-tech)', fontSize: '0.72rem', padding: '3px 10px', borderRadius: '20px', background: 'rgba(0,0,0,0.2)', color: 'var(--text-muted)', border: '1px solid var(--border-glass)' }}>
                    Phase {contractData.phase}
                  </span>
                  <span style={{
                    fontFamily: 'var(--font-tech)', fontSize: '0.75rem', padding: '3px 10px', borderRadius: '20px', border: '1px solid rgba(239,68,68,0.35)',
                    background: contractData.blocked ? 'rgba(239,68,68,0.12)' : 'rgba(16,185,129,0.12)',
                    color: contractData.blocked ? '#f87171' : '#10b981',
                  }}>
                    {contractData.blocked ? '⛔ BLOCKED' : '✓ UNBLOCKED'}
                  </span>
                </div>

                {/* Immutable safety values */}
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px' }}>
                  {[{
                    label: 'real_writer_implemented',
                    value: String(contractData.real_writer_implemented),
                    ok: contractData.real_writer_implemented === false,
                  }, {
                    label: 'destructive_operations_enabled',
                    value: String(contractData.destructive_operations_enabled),
                    ok: contractData.destructive_operations_enabled === false,
                  }].map(({ label, value, ok }) => (
                    <div key={label} style={{ background: 'rgba(0,0,0,0.25)', borderRadius: '8px', padding: '10px 12px', border: `1px solid ${ok ? 'rgba(16,185,129,0.25)' : 'rgba(239,68,68,0.35)'}`, display: 'flex', flexDirection: 'column', gap: '4px' }}>
                      <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)', fontFamily: 'var(--font-tech)' }}>{label}</span>
                      <span style={{ fontSize: '0.95rem', fontWeight: 700, color: ok ? '#10b981' : '#f87171', fontFamily: 'var(--font-tech)' }}>{value}</span>
                    </div>
                  ))}
                </div>

                {/* Gate results table */}
                {contractData.gate_results && (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                    <h3 style={{ fontSize: '0.82rem', color: 'var(--text-muted)', margin: 0, fontFamily: 'var(--font-tech)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Gate Results</h3>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                      {(contractData.required_gates || Object.keys(contractData.gate_results)).map((gate) => {
                        const passed = contractData.gate_results[gate];
                        return (
                          <div key={gate} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '6px 10px', background: 'rgba(0,0,0,0.2)', borderRadius: '6px', border: '1px solid var(--border-glass)', fontSize: '0.8rem' }}>
                            <span style={{ color: passed ? '#fff' : 'var(--text-muted)', fontFamily: 'var(--font-tech)' }}>{gate}</span>
                            <span style={{ fontSize: '0.72rem', fontWeight: 700, color: passed ? '#10b981' : '#94a3b8', fontFamily: 'var(--font-tech)' }}>{passed ? '✓ PASS' : '— PENDING'}</span>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                )}

                {/* Identity hashes */}
                {(contractData.device_identity?.identity_hash || contractData.image_identity?.identity_hash) && (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                    <h3 style={{ fontSize: '0.82rem', color: 'var(--text-muted)', margin: 0, fontFamily: 'var(--font-tech)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Identity Hashes</h3>
                    {contractData.device_identity?.identity_hash && (
                      <div style={{ fontFamily: 'var(--font-tech)', fontSize: '0.72rem', color: 'var(--text-muted)', background: 'rgba(0,0,0,0.25)', padding: '8px 10px', borderRadius: '6px', wordBreak: 'break-all' }}>
                        <span style={{ color: '#a78bfa', marginRight: '8px' }}>device:</span>{contractData.device_identity.identity_hash}
                      </div>
                    )}
                    {contractData.image_identity?.identity_hash && (
                      <div style={{ fontFamily: 'var(--font-tech)', fontSize: '0.72rem', color: 'var(--text-muted)', background: 'rgba(0,0,0,0.25)', padding: '8px 10px', borderRadius: '6px', wordBreak: 'break-all' }}>
                        <span style={{ color: '#a78bfa', marginRight: '8px' }}>image:</span>{contractData.image_identity.identity_hash}
                      </div>
                    )}
                  </div>
                )}

                {/* Block reasons */}
                {contractData.block_reasons?.length > 0 && (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                    <h3 style={{ fontSize: '0.82rem', color: '#f87171', margin: 0, fontFamily: 'var(--font-tech)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Block Reasons</h3>
                    {contractData.block_reasons.map((r, i) => (
                      <div key={i} style={{ fontSize: '0.8rem', color: '#fca5a5', paddingLeft: '14px', display: 'flex', gap: '6px', alignItems: 'flex-start', lineHeight: 1.4 }}>
                        <span style={{ color: '#ef4444', flexShrink: 0 }}>•</span>
                        <span>{r}</span>
                      </div>
                    ))}
                  </div>
                )}

                {/* Warnings */}
                {contractData.warnings?.length > 0 && (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                    <h3 style={{ fontSize: '0.82rem', color: '#fbbf24', margin: 0, fontFamily: 'var(--font-tech)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Warnings</h3>
                    {contractData.warnings.map((w, i) => (
                      <div key={i} style={{ fontSize: '0.78rem', color: '#fcd34d', paddingLeft: '14px', display: 'flex', gap: '6px', alignItems: 'flex-start', lineHeight: 1.4 }}>
                        <span style={{ color: '#f59e0b', flexShrink: 0 }}>⚠</span>
                        <span>{w}</span>
                      </div>
                    ))}
                  </div>
                )}

                {/* Next required action */}
                {contractData.next_required_action && (
                  <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', background: 'rgba(0,0,0,0.2)', padding: '8px 12px', borderRadius: '6px', border: '1px solid var(--border-glass)', display: 'flex', gap: '8px', alignItems: 'center' }}>
                    <ShieldAlert size={13} style={{ color: '#8b5cf6', flexShrink: 0 }} />
                    <span><strong style={{ color: '#c4b5fd' }}>Next action:</strong> {contractData.next_required_action}</span>
                  </div>
                )}

                {/* Session ID display (Phase 4C-4) */}
                {contractData.session_id && (
                  <div style={{ fontFamily: 'var(--font-tech)', fontSize: '0.72rem', color: 'var(--text-muted)', background: 'rgba(139,92,246,0.1)', padding: '6px 10px', borderRadius: '6px', border: '1px solid rgba(139,92,246,0.15)', wordBreak: 'break-all' }}>
                    <span style={{ color: '#a78bfa', marginRight: '8px', fontWeight: 600 }}>session:</span>{contractData.session_id}
                  </div>
                )}

                {/* Contract ID + timestamp */}
                <div style={{ fontSize: '0.72rem', color: 'rgba(148,163,184,0.5)', fontFamily: 'var(--font-tech)', borderTop: '1px solid rgba(255,255,255,0.04)', paddingTop: '8px' }}>
                  {contractData.contract_id} · {contractData.created_at}
                </div>

                {/* Contract Export Section (Phase 4C-3) */}
                <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', borderTop: '1px solid rgba(255,255,255,0.08)', paddingTop: '14px', marginTop: '4px' }}>
                  <h3 style={{ fontSize: '0.85rem', color: 'var(--text-muted)', margin: 0, fontFamily: 'var(--font-tech)', display: 'flex', alignItems: 'center', gap: '6px' }}>
                    <Settings size={13} style={{ color: '#8b5cf6' }} />
                    <span>Export Contract Evidence</span>
                  </h3>
                  
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                    <div style={{ display: 'flex', gap: '10px' }}>
                      <input
                        type="text"
                        value={contractExportPath}
                        onChange={(e) => {
                          setContractExportPath(e.target.value);
                          setContractExportResult(null);
                        }}
                        placeholder="Save path e.g. C:\Users\Bobby\contract.md (or .json)"
                        disabled={isExportingContract}
                        style={{
                          padding: '8px 10px',
                          background: 'rgba(0,0,0,0.3)',
                          border: '1px solid var(--border-glass)',
                          borderRadius: '6px',
                          color: '#fff',
                          outline: 'none',
                          flex: 1,
                          fontSize: '0.8rem'
                        }}
                      />
                      <select
                        value={contractExportType}
                        onChange={(e) => {
                          setContractExportType(e.target.value);
                          setContractExportResult(null);
                        }}
                        disabled={isExportingContract}
                        style={{
                          padding: '8px 10px',
                          background: 'rgba(0,0,0,0.3)',
                          border: '1px solid var(--border-glass)',
                          borderRadius: '6px',
                          color: '#fff',
                          outline: 'none',
                          fontSize: '0.8rem'
                        }}
                      >
                        <option value="json">JSON</option>
                        <option value="markdown">Markdown</option>
                      </select>
                    </div>

                    <button
                      className="btn-primary"
                      onClick={exportContractEvidence}
                      disabled={isExportingContract || !contractExportPath.trim()}
                      style={{
                        background: 'linear-gradient(135deg, #6d28d9 0%, #8b5cf6 100%)',
                        padding: '8px 14px',
                        borderRadius: '6px',
                        fontSize: '0.8rem',
                        cursor: contractExportPath.trim() ? 'pointer' : 'not-allowed',
                        opacity: (isExportingContract || !contractExportPath.trim()) ? 0.6 : 1,
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        gap: '6px'
                      }}
                    >
                      <RefreshCw size={12} className={isExportingContract ? 'spin-anim' : ''} />
                      <span>Export Contract Evidence</span>
                    </button>
                  </div>

                  {contractExportResult && (
                    <div style={{
                      fontSize: '0.8rem',
                      padding: '8px 12px',
                      borderRadius: '6px',
                      background: contractExportResult.status === 'success' ? 'rgba(16, 185, 129, 0.1)' : 'rgba(239, 68, 68, 0.1)',
                      color: contractExportResult.status === 'success' ? '#10b981' : '#f87171',
                      border: `1px solid ${contractExportResult.status === 'success' ? 'rgba(16, 185, 129, 0.2)' : 'rgba(239, 68, 68, 0.2)'}`
                    }}>
                      {contractExportResult.status === 'success' 
                        ? `Evidence exported successfully.` 
                        : `Export Blocked: ${contractExportResult.error}`}
                    </div>
                  )}
                </div>

                {/* Contract Ledger Section (Phase 4C-4) */}
                <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', borderTop: '1px solid rgba(255,255,255,0.08)', paddingTop: '14px', marginTop: '4px' }}>
                  <h3 style={{ fontSize: '0.85rem', color: 'var(--text-muted)', margin: 0, fontFamily: 'var(--font-tech)', display: 'flex', alignItems: 'center', gap: '6px' }}>
                    <Settings size={13} style={{ color: '#8b5cf6' }} />
                    <span>Append Contract Ledger Record</span>
                  </h3>
                  
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                    <input
                      type="text"
                      value={contractLedgerPath}
                      onChange={(e) => {
                        setContractLedgerPath(e.target.value);
                        setLedgerAppendResult(null);
                      }}
                      placeholder="Ledger path e.g. C:\Users\Bobby\history.jsonl"
                      disabled={isAppendingLedger}
                      style={{
                        padding: '8px 10px',
                        background: 'rgba(0,0,0,0.3)',
                        border: '1px solid var(--border-glass)',
                        borderRadius: '6px',
                        color: '#fff',
                        outline: 'none',
                        fontSize: '0.8rem'
                      }}
                    />

                    <button
                      className="btn-primary"
                      onClick={appendContractLedger}
                      disabled={isAppendingLedger || !contractLedgerPath.trim()}
                      style={{
                        background: 'linear-gradient(135deg, #6d28d9 0%, #8b5cf6 100%)',
                        padding: '8px 14px',
                        borderRadius: '6px',
                        fontSize: '0.8rem',
                        cursor: contractLedgerPath.trim() ? 'pointer' : 'not-allowed',
                        opacity: (isAppendingLedger || !contractLedgerPath.trim()) ? 0.6 : 1,
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        gap: '6px'
                      }}
                    >
                      <RefreshCw size={12} className={isAppendingLedger ? 'spin-anim' : ''} />
                      <span>Append Contract Ledger Record</span>
                    </button>
                  </div>

                  {ledgerAppendResult && (
                    <div style={{
                      fontSize: '0.8rem',
                      padding: '8px 12px',
                      borderRadius: '6px',
                      background: ledgerAppendResult.status === 'success' ? 'rgba(16, 185, 129, 0.1)' : 'rgba(239, 68, 68, 0.1)',
                      color: ledgerAppendResult.status === 'success' ? '#10b981' : '#f87171',
                      border: `1px solid ${ledgerAppendResult.status === 'success' ? 'rgba(16, 185, 129, 0.2)' : 'rgba(239, 68, 68, 0.2)'}`
                    }}>
                      {ledgerAppendResult.status === 'success' 
                        ? `Ledger record appended successfully.` 
                        : `Ledger Blocked: ${ledgerAppendResult.error}`}
                    </div>
                  )}
                </div>
              </div>
            )}
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
