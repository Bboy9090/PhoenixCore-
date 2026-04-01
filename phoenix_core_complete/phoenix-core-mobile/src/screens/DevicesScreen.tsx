/**
 * Phoenix Core - Devices Screen
 * USB device detection, listing, and selection for builds
 */

import React, { useEffect, useState } from 'react';
import {
  View,
  Text,
  ScrollView,
  StyleSheet,
  TouchableOpacity,
  ActivityIndicator,
  RefreshControl,
  Alert,
} from 'react-native';
import { Colors, Spacing, Typography, BorderRadius, Shadows, getRiskColor } from '../utils/theme';
import api, { USBDevice, DeviceListResponse } from '../services/api';

export default function DevicesScreen() {
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [devices, setDevices] = useState<USBDevice[]>([]);
  const [selectedDevice, setSelectedDevice] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const loadDevices = async () => {
    try {
      setError(null);
      const response = await api.listDevices();
      setDevices(response.devices);
      if (response.devices.length === 0) {
        setError('No USB devices found. Connect a USB drive to get started.');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to scan devices');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    loadDevices();
  }, []);

  const onRefresh = () => {
    setRefreshing(true);
    loadDevices();
  };

  const handleSelectDevice = (device: USBDevice) => {
    if (device.is_system_disk) {
      Alert.alert('⚠️ System Disk', 'Cannot select system disk for USB creation');
      return;
    }
    setSelectedDevice(device.id);
  };

  if (loading) {
    return (
      <View style={styles.container}>
        <ActivityIndicator size="large" color={Colors.accent.primary} />
      </View>
    );
  }

  return (
    <ScrollView
      style={styles.container}
      refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} />}
    >
      {/* Header */}
      <View style={styles.header}>
        <Text style={styles.headerTitle}>USB Devices</Text>
        <Text style={styles.headerSubtitle}>
          {devices.length} device{devices.length !== 1 ? 's' : ''} found
        </Text>
      </View>

      {/* Device List */}
      {devices.length > 0 ? (
        <View style={styles.deviceList}>
          {devices.map((device) => (
            <DeviceCard
              key={device.id}
              device={device}
              isSelected={selectedDevice === device.id}
              onSelect={() => handleSelectDevice(device)}
            />
          ))}
        </View>
      ) : (
        <View style={styles.emptyState}>
          <Text style={styles.emptyStateIcon}>💾</Text>
          <Text style={styles.emptyStateTitle}>No Devices Found</Text>
          <Text style={styles.emptyStateText}>
            Connect a USB drive or storage device to get started
          </Text>
          <TouchableOpacity style={styles.refreshButton} onPress={onRefresh}>
            <Text style={styles.refreshButtonText}>🔄 Refresh</Text>
          </TouchableOpacity>
        </View>
      )}

      {/* Error Message */}
      {error && (
        <View style={styles.errorCard}>
          <Text style={styles.errorText}>⚠️ {error}</Text>
        </View>
      )}

      {/* Selected Device Info */}
      {selectedDevice && (
        <View style={styles.selectedDeviceSection}>
          <Text style={styles.selectedDeviceTitle}>Selected Device</Text>
          {devices
            .filter((d) => d.id === selectedDevice)
            .map((device) => (
              <View key={device.id} style={styles.selectedDeviceCard}>
                <Text style={styles.selectedDeviceInfo}>
                  {device.friendly_name || device.name}
                </Text>
                <Text style={styles.selectedDeviceInfo}>
                  {device.size_human} • {device.filesystem || 'Unknown FS'}
                </Text>
                <TouchableOpacity style={styles.proceedButton}>
                  <Text style={styles.proceedButtonText}>Next: Choose Recipe →</Text>
                </TouchableOpacity>
              </View>
            ))}
        </View>
      )}

      <View style={{ height: Spacing.xl }} />
    </ScrollView>
  );
}

interface DeviceCardProps {
  device: USBDevice;
  isSelected: boolean;
  onSelect: () => void;
}

