import { ScrollView, Text, View, Pressable, ActivityIndicator } from 'react-native';
import { useState, useEffect } from 'react';
import { ScreenContainer } from '@/components/screen-container';
import { useColors } from '@/hooks/use-colors';
import { cn } from '@/lib/utils';

interface DeviceInfo {
  cpu: string;
  memory: string;
  storage: string;
  gpu: string;
  architecture: string;
  osType: string;
}

interface CompatibilityInfo {
  name: string;
  status: 'compatible' | 'partial' | 'incompatible';
  reason?: string;
  icon: string;
}

export default function DeviceWizardSimple() {
  const colors = useColors();
  const [loading, setLoading] = useState(true);
  const [deviceInfo, setDeviceInfo] = useState<DeviceInfo | null>(null);
  const [compatible, setCompatible] = useState<CompatibilityInfo[]>([]);

  useEffect(() => {
    // Simulate hardware detection
    setTimeout(() => {
      setDeviceInfo({
        cpu: 'Intel Core i7-12700K',
        memory: '16 GB',
        storage: '512 GB SSD',
        gpu: 'NVIDIA RTX 3080',
        architecture: 'x86_64',
        osType: 'Windows',
      });

      setCompatible([
        {
          name: 'Windows 11',
          status: 'compatible',
          icon: '🪟',
        },
        {
          name: 'Ubuntu Linux',
          status: 'compatible',
          icon: '🐧',
        },
        {
          name: 'ChromeOS Flex',
          status: 'compatible',
          icon: '🌐',
        },
        {
          name: 'macOS',
          status: 'partial',
          reason: 'Only on Intel Macs',
          icon: '🍎',
        },
      ]);

      setLoading(false);
    }, 2000);
  }, []);

  if (loading) {
    return (
      <ScreenContainer className="items-center justify-center">
        <ActivityIndicator size="large" color={colors.primary} />
        <Text className="mt-4 text-center text-muted">Checking your device...</Text>
      </ScreenContainer>
    );
  }

  return (
    <ScreenContainer className="p-4">
      <ScrollView contentContainerStyle={{ flexGrow: 1 }}>
        <View className="gap-6">
          {/* Hero Section */}
          <View className="items-center gap-2">
            <Text className="text-3xl font-bold text-foreground">Your Device</Text>
            <Text className="text-center text-muted">Here's what we found on your computer</Text>
          </View>

          {/* Device Info Card */}
          {deviceInfo && (
            <View className="rounded-2xl border border-border bg-surface p-4">
              <View className="gap-3">
                <InfoRow label="Processor" value={deviceInfo.cpu} />
                <InfoRow label="Memory" value={deviceInfo.memory} />
                <InfoRow label="Storage" value={deviceInfo.storage} />
                <InfoRow label="Graphics" value={deviceInfo.gpu} />
                <InfoRow label="Type" value={deviceInfo.architecture} />
              </View>
            </View>
          )}

          {/* Compatible OSes Section */}
          <View className="gap-3">
            <Text className="text-lg font-semibold text-foreground">What can you install?</Text>
            <View className="gap-2">
              {compatible.map((os, idx) => (
                <OSCard key={idx} os={os} colors={colors} />
              ))}
            </View>
          </View>

          {/* CTA Button */}
          <Pressable
            className="rounded-full bg-primary py-4"
            onPress={() => {
              // Navigate to USB Builder
            }}
          >
            <Text className="text-center font-semibold text-background">
              Build a USB for {compatible[0]?.name}
            </Text>
          </Pressable>

          {/* Help Text */}
          <View className="rounded-lg bg-blue-50 p-3">
            <Text className="text-sm text-muted">
              💡 <Text className="font-semibold">Tip:</Text> You can create one USB that boots all these operating systems!
            </Text>
          </View>
        </View>
      </ScrollView>
    </ScreenContainer>
  );
}

function InfoRow({ label, value }: { label: string; value: string }) {
  return (
    <View className="flex-row items-center justify-between">
      <Text className="text-muted">{label}</Text>
      <Text className="font-semibold text-foreground">{value}</Text>
    </View>
  );
}

function OSCard({ os, colors }: { os: CompatibilityInfo; colors: any }) {
  const statusColors = {
    compatible: { bg: 'bg-green-50', border: 'border-green-200', text: 'text-green-700' },
    partial: { bg: 'bg-yellow-50', border: 'border-yellow-200', text: 'text-yellow-700' },
    incompatible: { bg: 'bg-red-50', border: 'border-red-200', text: 'text-red-700' },
  };

  const status = statusColors[os.status];
  const statusIcon = {
    compatible: '✓',
    partial: '⚠',
    incompatible: '✗',
  }[os.status];

  return (
    <View className={cn('flex-row items-center gap-3 rounded-lg border p-3', status.bg, status.border)}>
      <Text className="text-2xl">{os.icon}</Text>
      <View className="flex-1">
        <Text className="font-semibold text-foreground">{os.name}</Text>
        {os.reason && <Text className="text-xs text-muted">{os.reason}</Text>}
      </View>
      <Text className={cn('text-lg font-bold', status.text)}>{statusIcon}</Text>
    </View>
  );
}
