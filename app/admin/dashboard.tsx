'use client';

import React, { useState, useEffect } from 'react';
import { View, Text, ScrollView, TouchableOpacity, ActivityIndicator } from 'react-native';

import { ScreenContainer } from '@/components/screen-container';
import { useColors } from '@/hooks/use-colors';
import { cn } from '@/lib/utils';

interface InstallationMetrics {
  total_installations: number;
  successful: number;
  failed: number;
  in_progress: number;
  success_rate: number;
  avg_duration_seconds: number;
  total_data_written_gb: number;
}

interface SystemMetrics {
  api_uptime_hours: number;
  total_requests: number;
  avg_response_time_ms: number;
  error_rate: number;
  active_connections: number;
  database_size_mb: number;
  backup_storage_used_gb: number;
}

interface Installation {
  installation_id: string;
  mac_model: string;
  status: 'in_progress' | 'completed' | 'failed';
  progress: number;
  started_at: string;
  duration_seconds?: number;
  components_completed: number;
  components_total: number;
  error_message?: string;
}

type DashboardTab = 'overview' | 'installations' | 'backups' | 'drivers';

export default function AdminDashboard() {
  const colors = useColors();
  const [activeTab, setActiveTab] = useState<DashboardTab>('overview');
  const [loading, setLoading] = useState(false);
  const [installationMetrics, setInstallationMetrics] = useState<InstallationMetrics | null>(null);
  const [systemMetrics, setSystemMetrics] = useState<SystemMetrics | null>(null);
  const [installations, setInstallations] = useState<Installation[]>([]);

  useEffect(() => {
    fetchMetrics();
  }, []);

  const fetchMetrics = async () => {
    try {
      setLoading(true);
      
      // Mock data for demonstration
      setInstallationMetrics({
        total_installations: 1247,
        successful: 1189,
        failed: 58,
        in_progress: 3,
        success_rate: 95.3,
        avg_duration_seconds: 1245.0,
        total_data_written_gb: 5847.3
      });

      setSystemMetrics({
        api_uptime_hours: 720.5,
        total_requests: 45230,
        avg_response_time_ms: 145.2,
        error_rate: 0.8,
        active_connections: 23,
        database_size_mb: 2847.5,
        backup_storage_used_gb: 125.3
      });

      setInstallations([
        {
          installation_id: 'inst_00001',
          mac_model: 'MacBook Pro 15" (2018)',
          status: 'in_progress',
          progress: 75,
          started_at: new Date().toISOString(),
          components_completed: 4,
          components_total: 6
        },
        {
          installation_id: 'inst_00002',
          mac_model: 'MacBook Air 13" (2020)',
          status: 'completed',
          progress: 100,
          started_at: new Date(Date.now() - 3600000).toISOString(),
          duration_seconds: 1245,
          components_completed: 6,
          components_total: 6
        }
      ]);
    } catch (error) {
      console.error('Failed to fetch metrics:', error);
    } finally {
      setLoading(false);
    }
  };

  const renderOverviewTab = () => (
    <View className="gap-6">
      {/* Installation Metrics */}
      <View className="gap-3 rounded-lg bg-surface p-4">
        <Text className="text-lg font-bold text-foreground">Installation Metrics</Text>
        
        <View className="gap-2">
          <View className="flex-row justify-between">
            <Text className="text-muted">Total Installations</Text>
            <Text className="font-semibold text-foreground">{installationMetrics?.total_installations}</Text>
          </View>
          <View className="flex-row justify-between">
            <Text className="text-muted">Successful</Text>
            <Text className="font-semibold text-success">{installationMetrics?.successful}</Text>
          </View>
          <View className="flex-row justify-between">
            <Text className="text-muted">Failed</Text>
            <Text className="font-semibold text-error">{installationMetrics?.failed}</Text>
          </View>
          <View className="flex-row justify-between">
            <Text className="text-muted">In Progress</Text>
            <Text className="font-semibold text-warning">{installationMetrics?.in_progress}</Text>
          </View>
          <View className="flex-row justify-between border-t border-border pt-2">
            <Text className="font-semibold text-foreground">Success Rate</Text>
            <Text className="font-bold text-primary">{installationMetrics?.success_rate.toFixed(1)}%</Text>
          </View>
        </View>
      </View>

      {/* System Metrics */}
      <View className="gap-3 rounded-lg bg-surface p-4">
        <Text className="text-lg font-bold text-foreground">System Metrics</Text>
        
        <View className="gap-2">
          <View className="flex-row justify-between">
            <Text className="text-muted">API Uptime</Text>
            <Text className="font-semibold text-foreground">{systemMetrics?.api_uptime_hours.toFixed(1)} hrs</Text>
          </View>
          <View className="flex-row justify-between">
            <Text className="text-muted">Avg Response Time</Text>
            <Text className="font-semibold text-foreground">{systemMetrics?.avg_response_time_ms.toFixed(0)} ms</Text>
          </View>
          <View className="flex-row justify-between">
            <Text className="text-muted">Error Rate</Text>
            <Text className={cn(
              'font-semibold',
              (systemMetrics?.error_rate ?? 0) > 2 ? 'text-error' : 'text-success'
            )}>
              {systemMetrics?.error_rate.toFixed(2)}%
            </Text>
          </View>
          <View className="flex-row justify-between">
            <Text className="text-muted">Active Connections</Text>
            <Text className="font-semibold text-foreground">{systemMetrics?.active_connections}</Text>
          </View>
          <View className="flex-row justify-between">
            <Text className="text-muted">Backup Storage</Text>
            <Text className="font-semibold text-foreground">{systemMetrics?.backup_storage_used_gb.toFixed(1)} GB</Text>
          </View>
        </View>
      </View>

      {/* Quick Stats */}
      <View className="gap-3">
        <View className="flex-row gap-3">
          <View className="flex-1 rounded-lg bg-primary/10 p-3">
            <Text className="text-xs text-muted">Data Written</Text>
            <Text className="text-xl font-bold text-primary">
              {installationMetrics?.total_data_written_gb.toFixed(1)} GB
            </Text>
          </View>
          <View className="flex-1 rounded-lg bg-success/10 p-3">
            <Text className="text-xs text-muted">Avg Duration</Text>
            <Text className="text-xl font-bold text-success">
              {Math.round((installationMetrics?.avg_duration_seconds ?? 0) / 60)} min
            </Text>
          </View>
        </View>
      </View>
    </View>
  );

  const renderInstallationsTab = () => (
    <View className="gap-4">
      <Text className="text-lg font-bold text-foreground">Active Installations</Text>
      
      {installations.map((inst) => (
        <View key={inst.installation_id} className="gap-2 rounded-lg bg-surface p-4">
          <View className="flex-row items-center justify-between">
            <View className="flex-1 gap-1">
              <Text className="font-semibold text-foreground">{inst.mac_model}</Text>
              <Text className="text-xs text-muted">{inst.installation_id}</Text>
            </View>
            <View className={cn(
              'rounded-full px-3 py-1',
              inst.status === 'in_progress' ? 'bg-warning/20' :
              inst.status === 'completed' ? 'bg-success/20' :
              'bg-error/20'
            )}>
              <Text className={cn(
                'text-xs font-semibold',
                inst.status === 'in_progress' ? 'text-warning' :
                inst.status === 'completed' ? 'text-success' :
                'text-error'
              )}>
                {inst.status}
              </Text>
            </View>
          </View>

          <View className="gap-1">
            <View className="flex-row items-center justify-between">
              <Text className="text-xs text-muted">Progress</Text>
              <Text className="text-xs font-semibold text-foreground">{inst.progress}%</Text>
            </View>
            <View className="h-2 w-full overflow-hidden rounded-full bg-border">
              <View
                className="h-full bg-primary"
                style={{ width: `${inst.progress}%` }}
              />
            </View>
          </View>

          <View className="flex-row justify-between text-xs text-muted">
            <Text>{inst.components_completed}/{inst.components_total} components</Text>
            {inst.duration_seconds && (
              <Text>{Math.round(inst.duration_seconds / 60)} min</Text>
            )}
          </View>
        </View>
      ))}
    </View>
  );

  const renderBackupsTab = () => (
    <View className="gap-4">
      <Text className="text-lg font-bold text-foreground">Driver Backups</Text>
      
      <View className="gap-2 rounded-lg bg-surface p-4">
        <View className="flex-row items-center justify-between">
          <Text className="font-semibold text-foreground">Total Backups</Text>
          <Text className="text-lg font-bold text-primary">1,247</Text>
        </View>
        <View className="flex-row items-center justify-between">
          <Text className="font-semibold text-foreground">Storage Used</Text>
          <Text className="text-lg font-bold text-primary">125.3 GB</Text>
        </View>
        <View className="flex-row items-center justify-between">
          <Text className="font-semibold text-foreground">Avg Backup Size</Text>
          <Text className="text-lg font-bold text-primary">102.5 MB</Text>
        </View>
      </View>

      <TouchableOpacity className="rounded-lg bg-primary px-4 py-3">
        <Text className="text-center font-semibold text-background">View All Backups</Text>
      </TouchableOpacity>
    </View>
  );

  const renderDriversTab = () => (
    <View className="gap-4">
      <Text className="text-lg font-bold text-foreground">Driver Database</Text>
      
      <View className="gap-2 rounded-lg bg-surface p-4">
        <View className="flex-row items-center justify-between">
          <Text className="font-semibold text-foreground">Supported Mac Models</Text>
          <Text className="text-lg font-bold text-primary">180+</Text>
        </View>
        <View className="flex-row items-center justify-between">
          <Text className="font-semibold text-foreground">Driver Packages</Text>
          <Text className="text-lg font-bold text-primary">45</Text>
        </View>
        <View className="flex-row items-center justify-between">
          <Text className="font-semibold text-foreground">Last Update</Text>
          <Text className="text-lg font-bold text-primary">2 days ago</Text>
        </View>
      </View>

      <TouchableOpacity className="rounded-lg bg-primary px-4 py-3">
        <Text className="text-center font-semibold text-background">Check for Updates</Text>
      </TouchableOpacity>
    </View>
  );

  return (
    <ScreenContainer className="p-4">
      <ScrollView contentContainerStyle={{ flexGrow: 1 }}>
        <View className="gap-6">
          {/* Header */}
          <View className="gap-2">
            <Text className="text-3xl font-bold text-foreground">Admin Dashboard</Text>
            <Text className="text-muted">Monitor installations and system health</Text>
          </View>

          {/* Tabs */}
          <View className="flex-row gap-2">
            {(['overview', 'installations', 'backups', 'drivers'] as const).map((tab) => (
              <TouchableOpacity
                key={tab}
                onPress={() => setActiveTab(tab)}
                className={cn(
                  'flex-1 rounded-lg px-3 py-2',
                  activeTab === tab ? 'bg-primary' : 'bg-surface'
                )}
              >
                <Text className={cn(
                  'text-center text-sm font-semibold',
                  activeTab === tab ? 'text-background' : 'text-foreground'
                )}>
                  {tab.charAt(0).toUpperCase() + tab.slice(1)}
                </Text>
              </TouchableOpacity>
            ))}
          </View>

          {/* Content */}
          {loading ? (
            <View className="items-center justify-center py-8">
              <ActivityIndicator size="large" color={colors.primary} />
            </View>
          ) : (
            <>
              {activeTab === 'overview' && renderOverviewTab()}
              {activeTab === 'installations' && renderInstallationsTab()}
              {activeTab === 'backups' && renderBackupsTab()}
              {activeTab === 'drivers' && renderDriversTab()}
            </>
          )}

          {/* Refresh Button */}
          <TouchableOpacity
            onPress={fetchMetrics}
            className="rounded-lg border border-border px-4 py-3"
          >
            <Text className="text-center font-semibold text-foreground">Refresh Data</Text>
          </TouchableOpacity>
        </View>
      </ScrollView>
    </ScreenContainer>
  );
}
