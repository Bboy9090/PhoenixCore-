/**
 * Phoenix Core - Dashboard Screen
 * Real-time system monitoring and quick actions
 */

import React, { useEffect, useState } from 'react';
import {
  View,
  Text,
  ScrollView,
  StyleSheet,
  RefreshControl,
  TouchableOpacity,
  ActivityIndicator,
  Dimensions,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { Colors, Spacing, Typography, BorderRadius, Shadows } from '../utils/theme';
import api, { SystemMetrics, HealthStatus, HardwareProfile } from '../services/api';

const { width } = Dimensions.get('window');

export default function DashboardScreen() {
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [metrics, setMetrics] = useState<SystemMetrics | null>(null);
  const [hardware, setHardware] = useState<HardwareProfile | null>(null);
  const [error, setError] = useState<string | null>(null);

  const loadData = async () => {
    try {
      setError(null);
      const [healthRes, metricsRes, hardwareRes] = await Promise.all([
        api.getHealth(),
        api.getSystemMetrics(),
        api.getHardwareProfile(),
      ]);
      setHealth(healthRes);
      setMetrics(metricsRes);
      setHardware(hardwareRes);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load data');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 5000); // Update every 5 seconds
    return () => clearInterval(interval);
  }, []);

  const onRefresh = () => {
    setRefreshing(true);
    loadData();
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
      <LinearGradient
        colors={[Colors.accent.primary, Colors.accent.secondary]}
        start={{ x: 0, y: 0 }}
        end={{ x: 1, y: 1 }}
        style={styles.header}
      >
        <Text style={styles.headerTitle}>Phoenix Core</Text>
        <Text style={styles.headerSubtitle}>System Status</Text>
      </LinearGradient>

      {/* Status Indicator */}
      {health && (
        <View style={styles.statusCard}>
          <View style={styles.statusBadge}>
            <View
              style={[
                styles.statusDot,
                { backgroundColor: health.status === 'healthy' ? Colors.status.success : Colors.status.warning },
              ]}
            />
            <Text style={styles.statusText}>{health.status.toUpperCase()}</Text>
          </View>
          <Text style={styles.versionText}>v{health.version}</Text>
        </View>
      )}

      {/* System Info */}
      {hardware && (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>System Information</Text>
          <View style={styles.infoGrid}>
            <InfoCard label="Device" value={hardware.model || 'Unknown'} />
            <InfoCard label="CPU" value={`${hardware.cpu.cores_logical} cores`} />
            <InfoCard label="RAM" value={hardware.memory.total_human} />
            <InfoCard label="Platform" value={hardware.platform.toUpperCase()} />
          </View>
        </View>
      )}

      {/* Real-time Metrics */}
      {metrics && (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Live Metrics</Text>

          {/* CPU */}
          <MetricCard
            title="CPU Usage"
            value={metrics.cpu_percent}
            unit="%"
            max={100}
            color={Colors.accent.primary}
          />

          {/* Memory */}
          <MetricCard
            title="Memory Usage"
            value={metrics.memory_percent}
            unit="%"
            max={100}
            color={Colors.status.warning}
          />

          {/* Disk */}
          <MetricCard
            title="Disk Usage"
            value={metrics.disk_usage_percent}
            unit="%"
            max={100}
            color={Colors.status.info}
          />

          {/* Temperature */}
          {metrics.temperature && (
            <MetricCard
              title="Temperature"
              value={metrics.temperature}
              unit="°C"
              max={100}
              color={metrics.temperature > 80 ? Colors.status.error : Colors.accent.primary}
            />
          )}
        </View>
      )}

      {/* Quick Actions */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Quick Actions</Text>
        <TouchableOpacity style={styles.actionButton}>
          <Text style={styles.actionButtonText}>🔍 Scan Devices</Text>
        </TouchableOpacity>
        <TouchableOpacity style={styles.actionButton}>
          <Text style={styles.actionButtonText}>⚙️ System Info</Text>
        </TouchableOpacity>
        <TouchableOpacity style={styles.actionButton}>
          <Text style={styles.actionButtonText}>🔧 Diagnostics</Text>
        </TouchableOpacity>
      </View>

      {/* Error Message */}
      {error && (
        <View style={styles.errorCard}>
          <Text style={styles.errorText}>⚠️ {error}</Text>
        </View>
      )}

      <View style={{ height: Spacing.xl }} />
    </ScrollView>
  );
}

interface InfoCardProps {
  label: string;
  value: string;
}

function InfoCard({ label, value }: InfoCardProps) {
  return (
    <View style={styles.infoCard}>
      <Text style={styles.infoLabel}>{label}</Text>
      <Text style={styles.infoValue}>{value}</Text>
    </View>
  );
}

interface MetricCardProps {
  title: string;
  value: number;
  unit: string;
  max: number;
  color: string;
}

function MetricCard({ title, value, unit, max, color }: MetricCardProps) {
  const percentage = (value / max) * 100;

  return (
    <View style={styles.metricCard}>
      <View style={styles.metricHeader}>
        <Text style={styles.metricTitle}>{title}</Text>
        <Text style={styles.metricValue}>
          {value.toFixed(1)}{unit}
        </Text>
      </View>
      <View style={styles.metricBar}>
        <View
          style={[
            styles.metricBarFill,
            {
              width: `${Math.min(percentage, 100)}%`,
              backgroundColor: color,
            },
          ]}
        />
      </View>
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
    paddingTop: Spacing['2xl'],
  },
  headerTitle: {
    fontSize: Typography.size['2xl'],
    fontWeight: Typography.weight.bold,
    color: Colors.text.primary,
    marginBottom: Spacing.sm,
  },
  headerSubtitle: {
    fontSize: Typography.size.md,
    color: 'rgba(255, 255, 255, 0.8)',
  },
  statusCard: {
    margin: Spacing.base,
    padding: Spacing.base,
    backgroundColor: Colors.bg.card,
    borderRadius: BorderRadius.lg,
    borderWidth: 1,
    borderColor: Colors.border.accent,
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    ...Shadows.md,
  },
  statusBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: Spacing.sm,
  },
  statusDot: {
    width: 12,
    height: 12,
    borderRadius: BorderRadius.full,
  },
  statusText: {
    color: Colors.text.primary,
    fontWeight: Typography.weight.semibold,
    fontSize: Typography.size.sm,
  },
  versionText: {
    color: Colors.text.tertiary,
    fontSize: Typography.size.xs,
  },
  section: {
    margin: Spacing.base,
    gap: Spacing.md,
  },
  sectionTitle: {
    fontSize: Typography.size.lg,
    fontWeight: Typography.weight.bold,
    color: Colors.text.primary,
    marginLeft: Spacing.sm,
  },
  infoGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: Spacing.md,
  },
  infoCard: {
    flex: 1,
    minWidth: '45%',
    padding: Spacing.base,
    backgroundColor: Colors.bg.card,
    borderRadius: BorderRadius.md,
    borderWidth: 1,
    borderColor: Colors.border.default,
  },
  infoLabel: {
    fontSize: Typography.size.xs,
    color: Colors.text.tertiary,
    marginBottom: Spacing.xs,
  },
  infoValue: {
    fontSize: Typography.size.md,
    fontWeight: Typography.weight.semibold,
    color: Colors.accent.primary,
  },
  metricCard: {
    padding: Spacing.base,
    backgroundColor: Colors.bg.card,
    borderRadius: BorderRadius.md,
    borderWidth: 1,
    borderColor: Colors.border.default,
    marginBottom: Spacing.md,
  },
  metricHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: Spacing.sm,
  },
  metricTitle: {
    fontSize: Typography.size.md,
    fontWeight: Typography.weight.semibold,
    color: Colors.text.primary,
  },
  metricValue: {
    fontSize: Typography.size.md,
    fontWeight: Typography.weight.bold,
    color: Colors.accent.primary,
  },
  metricBar: {
    height: 8,
    backgroundColor: Colors.bg.tertiary,
    borderRadius: BorderRadius.full,
    overflow: 'hidden',
  },
  metricBarFill: {
    height: '100%',
    borderRadius: BorderRadius.full,
  },
  actionButton: {
    padding: Spacing.base,
    backgroundColor: Colors.bg.card,
    borderRadius: BorderRadius.md,
    borderWidth: 1,
    borderColor: Colors.border.accent,
    marginBottom: Spacing.md,
  },
  actionButtonText: {
    fontSize: Typography.size.md,
    fontWeight: Typography.weight.semibold,
    color: Colors.accent.primary,
    textAlign: 'center',
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
});
