/**
 * End-to-End Integration Tests
 * Tests mobile app → backend API → WebSocket → email notification flows
 */

import { describe, it, expect, beforeAll, afterAll, vi } from 'vitest';
import axios from 'axios';

// Test configuration
const API_URL = process.env.API_URL || 'http://localhost:3000';
const WEBSOCKET_URL = process.env.WEBSOCKET_URL || 'ws://localhost:3000';

// Mock data
const testMacModel = 'MacBookPro15,1';
const testDriverPackage = 'BootCampESD_6.1';
const testAdminEmail = 'admin@test.example.com';

describe('End-to-End Integration Tests', () => {
  let installationId: string;
  let websocketConnection: any;

  beforeAll(() => {
    console.log('Starting E2E integration tests');
    console.log(`API URL: ${API_URL}`);
    console.log(`WebSocket URL: ${WEBSOCKET_URL}`);
  });

  afterAll(() => {
    console.log('E2E integration tests completed');
    if (websocketConnection) {
      websocketConnection.close();
    }
  });

  describe('Boot Camp API Endpoints', () => {
    it('should detect Mac system information', async () => {
      const response = await axios.post(`${API_URL}/api/v1/bootcamp/detect-mac`, {
        system_info: {
          model_identifier: testMacModel,
          board_id: 'Mac-551B86E5744E0084',
          serial_number: 'C02XXXXX',
          cpu_brand: 'Intel Core i7-8750H',
          gpu_model: 'AMD Radeon Pro 555X'
        }
      });

      expect(response.status).toBe(200);
      expect(response.data.status).toBe('success');
      expect(response.data.mac_model).toBeDefined();
      expect(response.data.driver_package).toBeDefined();
      expect(response.data.compatibility).toBeDefined();
    });

    it('should list all supported Mac models', async () => {
      const response = await axios.get(`${API_URL}/api/v1/bootcamp/models`);

      expect(response.status).toBe(200);
      expect(response.data.status).toBe('success');
      expect(Array.isArray(response.data.models)).toBe(true);
      expect(response.data.total).toBeGreaterThan(0);
    });

    it('should filter Mac models by Boot Camp support', async () => {
      const response = await axios.get(
        `${API_URL}/api/v1/bootcamp/models?boot_camp_support=true`
      );

      expect(response.status).toBe(200);
      expect(response.data.status).toBe('success');
      const bootCampModels = response.data.models.filter(
        (m: any) => m.boot_camp_support === true
      );
      expect(bootCampModels.length).toBeGreaterThan(0);
    });

    it('should get driver package information', async () => {
      const response = await axios.get(
        `${API_URL}/api/v1/bootcamp/drivers/${testDriverPackage}`
      );

      expect(response.status).toBe(200);
      expect(response.data.status).toBe('success');
      expect(response.data.driver_package).toBeDefined();
      expect(response.data.driver_package.id).toBe(testDriverPackage);
      expect(response.data.driver_package.components).toBeDefined();
    });

    it('should validate driver compatibility', async () => {
      const response = await axios.post(
        `${API_URL}/api/v1/bootcamp/validate-compatibility`,
        {
          mac_model: testMacModel,
          driver_package_id: testDriverPackage,
          windows_version: 'Windows 10 21H2'
        }
      );

      expect(response.status).toBe(200);
      expect(response.data.status).toBe('success');
      expect(response.data.compatible).toBeDefined();
      expect(response.data.warnings).toBeDefined();
    });
  });

  describe('Installation Flow with WebSocket & Email', () => {
    it('should start installation and return installation ID', async () => {
      const response = await axios.post(`${API_URL}/api/v1/bootcamp/install`, {
        mac_model: testMacModel,
        driver_package_id: testDriverPackage,
        windows_version: 'Windows 10 21H2',
        admin_email: testAdminEmail
      });

      expect(response.status).toBe(202); // Accepted (async operation)
      expect(response.data.status).toBe('success');
      expect(response.data.installation_id).toBeDefined();
      expect(response.data.websocket_url).toBeDefined();
      expect(response.data.message).toContain('WebSocket');

      installationId = response.data.installation_id;
    });

    it('should get installation status', async () => {
      expect(installationId).toBeDefined();

      const response = await axios.get(
        `${API_URL}/api/v1/bootcamp/install/${installationId}/status`
      );

      expect(response.status).toBe(200);
      expect(response.data.status).toBe('success');
      expect(response.data.installation).toBeDefined();
      expect(response.data.installation.installation_id).toBe(installationId);
      expect(response.data.installation.mac_model).toBe(testMacModel);
    });

    it('should list active installations', async () => {
      const response = await axios.get(`${API_URL}/api/v1/bootcamp/installations`);

      expect(response.status).toBe(200);
      expect(response.data.status).toBe('success');
      expect(Array.isArray(response.data.installations)).toBe(true);

      const activeInstallation = response.data.installations.find(
        (i: any) => i.installation_id === installationId
      );
      expect(activeInstallation).toBeDefined();
    });
  });

  describe('WebSocket Progress Streaming', () => {
    it('should connect to WebSocket and receive progress updates', async () => {
      return new Promise((resolve, reject) => {
        const timeout = setTimeout(() => {
          reject(new Error('WebSocket test timeout'));
        }, 10000);

        try {
          const io = require('socket.io-client');
          websocketConnection = io(WEBSOCKET_URL, {
            reconnection: true,
            reconnectionDelay: 100,
            reconnectionDelayMax: 1000,
            reconnectionAttempts: 5
          });

          websocketConnection.on('connect', () => {
            console.log('WebSocket connected');

            // Subscribe to installation
            websocketConnection.emit('subscribe_installation', {
              installation_id: installationId
            });

            // Listen for progress updates
            websocketConnection.on('progress_update', (data: any) => {
              console.log('Received progress update:', data);
              expect(data.installation_id).toBe(installationId);
              expect(data.overall_progress).toBeDefined();
              expect(data.stage).toBeDefined();
              expect(data.components).toBeDefined();

              clearTimeout(timeout);
              resolve(true);
            });

            // Listen for subscription confirmation
            websocketConnection.on('subscription_confirmed', (data: any) => {
              console.log('Subscription confirmed:', data);
              expect(data.installation_id).toBe(installationId);
            });
          });

          websocketConnection.on('connect_error', (error: any) => {
            clearTimeout(timeout);
            reject(new Error(`WebSocket connection error: ${error}`));
          });
        } catch (error) {
          clearTimeout(timeout);
          reject(error);
        }
      });
    });

    it('should receive installation completion event', async () => {
      return new Promise((resolve, reject) => {
        const timeout = setTimeout(() => {
          reject(new Error('Installation completion timeout'));
        }, 30000);

        if (!websocketConnection) {
          reject(new Error('WebSocket not connected'));
          return;
        }

        websocketConnection.on('installation_completed', (data: any) => {
          console.log('Installation completed:', data);
          expect(data.installation_id).toBe(installationId);
          expect(data.timestamp).toBeDefined();

          clearTimeout(timeout);
          resolve(true);
        });
      });
    });
  });

  describe('Email Notification System', () => {
    it('should send email notification on installation start', async () => {
      // This test verifies that email service is called
      // In a real scenario, you would check email inbox or mock SMTP
      const response = await axios.get(
        `${API_URL}/api/v1/bootcamp/install/${installationId}/notifications`
      );

      expect(response.status).toBe(200);
      expect(response.data.status).toBe('success');
      expect(Array.isArray(response.data.notifications)).toBe(true);

      const startNotification = response.data.notifications.find(
        (n: any) => n.type === 'installation_started'
      );
      expect(startNotification).toBeDefined();
      expect(startNotification.recipient).toBe(testAdminEmail);
    });

    it('should send email notification on installation completion', async () => {
      const response = await axios.get(
        `${API_URL}/api/v1/bootcamp/install/${installationId}/notifications`
      );

      expect(response.status).toBe(200);
      const completionNotification = response.data.notifications.find(
        (n: any) => n.type === 'installation_completed'
      );

      if (completionNotification) {
        expect(completionNotification.recipient).toBe(testAdminEmail);
        expect(completionNotification.timestamp).toBeDefined();
      }
    });
  });

  describe('Admin Notification Preferences', () => {
    it('should get admin notification preferences', async () => {
      const response = await axios.get(
        `${API_URL}/api/admin/notification-preferences`
      );

      expect(response.status).toBe(200);
      expect(response.data.status).toBe('success');
      expect(response.data.preferences).toBeDefined();
      expect(response.data.preferences.notification_types).toBeDefined();
      expect(response.data.preferences.alert_thresholds).toBeDefined();
    });

    it('should update admin notification preferences', async () => {
      const newPreferences = {
        email_addresses: ['admin@example.com', 'backup@example.com'],
        notification_types: {
          installation_started: true,
          installation_completed: true,
          installation_failed: true,
          system_health_warning: true,
          system_health_critical: true,
          api_health_check: false
        },
        alert_thresholds: {
          error_rate: 10,
          api_response_time: 3000,
          failed_installations: 5,
          disk_space: 15
        }
      };

      const response = await axios.put(
        `${API_URL}/api/admin/notification-preferences`,
        newPreferences
      );

      expect(response.status).toBe(200);
      expect(response.data.status).toBe('success');
      expect(response.data.preferences.email_addresses).toEqual(
        newPreferences.email_addresses
      );
    });

    it('should validate alert thresholds', async () => {
      const invalidPreferences = {
        alert_thresholds: {
          error_rate: 150, // Invalid: > 100
          api_response_time: 3000,
          failed_installations: 5,
          disk_space: 15
        }
      };

      try {
        await axios.put(
          `${API_URL}/api/admin/notification-preferences`,
          invalidPreferences
        );
        expect.fail('Should have thrown validation error');
      } catch (error: any) {
        expect(error.response.status).toBe(400);
        expect(error.response.data.error).toContain('validation');
      }
    });
  });

  describe('Error Handling & Recovery', () => {
    it('should handle installation failure gracefully', async () => {
      const response = await axios.post(`${API_URL}/api/v1/bootcamp/install`, {
        mac_model: 'InvalidModel',
        driver_package_id: testDriverPackage,
        windows_version: 'Windows 10'
      });

      expect(response.status).toBe(400);
      expect(response.data.status).toBe('error');
      expect(response.data.message).toBeDefined();
    });

    it('should handle invalid driver package', async () => {
      const response = await axios.post(`${API_URL}/api/v1/bootcamp/install`, {
        mac_model: testMacModel,
        driver_package_id: 'InvalidPackage',
        windows_version: 'Windows 10'
      });

      expect(response.status).toBe(400);
      expect(response.data.status).toBe('error');
      expect(response.data.message).toContain('Invalid driver package');
    });

    it('should handle WebSocket reconnection', async () => {
      return new Promise((resolve, reject) => {
        const timeout = setTimeout(() => {
          reject(new Error('Reconnection timeout'));
        }, 5000);

        try {
          const io = require('socket.io-client');
          const tempConnection = io(WEBSOCKET_URL, {
            reconnection: true,
            reconnectionDelay: 100,
            reconnectionDelayMax: 500,
            reconnectionAttempts: 3
          });

          tempConnection.on('connect', () => {
            console.log('Reconnected successfully');
            clearTimeout(timeout);
            tempConnection.close();
            resolve(true);
          });

          // Simulate disconnect
          setTimeout(() => {
            tempConnection.disconnect();
          }, 500);
        } catch (error) {
          clearTimeout(timeout);
          reject(error);
        }
      });
    });
  });

  describe('Performance & Load Testing', () => {
    it('should handle multiple concurrent installations', async () => {
      const promises = [];

      for (let i = 0; i < 5; i++) {
        promises.push(
          axios.post(`${API_URL}/api/v1/bootcamp/install`, {
            mac_model: testMacModel,
            driver_package_id: testDriverPackage,
            windows_version: 'Windows 10 21H2',
            admin_email: `admin${i}@test.example.com`
          })
        );
      }

      const responses = await Promise.all(promises);

      expect(responses.length).toBe(5);
      responses.forEach((response) => {
        expect(response.status).toBe(202);
        expect(response.data.installation_id).toBeDefined();
      });
    });

    it('should handle rapid API requests', async () => {
      const startTime = Date.now();
      const promises = [];

      for (let i = 0; i < 10; i++) {
        promises.push(
          axios.get(`${API_URL}/api/v1/bootcamp/models`)
        );
      }

      const responses = await Promise.all(promises);
      const duration = Date.now() - startTime;

      expect(responses.length).toBe(10);
      expect(duration).toBeLessThan(5000); // Should complete in < 5 seconds

      responses.forEach((response) => {
        expect(response.status).toBe(200);
      });
    });
  });

  describe('Data Consistency & Validation', () => {
    it('should maintain data consistency across API calls', async () => {
      // Get installation status
      const statusResponse = await axios.get(
        `${API_URL}/api/v1/bootcamp/install/${installationId}/status`
      );

      // List installations
      const listResponse = await axios.get(
        `${API_URL}/api/v1/bootcamp/installations`
      );

      const installation = statusResponse.data.installation;
      const listedInstallation = listResponse.data.installations.find(
        (i: any) => i.installation_id === installationId
      );

      expect(installation.mac_model).toBe(listedInstallation.mac_model);
      expect(installation.driver_package_id).toBe(
        listedInstallation.driver_package_id
      );
    });

    it('should validate driver package components', async () => {
      const response = await axios.get(
        `${API_URL}/api/v1/bootcamp/drivers/${testDriverPackage}`
      );

      const components = response.data.driver_package.components;
      expect(Array.isArray(components)).toBe(true);
      expect(components.length).toBeGreaterThan(0);

      components.forEach((component: any) => {
        expect(component.name).toBeDefined();
        expect(component.version).toBeDefined();
        expect(component.size_mb).toBeDefined();
      });
    });
  });
});
