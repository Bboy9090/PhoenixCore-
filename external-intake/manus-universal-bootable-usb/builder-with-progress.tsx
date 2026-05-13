import { useState, useEffect } from 'react';
import { ScrollView, Text, View, TouchableOpacity, ActivityIndicator, FlatList } from 'react-native';
import { ScreenContainer } from '@/components/screen-container';
import { useUSBDevices, useBuildRecipe, useStartUSBBuild } from '@/hooks/use-phoenix-api';
import { usePollingProgress } from '@/hooks/use-websocket-progress';
import { useRecipeCache } from '@/hooks/use-recipe-cache';
import { useColors } from '@/hooks/use-colors';

type BuilderStep = 'devices' | 'os-selection' | 'tools' | 'review' | 'building' | 'complete';

const OS_CATALOG = [
  {
    id: 'windows_11',
    name: 'Windows 11',
    size_gb: 5.5,
    family: 'windows',
    description: 'Latest Windows OS',
    icon: '🪟',
  },
  {
    id: 'windows_10',
    name: 'Windows 10',
    size_gb: 4.8,
    family: 'windows',
    description: 'Stable Windows OS',
    icon: '🪟',
  },
  {
    id: 'ubuntu_22_04',
    name: 'Ubuntu 22.04 LTS',
    size_gb: 3.2,
    family: 'linux',
    description: 'Long-term support Linux',
    icon: '🐧',
  },
  {
    id: 'fedora_38',
    name: 'Fedora 38',
    size_gb: 2.8,
    family: 'linux',
    description: 'Cutting-edge Linux',
    icon: '🐧',
  },
  {
    id: 'chromeos_flex',
    name: 'ChromeOS Flex',
    size_gb: 2.1,
    family: 'chromeos',
    description: 'Lightweight Chrome OS',
    icon: '💻',
  },
];

const TOOLS_CATALOG = [
  {
    id: 'gparted',
    name: 'GParted',
    size_gb: 0.8,
    description: 'Partition manager',
  },
  {
    id: 'clonezilla',
    name: 'Clonezilla',
    size_gb: 1.2,
    description: 'Disk cloning tool',
  },
  {
    id: 'memtest',
    name: 'Memtest86+',
    size_gb: 0.05,
    description: 'RAM testing',
  },
  {
    id: 'hirens',
    name: "Hiren's Boot CD",
    size_gb: 0.9,
    description: 'System recovery tools',
  },
];

