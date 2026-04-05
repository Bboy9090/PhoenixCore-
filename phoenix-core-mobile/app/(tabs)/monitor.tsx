/**
 * Phoenix Core Enterprise - System Monitor Screen
 * Real-time system metrics and hardware monitoring
 */

import React, { useEffect, useState } from 'react';
import { View, ScrollView, RefreshControl, ActivityIndicator, Text, TouchableOpacity, Alert } from 'react-native';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { phoenixClient, SystemMetrics, HardwareProfile } from '@/lib/api/phoenix-enterprise-client';
import { Ionicons } from '@expo/vector-icons';

export default function MonitorScreen() {
  const [refreshing, setRefreshing] = useState(false);
  const queryClient = useQueryClient();

  // Query for system metrics
  const { data: metrics, refetch: refetchMetrics } = useQuery({
    queryKey: ['system-metrics'],
    queryFn: () => phoenixClient.getSystemMetrics(),
    refetchInterval: 2000, // Update every 2 seconds
  });

  // Query for hardware profile
  const { data: hardware, isLoading } = useQuery({
    queryKey: ['hardware-profile'],
    queryFn: () => phoenixClient.getHardwareProfile(),
    refetchInterval: 30000, // Update every 30 seconds
  });

  const { data: auditSummary, refetch: refetchAudit } = useQuery({
    queryKey: ['audit-jobs-summary'],
    queryFn: () => phoenixClient.getAuditJobsSummary(25),
    refetchInterval: 15000,
  });

  const rebuildMutation = useMutation({
    mutationFn: () => phoenixClient.rebuildAuditIndex(),
    onSuccess: (r) => {
      queryClient.invalidateQueries({ queryKey: ['audit-jobs-summary'] });
      Alert.alert('Audit index', `Indexed records: ${String(r.indexed_records ?? '—')}`);
    },
    onError: (e: unknown) => {
      Alert.alert('Rebuild failed', e instanceof Error ? e.message : String(e));
    },
  });

  const onRefresh = async () => {
    setRefreshing(true);
    await refetchMetrics();
    await refetchAudit();
    setRefreshing(false);
  };

  const getMetricColor = (percent: number) => {
    if (percent < 50) return '#10b981'; // Green
    if (percent < 75) return '#f59e0b'; // Orange
    return '#ef4444'; // Red
  };

  const MetricCard = ({ icon, label, value, unit, percent }: any) => (
    <View className="bg-slate-800 rounded-lg p-4 mb-3 border border-slate-700">
      <View className="flex-row items-center mb-2">
        <Ionicons name={icon} size={20} color="#00d4ff" />
        <Text className="text-gray-300 ml-2 flex-1">{label}</Text>
        <Text style={{ color: getMetricColor(percent) }} className="font-bold">
          {percent}%
        </Text>
      </View>
      <View className="h-2 bg-slate-700 rounded-full overflow-hidden mb-2">
        <View
          className="h-full"
          style={{
            width: `${percent}%`,
            backgroundColor: getMetricColor(percent),
          }}
        />
      </View>
      <Text className="text-gray-400 text-xs">
        {value} {unit}
      </Text>
    </View>
  );

  if (isLoading) {
    return (
      <View className="flex-1 justify-center items-center bg-slate-900">
        <ActivityIndicator size="large" color="#00d4ff" />
      </View>
    );
  }

  return (
    <ScrollView
      className="flex-1 bg-slate-900"
      refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor="#00d4ff" />}
    >
      {/* Destructive job history (host audit) */}
      <View className="p-4 border-b border-slate-700">
        <View className="flex-row justify-between items-center mb-2">
          <Text className="text-white text-lg font-bold">Recent destructive jobs</Text>
          <TouchableOpacity
            onPress={() => rebuildMutation.mutate()}
            disabled={rebuildMutation.isPending}
            className="bg-slate-700 px-3 py-1 rounded"
          >
            <Text className="text-cyan-300 text-xs">
              {rebuildMutation.isPending ? 'Rebuilding…' : 'Rebuild index'}
            </Text>
          </TouchableOpacity>
        </View>
        <Text className="text-gray-500 text-xs mb-3">
          From host audit (JSONL + SQLite). Rollback is never automatic. Query: GET /api/audit/query?job_id=…
        </Text>
        {!auditSummary?.jobs?.length ? (
          <Text className="text-gray-500 text-sm">No indexed jobs yet (run a USB flow on the host).</Text>
        ) : (
          auditSummary.jobs.map((j) => (
            <View
              key={j.job_id || j.last_written_at}
              className="bg-slate-800 rounded-lg p-3 mb-2 border border-slate-600"
            >
              <Text className="text-cyan-300 text-xs font-mono" numberOfLines={1}>
                {j.job_id || '(no id)'}
              </Text>
              <Text className="text-white text-sm mt-1">
                {j.last_event || '?'} · {j.recipe_id || '—'}
              </Text>
              <Text className="text-gray-400 text-xs mt-1" numberOfLines={2}>
                Target: {j.target_device_path || '—'}
              </Text>
              <Text className="text-gray-500 text-xs mt-1">
                {j.last_written_at || ''} · rollback: {j.rollback_available ? 'yes' : 'no'}
                {j.failure_stage ? ` · stage: ${j.failure_stage}` : ''}
              </Text>
            </View>
          ))
        )}
      </View>

      {/* System Info */}
      {hardware && (
        <View className="p-4 border-b border-slate-700">
          <Text className="text-white text-lg font-bold mb-3">System Information</Text>
          <View className="bg-slate-800 rounded-lg p-4 space-y-2 border border-slate-700">
            <View className="flex-row justify-between py-2 border-b border-slate-700">
              <Text className="text-gray-400">OS</Text>
              <Text className="text-white font-semibold">
                {hardware.os_name} {hardware.os_version}
              </Text>
            </View>
            <View className="flex-row justify-between py-2 border-b border-slate-700">
              <Text className="text-gray-400">Hostname</Text>
              <Text className="text-white font-semibold">{hardware.hostname}</Text>
            </View>
            <View className="flex-row justify-between py-2 border-b border-slate-700">
              <Text className="text-gray-400">Architecture</Text>
              <Text className="text-white font-semibold">{hardware.architecture}</Text>
            </View>
            <View className="flex-row justify-between py-2">
              <Text className="text-gray-400">Uptime</Text>
              <Text className="text-white font-semibold">
                {metrics ? `${Math.floor(metrics.uptime_seconds / 3600)}h ${Math.floor((metrics.uptime_seconds % 3600) / 60)}m` : 'N/A'}
              </Text>
            </View>
          </View>
        </View>
      )}

      {/* Real-time Metrics */}
      {metrics && (
        <View className="p-4">
          <Text className="text-white text-lg font-bold mb-3">Real-Time Metrics</Text>

          <MetricCard
            icon="flash"
            label="CPU Usage"
            value={metrics.cpu_percent.toFixed(1)}
            unit="%"
            percent={Math.round(metrics.cpu_percent)}
          />

          <MetricCard
            icon="memory"
            label="Memory Usage"
            value={`${metrics.memory_available_mb.toFixed(0)} / ${metrics.memory_total_mb.toFixed(0)} MB`}
            unit=""
            percent={Math.round(metrics.memory_percent)}
          />

          <MetricCard
            icon="disc"
            label="Disk Usage"
            value={`${metrics.disk_free_gb.toFixed(1)} / ${metrics.disk_total_gb.toFixed(1)} GB Free`}
            unit=""
            percent={Math.round(metrics.disk_percent)}
          />
        </View>
      )}

      {/* Hardware Details */}
      {hardware && (
        <View className="p-4 border-t border-slate-700">
          <Text className="text-white text-lg font-bold mb-3">Hardware Details</Text>

          <View className="bg-slate-800 rounded-lg p-4 space-y-2 border border-slate-700">
            <View className="flex-row justify-between py-2 border-b border-slate-700">
              <Text className="text-gray-400">CPU Model</Text>
              <Text className="text-white font-semibold text-right flex-1 ml-2">{hardware.cpu_model}</Text>
            </View>
            <View className="flex-row justify-between py-2 border-b border-slate-700">
              <Text className="text-gray-400">CPU Cores</Text>
              <Text className="text-white font-semibold">
                {hardware.cpu_cores} ({hardware.cpu_threads} threads)
              </Text>
            </View>
            <View className="flex-row justify-between py-2 border-b border-slate-700">
              <Text className="text-gray-400">CPU Frequency</Text>
              <Text className="text-white font-semibold">{hardware.cpu_frequency_ghz.toFixed(2)} GHz</Text>
            </View>
            <View className="flex-row justify-between py-2 border-b border-slate-700">
              <Text className="text-gray-400">RAM</Text>
              <Text className="text-white font-semibold">{hardware.ram_gb} GB</Text>
            </View>
            <View className="flex-row justify-between py-2">
              <Text className="text-gray-400">Total Disk</Text>
              <Text className="text-white font-semibold">{hardware.disk_total_gb} GB</Text>
            </View>
            {hardware.gpu_model && (
              <View className="flex-row justify-between py-2 border-t border-slate-700 mt-2">
                <Text className="text-gray-400">GPU</Text>
                <Text className="text-white font-semibold text-right flex-1 ml-2">{hardware.gpu_model}</Text>
              </View>
            )}
          </View>
        </View>
      )}

      {/* Last Updated */}
      {metrics && (
        <View className="p-4 items-center border-t border-slate-700">
          <Text className="text-gray-500 text-xs">
            Last updated: {new Date(metrics.timestamp).toLocaleTimeString()}
          </Text>
        </View>
      )}
    </ScrollView>
  );
}
