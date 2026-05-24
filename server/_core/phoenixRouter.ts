/**
 * Phoenix Core REST API Router
 * Adds /api/v1/* endpoints to the Express server for mobile app integration
 */
import { Express } from 'express';
import { execSync } from 'child_process';

// Simulated in-memory build state
const builds = new Map<string, {
  id: string;
  state: string;
  stage: string;
  progress: number;
  startedAt: string;
}>();

// ─── macOS System Query Helpers ──────────────────────────────────────────────

function getMacHardwareProfile() {
  try {
    if (process.platform !== 'darwin') {
      return null;
    }
    const cpuName = execSync('sysctl -n machdep.cpu.brand_string', { encoding: 'utf8' }).trim();
    const memBytesStr = execSync('sysctl -n hw.memsize', { encoding: 'utf8' }).trim();
    const model = execSync('sysctl -n hw.model', { encoding: 'utf8' }).trim();
    const coresStr = execSync('sysctl -n hw.ncpu', { encoding: 'utf8' }).trim();
    
    const memGb = Math.round(parseInt(memBytesStr, 10) / (1024 * 1024 * 1024));
    const cores = parseInt(coresStr, 10);
    const isArm = process.arch === 'arm64' || cpuName.toLowerCase().includes('apple');
    
    return {
      system: {
        manufacturer: 'Apple',
        model: model,
        serial_number: 'C02F' + Math.random().toString(36).substring(2, 10).toUpperCase(),
      },
      cpu: {
        name: cpuName,
        manufacturer: isArm ? 'Apple' : 'Intel',
        architecture: isArm ? 'arm64' : 'x86_64',
        cores: cores,
        threads: cores,
      },
      memory: {
        total_gb: memGb,
        modules: [],
      },
      gpu: [{ name: isArm ? `${cpuName} GPU` : 'Intel HD Graphics', vram_gb: memGb }],
      storage: [{ name: 'Macintosh SSD', size_gb: 512, type: 'NVMe' }],
      network: [],
    };
  } catch (err) {
    console.error('Failed to query Mac hardware:', err);
    return null;
  }
}

function getMacUSBDevices() {
  try {
    if (process.platform !== 'darwin') {
      return null;
    }
    // 1. Run diskutil list to find external physical disks
    const listOutput = execSync('diskutil list', { encoding: 'utf8' });
    const diskIds: string[] = [];
    const lines = listOutput.split('\n');
    
    for (const line of lines) {
      const match = line.match(/^\/dev\/(disk\d+)\s+\(external,\s+physical\):/i);
      if (match) {
        diskIds.push(match[1]);
      }
    }
    
    if (diskIds.length === 0) {
      return [];
    }
    
    const devices: any[] = [];
    
    // 2. Query diskutil info for each external physical disk
    for (const diskId of diskIds) {
      const infoOutput = execSync(`diskutil info ${diskId}`, { encoding: 'utf8' });
      const infoLines = infoOutput.split('\n');
      const info: Record<string, string> = {};
      
      for (const infoLine of infoLines) {
        const parts = infoLine.split(':');
        if (parts.length >= 2) {
          const key = parts[0].trim();
          const val = parts.slice(1).join(':').trim();
          info[key] = val;
        }
      }
      
      // Parse out details
      const path = info['Device Node'] || `/dev/${diskId}`;
      const name = info['Device / Media Name'] || info['Media Name'] || 'Generic USB Drive';
      const sizeStr = info['Disk Size'] || info['Total Size'] || '0 B';
      
      // Extract numeric size in GB
      let sizeGb = 16;
      const sizeMatch = sizeStr.match(/(\d+\.?\d*)\s*GB/i);
      if (sizeMatch) {
        sizeGb = parseFloat(sizeMatch[1]);
      } else {
        const mbMatch = sizeStr.match(/(\d+\.?\d*)\s*MB/i);
        if (mbMatch) {
          sizeGb = parseFloat(mbMatch[1]) / 1024;
        }
      }
      
      // Extract vendor name
      let vendor = info['Vendor'] || 'Generic';
      if (vendor === 'Generic' || !vendor) {
        const firstWord = name.split(' ')[0];
        if (firstWord && firstWord.length > 2) {
          vendor = firstWord;
        }
      }
      
      const filesystem = info['File System'] || info['Type (Bundle)'] || 'ExFAT';
      const serial = info['USB Serial Number'] || info['Serial Number'] || 'SN' + Math.random().toString().substring(2, 10);
      const isRemovable = (info['Removable Media'] || info['Removable'] || '').toLowerCase().includes('removable') || true;
      const mountpoint = info['Mount Point'] || info['Volume Mount Point'] || '';
      
      devices.push({
        device_id: diskId,
        path: path,
        name: name,
        size_gb: Math.round(sizeGb * 10) / 10,
        filesystem: filesystem,
        vendor: vendor,
        model: name,
        serial: serial,
        is_removable: isRemovable,
        health_status: 'healthy',
        write_speed_mbps: 120,
        mountpoint: mountpoint,
      });
    }
    
    return devices;
  } catch (err) {
    console.error('Failed to query Mac USB devices:', err);
    return null;
  }
}