export default function USBBuilderWithProgressScreen() {
  const colors = useColors();
  const [step, setStep] = useState<BuilderStep>('devices');
  const [selectedDevice, setSelectedDevice] = useState<string | null>(null);
  const [selectedOS, setSelectedOS] = useState<string[]>([]);
  const [selectedTools, setSelectedTools] = useState<string[]>([]);
  const [recipeName, setRecipeName] = useState('');
  const [buildId, setBuildId] = useState<string | null>(null);

  const { data: devices, isLoading: devicesLoading } = useUSBDevices(4);
  const buildRecipeMutation = useBuildRecipe();
  const startBuildMutation = useStartUSBBuild();
  const { progress } = usePollingProgress(buildId);
  const { recipes, saveRecipe, getRecipe } = useRecipeCache();

  const calculateTotalSize = () => {
    let total = 0;
    selectedOS.forEach((osId) => {
      const os = OS_CATALOG.find((o) => o.id === osId);
      if (os) total += os.size_gb;
    });
    selectedTools.forEach((toolId) => {
      const tool = TOOLS_CATALOG.find((t) => t.id === toolId);
      if (tool) total += tool.size_gb;
    });
    return total.toFixed(2);
  };

  const selectedDeviceData = devices?.find((d) => d.device_id === selectedDevice);
  const totalSize = parseFloat(calculateTotalSize());
  const canBuild = selectedDevice && selectedOS.length > 0 && totalSize < (selectedDeviceData?.size_gb || 0);

  const handleBuildRecipe = async () => {
    if (!selectedDevice || selectedOS.length === 0) return;

    try {
      const recipe = await buildRecipeMutation.mutateAsync({
        name: recipeName || `Recipe-${new Date().toISOString().slice(0, 10)}`,
        deploymentType: selectedOS.length > 1 ? 'MULTIBOOT' : 'SINGLE_BOOT',
        osSelections: selectedOS,
        toolSelections: selectedTools,
        targetDeviceId: selectedDevice,
        targetDeviceSizeGb: selectedDeviceData?.size_gb || 32,
      });

      // Cache the recipe
      await saveRecipe(recipe);

      // Start the build
      const build = await startBuildMutation.mutateAsync({
        recipeId: recipe.recipe_id,
        devicePath: selectedDeviceData?.path || '',
        dryRun: false,
        verifyAfterWrite: true,
      });

      setBuildId(build.build_id);
      setStep('building');
    } catch (error) {
      console.error('Build failed:', error);
    }
  };

  const loadSavedRecipe = (recipeId: string) => {
    const recipe = getRecipe(recipeId);
    if (recipe) {
      setRecipeName(recipe.name);
      setSelectedOS(recipe.os_images.map((img) => img.image_id));
      setSelectedTools(recipe.tools);
      setStep('review');
    }
  };

  // Step 1: Device Selection
  const renderDeviceSelection = () => (
    <ScreenContainer className="p-6">
      <ScrollView contentContainerStyle={{ flexGrow: 1 }}>
        <Text className="text-3xl font-bold text-foreground mb-2">Select USB Device</Text>
        <Text className="text-muted mb-6">Choose the USB drive to create your bootable drive</Text>

        {devicesLoading ? (
          <View className="items-center justify-center py-12">
            <ActivityIndicator size="large" color={colors.primary} />
            <Text className="mt-4 text-muted">Scanning USB devices...</Text>
          </View>
        ) : devices && devices.length > 0 ? (
          <FlatList
            scrollEnabled={false}
            data={devices}
            keyExtractor={(item) => item.device_id}
            renderItem={({ item }) => (
              <TouchableOpacity
                onPress={() => setSelectedDevice(item.device_id)}
                className={`p-4 rounded-xl mb-3 border-2 ${
                  selectedDevice === item.device_id
                    ? 'border-primary bg-primary/10'
                    : 'border-border bg-surface'
                }`}
              >
                <View className="flex-row justify-between items-start">
                  <View className="flex-1">
                    <Text className="text-lg font-semibold text-foreground">
                      {item.vendor} {item.model}
                    </Text>
                    <Text className="text-sm text-muted mt-1">
                      {item.size_gb.toFixed(1)} GB • {item.filesystem}
                    </Text>
                    <Text className="text-xs text-muted mt-1">
                      {item.path} • {item.health_status}
                    </Text>
                  </View>
                  {selectedDevice === item.device_id && (
                    <View className="w-6 h-6 rounded-full bg-primary items-center justify-center">
                      <Text className="text-white font-bold">✓</Text>
                    </View>
                  )}
                </View>
              </TouchableOpacity>
            )}
          />
        ) : (
          <View className="items-center justify-center py-12 bg-surface rounded-xl border border-border">
            <Text className="text-2xl mb-2">🔌</Text>
            <Text className="text-foreground font-semibold">No USB Devices Found</Text>
            <Text className="text-muted text-center mt-2">
              Connect a USB drive (at least 4GB) to continue
            </Text>
          </View>
        )}

        <TouchableOpacity
          disabled={!selectedDevice}
          className={`mt-8 py-4 rounded-full items-center ${
            selectedDevice ? 'bg-primary' : 'bg-muted/30'
          }`}
          onPress={() => setStep('os-selection')}
        >
          <Text className={`font-semibold text-lg ${selectedDevice ? 'text-background' : 'text-muted'}`}>
            Continue
          </Text>
        </TouchableOpacity>
      </ScrollView>
    </ScreenContainer>
  );

  // Step 2: OS Selection
  const renderOSSelection = () => (
    <ScreenContainer className="p-6">
      <ScrollView contentContainerStyle={{ flexGrow: 1 }}>
        <Text className="text-3xl font-bold text-foreground mb-2">Select Operating Systems</Text>
        <Text className="text-muted mb-6">
          Choose one or more OSes to include (total: {calculateTotalSize()} GB)
        </Text>

        <FlatList
          scrollEnabled={false}
          data={OS_CATALOG}
          keyExtractor={(item) => item.id}
          renderItem={({ item }) => (
            <TouchableOpacity
              onPress={() => {
                setSelectedOS((prev) =>
                  prev.includes(item.id) ? prev.filter((id) => id !== item.id) : [...prev, item.id]
                );
              }}
              className={`p-4 rounded-xl mb-3 border-2 flex-row items-center ${
                selectedOS.includes(item.id)
                  ? 'border-primary bg-primary/10'
                  : 'border-border bg-surface'
              }`}
            >
              <View className="flex-1">
                <Text className="text-lg font-semibold text-foreground">
                  {item.icon} {item.name}
                </Text>
                <Text className="text-sm text-muted mt-1">{item.description}</Text>
                <Text className="text-xs text-muted mt-1">{item.size_gb} GB</Text>
              </View>
              <View
                className={`w-6 h-6 rounded-lg border-2 items-center justify-center ${
                  selectedOS.includes(item.id)
                    ? 'bg-primary border-primary'
                    : 'border-border bg-surface'
                }`}
              >
                {selectedOS.includes(item.id) && <Text className="text-white font-bold">✓</Text>}
              </View>
            </TouchableOpacity>
          )}
        />

        <View className="flex-row gap-3 mt-8">
          <TouchableOpacity
            className="flex-1 py-4 rounded-full items-center bg-surface border border-border"
            onPress={() => setStep('devices')}
          >
            <Text className="font-semibold text-foreground">Back</Text>
          </TouchableOpacity>
          <TouchableOpacity
            disabled={selectedOS.length === 0}
            className={`flex-1 py-4 rounded-full items-center ${
              selectedOS.length > 0 ? 'bg-primary' : 'bg-muted/30'
            }`}
            onPress={() => setStep('tools')}
          >
            <Text className={`font-semibold ${selectedOS.length > 0 ? 'text-background' : 'text-muted'}`}>
              Next
            </Text>
          </TouchableOpacity>
        </View>
      </ScrollView>
    </ScreenContainer>
  );

  // Step 3: Tools Selection
  const renderToolsSelection = () => (
    <ScreenContainer className="p-6">
      <ScrollView contentContainerStyle={{ flexGrow: 1 }}>
        <Text className="text-3xl font-bold text-foreground mb-2">Add Tools (Optional)</Text>
        <Text className="text-muted mb-6">
          Add repair and diagnostic tools (total: {calculateTotalSize()} GB)
        </Text>

        <FlatList
          scrollEnabled={false}
          data={TOOLS_CATALOG}
          keyExtractor={(item) => item.id}
          renderItem={({ item }) => (
            <TouchableOpacity
              onPress={() => {
                setSelectedTools((prev) =>
                  prev.includes(item.id) ? prev.filter((id) => id !== item.id) : [...prev, item.id]
                );
              }}
              className={`p-4 rounded-xl mb-3 border-2 flex-row items-center ${
                selectedTools.includes(item.id)
                  ? 'border-primary bg-primary/10'
                  : 'border-border bg-surface'
              }`}
            >
              <View className="flex-1">
                <Text className="text-lg font-semibold text-foreground">{item.name}</Text>
                <Text className="text-sm text-muted mt-1">{item.description}</Text>
                <Text className="text-xs text-muted mt-1">{item.size_gb} GB</Text>
              </View>
              <View
                className={`w-6 h-6 rounded-lg border-2 items-center justify-center ${
                  selectedTools.includes(item.id)
                    ? 'bg-primary border-primary'
                    : 'border-border bg-surface'
                }`}
              >
                {selectedTools.includes(item.id) && <Text className="text-white font-bold">✓</Text>}
              </View>
            </TouchableOpacity>
          )}
        />

        <View className="flex-row gap-3 mt-8">
          <TouchableOpacity
            className="flex-1 py-4 rounded-full items-center bg-surface border border-border"
            onPress={() => setStep('os-selection')}
          >
            <Text className="font-semibold text-foreground">Back</Text>
          </TouchableOpacity>
          <TouchableOpacity
            className="flex-1 py-4 rounded-full items-center bg-primary"
            onPress={() => setStep('review')}
          >
            <Text className="font-semibold text-background">Review</Text>
          </TouchableOpacity>
        </View>
      </ScrollView>
    </ScreenContainer>
  );

  // Step 4: Review
  const renderReview = () => (
    <ScreenContainer className="p-6">
      <ScrollView contentContainerStyle={{ flexGrow: 1 }}>
        <Text className="text-3xl font-bold text-foreground mb-6">Review Recipe</Text>

        <View className="bg-surface rounded-xl p-4 mb-4 border border-border">
          <Text className="text-sm text-muted mb-2">USB Device</Text>
          <Text className="text-lg font-semibold text-foreground">
            {selectedDeviceData?.vendor} {selectedDeviceData?.model}
          </Text>
          <Text className="text-sm text-muted mt-1">
            {selectedDeviceData?.size_gb.toFixed(1)} GB • {selectedDeviceData?.path}
          </Text>
        </View>

        <View className="bg-surface rounded-xl p-4 mb-4 border border-border">
          <Text className="text-sm text-muted mb-2">Operating Systems ({selectedOS.length})</Text>
          {selectedOS.map((osId) => {
            const os = OS_CATALOG.find((o) => o.id === osId);
            return (
              <View key={osId} className="flex-row justify-between items-center py-2">
                <Text className="text-foreground">{os?.name}</Text>
                <Text className="text-muted text-sm">{os?.size_gb} GB</Text>
              </View>
            );
          })}
        </View>

        {selectedTools.length > 0 && (
          <View className="bg-surface rounded-xl p-4 mb-4 border border-border">
            <Text className="text-sm text-muted mb-2">Tools ({selectedTools.length})</Text>
            {selectedTools.map((toolId) => {
              const tool = TOOLS_CATALOG.find((t) => t.id === toolId);
              return (
                <View key={toolId} className="flex-row justify-between items-center py-2">
                  <Text className="text-foreground">{tool?.name}</Text>
                  <Text className="text-muted text-sm">{tool?.size_gb} GB</Text>
                </View>
              );
            })}
          </View>
        )}

        <View
          className={`rounded-xl p-4 mb-6 border ${
            canBuild ? 'bg-success/10 border-success' : 'bg-error/10 border-error'
          }`}
        >
          <View className="flex-row justify-between items-center">
            <Text className={canBuild ? 'text-success font-semibold' : 'text-error font-semibold'}>
              Total Size: {calculateTotalSize()} GB
            </Text>
            <Text className={canBuild ? 'text-success text-sm' : 'text-error text-sm'}>
              {canBuild ? '✓ Fits' : '✗ Too Large'}
            </Text>
          </View>
        </View>

        {/* Saved Recipes */}
        {recipes.length > 0 && (
          <View className="bg-surface rounded-xl p-4 mb-6 border border-border">
            <Text className="text-sm text-muted mb-3">Or use a saved recipe:</Text>
            <FlatList
              scrollEnabled={false}
              data={recipes.slice(0, 3)}
              keyExtractor={(item) => item.recipe_id}
              renderItem={({ item }) => (
                <TouchableOpacity
                  onPress={() => loadSavedRecipe(item.recipe_id)}
                  className="py-2 px-3 bg-primary/10 rounded-lg mb-2 border border-primary/20"
                >
                  <Text className="text-sm font-semibold text-foreground">{item.name}</Text>
                  <Text className="text-xs text-muted mt-1">
                    {item.os_images.length} OS • {item.tools.length} tools
                  </Text>
                </TouchableOpacity>
              )}
            />
          </View>
        )}

        <View className="flex-row gap-3">
          <TouchableOpacity
            className="flex-1 py-4 rounded-full items-center bg-surface border border-border"
            onPress={() => setStep('tools')}
          >
            <Text className="font-semibold text-foreground">Back</Text>
          </TouchableOpacity>
          <TouchableOpacity
            disabled={!canBuild || buildRecipeMutation.isPending}
            className={`flex-1 py-4 rounded-full items-center ${
              canBuild ? 'bg-primary' : 'bg-muted/30'
            }`}
            onPress={handleBuildRecipe}
          >
            {buildRecipeMutation.isPending ? (
              <ActivityIndicator size="small" color={colors.background} />
            ) : (
              <Text className={`font-semibold ${canBuild ? 'text-background' : 'text-muted'}`}>
                Build USB
              </Text>
            )}
          </TouchableOpacity>
        </View>
      </ScrollView>
    </ScreenContainer>
  );

  // Step 5: Building with Real-Time Progress
  const renderBuilding = () => (
    <ScreenContainer className="items-center justify-center p-6">
      <View className="w-24 h-24 rounded-full bg-primary/10 items-center justify-center mb-6">
        <ActivityIndicator size="large" color={colors.primary} />
      </View>

      <Text className="text-2xl font-bold text-foreground mb-2">Building USB...</Text>
      <Text className="text-muted text-center mb-8">
        {progress?.current_operation || 'Preparing your bootable drive'}
      </Text>

      {progress && (
        <>
          <View className="w-full bg-surface rounded-full h-2 mb-4 overflow-hidden border border-border">
            <View
              className="h-full bg-primary"
              style={{ width: `${progress.overall_progress}%` }}
            />
          </View>

          <Text className="text-lg font-semibold text-foreground mb-6">
            {progress.overall_progress}%
          </Text>

          <View className="w-full bg-surface rounded-xl p-4 border border-border mb-6">
            <View className="flex-row justify-between mb-3">
              <Text className="text-sm text-muted">Stage</Text>
              <Text className="text-sm font-semibold text-foreground capitalize">
                {progress.stage}
              </Text>
            </View>
            <View className="flex-row justify-between mb-3">
              <Text className="text-sm text-muted">Speed</Text>
              <Text className="text-sm font-semibold text-foreground">
                {progress.speed_mbps.toFixed(1)} MB/s
              </Text>
            </View>
            <View className="flex-row justify-between">
              <Text className="text-sm text-muted">ETA</Text>
              <Text className="text-sm font-semibold text-foreground">
                {Math.ceil(progress.eta_seconds / 60)} min
              </Text>
            </View>
          </View>

          {progress.state === 'complete' && (
            <View className="w-full bg-success/10 rounded-xl p-4 border border-success">
              <Text className="text-center text-success font-semibold">✓ Build Complete!</Text>
            </View>
          )}

          {progress.state === 'error' && (
            <View className="w-full bg-error/10 rounded-xl p-4 border border-error">
              <Text className="text-center text-error font-semibold">✗ Build Failed</Text>
              {progress.error_message && (
                <Text className="text-center text-error text-sm mt-2">{progress.error_message}</Text>
              )}
            </View>
          )}
        </>
      )}
    </ScreenContainer>
  );

  // Render based on current step
  switch (step) {
    case 'devices':
      return renderDeviceSelection();
    case 'os-selection':
      return renderOSSelection();
    case 'tools':
      return renderToolsSelection();
    case 'review':
      return renderReview();
    case 'building':
      return renderBuilding();
    default:
      return renderDeviceSelection();
  }
}