function DeviceCard({ device, isSelected, onSelect }: DeviceCardProps) {
  const riskColor = getRiskColor(device.risk_level);

  return (
    <TouchableOpacity
      style={[
        styles.deviceCard,
        isSelected && styles.deviceCardSelected,
        device.is_system_disk && styles.deviceCardDisabled,
      ]}
      onPress={onSelect}
      disabled={device.is_system_disk}
    >
      {/* Device Icon & Name */}
      <View style={styles.deviceHeader}>
        <Text style={styles.deviceIcon}>
          {device.is_system_disk ? '🖥️' : '💾'}
        </Text>
        <View style={styles.deviceInfo}>
          <Text style={styles.deviceName}>
            {device.friendly_name || device.name}
            {device.is_system_disk && ' (System)'}
          </Text>
          <Text style={styles.devicePath}>{device.path}</Text>
        </View>
        {isSelected && <Text style={styles.checkmark}>✓</Text>}
      </View>

      {/* Device Details */}
      <View style={styles.deviceDetails}>
        <DetailBadge label="Size" value={device.size_human} />
        <DetailBadge label="FS" value={device.filesystem || 'Unknown'} />
        <DetailBadge
          label="Risk"
          value={device.risk_level.toUpperCase()}
          color={riskColor}
        />
        <DetailBadge
          label="Status"
          value={device.health_status}
          color={device.health_status === 'healthy' ? Colors.status.success : Colors.status.warning}
        />
      </View>

      {/* Partitions */}
      {device.partitions.length > 0 && (
        <View style={styles.partitionsList}>
          <Text style={styles.partitionsLabel}>Partitions ({device.partitions.length})</Text>
          {device.partitions.map((part, idx) => (
            <Text key={idx} style={styles.partitionItem}>
              • {part.id}: {part.size_human} ({part.filesystem || 'unknown'})
            </Text>
          ))}
        </View>
      )}

      {/* Warning for System Disk */}
      {device.is_system_disk && (
        <View style={styles.warningBanner}>
          <Text style={styles.warningText}>⚠️ This is your system disk - cannot be selected</Text>
        </View>
      )}
    </TouchableOpacity>
  );
}

interface DetailBadgeProps {
  label: string;
  value: string;
  color?: string;
}

