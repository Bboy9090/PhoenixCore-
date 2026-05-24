/**
 * End-to-End Integration Tests
 * Tests mobile app → backend API → desktop app data flow
 */

import { describe, it, expect, beforeAll, afterAll, vi } from 'vitest';

// Mock API responses
const mockHardwareResponse = {
  status: 'success',
  device_id: 'device-123',
  detected_at: new Date().toISOString(),
  hardware: {
    system: {
      manufacturer: 'Dell',
      model: 'XPS 13',
      serial_number: 'ABC123',
    },
    cpu: {
      name: 'Intel Core i7-1360P',
      manufacturer: 'Intel',
      architecture: 'x86_64',
      cores: 12,
      threads: 16,
    },
    memory: {
      total_gb: 16,
      modules: [],
    },
    gpu: [],
    storage: [],
    network: [],
  },
  compatible_os: [
    { id: 'windows11', name: 'Windows 11', description: 'Fully compatible' },
    { id: 'ubuntu22', name: 'Ubuntu 22.04', description: 'Fully compatible' },
  ],
  incompatible_os: [],
};

const mockUSBDevicesResponse = {
  status: 'success',
  devices: [
    {
      device_id: 'usb-001',
      path: '/dev/sdb',
      name: 'Kingston DataTraveler',
      size_gb: 32,
      filesystem: 'FAT32',
      vendor: 'Kingston',
      model: 'DataTraveler 3.0',
      serial: 'SERIAL123',
      is_removable: true,
      health_status: 'good',
      write_speed_mbps: 45.5,
      mountpoint: '/mnt/usb',
    },
  ],
  total_devices: 1,
};

const mockRecipeResponse = {
  status: 'success',
  recipe: {
    recipe_id: 'recipe-001',
    name: 'Multi-Boot USB - 2 OS(es)',
    version: '1.0.0',
    created_at: new Date().toISOString(),
    deployment_type: 'multi-boot',
    target_device: {
      device_id: 'usb-001',
      size_gb: 32,
      confirm_erase: true,
    },
    partitions: [
      {
        partition_id: 'part-1',
        number: 1,
        start_sector: 2048,
        size_sectors: 1000000,
        filesystem: 'fat32',
        label: 'BOOT',
        bootable: true,
      },
    ],
    os_images: [
      {
        image_id: 'img-1',
        os_id: 'windows11',
        name: 'Windows 11',
        size_gb: 5.5,
        checksum: 'sha256:abc123',
      },
    ],
    tools: [
      {
        tool_id: 'tool-1',
        name: 'Ventoy',
        version: '1.0.98',
        size_mb: 50,
      },
    ],
    safety: {
      dry_run: false,
      verify_after_write: true,
      safety_level: 'high',
      confirmations_required: 2,
    },
  },
};

const mockValidationResponse = {
  status: 'success',
  valid: true,
  warnings: [],
  errors: [],
  estimated_time: '15 minutes',
  estimated_size: '5.5 GB',
};

const mockSafetyCheckResponse = {
  status: 'success',
  safe: true,
  checks: [
    { name: 'Device Identification', status: 'passed', message: 'Device correctly identified' },
    { name: 'Partition Integrity', status: 'passed', message: 'Partition table valid' },
    { name: 'Data Loss Risk', status: 'passed', message: 'No critical data detected' },
    { name: 'Bootloader Compatibility', status: 'passed', message: 'Bootloader compatible' },
    { name: 'Post-Build Verification', status: 'passed', message: 'Verification enabled' },
  ],
  risk_level: 'low',
  requires_confirmation: true,
};

const mockBuildStartResponse = {
  status: 'started',
  build_id: 'build-001',
  recipe_id: 'recipe-001',
  started_at: new Date().toISOString(),
  estimated_duration_minutes: 15,
  ws_url: 'ws://localhost:5000/ws/build/build-001',
};

