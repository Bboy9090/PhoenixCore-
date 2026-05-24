/**
 * Device Wizard with Backend API Integration
 * Uses real hardware detection from PhoenixCore backend
 */

import React, { useState, useEffect } from 'react';
import { ScrollView, Text, View, Pressable, ActivityIndicator, Alert } from 'react-native';
import { ScreenContainer } from '@/components/screen-container';
import { useHardwareDetection, useUSBDevices, useRefreshUSBDevices } from '@/lib/hooks/use-phoenix-api';

export default function DeviceWizardAPIScreen() {
  const [step, setStep] = useState<'hardware' | 'usb' | 'confirm'>('hardware');
  const [selectedUSB, setSelectedUSB] = useState<string | null>(null);

  // Fetch hardware info
  const {
    data: hardwareData,
    isLoading: hwLoading,
    error: hwError,
  } = useHardwareDetection();

  // Fetch USB devices
  const {
    data: usbDevices = [],
    isLoading: usbLoading,
    error: usbError,
    refetch: refetchUSB,
  } = useUSBDevices();

  const refreshUSB = useRefreshUSBDevices();

  // Handle errors
  useEffect(() => {
    if (hwError) {
      Alert.alert('Hardware Detection Error', hwError.message);
    }
  }, [hwError]);

  useEffect(() => {
    if (usbError) {
      Alert.alert('USB Detection Error', usbError.message);
    }
  }, [usbError]);

  const handleRefreshUSB = async () => {
    const result = await refreshUSB();
    if (result.error) {
      Alert.alert('Refresh Error', 'Failed to refresh USB devices');
    }
  };

  const handleSelectUSB = (deviceId: string) => {
    setSelectedUSB(deviceId);
    setStep('confirm');
  };

  return (
    <ScreenContainer className="p-4">
      <ScrollView contentContainerStyle={{ flexGrow: 1 }}>
        <View className="flex-1 gap-6">
          {/* Header */}
          <View className="items-center gap-2">
            <Text className="text-3xl font-bold text-foreground">Device Wizard</Text>
            <Text className="text-sm text-muted">
              {step === 'hardware' && 'Detecting your system...'}
              {step === 'usb' && 'Select USB device'}
              {step === 'confirm' && 'Confirm selection'}
            </Text>
          </View>

          {/* Step 1: Hardware Detection */}
          {step === 'hardware' && (
            <View className="gap-4">
              {hwLoading ? (
                <View className="items-center gap-4 py-8">
                  <ActivityIndicator size="large" color="#0a7ea4" />
                  <Text className="text-muted">Detecting hardware...</Text>
                </View>
              ) : hardwareData?.hardware ? (
                <View className="gap-3 bg-surface p-4 rounded-lg">
                  <Text className="font-semibold text-foreground">System Information</Text>

                  <View className="gap-2">
                    <View className="flex-row justify-between">
                      <Text className="text-muted">System:</Text>
                      <Text className="font-medium text-foreground">
                        {hardwareData.hardware.system.manufacturer} {hardwareData.hardware.system.model}
                      </Text>
                    </View>

                    <View className="flex-row justify-between">
                      <Text className="text-muted">CPU:</Text>
                      <Text className="font-medium text-foreground">
                        {hardwareData.hardware.cpu.name} ({hardwareData.hardware.cpu.cores} cores)
                      </Text>
                    </View>

                    <View className="flex-row justify-between">
                      <Text className="text-muted">Memory:</Text>
                      <Text className="font-medium text-foreground">
                        {hardwareData.hardware.memory.total_gb.toFixed(1)} GB
                      </Text>
                    </View>

                    <View className="flex-row justify-between">
                      <Text className="text-muted">Architecture:</Text>
                      <Text className="font-medium text-foreground">
                        {hardwareData.hardware.cpu.architecture}
                      </Text>
                    </View>
                  </View>
                </View>
              ) : (
                <View className="bg-error/10 p-4 rounded-lg">
                  <Text className="text-error">Failed to detect hardware</Text>
                </View>
              )}

              {/* Compatible OS */}
              {hardwareData?.compatible_os && hardwareData.compatible_os.length > 0 && (
                <View className="gap-2">
                  <Text className="font-semibold text-foreground">Compatible Operating Systems</Text>
                  {hardwareData.compatible_os.map((os: any) => (
                    <View key={os.id} className="bg-success/10 p-3 rounded-lg flex-row gap-2">
                      <Text className="text-success">✓</Text>
                      <View className="flex-1">
                        <Text className="font-medium text-foreground">{os.name}</Text>
                        <Text className="text-xs text-muted">{os.description}</Text>
                      </View>
                    </View>
                  ))}
                </View>
              )}

              <Pressable
                onPress={() => setStep('usb')}
                style={({ pressed }) => [
                  {
                    opacity: pressed ? 0.7 : 1,
                  },
                ]}
                className="bg-primary py-3 rounded-lg items-center"
              >
                <Text className="text-background font-semibold">Continue to USB Selection</Text>
              </Pressable>
            </View>
          )}

          {/* Step 2: USB Device Selection */}
          {step === 'usb' && (
            <View className="gap-4">
              <View className="flex-row gap-2">
                <Pressable
                  onPress={handleRefreshUSB}
                  style={({ pressed }) => [
                    {
                      opacity: pressed ? 0.7 : 1,
                    },
                  ]}
                  className="flex-1 bg-surface py-2 rounded-lg items-center"
                >
                  <Text className="text-foreground font-medium">
                    {usbLoading ? 'Scanning...' : 'Refresh'}
                  </Text>
                </Pressable>
              </View>

              {usbLoading ? (
                <View className="items-center gap-4 py-8">
                  <ActivityIndicator size="large" color="#0a7ea4" />
                  <Text className="text-muted">Scanning for USB devices...</Text>
                </View>
              ) : usbDevices.length > 0 ? (
                <View className="gap-3">
                  {usbDevices.map((device: any) => (
                    <Pressable
                      key={device.device_id}
                      onPress={() => handleSelectUSB(device.device_id)}
                      style={({ pressed }) => [
                        {
                          opacity: pressed ? 0.7 : 1,
                        },
                      ]}
                      className={`p-4 rounded-lg border-2 ${
                        selectedUSB === device.device_id
                          ? 'border-primary bg-primary/10'
                          : 'border-border bg-surface'
                      }`}
                    >
                      <View className="gap-2">
                        <View className="flex-row justify-between">
                          <Text className="font-semibold text-foreground">{device.name}</Text>
                          <Text className="text-sm text-muted">{device.size_gb.toFixed(1)} GB</Text>
                        </View>

                        <Text className="text-xs text-muted">
                          {device.vendor} {device.model}
                        </Text>

                        <View className="flex-row gap-2">
                          <View className="flex-1 bg-border/20 rounded px-2 py-1">
                            <Text className="text-xs text-muted">{device.filesystem}</Text>
                          </View>
                          <View className="flex-1 bg-border/20 rounded px-2 py-1">
                            <Text className="text-xs text-muted">{device.health_status}</Text>
                          </View>
                        </View>
                      </View>
                    </Pressable>
                  ))}
                </View>
              ) : (
                <View className="bg-warning/10 p-4 rounded-lg">
                  <Text className="text-warning">No USB devices detected</Text>
                  <Text className="text-xs text-muted mt-1">
                    Connect a USB device and tap Refresh
                  </Text>
                </View>
              )}

              <Pressable
                onPress={() => setStep('hardware')}
                style={({ pressed }) => [
                  {
                    opacity: pressed ? 0.7 : 1,
                  },
                ]}
                className="bg-surface py-3 rounded-lg items-center"
              >
                <Text className="text-foreground font-semibold">Back</Text>
              </Pressable>
            </View>
          )}

          {/* Step 3: Confirmation */}
          {step === 'confirm' && selectedUSB && (
            <View className="gap-4">
              {usbDevices.find((d: any) => d.device_id === selectedUSB) && (
                <>
                  <View className="bg-error/10 p-4 rounded-lg gap-2">
                    <Text className="font-semibold text-error">⚠️ Warning</Text>
                    <Text className="text-sm text-foreground">
                      All data on the selected device will be erased. This action cannot be undone.
                    </Text>
                  </View>

                  <View className="bg-surface p-4 rounded-lg gap-2">
                    <Text className="font-semibold text-foreground">Selected Device</Text>
                    {usbDevices
                      .filter((d: any) => d.device_id === selectedUSB)
                      .map((device: any) => (
                        <View key={device.device_id} className="gap-1">
                          <Text className="text-foreground">{device.name}</Text>
                          <Text className="text-sm text-muted">
                            {device.size_gb.toFixed(1)} GB • {device.filesystem}
                          </Text>
                        </View>
                      ))}
                  </View>

                  <Pressable
                    onPress={() => {
                      Alert.alert('Device Selected', `Ready to build on ${selectedUSB}`);
                      // TODO: Navigate to next step or trigger build
                    }}
                    style={({ pressed }) => [
                      {
                        opacity: pressed ? 0.7 : 1,
                      },
                    ]}
                    className="bg-primary py-3 rounded-lg items-center"
                  >
                    <Text className="text-background font-semibold">Confirm & Continue</Text>
                  </Pressable>

                  <Pressable
                    onPress={() => setStep('usb')}
                    style={({ pressed }) => [
                      {
                        opacity: pressed ? 0.7 : 1,
                      },
                    ]}
                    className="bg-surface py-3 rounded-lg items-center"
                  >
                    <Text className="text-foreground font-semibold">Choose Different Device</Text>
                  </Pressable>
                </>
              )}
            </View>
          )}
        </View>
      </ScrollView>
    </ScreenContainer>
  );
}
