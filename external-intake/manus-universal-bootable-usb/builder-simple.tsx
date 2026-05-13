import { ScrollView, Text, View, Pressable, Switch, ActivityIndicator } from 'react-native';
import { useState } from 'react';
import { ScreenContainer } from '@/components/screen-container';
import { useColors } from '@/hooks/use-colors';
import { cn } from '@/lib/utils';

interface QuickRecipe {
  id: string;
  name: string;
  description: string;
  osCount: number;
  toolCount: number;
  sizeGb: number;
  icon: string;
  recommended: boolean;
}

export default function BuilderSimple() {
  const colors = useColors();
  const [step, setStep] = useState<'select' | 'confirm' | 'building'>('select');
  const [selectedRecipe, setSelectedRecipe] = useState<QuickRecipe | null>(null);
  const [buildProgress, setBuildProgress] = useState(0);

  const quickRecipes: QuickRecipe[] = [
    {
      id: 'windows-repair',
      name: 'Windows Repair Kit',
      description: 'Fix Windows problems with repair tools',
      osCount: 1,
      toolCount: 3,
      sizeGb: 8,
      icon: '🪟',
      recommended: true,
    },
    {
      id: 'linux-installer',
      name: 'Linux Installer',
      description: 'Install Ubuntu or other Linux distros',
      osCount: 2,
      toolCount: 2,
      sizeGb: 6,
      icon: '🐧',
      recommended: false,
    },
    {
      id: 'multi-boot',
      name: 'Multi-Boot USB',
      description: 'Boot Windows, Linux, and repair tools',
      osCount: 3,
      toolCount: 5,
      sizeGb: 16,
      icon: '⚡',
      recommended: false,
    },
    {
      id: 'chromeos',
      name: 'ChromeOS Flex',
      description: 'Turn old computers into Chromebooks',
      osCount: 1,
      toolCount: 1,
      sizeGb: 4,
      icon: '🌐',
      recommended: false,
    },
  ];

  const handleBuild = () => {
    if (!selectedRecipe) return;
    setStep('building');
    // Simulate build progress
    let progress = 0;
    const interval = setInterval(() => {
      progress += Math.random() * 15;
      if (progress >= 100) {
        progress = 100;
        clearInterval(interval);
      }
      setBuildProgress(progress);
    }, 500);
  };

  if (step === 'building') {
    return (
      <ScreenContainer className="items-center justify-center p-6">
        <View className="w-full gap-6">
          <View className="items-center gap-2">
            <Text className="text-3xl">🔥</Text>
            <Text className="text-2xl font-bold text-foreground">Building Your USB</Text>
            <Text className="text-center text-muted">Plug in your USB drive now</Text>
          </View>

          {/* Progress Bar */}
          <View className="gap-2">
            <View className="h-3 w-full overflow-hidden rounded-full bg-border">
              <View
                className="h-full bg-primary"
                style={{ width: `${buildProgress}%` }}
              />
            </View>
            <Text className="text-center text-lg font-bold text-primary">
              {Math.round(buildProgress)}%
            </Text>
          </View>

          {/* Status Messages */}
          <View className="gap-2 rounded-lg bg-surface p-4">
            <Text className="text-sm text-muted">
              {buildProgress < 30 && '📥 Downloading files...'}
              {buildProgress >= 30 && buildProgress < 70 && '✍️ Writing to USB...'}
              {buildProgress >= 70 && buildProgress < 100 && '✔️ Finalizing...'}
              {buildProgress >= 100 && '🎉 Done! Your USB is ready!'}
            </Text>
          </View>

          {buildProgress >= 100 && (
            <Pressable
              className="rounded-full bg-primary py-4"
              onPress={() => {
                setStep('select');
                setSelectedRecipe(null);
                setBuildProgress(0);
              }}
            >
              <Text className="text-center font-semibold text-background">Build Another USB</Text>
            </Pressable>
          )}
        </View>
      </ScreenContainer>
    );
  }

  if (step === 'confirm' && selectedRecipe) {
    return (
      <ScreenContainer className="p-4">
        <ScrollView contentContainerStyle={{ flexGrow: 1 }}>
          <View className="gap-6">
            <View className="items-center gap-2">
              <Text className="text-4xl">{selectedRecipe.icon}</Text>
              <Text className="text-2xl font-bold text-foreground">{selectedRecipe.name}</Text>
              <Text className="text-center text-muted">{selectedRecipe.description}</Text>
            </View>

            {/* Details */}
            <View className="rounded-lg bg-surface p-4">
              <View className="gap-3">
                <DetailRow label="Operating Systems" value={`${selectedRecipe.osCount} included`} />
                <DetailRow label="Repair Tools" value={`${selectedRecipe.toolCount} included`} />
                <DetailRow label="USB Size Needed" value={`${selectedRecipe.sizeGb} GB minimum`} />
                <DetailRow label="Time to Build" value="~10-15 minutes" />
              </View>
            </View>

            {/* Warning */}
            <View className="rounded-lg bg-yellow-50 p-3">
              <Text className="text-sm text-yellow-700">
                ⚠️ <Text className="font-semibold">Important:</Text> All data on the USB will be erased. Make sure you have the right USB!
              </Text>
            </View>

            {/* Buttons */}
            <View className="gap-3">
              <Pressable
                className="rounded-full bg-primary py-4"
                onPress={handleBuild}
              >
                <Text className="text-center font-semibold text-background">
                  Yes, Build This USB
                </Text>
              </Pressable>

              <Pressable
                className="rounded-full border border-border py-4"
                onPress={() => {
                  setStep('select');
                  setSelectedRecipe(null);
                }}
              >
                <Text className="text-center font-semibold text-foreground">
                  Go Back
                </Text>
              </Pressable>
            </View>
          </View>
        </ScrollView>
      </ScreenContainer>
    );
  }

  return (
    <ScreenContainer className="p-4">
      <ScrollView contentContainerStyle={{ flexGrow: 1 }}>
        <View className="gap-6">
          {/* Header */}
          <View className="gap-2">
            <Text className="text-3xl font-bold text-foreground">What do you need?</Text>
            <Text className="text-muted">Choose a pre-built USB recipe</Text>
          </View>

          {/* Quick Recipes */}
          <View className="gap-3">
            {quickRecipes.map((recipe) => (
              <Pressable
                key={recipe.id}
                className={cn(
                  'rounded-xl border-2 p-4 transition-all',
                  selectedRecipe?.id === recipe.id
                    ? 'border-primary bg-blue-50'
                    : 'border-border bg-surface'
                )}
                onPress={() => setSelectedRecipe(recipe)}
              >
                <View className="flex-row items-start gap-3">
                  <Text className="text-3xl">{recipe.icon}</Text>
                  <View className="flex-1">
                    <View className="flex-row items-center gap-2">
                      <Text className="flex-1 text-lg font-bold text-foreground">
                        {recipe.name}
                      </Text>
                      {recipe.recommended && (
                        <View className="rounded-full bg-green-100 px-2 py-1">
                          <Text className="text-xs font-semibold text-green-700">
                            Recommended
                          </Text>
                        </View>
                      )}
                    </View>
                    <Text className="mt-1 text-sm text-muted">{recipe.description}</Text>
                    <View className="mt-2 flex-row gap-3">
                      <Badge label={`${recipe.osCount} OS`} />
                      <Badge label={`${recipe.toolCount} tools`} />
                      <Badge label={`${recipe.sizeGb}GB`} />
                    </View>
                  </View>
                </View>
              </Pressable>
            ))}
          </View>

          {/* CTA */}
          {selectedRecipe && (
            <Pressable
              className="rounded-full bg-primary py-4"
              onPress={() => setStep('confirm')}
            >
              <Text className="text-center font-semibold text-background">
                Continue with {selectedRecipe.name}
              </Text>
            </Pressable>
          )}

          {/* Help */}
          <View className="rounded-lg bg-blue-50 p-3">
            <Text className="text-sm text-blue-700">
              💡 <Text className="font-semibold">Not sure?</Text> Start with "Windows Repair Kit" to fix common problems.
            </Text>
          </View>
        </View>
      </ScrollView>
    </ScreenContainer>
  );
}

function DetailRow({ label, value }: { label: string; value: string }) {
  return (
    <View className="flex-row items-center justify-between">
      <Text className="text-muted">{label}</Text>
      <Text className="font-semibold text-foreground">{value}</Text>
    </View>
  );
}

function Badge({ label }: { label: string }) {
  return (
    <View className="rounded-full bg-primary/10 px-2 py-1">
      <Text className="text-xs font-semibold text-primary">{label}</Text>
    </View>
  );
}