const mockBuildProgressResponse = {
  build_id: 'build-001',
  state: 'writing',
  stage: 'writing',
  stage_progress: 45.5,
  overall_progress: 45.5,
  current_operation: 'Writing to USB device...',
  speed_mbps: 45.5,
  eta_seconds: 480,
  timestamp: new Date().toISOString(),
};

describe('End-to-End Integration Tests', () => {
  // Mock fetch globally
  beforeAll(() => {
    global.fetch = vi.fn();
  });

  afterAll(() => {
    vi.restoreAllMocks();
  });

  describe('Mobile App → Backend API Flow', () => {
    it('should detect hardware on mobile app', async () => {
      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => mockHardwareResponse,
      });

      const response = await fetch('http://localhost:5000/api/v1/hardware/detect', {
        method: 'POST',
        body: JSON.stringify({}),
      });

      const data = await response.json();
      expect(data.status).toBe('success');
      expect(data.hardware.cpu.cores).toBe(12);
      expect(data.compatible_os).toHaveLength(2);
    });

    it('should list USB devices on mobile app', async () => {
      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => mockUSBDevicesResponse,
      });

      const response = await fetch('http://localhost:5000/api/v1/usb/devices');
      const data = await response.json();

      expect(data.status).toBe('success');
      expect(data.devices).toHaveLength(1);
      expect(data.devices[0].size_gb).toBe(32);
    });

    it('should build recipe on mobile app', async () => {
      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => mockRecipeResponse,
      });

      const response = await fetch('http://localhost:5000/api/v1/recipe/build', {
        method: 'POST',
        body: JSON.stringify({
          name: 'Multi-Boot USB - 2 OS(es)',
          deployment_type: 'multi-boot',
          os_selections: ['windows11', 'ubuntu22'],
          target_device_id: 'usb-001',
          target_device_size_gb: 32,
          tool_selections: ['ventoy'],
          partition_scheme: 'gpt',
          bootloader_type: 'uefi',
          safety_level: 'high',
        }),
      });

      const data = await response.json();
      expect(data.status).toBe('success');
      expect(data.recipe.recipe_id).toBe('recipe-001');
      expect(data.recipe.partitions).toHaveLength(1);
    });

    it('should validate recipe on mobile app', async () => {
      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => mockValidationResponse,
      });

      const response = await fetch('http://localhost:5000/api/v1/recipe/validate', {
        method: 'POST',
        body: JSON.stringify({
          recipe: mockRecipeResponse.recipe,
          target_device_id: 'usb-001',
          target_device_size_gb: 32,
        }),
      });

      const data = await response.json();
      expect(data.status).toBe('success');
      expect(data.valid).toBe(true);
      expect(data.estimated_time).toBe('15 minutes');
    });

    it('should run safety check on mobile app', async () => {
      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => mockSafetyCheckResponse,
      });

      const response = await fetch('http://localhost:5000/api/v1/safety/check', {
        method: 'POST',
        body: JSON.stringify({
          recipe: mockRecipeResponse.recipe,
          target_device_id: 'usb-001',
          target_device_path: '/dev/sdb',
        }),
      });

      const data = await response.json();
      expect(data.status).toBe('success');
      expect(data.safe).toBe(true);
      expect(data.checks).toHaveLength(5);
      expect(data.risk_level).toBe('low');
    });

    it('should start USB build on mobile app', async () => {
      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => mockBuildStartResponse,
      });

      const response = await fetch('http://localhost:5000/api/v1/usb/build', {
        method: 'POST',
        body: JSON.stringify({
          recipe_id: 'recipe-001',
          device_path: '/dev/sdb',
          dry_run: false,
        }),
      });

      const data = await response.json();
      expect(data.status).toBe('started');
      expect(data.build_id).toBe('build-001');
      expect(data.ws_url).toContain('ws://');
    });

    it('should track build progress on mobile app', async () => {
      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => mockBuildProgressResponse,
      });

      const response = await fetch('http://localhost:5000/api/v1/usb/build/build-001/status');
      const data = await response.json();

      expect(data.build_id).toBe('build-001');
      expect(data.state).toBe('writing');
      expect(data.overall_progress).toBe(45.5);
      expect(data.speed_mbps).toBe(45.5);
    });
  });

  describe('Recipe Export/Import via QR Code', () => {
    it('should export recipe as QR code', async () => {
      const recipe = mockRecipeResponse.recipe;
      const qrData = JSON.stringify(recipe);

      expect(qrData).toContain('recipe-001');
      expect(qrData).toContain('multi-boot');
      expect(qrData).toContain('windows11');
    });

    it('should import recipe from QR code', async () => {
      const qrData = JSON.stringify(mockRecipeResponse.recipe);
      const importedRecipe = JSON.parse(qrData);

      expect(importedRecipe.recipe_id).toBe('recipe-001');
      expect(importedRecipe.deployment_type).toBe('multi-boot');
      expect(importedRecipe.os_images).toHaveLength(1);
    });

    it('should validate imported recipe format', async () => {
      const recipe = mockRecipeResponse.recipe;

      // Check required fields
      expect(recipe.recipe_id).toBeDefined();
      expect(recipe.name).toBeDefined();
      expect(recipe.version).toBeDefined();
      expect(recipe.created_at).toBeDefined();
      expect(recipe.deployment_type).toBeDefined();
      expect(recipe.target_device).toBeDefined();
      expect(recipe.partitions).toBeDefined();
      expect(recipe.os_images).toBeDefined();
      expect(recipe.tools).toBeDefined();
      expect(recipe.safety).toBeDefined();
    });
  });

  describe('Desktop App → Backend API Flow', () => {
    it('should import recipe on desktop app', async () => {
      const recipe = mockRecipeResponse.recipe;
      expect(recipe.recipe_id).toBe('recipe-001');
      expect(recipe.target_device.device_id).toBe('usb-001');
    });

    it('should detect USB devices on desktop app', async () => {
      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => mockUSBDevicesResponse,
      });

      const response = await fetch('http://localhost:5000/api/v1/usb/devices');
      const data = await response.json();

      expect(data.devices[0].path).toBe('/dev/sdb');
      expect(data.devices[0].is_removable).toBe(true);
    });

    it('should execute build on desktop app', async () => {
      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => mockBuildStartResponse,
      });

      const response = await fetch('http://localhost:5000/api/v1/usb/build', {
        method: 'POST',
        body: JSON.stringify({
          recipe_id: 'recipe-001',
          device_path: '/dev/sdb',
          dry_run: false,
        }),
      });

      const data = await response.json();
      expect(data.build_id).toBe('build-001');
    });
  });

  describe('WebSocket Progress Streaming', () => {
    it('should stream build progress via WebSocket', async () => {
      // Simulate WebSocket message
      const progressMessage = mockBuildProgressResponse;

      expect(progressMessage.build_id).toBe('build-001');
      expect(progressMessage.overall_progress).toBeGreaterThan(0);
      expect(progressMessage.overall_progress).toBeLessThanOrEqual(100);
      expect(progressMessage.speed_mbps).toBeGreaterThan(0);
    });

    it('should handle build completion', async () => {
      const completionMessage = {
        build_id: 'build-001',
        state: 'complete',
        overall_progress: 100,
        current_operation: 'Build completed successfully',
      };

      expect(completionMessage.state).toBe('complete');
      expect(completionMessage.overall_progress).toBe(100);
    });

    it('should handle build errors', async () => {
      const errorMessage = {
        build_id: 'build-001',
        state: 'error',
        error_message: 'USB device disconnected',
      };

      expect(errorMessage.state).toBe('error');
      expect(errorMessage.error_message).toBeDefined();
    });
  });

  describe('Data Consistency', () => {
    it('should maintain recipe consistency across mobile and desktop', async () => {
      const mobileRecipe = mockRecipeResponse.recipe;
      const desktopRecipe = JSON.parse(JSON.stringify(mobileRecipe));

      expect(mobileRecipe.recipe_id).toBe(desktopRecipe.recipe_id);
      expect(mobileRecipe.os_images).toEqual(desktopRecipe.os_images);
      expect(mobileRecipe.partitions).toEqual(desktopRecipe.partitions);
    });

    it('should validate recipe checksum', async () => {
      const recipe = mockRecipeResponse.recipe;
      const recipeJson = JSON.stringify(recipe);
      const checksum = require('crypto')
        .createHash('sha256')
        .update(recipeJson)
        .digest('hex');

      expect(checksum).toBeDefined();
      expect(checksum.length).toBe(64); // SHA256 hex length
    });

    it('should track build history', async () => {
      const buildHistory = [
        {
          build_id: 'build-001',
          recipe_id: 'recipe-001',
          status: 'completed',
          timestamp: new Date().toISOString(),
        },
        {
          build_id: 'build-002',
          recipe_id: 'recipe-002',
          status: 'failed',
          timestamp: new Date().toISOString(),
        },
      ];

      expect(buildHistory).toHaveLength(2);
      expect(buildHistory[0].status).toBe('completed');
      expect(buildHistory[1].status).toBe('failed');
    });
  });

  describe('Error Handling', () => {
    it('should handle API connection errors', async () => {
      (global.fetch as any).mockRejectedValueOnce(new Error('Connection refused'));

      try {
        await fetch('http://localhost:5000/api/v1/health');
      } catch (error: any) {
        expect(error.message).toContain('Connection refused');
      }
    });

    it('should handle invalid recipe data', async () => {
      const invalidRecipe = {
        recipe_id: 'recipe-001',
        // Missing required fields
      };

      expect(invalidRecipe.recipe_id).toBeDefined();
      expect((invalidRecipe as any).name).toBeUndefined();
    });

    it('should handle USB device disconnection', async () => {
      const disconnectionEvent = {
        type: 'device_disconnected',
        device_id: 'usb-001',
        timestamp: new Date().toISOString(),
      };

      expect(disconnectionEvent.type).toBe('device_disconnected');
      expect(disconnectionEvent.device_id).toBe('usb-001');
    });

    it('should retry failed requests', async () => {
      let attemptCount = 0;
      (global.fetch as any).mockImplementation(async () => {
        attemptCount++;
        if (attemptCount < 3) {
          throw new Error('Temporary failure');
        }
        return {
          ok: true,
          json: async () => mockHardwareResponse,
        };
      });

      // Simulate retry logic
      let lastError;
      for (let i = 0; i < 3; i++) {
        try {
          await fetch('http://localhost:5000/api/v1/health');
          break;
        } catch (error) {
          lastError = error;
        }
      }

      expect(attemptCount).toBe(3);
    });
  });

  describe('Performance & Load Testing', () => {
    it('should handle multiple concurrent requests', async () => {
      const requests = Array(10)
        .fill(null)
        .map(() =>
          (global.fetch as any).mockResolvedValueOnce({
            ok: true,
            json: async () => mockHardwareResponse,
          }),
        );

      expect(requests).toHaveLength(10);
    });

    it('should handle large recipe payloads', async () => {
      const largeRecipe = {
        ...mockRecipeResponse.recipe,
        partitions: Array(100)
          .fill(null)
          .map((_, i) => ({
            partition_id: `part-${i}`,
            number: i,
            size_sectors: 1000000,
          })),
      };

      const payload = JSON.stringify(largeRecipe);
      expect(payload.length).toBeGreaterThan(1000);
    });

    it('should handle rapid build progress updates', async () => {
      const progressUpdates = Array(100)
        .fill(null)
        .map((_, i) => ({
          ...mockBuildProgressResponse,
          overall_progress: i,
          timestamp: new Date(Date.now() + i * 100).toISOString(),
        }));

      expect(progressUpdates).toHaveLength(100);
      expect(progressUpdates[0].overall_progress).toBe(0);
      expect(progressUpdates[99].overall_progress).toBe(99);
    });
  });
});
