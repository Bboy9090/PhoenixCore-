import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  ScrollView,
  TouchableOpacity,
  ActivityIndicator,
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

import { ScreenContainer } from '@/components/screen-container';
import { cn } from '@/lib/utils';
import { useColors } from '@/hooks/use-colors';

interface MacModel {
  model_id: string;
  display_name: string;
  year: number;
  cpu_type: string;
  gpu_type: string;
  boot_camp_support: boolean;
}

interface DriverPackage {
  package_id: string;
  version: string;
  compatible_models: string[];
  components: Record<string, string>;
}

type WizardStep = 'detection' | 'compatibility' | 'download' | 'install' | 'complete' | 'error';

export default function BootCampWizardScreen() {
  const colors = useColors();
  const insets = useSafeAreaInsets();

  const [step, setStep] = useState<WizardStep>('detection');
  const [macModel, setMacModel] = useState<MacModel | null>(null);
  const [driverPackage, setDriverPackage] = useState<DriverPackage | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [progress, setProgress] = useState(0);

  useEffect(() => {
    detectMacSystem();
  }, []);

  const detectMacSystem = async () => {
    try {
      setLoading(true);
      setError(null);

      // Simulate Mac detection
      const mockMacModel: MacModel = {
        model_id: 'MacBookPro15,1',
        display_name: 'MacBook Pro 15-inch (2018)',
        year: 2018,
        cpu_type: 'Intel Core i7-8750H',
        gpu_type: 'AMD Radeon Pro 555X',
        boot_camp_support: true,
      };

      setMacModel(mockMacModel);
      setStep('compatibility');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Detection failed');
      setStep('error');
    } finally {
      setLoading(false);
    }
  };

  const proceedToDownload = async () => {
    try {
      setLoading(true);
      setError(null);

      const mockPackage: DriverPackage = {
        package_id: 'BootCampESD_6.1',
        version: '6.1',
        compatible_models: ['MacBookPro15,1'],
        components: {
          chipset: 'Chipset_6.1.zip',
          gpu: 'GPU_6.1.zip',
          audio: 'Audio_6.1.zip',
          trackpad: 'Trackpad_6.1.zip',
        },
      };

      setDriverPackage(mockPackage);
      setStep('download');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to get driver package');
      setStep('error');
    } finally {
      setLoading(false);
    }
  };

  const startDriverInstallation = async () => {
    try {
      setLoading(true);
      setError(null);
      setStep('install');

      // Simulate installation progress
      for (let i = 0; i <= 100; i += 10) {
        await new Promise((resolve) => setTimeout(resolve, 500));
        setProgress(i);
      }

      setStep('complete');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Installation failed');
      setStep('error');
    } finally {
      setLoading(false);
    }
  };

  const handleRetry = () => {
    setStep('detection');
    setError(null);
    setProgress(0);
    detectMacSystem();
  };

  const renderDetectionStep = () => (
    <View className="gap-6">
      <View className="items-center gap-3">
        <Text className="text-3xl font-bold text-foreground">Detecting Mac</Text>
        <Text className="text-center text-muted">
          We are identifying your Mac model and hardware specifications
        </Text>
      </View>

      {loading ? (
        <View className="items-center gap-4 py-8">
          <ActivityIndicator size="large" color={colors.primary} />
          <Text className="text-muted">Scanning hardware...</Text>
        </View>
      ) : macModel ? (
        <View className="gap-4 rounded-lg bg-surface p-4">
          <View className="gap-2">
            <Text className="text-sm font-semibold text-muted">Mac Model</Text>
            <Text className="text-lg font-bold text-foreground">{macModel.display_name}</Text>
          </View>
          <View className="gap-2">
            <Text className="text-sm font-semibold text-muted">CPU</Text>
            <Text className="text-foreground">{macModel.cpu_type}</Text>
          </View>
          <View className="gap-2">
            <Text className="text-sm font-semibold text-muted">GPU</Text>
            <Text className="text-foreground">{macModel.gpu_type}</Text>
          </View>
          <View className="gap-2">
            <Text className="text-sm font-semibold text-muted">Year</Text>
            <Text className="text-foreground">{macModel.year}</Text>
          </View>
        </View>
      ) : null}
    </View>
  );

  const renderCompatibilityStep = () => (
    <View className="gap-6">
      <View className="items-center gap-3">
        <Text className="text-3xl font-bold text-foreground">✓ Compatible</Text>
        <Text className="text-center text-muted">
          Your Mac is compatible with Boot Camp and Windows drivers
        </Text>
      </View>

      <View className="gap-3 rounded-lg bg-success/10 p-4">
        <Text className="font-semibold text-success">System meets requirements:</Text>
        <Text className="text-sm text-foreground">• Sufficient RAM</Text>
        <Text className="text-sm text-foreground">• Sufficient storage</Text>
        <Text className="text-sm text-foreground">• Intel processor</Text>
      </View>

      <TouchableOpacity
        onPress={proceedToDownload}
        disabled={loading}
        className={cn('rounded-full bg-primary px-6 py-3', loading && 'opacity-50')}
      >
        <Text className="text-center font-semibold text-background">
          {loading ? 'Preparing...' : 'Download Drivers'}
        </Text>
      </TouchableOpacity>
    </View>
  );

  const renderDownloadStep = () => (
    <View className="gap-6">
      <View className="items-center gap-3">
        <Text className="text-3xl font-bold text-foreground">Ready to Install</Text>
        <Text className="text-center text-muted">
          Boot Camp drivers are ready to download and install
        </Text>
      </View>

      {driverPackage && (
        <View className="gap-4 rounded-lg bg-surface p-4">
          <View className="gap-2">
            <Text className="text-sm font-semibold text-muted">Driver Package</Text>
            <Text className="text-lg font-bold text-foreground">
              {driverPackage.package_id} v{driverPackage.version}
            </Text>
          </View>
          <View className="gap-2">
            <Text className="text-sm font-semibold text-muted">Components</Text>
            <Text className="text-sm text-foreground">
              {Object.keys(driverPackage.components).length} drivers included
            </Text>
          </View>
        </View>
      )}

      <TouchableOpacity
        onPress={startDriverInstallation}
        disabled={loading}
        className={cn('rounded-full bg-primary px-6 py-3', loading && 'opacity-50')}
      >
        <Text className="text-center font-semibold text-background">
          {loading ? 'Starting...' : 'Begin Installation'}
        </Text>
      </TouchableOpacity>
    </View>
  );

  const renderInstallStep = () => (
    <View className="gap-6">
      <View className="items-center gap-3">
        <Text className="text-3xl font-bold text-foreground">Installing Drivers</Text>
        <Text className="text-center text-muted">
          Please wait while drivers are installed to your Windows system
        </Text>
      </View>

      <View className="gap-4">
        <View className="gap-2">
          <View className="flex-row items-center justify-between">
            <Text className="font-semibold text-foreground">Overall Progress</Text>
            <Text className="text-sm text-muted">{Math.round(progress)}%</Text>
          </View>
          <View className="h-2 w-full overflow-hidden rounded-full bg-border">
            <View
              className="h-full bg-primary"
              style={{ width: `${progress}%` }}
            />
          </View>
        </View>
      </View>

      <View className="gap-2 rounded-lg bg-warning/10 p-4">
        <Text className="text-sm font-semibold text-warning">Do not restart your computer</Text>
        <Text className="text-xs text-foreground">
          Installation may take several minutes. Your computer will restart automatically when complete.
        </Text>
      </View>
    </View>
  );

  const renderCompleteStep = () => (
    <View className="gap-6">
      <View className="items-center gap-3">
        <Text className="text-4xl">✓</Text>
        <Text className="text-3xl font-bold text-success">Installation Complete</Text>
        <Text className="text-center text-muted">
          Boot Camp drivers have been successfully installed
        </Text>
      </View>

      <View className="gap-3 rounded-lg bg-success/10 p-4">
        <Text className="font-semibold text-success">Next steps:</Text>
        <Text className="text-sm text-foreground">1. Restart your computer</Text>
        <Text className="text-sm text-foreground">2. Boot into Windows</Text>
        <Text className="text-sm text-foreground">3. Verify all hardware is working</Text>
      </View>

      <TouchableOpacity
        onPress={() => setStep('detection')}
        className="rounded-full bg-primary px-6 py-3"
      >
        <Text className="text-center font-semibold text-background">Start Over</Text>
      </TouchableOpacity>
    </View>
  );

  const renderErrorStep = () => (
    <View className="gap-6">
      <View className="items-center gap-3">
        <Text className="text-4xl">✕</Text>
        <Text className="text-3xl font-bold text-error">Something Went Wrong</Text>
        <Text className="text-center text-muted">{error}</Text>
      </View>

      <View className="gap-3 rounded-lg bg-error/10 p-4">
        <Text className="font-semibold text-error">Troubleshooting:</Text>
        <Text className="text-sm text-foreground">• Check your internet connection</Text>
        <Text className="text-sm text-foreground">• Ensure you have admin privileges</Text>
        <Text className="text-sm text-foreground">• Check available disk space</Text>
      </View>

      <TouchableOpacity
        onPress={handleRetry}
        disabled={loading}
        className={cn('rounded-full bg-primary px-6 py-3', loading && 'opacity-50')}
      >
        <Text className="text-center font-semibold text-background">
          {loading ? 'Retrying...' : 'Try Again'}
        </Text>
      </TouchableOpacity>
    </View>
  );

  const renderStep = () => {
    switch (step) {
      case 'detection':
        return renderDetectionStep();
      case 'compatibility':
        return renderCompatibilityStep();
      case 'download':
        return renderDownloadStep();
      case 'install':
        return renderInstallStep();
      case 'complete':
        return renderCompleteStep();
      case 'error':
        return renderErrorStep();
      default:
        return null;
    }
  };

  return (
    <ScreenContainer className="p-6">
      <ScrollView contentContainerStyle={{ flexGrow: 1 }}>
        <View className="flex-1 justify-center gap-8">
          <View className="items-center gap-2">
            <Text className="text-2xl font-bold text-foreground">Boot Camp Setup</Text>
            <View className="h-1 w-16 rounded-full bg-primary" />
          </View>

          {renderStep()}

          <View className="flex-row items-center justify-center gap-2">
            {(['detection', 'compatibility', 'download', 'install', 'complete'] as const).map(
              (s, i) => (
                <View
                  key={s}
                  className={cn(
                    'h-2 w-2 rounded-full',
                    step === s || (['complete', 'error'].includes(step) && i < 4)
                      ? 'bg-primary'
                      : 'bg-border'
                  )}
                />
              )
            )}
          </View>
        </View>
      </ScrollView>
    </ScreenContainer>
  );
}
