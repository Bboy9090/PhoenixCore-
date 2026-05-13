/**
 * USB Builder with Backend API Integration
 * Uses real recipe building and validation from PhoenixCore backend
 */

import React, { useState, useEffect } from 'react';
import { ScrollView, Text, View, Pressable, ActivityIndicator, Alert, FlatList } from 'react-native';
import { ScreenContainer } from '@/components/screen-container';
import {
  useBuildRecipe,
  useValidateRecipe,
  useSafetyCheck,
  useStartUSBBuild,
  useBuildProgress,
  type Recipe,
  type USBDevice,
} from '@/lib/hooks/use-phoenix-api';

interface BuildStep {
  id: 'os' | 'tools' | 'device' | 'validate' | 'safety' | 'confirm' | 'building';
  name: string;
  description: string;
  completed: boolean;
}

interface OSSelection {
  id: string;
  name: string;
  version: string;
  size_gb: number;
  selected: boolean;
}

interface ToolSelection {
  id: string;
  name: string;
  version: string;
  size_mb: number;
  selected: boolean;
}

export default function USBBuilderAPIScreen() {
  const [currentStep, setCurrentStep] = useState<BuildStep['id']>('os');
  const [osSelections, setOsSelections] = useState<OSSelection[]>([
    { id: 'windows11', name: 'Windows 11', version: '23H2', size_gb: 5.5, selected: false },
    { id: 'ubuntu22', name: 'Ubuntu 22.04 LTS', version: '22.04', size_gb: 3.2, selected: false },
    { id: 'fedora39', name: 'Fedora 39', version: '39', size_gb: 2.8, selected: false },
    { id: 'macos14', name: 'macOS Sonoma', version: '14', size_gb: 12.0, selected: false },
  ]);

  const [toolSelections, setToolSelections] = useState<ToolSelection[]>([
    { id: 'ventoy', name: 'Ventoy', version: '1.0.98', size_mb: 50, selected: false },
    { id: 'grub', name: 'GRUB', version: '2.06', size_mb: 30, selected: false },
    { id: 'refind', name: 'rEFInd', version: '0.14.2', size_mb: 20, selected: false },
  ]);

  const [selectedDevice, setSelectedDevice] = useState<USBDevice | null>(null);
  const [recipe, setRecipe] = useState<Recipe | null>(null);
  const [buildId, setBuildId] = useState<string | null>(null);

  // API hooks
  const buildRecipeMutation = useBuildRecipe();
  const validateRecipeMutation = useValidateRecipe();
  const safetyCheckMutation = useSafetyCheck();
  const startBuildMutation = useStartUSBBuild();
  const { progress: buildProgress } = useBuildProgress(buildId);

  const steps: BuildStep[] = [
    { id: 'os', name: 'Select OS', description: 'Choose operating systems', completed: osSelections.some((o) => o.selected) },
    { id: 'tools', name: 'Select Tools', description: 'Choose boot tools', completed: toolSelections.some((t) => t.selected) },
    { id: 'device', name: 'Select Device', description: 'Choose USB device', completed: !!selectedDevice },
    { id: 'validate', name: 'Validate', description: 'Validate recipe', completed: !!recipe },
    { id: 'safety', name: 'Safety Check', description: 'Run safety checks', completed: false },
    { id: 'confirm', name: 'Confirm', description: 'Review & confirm', completed: false },
    { id: 'building', name: 'Building', description: 'Building USB', completed: false },
  ];

  const calculateTotalSize = () => {
    const osSize = osSelections.filter((o) => o.selected).reduce((sum, o) => sum + o.size_gb, 0);
    const toolSize = toolSelections.filter((t) => t.selected).reduce((sum, t) => sum + t.size_mb, 0) / 1024;
    return osSize + toolSize;
  };

  const handleBuildRecipe = async () => {
    if (!selectedDevice) {
      Alert.alert('Error', 'Please select a USB device');
      return;
    }

    const selectedOSIds = osSelections.filter((o) => o.selected).map((o) => o.id);
    const selectedToolIds = toolSelections.filter((t) => t.selected).map((t) => t.id);

    if (selectedOSIds.length === 0) {
      Alert.alert('Error', 'Please select at least one OS');
      return;
    }

    try {
      const result = await buildRecipeMutation.mutateAsync({
        name: `Multi-Boot USB - ${selectedOSIds.length} OS(es)`,
        deployment_type: 'multi-boot',
        os_selections: selectedOSIds,
        target_device_id: selectedDevice.device_id,
        target_device_size_gb: selectedDevice.size_gb,
        tool_selections: selectedToolIds,
        partition_scheme: 'gpt',
        bootloader_type: 'uefi',
        safety_level: 'high',
      });

      setRecipe(result);
      setCurrentStep('validate');
    } catch (error) {
      Alert.alert('Error', `Failed to build recipe: ${error}`);
    }
  };

  const handleValidateRecipe = async () => {
    if (!recipe || !selectedDevice) return;

    try {
      const result = await validateRecipeMutation.mutateAsync({
        recipe,
        target_device_id: selectedDevice.device_id,
        target_device_size_gb: selectedDevice.size_gb,
      });

      if (!result.valid) {
        Alert.alert('Validation Failed', result.errors.map((e: any) => e.message).join('
'));
        return;
      }

      setCurrentStep('safety');
    } catch (error) {
      Alert.alert('Error', `Validation failed: ${error}`);
    }
  };

  const handleSafetyCheck = async () => {
    if (!recipe || !selectedDevice) return;

    try {
      const result = await safetyCheckMutation.mutateAsync({
        recipe,
        target_device_id: selectedDevice.device_id,
        target_device_path: selectedDevice.path,
      });

      if (!result.safe) {
        Alert.alert('Safety Check Failed', 'This operation is not safe to perform');
        return;
      }

      setCurrentStep('confirm');
    } catch (error) {
      Alert.alert('Error', `Safety check failed: ${error}`);
    }
  };

  const handleStartBuild = async () => {
    if (!recipe || !selectedDevice) return;

    try {
      const result = await startBuildMutation.mutateAsync({
        recipe_id: recipe.recipe_id,
        device_path: selectedDevice.path,
        dry_run: false,
      });

      setBuildId(result.build_id);
      setCurrentStep('building');
    } catch (error) {
      Alert.alert('Error', `Failed to start build: ${error}`);
    }
  };

  return (
    <ScreenContainer className="p-4">
      <ScrollView contentContainerStyle={{ flexGrow: 1 }}>
        <View className="flex-1 gap-6">
          {/* Header */}
          <View className="items-center gap-2">
            <Text className="text-3xl font-bold text-foreground">USB Builder</Text>
            <Text className="text-sm text-muted">Create multi-boot USB recipes</Text>
          </View>

          {/* Progress Steps */}
          <View className="gap-3">
            {steps.map((step, index) => (
              <Pressable
                key={step.id}
                onPress={() => {
                  if (step.completed || steps.slice(0, index).every((s) => s.completed)) {
                    setCurrentStep(step.id);
                  }
                }}
                style={({ pressed }) => [{ opacity: pressed ? 0.7 : 1 }]}
                className={`p-3 rounded-lg flex-row gap-3 ${
                  currentStep === step.id
                    ? 'bg-primary'
                    : step.completed
                      ? 'bg-success/20'
                      : 'bg-surface'
                }`}
              >
                <View className="w-8 h-8 rounded-full items-center justify-center bg-foreground/20">
                  <Text className="text-sm font-bold text-foreground">{index + 1}</Text>
                </View>
                <View className="flex-1">
                  <Text className={`font-semibold ${currentStep === step.id ? 'text-background' : 'text-foreground'}`}>
                    {step.name}
                  </Text>
                  <Text className={`text-xs ${currentStep === step.id ? 'text-background/70' : 'text-muted'}`}>
                    {step.description}
                  </Text>
                </View>
                {step.completed && <Text className="text-success">✓</Text>}
              </Pressable>
            ))}
          </View>

          {/* Step Content */}
          {currentStep === 'os' && (
            <View className="gap-4">
              <Text className="font-semibold text-foreground">Select Operating Systems</Text>
              <FlatList
                scrollEnabled={false}
                data={osSelections}
                keyExtractor={(item) => item.id}
                renderItem={({ item }) => (
                  <Pressable
                    onPress={() => {
                      setOsSelections(
                        osSelections.map((o) =>
                          o.id === item.id ? { ...o, selected: !o.selected } : o,
                        ),
                      );
                    }}
                    style={({ pressed }) => [{ opacity: pressed ? 0.7 : 1 }]}
                    className={`p-3 rounded-lg mb-2 flex-row gap-3 ${
                      item.selected ? 'bg-primary/20 border-2 border-primary' : 'bg-surface border-2 border-border'
                    }`}
                  >
                    <View className="w-6 h-6 rounded-md border-2 border-foreground items-center justify-center">
                      {item.selected && <Text className="text-primary font-bold">✓</Text>}
                    </View>
                    <View className="flex-1">
                      <Text className="font-medium text-foreground">{item.name}</Text>
                      <Text className="text-xs text-muted">{item.version}</Text>
                    </View>
                    <Text className="text-sm text-muted">{item.size_gb.toFixed(1)} GB</Text>
                  </Pressable>
                )}
              />

              <Pressable
                onPress={() => setCurrentStep('tools')}
                style={({ pressed }) => [{ opacity: pressed ? 0.7 : 1 }]}
                className="bg-primary py-3 rounded-lg items-center"
              >
                <Text className="text-background font-semibold">Continue</Text>
              </Pressable>
            </View>
          )}

          {currentStep === 'tools' && (
            <View className="gap-4">
              <Text className="font-semibold text-foreground">Select Boot Tools</Text>
              <FlatList
                scrollEnabled={false}
                data={toolSelections}
                keyExtractor={(item) => item.id}
                renderItem={({ item }) => (
                  <Pressable
                    onPress={() => {
                      setToolSelections(
                        toolSelections.map((t) =>
                          t.id === item.id ? { ...t, selected: !t.selected } : t,
                        ),
                      );
                    }}
                    style={({ pressed }) => [{ opacity: pressed ? 0.7 : 1 }]}
                    className={`p-3 rounded-lg mb-2 flex-row gap-3 ${
                      item.selected ? 'bg-primary/20 border-2 border-primary' : 'bg-surface border-2 border-border'
                    }`}
                  >
                    <View className="w-6 h-6 rounded-md border-2 border-foreground items-center justify-center">
                      {item.selected && <Text className="text-primary font-bold">✓</Text>}
                    </View>
                    <View className="flex-1">
                      <Text className="font-medium text-foreground">{item.name}</Text>
                      <Text className="text-xs text-muted">{item.version}</Text>
                    </View>
                    <Text className="text-sm text-muted">{item.size_mb.toFixed(0)} MB</Text>
                  </Pressable>
                )}
              />

              <Pressable
                onPress={() => setCurrentStep('device')}
                style={({ pressed }) => [{ opacity: pressed ? 0.7 : 1 }]}
                className="bg-primary py-3 rounded-lg items-center"
              >
                <Text className="text-background font-semibold">Continue</Text>
              </Pressable>
            </View>
          )}

          {currentStep === 'device' && (
            <View className="gap-4">
              <Text className="font-semibold text-foreground">Select USB Device</Text>
              <Text className="text-sm text-muted">
                Total size needed: {calculateTotalSize().toFixed(1)} GB
              </Text>

              <View className="bg-surface p-4 rounded-lg gap-2">
                <Text className="font-medium text-foreground">Selected Device</Text>
                {selectedDevice ? (
                  <>
                    <Text className="text-foreground">{selectedDevice.name}</Text>
                    <Text className="text-sm text-muted">
                      {selectedDevice.size_gb.toFixed(1)} GB • {selectedDevice.filesystem}
                    </Text>
                  </>
                ) : (
                  <Text className="text-muted italic">No device selected</Text>
                )}
              </View>

              <Pressable
                onPress={handleBuildRecipe}
                disabled={!selectedDevice || osSelections.every((o) => !o.selected)}
                style={({ pressed }) => [{ opacity: pressed ? 0.7 : 1 }]}
                className="bg-primary py-3 rounded-lg items-center disabled:opacity-50"
              >
                <Text className="text-background font-semibold">Build Recipe</Text>
              </Pressable>
            </View>
          )}

          {currentStep === 'validate' && (
            <View className="gap-4">
              <Text className="font-semibold text-foreground">Validate Recipe</Text>
              {buildRecipeMutation.isPending ? (
                <View className="items-center gap-4 py-8">
                  <ActivityIndicator size="large" color="#0a7ea4" />
                  <Text className="text-muted">Building recipe...</Text>
                </View>
              ) : recipe ? (
                <View className="bg-surface p-4 rounded-lg gap-3">
                  <View className="flex-row justify-between">
                    <Text className="text-muted">Recipe ID:</Text>
                    <Text className="font-mono text-xs text-foreground">{recipe.recipe_id.slice(0, 8)}...</Text>
                  </View>
                  <View className="flex-row justify-between">
                    <Text className="text-muted">Type:</Text>
                    <Text className="text-foreground">{recipe.deployment_type}</Text>
                  </View>
                  <View className="flex-row justify-between">
                    <Text className="text-muted">Partitions:</Text>
                    <Text className="text-foreground">{recipe.partitions.length}</Text>
                  </View>
                </View>
              ) : null}

              <Pressable
                onPress={handleValidateRecipe}
                disabled={validateRecipeMutation.isPending}
                style={({ pressed }) => [{ opacity: pressed ? 0.7 : 1 }]}
                className="bg-primary py-3 rounded-lg items-center disabled:opacity-50"
              >
                <Text className="text-background font-semibold">
                  {validateRecipeMutation.isPending ? 'Validating...' : 'Validate Recipe'}
                </Text>
              </Pressable>
            </View>
          )}

          {currentStep === 'safety' && (
            <View className="gap-4">
              <Text className="font-semibold text-foreground">Safety Check</Text>
              <View className="bg-warning/10 p-4 rounded-lg gap-2">
                <Text className="font-semibold text-warning">⚠️ Destructive Operation</Text>
                <Text className="text-sm text-foreground">
                  This will erase all data on the selected USB device. Please confirm you want to proceed.
                </Text>
              </View>

              <Pressable
                onPress={handleSafetyCheck}
                disabled={safetyCheckMutation.isPending}
                style={({ pressed }) => [{ opacity: pressed ? 0.7 : 1 }]}
                className="bg-primary py-3 rounded-lg items-center disabled:opacity-50"
              >
                <Text className="text-background font-semibold">
                  {safetyCheckMutation.isPending ? 'Checking...' : 'Run Safety Check'}
                </Text>
              </Pressable>
            </View>
          )}

          {currentStep === 'confirm' && (
            <View className="gap-4">
              <Text className="font-semibold text-foreground">Confirm & Start Build</Text>
              <View className="bg-surface p-4 rounded-lg gap-3">
                <View className="gap-2">
                  <Text className="text-muted text-xs">OPERATING SYSTEMS</Text>
                  {osSelections
                    .filter((o) => o.selected)
                    .map((o) => (
                      <Text key={o.id} className="text-foreground">
                        • {o.name} {o.version}
                      </Text>
                    ))}
                </View>
                <View className="h-px bg-border" />
                <View className="gap-2">
                  <Text className="text-muted text-xs">BOOT TOOLS</Text>
                  {toolSelections
                    .filter((t) => t.selected)
                    .map((t) => (
                      <Text key={t.id} className="text-foreground">
                        • {t.name} {t.version}
                      </Text>
                    ))}
                </View>
                <View className="h-px bg-border" />
                <View className="flex-row justify-between">
                  <Text className="text-muted">Target Device:</Text>
                  <Text className="text-foreground font-medium">{selectedDevice?.name}</Text>
                </View>
              </View>

              <Pressable
                onPress={handleStartBuild}
                disabled={startBuildMutation.isPending}
                style={({ pressed }) => [{ opacity: pressed ? 0.7 : 1 }]}
                className="bg-primary py-3 rounded-lg items-center disabled:opacity-50"
              >
                <Text className="text-background font-semibold">
                  {startBuildMutation.isPending ? 'Starting...' : 'Start Build'}
                </Text>
              </Pressable>
            </View>
          )}

          {currentStep === 'building' && buildProgress && (
            <View className="gap-4">
              <Text className="font-semibold text-foreground">Building USB</Text>
              <View className="bg-surface p-4 rounded-lg gap-4">
                <View className="gap-2">
                  <View className="flex-row justify-between">
                    <Text className="text-muted">Progress</Text>
                    <Text className="font-semibold text-foreground">{buildProgress.overall_progress.toFixed(0)}%</Text>
                  </View>
                  <View className="h-2 bg-border rounded-full overflow-hidden">
                    <View
                      className="h-full bg-primary"
                      style={{ width: `${buildProgress.overall_progress}%` }}
                    />
                  </View>
                </View>

                <View className="gap-2">
                  <Text className="text-muted text-xs">{buildProgress.current_operation}</Text>
                  <View className="flex-row justify-between">
                    <Text className="text-sm text-muted">Speed: {buildProgress.speed_mbps.toFixed(1)} MB/s</Text>
                    <Text className="text-sm text-muted">ETA: {Math.ceil(buildProgress.eta_seconds / 60)}m</Text>
                  </View>
                </View>
              </View>
            </View>
          )}
        </View>
      </ScrollView>
    </ScreenContainer>
  );
}
