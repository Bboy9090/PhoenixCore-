/**
 * Phoenix Core Enterprise - Devices Screen
 * Real-time device detection and management interface
 */

import React, { useEffect, useState, useCallback } from 'react';
import { View, ScrollView, RefreshControl, Alert, ActivityIndicator, TouchableOpacity, Text } from 'react-native';
import { useQuery } from '@tanstack/react-query';
import { phoenixClient, StorageDevice, StorageSummary } from '@/lib/api/phoenix-enterprise-client';
import { Ionicons } from '@expo/vector-icons';

export default function DevicesScreen() {
  const [selectedDeviceType, setSelectedDeviceType] = useState<'all' | 'usb' | 'ssd' | 'hdd' | 'vdd'>('all');
  const [refreshing, setRefreshing] = useState(false);

  // Query for storage summary
  const { data: summary, isLoading, refetch } = useQuery({
    queryKey: ['storage-summary'],
    queryFn: () => phoenixClient.getStorageSummary(),
    refetchInterval: 5000, // Auto-refresh every 5 seconds
  });

  // Query for devices based on selected type
  const { data: devices = [] } = useQuery({
    queryKey: ['devices', selectedDeviceType],
    queryFn: async () => {
      switch (selectedDeviceType) {
        case 'usb':
          return phoenixClient.getUSBDevices();
        case 'ssd':
          return phoenixClient.getSSDDevices();
        case 'hdd':
          return phoenixClient.getHDDDevices();
        case 'vdd':
          return phoenixClient.getVirtualDevices();
        default:
          return phoenixClient.getAllDevices();
      }
    },
    refetchInterval: 5000,
  });

  const onRefresh = useCallback(async () => {
    setRefreshing(true);
    await refetch();
    setRefreshing(false);
  }, [refetch]);

  const getDeviceIcon = (type: string) => {
    switch (type) {
      case 'usb':
        return 'usb';
      case 'ssd':
        return 'server';
      case 'hdd':
        return 'server';
      case 'nvme':
        return 'flash';
      case 'vdd':
        return 'folder';
      default:
        return 'disc';
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'mounted':
        return '#10b981';
      case 'unmounted':
        return '#f59e0b';
      case 'disconnected':
        return '#ef4444';
      default:
        return '#6b7280';
    }
  };

  const formatBytes = (bytes: number) => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i];
  };

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
      <View className="p-4 bg-slate-800 border-b border-slate-600">
        <Text className="text-cyan-300 text-sm font-semibold mb-1">Host machine</Text>
        <Text className="text-gray-400 text-xs">
          Lists disks from the computer running the Phoenix Core API ({phoenixClient.getBackendUrl()}). Mount, unmount, and raw erase are not available in the mobile app — use the desktop BootForge app or the host OS.
        </Text>
      </View>

      {/* Summary Stats */}
      {summary && (
        <View className="p-4 border-b border-slate-700">
          <Text className="text-white text-lg font-bold mb-3">Storage Summary</Text>
          <View className="flex-row flex-wrap gap-2">
            <View className="flex-1 min-w-[45%] bg-slate-800 p-3 rounded-lg">
              <Text className="text-gray-400 text-xs">Total Devices</Text>
              <Text className="text-cyan-400 text-2xl font-bold">{summary.total_devices}</Text>
            </View>
            <View className="flex-1 min-w-[45%] bg-slate-800 p-3 rounded-lg">
              <Text className="text-gray-400 text-xs">Total Capacity</Text>
              <Text className="text-cyan-400 text-lg font-bold">{formatBytes(summary.capacity.total_bytes)}</Text>
            </View>
            <View className="flex-1 min-w-[45%] bg-slate-800 p-3 rounded-lg">
              <Text className="text-gray-400 text-xs">Used</Text>
              <Text className="text-orange-400 text-lg font-bold">{formatBytes(summary.capacity.used_bytes)}</Text>
            </View>
            <View className="flex-1 min-w-[45%] bg-slate-800 p-3 rounded-lg">
              <Text className="text-gray-400 text-xs">Free</Text>
              <Text className="text-green-400 text-lg font-bold">{formatBytes(summary.capacity.free_bytes)}</Text>
            </View>
          </View>
        </View>
      )}

      {/* Device Type Filter */}
      <View className="p-4 border-b border-slate-700">
        <Text className="text-white text-sm font-semibold mb-2">Filter by Type</Text>
        <View className="flex-row flex-wrap gap-2">
          {(['all', 'usb', 'ssd', 'hdd', 'vdd'] as const).map((type) => (
            <TouchableOpacity
              key={type}
              onPress={() => setSelectedDeviceType(type)}
              className={`px-4 py-2 rounded-full ${
                selectedDeviceType === type ? 'bg-cyan-500' : 'bg-slate-700'
              }`}
            >
              <Text className={selectedDeviceType === type ? 'text-white font-bold' : 'text-gray-300'}>
                {type.toUpperCase()}
              </Text>
            </TouchableOpacity>
          ))}
        </View>
      </View>

      {/* Devices List */}
      <View className="p-4">
        {devices.length === 0 ? (
          <View className="py-8 items-center">
            <Ionicons name="disc-outline" size={48} color="#6b7280" />
            <Text className="text-gray-400 mt-2">No devices found</Text>
          </View>
        ) : (
          devices.map((device) => (
            <View key={device.device_id} className="bg-slate-800 rounded-lg p-4 mb-3 border border-slate-700">
              {/* Device Header */}
              <View className="flex-row items-center mb-3">
                <Ionicons name={getDeviceIcon(device.device_type) as any} size={24} color="#00d4ff" />
                <View className="flex-1 ml-3">
                  <Text className="text-white font-bold text-base">{device.device_name}</Text>
                  <Text className="text-gray-400 text-xs">
                    {device.vendor} {device.model}
                  </Text>
                </View>
                <View
                  className="px-2 py-1 rounded"
                  style={{ backgroundColor: getStatusColor(device.status) + '20', borderColor: getStatusColor(device.status), borderWidth: 1 }}
                >
                  <Text style={{ color: getStatusColor(device.status) }} className="text-xs font-semibold">
                    {device.status.toUpperCase()}
                  </Text>
                </View>
              </View>

              {/* Device Info */}
              <View className="bg-slate-900 rounded p-2 mb-3">
                <View className="flex-row justify-between mb-2">
                  <Text className="text-gray-400 text-xs">Capacity</Text>
                  <Text className="text-cyan-400 text-xs font-semibold">{formatBytes(device.size_bytes)}</Text>
                </View>
                <View className="flex-row justify-between mb-2">
                  <Text className="text-gray-400 text-xs">Used</Text>
                  <Text className="text-orange-400 text-xs font-semibold">{formatBytes(device.used_bytes)}</Text>
                </View>
                <View className="flex-row justify-between">
                  <Text className="text-gray-400 text-xs">Free</Text>
                  <Text className="text-green-400 text-xs font-semibold">{formatBytes(device.free_bytes)}</Text>
                </View>

                {/* Progress Bar */}
                <View className="mt-2 h-2 bg-slate-700 rounded-full overflow-hidden">
                  <View
                    className="h-full bg-gradient-to-r from-cyan-500 to-blue-500"
                    style={{ width: `${(device.used_bytes / device.size_bytes) * 100}%` }}
                  />
                </View>
              </View>

              {/* Device Details */}
              {device.mount_point && (
                <View className="mb-2">
                  <Text className="text-gray-400 text-xs">Mount Point: {device.mount_point}</Text>
                </View>
              )}

            </View>
          ))
        )}
      </View>
    </ScrollView>
  );
}
