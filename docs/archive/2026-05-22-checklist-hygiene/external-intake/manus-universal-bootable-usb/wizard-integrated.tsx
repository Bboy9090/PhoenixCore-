import { useState, useEffect } from 'react';
import { ScrollView, Text, View, TouchableOpacity, ActivityIndicator } from 'react-native';
import { ScreenContainer } from '@/components/screen-container';
import { useHardwareDetection } from '@/hooks/use-phoenix-api';
import { useColors } from '@/hooks/use-colors';

type WizardStep = 'loading' | 'hardware' | 'compatibility' | 'ready';

export default function DeviceWizardScreen() {
  const colors = useColors();
  const [step, setStep] = useState<WizardStep>('loading');
  const [selectedOs, setSelectedOs] = useState<string | null>(null);

  const { data: hardware, isLoading, error } = useHardwareDetection();

  useEffect(() => {
    if (isLoading) {
      setStep('loading');
    } else if (hardware) {
      setStep('hardware');
    } else if (error) {
      setStep('compatibility');
    }
  }, [isLoading, hardware, error]);

  const getCompatibilityColor = (status: 'compatible' | 'incompatible' | 'partial') => {
    switch (status) {
      case 'compatible':
        return colors.success;
      case 'incompatible':
        return colors.error;
      case 'partial':
        return colors.warning;
    }
  };

  const renderLoading = () => (
    <ScreenContainer className="items-center justify-center p-6">
      <ActivityIndicator size="large" color={colors.primary} />
      <Text className="mt-4 text-foreground text-center">Detecting your hardware...</Text>
      <Text className="mt-2 text-muted text-sm text-center">
        This helps us find the perfect OS options for your device
      </Text>
    </ScreenContainer>
  );

  const renderHardwareDetection = () => (
    <ScreenContainer className="p-6">
      <ScrollView contentContainerStyle={{ flexGrow: 1 }}>
        {/* Header */}
        <View className="mb-6">
          <Text className="text-3xl font-bold text-foreground mb-2">Your Device</Text>
          <Text className="text-muted">
            {hardware?.hardware.system.manufacturer} {hardware?.hardware.system.model}
          </Text>
        </View>

        {/* Hardware Details Card */}
        <View className="bg-surface rounded-2xl p-6 mb-6 border border-border">
          <Text className="text-lg font-semibold text-foreground mb-4">Hardware Specs</Text>

          {/* CPU */}
          <View className="mb-4 pb-4 border-b border-border">
            <Text className="text-sm text-muted mb-1">Processor</Text>
            <Text className="text-base font-semibold text-foreground">
              {hardware?.hardware.cpu.name}
            </Text>
            <Text className="text-xs text-muted mt-1">
              {hardware?.hardware.cpu.cores} cores • {hardware?.hardware.cpu.threads} threads •{' '}
              {hardware?.hardware.cpu.architecture}
            </Text>
          </View>

          {/* Memory */}
          <View className="mb-4 pb-4 border-b border-border">
            <Text className="text-sm text-muted mb-1">Memory</Text>
            <Text className="text-base font-semibold text-foreground">
              {hardware?.hardware.memory.total_gb?.toFixed(1)} GB RAM
            </Text>
          </View>

          {/* GPU */}
          {hardware?.hardware.gpu && hardware.hardware.gpu.length > 0 && (
            <View className="mb-4 pb-4 border-b border-border">
              <Text className="text-sm text-muted mb-1">Graphics</Text>
              <Text className="text-base font-semibold text-foreground">
                {hardware.hardware.gpu[0].name}
              </Text>
            </View>
          )}

          {/* Storage */}
          {hardware?.hardware.storage && hardware.hardware.storage.length > 0 && (
            <View>
              <Text className="text-sm text-muted mb-1">Storage</Text>
              <Text className="text-base font-semibold text-foreground">
                {hardware.hardware.storage[0].size_gb?.toFixed(1)} GB
              </Text>
              <Text className="text-xs text-muted mt-1">{hardware.hardware.storage[0].filesystem}</Text>
            </View>
          )}
        </View>

        {/* Platform Info */}
        <View className="bg-surface rounded-2xl p-6 mb-6 border border-border">
          <Text className="text-lg font-semibold text-foreground mb-4">Platform</Text>

          <View className="mb-3">
            <Text className="text-sm text-muted">Operating System</Text>
            <Text className="text-base font-semibold text-foreground capitalize">
              {hardware?.platform.os} {hardware?.platform.version}
            </Text>
          </View>

          <View className="mb-3">
            <Text className="text-sm text-muted">Architecture</Text>
            <Text className="text-base font-semibold text-foreground">
              {hardware?.platform.architecture}
            </Text>
          </View>

          <View>
            <Text className="text-sm text-muted">Boot Mode</Text>
            <Text className="text-base font-semibold text-foreground">
              {hardware?.platform.bios_mode?.toUpperCase()}
            </Text>
          </View>
        </View>

        {/* Compatibility Info */}
        <View className="bg-surface rounded-2xl p-6 border border-border">
          <Text className="text-lg font-semibold text-foreground mb-4">OS Compatibility</Text>

          {hardware?.compatible_os && hardware.compatible_os.length > 0 && (
            <View className="mb-6">
              <View className="flex-row items-center mb-3">
                <View
                  className="w-3 h-3 rounded-full mr-2"
                  style={{ backgroundColor: colors.success }}
                />
                <Text className="text-sm font-semibold text-foreground">
                  Compatible ({hardware.compatible_os.length})
                </Text>
              </View>
              {hardware.compatible_os.slice(0, 5).map((os, idx) => (
                <Text key={idx} className="text-sm text-muted ml-5 mb-1">
                  • {os.replace(/_/g, ' ').toUpperCase()}
                </Text>
              ))}
              {hardware.compatible_os.length > 5 && (
                <Text className="text-xs text-muted ml-5 mt-2">
                  +{hardware.compatible_os.length - 5} more
                </Text>
              )}
            </View>
          )}

          {hardware?.incompatible_os && hardware.incompatible_os.length > 0 && (
            <View>
              <View className="flex-row items-center mb-3">
                <View
                  className="w-3 h-3 rounded-full mr-2"
                  style={{ backgroundColor: colors.error }}
                />
                <Text className="text-sm font-semibold text-foreground">
                  Not Compatible ({hardware.incompatible_os.length})
                </Text>
              </View>
              {hardware.incompatible_os.slice(0, 3).map((os, idx) => (
                <Text key={idx} className="text-sm text-muted ml-5 mb-1">
                  • {os.replace(/_/g, ' ').toUpperCase()}
                </Text>
              ))}
              {hardware.incompatible_reason && (
                <View className="mt-3 p-3 bg-error/10 rounded-lg border border-error/20">
                  <Text className="text-xs text-error">{hardware.incompatible_reason}</Text>
                </View>
              )}
            </View>
          )}
        </View>

        {/* Action Button */}
        <TouchableOpacity
          className="mt-8 mb-4 bg-primary py-4 rounded-full items-center"
          onPress={() => setStep('ready')}
        >
          <Text className="text-background font-semibold text-lg">Build USB for This Device</Text>
        </TouchableOpacity>
      </ScrollView>
    </ScreenContainer>
  );

  const renderError = () => (
    <ScreenContainer className="items-center justify-center p-6">
      <View className="w-12 h-12 rounded-full bg-error/10 items-center justify-center mb-4">
        <Text className="text-2xl">⚠️</Text>
      </View>
      <Text className="text-lg font-semibold text-foreground text-center mb-2">
        Detection Failed
      </Text>
      <Text className="text-muted text-center mb-6">
        {error instanceof Error ? error.message : 'Could not detect your hardware'}
      </Text>
      <TouchableOpacity
        className="bg-primary px-6 py-3 rounded-full"
        onPress={() => window.location.reload()}
      >
        <Text className="text-background font-semibold">Try Again</Text>
      </TouchableOpacity>
    </ScreenContainer>
  );

  if (step === 'loading') return renderLoading();
  if (step === 'compatibility' || error) return renderError();
  if (step === 'hardware' && hardware) return renderHardwareDetection();

  return renderLoading();
}