function DetailBadge({ label, value, color }: DetailBadgeProps) {
  return (
    <View style={styles.detailBadge}>
      <Text style={styles.detailLabel}>{label}</Text>
      <Text style={[styles.detailValue, color && { color }]}>
        {value}
      </Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: Colors.bg.primary,
  },
  header: {
    padding: Spacing.xl,
    paddingBottom: Spacing.base,
  },
  headerTitle: {
    fontSize: Typography.size['2xl'],
    fontWeight: Typography.weight.bold,
    color: Colors.text.primary,
    marginBottom: Spacing.sm,
  },
  headerSubtitle: {
    fontSize: Typography.size.md,
    color: Colors.text.tertiary,
  },
  deviceList: {
    paddingHorizontal: Spacing.base,
    gap: Spacing.md,
  },
  deviceCard: {
    backgroundColor: Colors.bg.card,
    borderRadius: BorderRadius.lg,
    borderWidth: 2,
    borderColor: Colors.border.default,
    padding: Spacing.base,
    marginBottom: Spacing.md,
    ...Shadows.md,
  },
  deviceCardSelected: {
    borderColor: Colors.accent.primary,
    backgroundColor: Colors.bg.elevated,
  },
  deviceCardDisabled: {
    opacity: 0.5,
  },
  deviceHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: Spacing.md,
    gap: Spacing.md,
  },
  deviceIcon: {
    fontSize: Typography.size['2xl'],
  },
  deviceInfo: {
    flex: 1,
  },
  deviceName: {
    fontSize: Typography.size.md,
    fontWeight: Typography.weight.semibold,
    color: Colors.text.primary,
    marginBottom: Spacing.xs,
  },
  devicePath: {
    fontSize: Typography.size.xs,
    color: Colors.text.tertiary,
    fontFamily: 'Courier',
  },
  checkmark: {
    fontSize: Typography.size.xl,
    color: Colors.accent.primary,
    fontWeight: Typography.weight.bold,
  },
  deviceDetails: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: Spacing.sm,
    marginBottom: Spacing.md,
  },
  detailBadge: {
    backgroundColor: Colors.bg.tertiary,
    paddingHorizontal: Spacing.sm,
    paddingVertical: Spacing.xs,
    borderRadius: BorderRadius.sm,
    borderWidth: 1,
    borderColor: Colors.border.default,
  },
  detailLabel: {
    fontSize: Typography.size.xs,
    color: Colors.text.tertiary,
  },
  detailValue: {
    fontSize: Typography.size.xs,
    fontWeight: Typography.weight.semibold,
    color: Colors.accent.primary,
  },
  partitionsList: {
    marginBottom: Spacing.md,
    paddingTop: Spacing.md,
    borderTopWidth: 1,
    borderTopColor: Colors.border.default,
  },
  partitionsLabel: {
    fontSize: Typography.size.sm,
    fontWeight: Typography.weight.semibold,
    color: Colors.text.secondary,
    marginBottom: Spacing.sm,
  },
  partitionItem: {
    fontSize: Typography.size.xs,
    color: Colors.text.tertiary,
    marginBottom: Spacing.xs,
    fontFamily: 'Courier',
  },
  warningBanner: {
    backgroundColor: Colors.status.errorBg,
    borderRadius: BorderRadius.md,
    padding: Spacing.sm,
    borderWidth: 1,
    borderColor: Colors.status.error,
  },
  warningText: {
    color: Colors.status.error,
    fontSize: Typography.size.xs,
    fontWeight: Typography.weight.semibold,
  },
  emptyState: {
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: Spacing['3xl'],
    paddingHorizontal: Spacing.base,
  },
  emptyStateIcon: {
    fontSize: 64,
    marginBottom: Spacing.lg,
  },
  emptyStateTitle: {
    fontSize: Typography.size.lg,
    fontWeight: Typography.weight.bold,
    color: Colors.text.primary,
    marginBottom: Spacing.sm,
    textAlign: 'center',
  },
  emptyStateText: {
    fontSize: Typography.size.md,
    color: Colors.text.tertiary,
    textAlign: 'center',
    marginBottom: Spacing.lg,
  },
  refreshButton: {
    paddingHorizontal: Spacing.lg,
    paddingVertical: Spacing.md,
    backgroundColor: Colors.accent.primary,
    borderRadius: BorderRadius.md,
  },
  refreshButtonText: {
    color: Colors.bg.primary,
    fontWeight: Typography.weight.bold,
    fontSize: Typography.size.md,
  },
  errorCard: {
    margin: Spacing.base,
    padding: Spacing.base,
    backgroundColor: Colors.status.errorBg,
    borderRadius: BorderRadius.md,
    borderWidth: 1,
    borderColor: Colors.status.error,
  },
  errorText: {
    color: Colors.status.error,
    fontSize: Typography.size.sm,
    fontWeight: Typography.weight.semibold,
  },
  selectedDeviceSection: {
    margin: Spacing.base,
    padding: Spacing.base,
    backgroundColor: Colors.accent.glow,
    borderRadius: BorderRadius.lg,
    borderWidth: 2,
    borderColor: Colors.accent.primary,
  },
  selectedDeviceTitle: {
    fontSize: Typography.size.md,
    fontWeight: Typography.weight.bold,
    color: Colors.accent.primary,
    marginBottom: Spacing.md,
  },
  selectedDeviceCard: {
    backgroundColor: Colors.bg.card,
    padding: Spacing.base,
    borderRadius: BorderRadius.md,
    gap: Spacing.sm,
  },
  selectedDeviceInfo: {
    fontSize: Typography.size.md,
    color: Colors.text.primary,
    fontWeight: Typography.weight.semibold,
  },
  proceedButton: {
    marginTop: Spacing.md,
    paddingVertical: Spacing.md,
    backgroundColor: Colors.accent.primary,
    borderRadius: BorderRadius.md,
  },
  proceedButtonText: {
    color: Colors.bg.primary,
    fontWeight: Typography.weight.bold,
    fontSize: Typography.size.md,
    textAlign: 'center',
  },
});
