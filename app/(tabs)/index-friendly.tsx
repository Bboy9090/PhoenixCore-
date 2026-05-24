import { ScrollView, Text, View, TouchableOpacity, Pressable } from 'react-native';
import { useState } from 'react';
import { ScreenContainer } from '@/components/screen-container';
import { useColors } from '@/hooks/use-colors';
import { cn } from '@/lib/utils';

interface OnboardingStep {
  id: string;
  title: string;
  description: string;
  icon: string;
  action: string;
}

export default function HomeScreenFriendly() {
  const colors = useColors();
  const [showOnboarding, setShowOnboarding] = useState(true);
  const [completedSteps, setCompletedSteps] = useState<string[]>([]);

  const onboardingSteps: OnboardingStep[] = [
    {
      id: 'welcome',
      title: 'Welcome to Bobby\'s PhoenixDrive',
      description: 'Your computer\'s emergency repair kit. Fix any device, any OS, any problem.',
      icon: '🔥',
      action: 'Next',
    },
    {
      id: 'how-it-works',
      title: 'How It Works',
      description: 'Plug a USB into your computer. Bobby\'s builds a bootable USB with everything you need to fix problems.',
      icon: '⚡',
      action: 'Next',
    },
    {
      id: 'ready',
      title: 'Ready to Build?',
      description: 'Choose a pre-built USB recipe or customize your own. Takes just 10 minutes!',
      icon: '🚀',
      action: 'Get Started',
    },
  ];

  const quickActions = [
    {
      id: 'windows-repair',
      title: 'Fix Windows',
      description: 'Repair Windows problems',
      icon: '🪟',
      color: 'bg-blue-500',
    },
    {
      id: 'linux-install',
      title: 'Install Linux',
      description: 'Try a new OS',
      icon: '🐧',
      color: 'bg-orange-500',
    },
    {
      id: 'chromeos',
      title: 'ChromeOS Flex',
      description: 'Revive old computers',
      icon: '🌐',
      color: 'bg-green-500',
    },
    {
      id: 'custom',
      title: 'Custom USB',
      description: 'Build your own',
      icon: '⚙️',
      color: 'bg-purple-500',
    },
  ];

  if (showOnboarding) {
    return (
      <ScreenContainer className="items-center justify-center p-6">
        <View className="w-full gap-6">
          {/* Onboarding Content */}
          <View className="items-center gap-4">
            <Text className="text-6xl">{onboardingSteps[0].icon}</Text>
            <Text className="text-center text-3xl font-bold text-foreground">
              {onboardingSteps[0].title}
            </Text>
            <Text className="text-center text-lg text-muted">
              {onboardingSteps[0].description}
            </Text>
          </View>

          {/* Features List */}
          <View className="gap-3">
            {[
              { icon: '✓', text: 'Fix any computer problem' },
              { icon: '✓', text: 'Install any operating system' },
              { icon: '✓', text: 'One USB, unlimited possibilities' },
              { icon: '✓', text: 'Works offline' },
            ].map((feature, idx) => (
              <View key={idx} className="flex-row items-center gap-3">
                <Text className="text-2xl text-green-500">{feature.icon}</Text>
                <Text className="text-base text-foreground">{feature.text}</Text>
              </View>
            ))}
          </View>

          {/* CTA Button */}
          <Pressable
            className="rounded-full bg-primary py-4"
            onPress={() => setShowOnboarding(false)}
          >
            <Text className="text-center font-bold text-background text-lg">
              Let's Get Started
            </Text>
          </Pressable>

          {/* Skip Link */}
          <Pressable onPress={() => setShowOnboarding(false)}>
            <Text className="text-center text-muted underline">Skip for now</Text>
          </Pressable>
        </View>
      </ScreenContainer>
    );
  }

  return (
    <ScreenContainer className="p-4">
      <ScrollView contentContainerStyle={{ flexGrow: 1 }}>
        <View className="gap-6">
          {/* Hero Section */}
          <View className="gap-2">
            <Text className="text-4xl font-bold text-foreground">
              Any Device.{' '}Any OS. Fixed.
            </Text>
            <Text className="text-lg text-muted">
              Bobby's got your back. Plug it in, boot it up, problem over in a jiffy.
            </Text>
          </View>

          {/* Quick Actions */}
          <View className="gap-3">
            <Text className="text-lg font-semibold text-foreground">Quick Actions</Text>
            <View className="gap-2">
              {quickActions.map((action) => (
                <Pressable
                  key={action.id}
                  className="flex-row items-center gap-3 rounded-xl bg-surface p-4 active:opacity-70"
                >
                  <View className={cn('rounded-lg p-3', action.color)}>
                    <Text className="text-2xl">{action.icon}</Text>
                  </View>
                  <View className="flex-1">
                    <Text className="font-semibold text-foreground">{action.title}</Text>
                    <Text className="text-sm text-muted">{action.description}</Text>
                  </View>
                  <Text className="text-xl text-muted">›</Text>
                </Pressable>
              ))}
            </View>
          </View>

          {/* Stats */}
          <View className="flex-row gap-3">
            {[
              { label: 'OSes', value: '10+' },
              { label: 'Tools', value: '7+' },
              { label: 'Guides', value: '6+' },
            ].map((stat, idx) => (
              <View
                key={idx}
                className="flex-1 items-center rounded-lg bg-surface py-3"
              >
                <Text className="text-2xl font-bold text-primary">{stat.value}</Text>
                <Text className="text-xs text-muted">{stat.label}</Text>
              </View>
            ))}
          </View>

          {/* Info Card */}
          <View className="rounded-lg bg-blue-50 p-4">
            <Text className="text-sm text-blue-900">
              <Text className="font-semibold">💡 First time?</Text>{' '}
              Start with "Fix Windows" to repair common problems. Takes 10 minutes!
            </Text>
          </View>

          {/* Help Section */}
          <View className="gap-2">
            <Text className="text-sm font-semibold text-muted">Need help?</Text>
            <Pressable className="flex-row items-center justify-between rounded-lg border border-border p-3">
              <Text className="text-foreground">📖 Read Getting Started Guide</Text>
              <Text className="text-muted">›</Text>
            </Pressable>
            <Pressable className="flex-row items-center justify-between rounded-lg border border-border p-3">
              <Text className="text-foreground">🎥 Watch Video Tutorial</Text>
              <Text className="text-muted">›</Text>
            </Pressable>
          </View>
        </View>
      </ScrollView>
    </ScreenContainer>
  );
}