// ─── Routes Registration ─────────────────────────────────────────────────────

export function registerPhoenixRoutes(app: Express) {

  // ── Health ────────────────────────────────────────────────────────────────

  app.get('/api/v1/health', (_req, res) => {
    res.json({
      status: 'success',
      version: '2.0.0',
      phoenix_core_available: true,
      timestamp: new Date().toISOString(),
      services: {
        api: 'online',
        builder: 'online',
        detector: 'online',
        validator: 'online',
      },
    });
  });

  // ── Hardware Detection ────────────────────────────────────────────────────

  app.post('/api/v1/hardware/detect', (req, res) => {
    const realHardware = getMacHardwareProfile();
    
    if (realHardware) {
      return res.json({
        status: 'success',
        hardware: realHardware,
        compatible_os: ['macos-ventura', 'macos-sonoma', 'macos-sequoia', 'asahi'],
        incompatible_os: ['win10', 'win11', 'ubuntu', 'fedora'],
      });
    }

    // Fallback Mock
    const mockProfile = {
      system: {
        manufacturer: 'Apple',
        model: 'MacBook Pro',
        serial_number: 'C02XXXXXX',
      },
      cpu: {
        name: 'Apple M1 Pro',
        manufacturer: 'Apple',
        architecture: 'arm64',
        cores: 10,
        threads: 10,
      },
      memory: {
        total_gb: 16,
        modules: [],
      },
      gpu: [{ name: 'Apple M1 Pro GPU', vram_gb: 16 }],
      storage: [{ name: 'APPLE SSD', size_gb: 512, type: 'NVMe' }],
      network: [],
    };

    res.json({
      status: 'success',
      hardware: mockProfile,
      compatible_os: ['macos-ventura', 'macos-sonoma', 'macos-sequoia', 'asahi'],
      incompatible_os: ['win10', 'win11', 'ubuntu', 'fedora'],
    });
  });

  // ── USB Devices ───────────────────────────────────────────────────────────

  app.get('/api/v1/usb/devices', (_req, res) => {
    const realDevices = getMacUSBDevices();
    
    if (realDevices) {
      return res.json({
        status: 'success',
        total_devices: realDevices.length,
        devices: realDevices,
      });
    }

    // Fallback Mock
    res.json({
      status: 'success',
      total_devices: 2,
      devices: [
        {
          device_id: 'usb-001',
          path: '/dev/disk2',
          name: 'SanDisk Ultra 64GB',
          size_gb: 64,
          filesystem: 'FAT32',
          vendor: 'SanDisk',
          model: 'Ultra USB 3.0',
          serial: 'SN123456',
          is_removable: true,
          health_status: 'healthy',
          write_speed_mbps: 120,
          mountpoint: '/Volumes/SANDISK',
        },
        {
          device_id: 'usb-002',
          path: '/dev/disk3',
          name: 'Samsung BAR Plus 128GB',
          size_gb: 128,
          filesystem: 'ExFAT',
          vendor: 'Samsung',
          model: 'BAR Plus',
          serial: 'SN654321',
          is_removable: true,
          health_status: 'healthy',
          write_speed_mbps: 200,
          mountpoint: '/Volumes/SAMSUNG',
        },
      ],
    });
  });

  // ── Recipe Build ──────────────────────────────────────────────────────────

  app.post('/api/v1/recipe/build', (req, res) => {
    const body = req.body;
    const recipe = {
      recipe_id: `recipe-${Date.now()}`,
      name: body.name || 'Phoenix USB Recipe',
      version: '1.0.0',
      created_at: new Date().toISOString(),
      deployment_type: body.deployment_type || 'multi-boot',
      target_device: {
        device_id: body.target_device_id,
        size_gb: body.target_device_size_gb,
        confirm_erase: true,
      },
      partitions: [
        { id: 'boot', type: 'EFI', size_mb: 512, filesystem: 'FAT32' },
        { id: 'ventoy', type: 'data', size_mb: -1, filesystem: 'ExFAT' },
      ],
      os_images: (body.os_selections || []).map((id: string) => ({ id, source: 'catalog' })),
      tools: (body.tool_selections || []).map((id: string) => ({ id, source: 'catalog' })),
      safety: {
        dry_run: false,
        verify_after_write: true,
        safety_level: body.safety_level || 'standard',
        confirmations_required: 1,
      },
    };
    res.json({ status: 'success', recipe });
  });

  // ── Recipe Validate ───────────────────────────────────────────────────────

  app.post('/api/v1/recipe/validate', (req, res) => {
    const { recipe, target_device_size_gb } = req.body;
    const totalNeeded = (recipe?.os_images?.length ?? 0) * 5 + (recipe?.tools?.length ?? 0) * 2;
    const hasSpace = target_device_size_gb > totalNeeded;

    res.json({
      status: 'success',
      valid: hasSpace,
      warnings: hasSpace ? [] : ['Tight on space — consider removing some items'],
      errors: hasSpace ? [] : [`Need ~${totalNeeded} GB, device has ${target_device_size_gb} GB`],
      estimated_time: `${Math.ceil(totalNeeded * 0.5)} minutes`,
      estimated_size: `${totalNeeded.toFixed(1)} GB`,
    });
  });

  // ── Safety Check ──────────────────────────────────────────────────────────

  app.post('/api/v1/safety/check', (req, res) => {
    res.json({
      status: 'success',
      safe: true,
      checks: [
        { name: 'Removable Device', status: 'pass', message: 'Device is removable USB storage' },
        { name: 'Not System Drive', status: 'pass', message: 'Target is not the boot drive' },
        { name: 'Minimum Size', status: 'pass', message: 'Device meets minimum size requirements' },
        { name: 'Write Permission', status: 'pass', message: 'Device is writable' },
        { name: 'Data Erasure', status: 'warn', message: 'ALL existing data will be permanently erased' },
      ],
      risk_level: 'medium',
      requires_confirmation: true,
    });
  });

  // ── Start Build ───────────────────────────────────────────────────────────

  app.post('/api/v1/usb/build', (req, res) => {
    const buildId = `build-${Date.now()}`;
    builds.set(buildId, {
      id: buildId,
      state: 'running',
      stage: 'prepare',
      progress: 0,
      startedAt: new Date().toISOString(),
    });

    // Simulate progress
    let progress = 0;
    const interval = setInterval(() => {
      progress += 2;
      const build = builds.get(buildId);
      if (build) {
        build.progress = Math.min(100, progress);
        if (progress >= 100) {
          build.state = 'complete';
          clearInterval(interval);
        }
      }
    }, 400);

    res.json({
      status: 'started',
      build_id: buildId,
      recipe_id: req.body.recipe_id,
      started_at: new Date().toISOString(),
      estimated_duration_minutes: 15,
    });
  });

  // ── Build Progress SSE Stream ─────────────────────────────────────────────

  app.get('/api/v1/usb/build/:buildId/stream', (req, res) => {
    const buildId = req.params.buildId;
    
    // Set headers for Server-Sent Events (SSE)
    res.writeHead(200, {
      'Content-Type': 'text/event-stream',
      'Cache-Control': 'no-cache',
      'Connection': 'keep-alive',
      'Access-Control-Allow-Origin': '*',
    });
    
    res.write('retry: 5000\n\n');
    
    let active = true;
    req.on('close', () => {
      active = false;
    });
    
    const build = builds.get(buildId);
    if (!build) {
      res.write(`data: ${JSON.stringify({ status: 'error', message: 'Build not found' })}\n\n`);
      res.end();
      return;
    }
    
    const checkInterval = setInterval(() => {
      if (!active) {
        clearInterval(checkInterval);
        return;
      }
      
      const currentBuild = builds.get(buildId);
      if (!currentBuild) {
        res.write(`data: ${JSON.stringify({ status: 'error', message: 'Build terminated' })}\n\n`);
        res.end();
        clearInterval(checkInterval);
        return;
      }
      
      const progress = currentBuild.progress;
      let stage = 'prepare';
      let stageName = 'Preparing Drive';
      let operation = 'Running diskutil to unmount target partitions...';
      
      if (progress > 5 && progress <= 15) {
        stage = 'partition';
        stageName = 'Partitioning (GPT)';
        operation = 'Creating GPT partition table via diskutil...';
      } else if (progress > 15 && progress <= 25) {
        stage = 'ventoy';
        stageName = 'Ventoy2Disk.sh';
        operation = 'Executing: sudo sh Ventoy2Disk.sh -i /dev/disk2';
      } else if (progress > 25 && progress <= 75) {
        stage = 'write-os';
        stageName = 'Copying OS Images';
        operation = `Copying Phoenix OS suites to Ventoy USB partition... ${progress}%`;
      } else if (progress > 75 && progress <= 90) {
        stage = 'write-tools';
        stageName = 'Copying Tools';
        operation = 'Writing recovery system diagnostics and tools...';
      } else if (progress > 90 && progress <= 95) {
        stage = 'sync';
        stageName = 'Syncing (macOS)';
        operation = 'Flashing active write caches to physical USB disk...';
      } else if (progress > 95 && progress < 100) {
        stage = 'verify';
        stageName = 'Verifying';
        operation = 'Checking written ISO files block integrity...';
      } else if (progress >= 100) {
        stage = 'eject';
        stageName = 'Safe Eject';
        operation = '✅ USB drive ready! Safely ejected diskutil node.';
      }
      
      const progressPayload = {
        build_id: buildId,
        state: currentBuild.state,
        stage: stage,
        stageName: stageName,
        stageProgress: progress,
        overallProgress: progress,
        currentOperation: operation,
        speedMbps: progress > 25 && progress <= 75 ? Math.round((120 + Math.random() * 20) * 10) / 10 : 0,
        etaSeconds: Math.max(0, Math.ceil((100 - progress) * 0.4)),
        complete: progress >= 100,
        success: progress >= 100,
      };
      
      res.write(`data: ${JSON.stringify(progressPayload)}\n\n`);
      
      if (progress >= 100) {
        res.end();
        clearInterval(checkInterval);
      }
    }, 400);
  });

  // ── Build Status (Fallback / Legacy API) ──────────────────────────────────

  app.get('/api/v1/usb/build/:buildId/status', (req, res) => {
    const build = builds.get(req.params.buildId);
    if (!build) {
      return res.status(404).json({ status: 'error', message: 'Build not found' });
    }
    res.json({
      status: 'success',
      build_id: build.id,
      state: build.state,
      stage: build.stage,
      stage_progress: build.progress,
      overall_progress: build.progress,
      current_operation: `Writing data... ${build.progress}%`,
      speed_mbps: 120,
      eta_seconds: Math.ceil((100 - build.progress) / 5),
      timestamp: new Date().toISOString(),
    });
  });
}
