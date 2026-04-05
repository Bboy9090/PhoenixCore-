/**
 * Phoenix Core Enterprise - USB Creation Workflow Screen
 * Complete bootable USB creation with real-time progress tracking
 */

import React, { useEffect, useState, useCallback } from 'react';
import { View, ScrollView, RefreshControl, Alert, ActivityIndicator, TouchableOpacity, Text, Modal, FlatList } from 'react-native';
import { useQuery, useMutation } from '@tanstack/react-query';
import {
  phoenixClient,
  Recipe,
  StorageDevice,
  BuildJob,
  SafetyCheckResult,
} from '@/lib/api/phoenix-enterprise-client';
import { Ionicons } from '@expo/vector-icons';
import * as Progress from 'react-native-progress';

type WorkflowStep = 'recipe-selection' | 'device-selection' | 'safety-check' | 'building' | 'complete';

export default function USBCreateScreen() {
  const [step, setStep] = useState<WorkflowStep>('recipe-selection');
  const [selectedRecipe, setSelectedRecipe] = useState<Recipe | null>(null);
  const [selectedDevice, setSelectedDevice] = useState<StorageDevice | null>(null);
  const [currentJob, setCurrentJob] = useState<BuildJob | null>(null);
  const [showRecipeModal, setShowRecipeModal] = useState(false);
  const [showDeviceModal, setShowDeviceModal] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const { data: hostCaps, isLoading: capsLoading } = useQuery({
    queryKey: ['host-capabilities'],
    queryFn: () => phoenixClient.refreshCapabilities(),
  });
  const usbWriteBlocked = hostCaps != null && !hostCaps.destructiveUsbWriteNative;

  // Query recipes
  const { data: recipes = [], isLoading: recipesLoading } = useQuery({
    queryKey: ['recipes'],
    queryFn: () => phoenixClient.getRecipes(),
    enabled: !usbWriteBlocked,
  });

  // Query USB devices
  const { data: usbDevices = [] } = useQuery({
    queryKey: ['usb-devices'],
    queryFn: () => phoenixClient.getUSBDevices(),
    refetchInterval: 3000,
  });

  // Query build job progress
  const { data: jobProgress } = useQuery({
    queryKey: ['build-job', currentJob?.job_id],
    queryFn: () => (currentJob ? phoenixClient.getBuildProgress(currentJob.job_id) : null),
    refetchInterval: currentJob && currentJob.status === 'running' ? 1000 : undefined,
    enabled: !!currentJob,
  });

  // Safety check mutation
  const needsElevatedConfirmation = (r: SafetyCheckResult) => {
    const lvl = (r.risk_level || '').toLowerCase();
    const overall = String((r.device_risk as { overall_risk?: string } | undefined)?.overall_risk || '').toLowerCase();
    return lvl === 'medium' || lvl === 'high' || overall === 'warning';
  };

  const proceedAfterSafetyOk = (result: SafetyCheckResult) => {
    const path = selectedDevice?.device_id || '';
    const runBuild = () => {
      setStep('building');
      startBuildMutation.mutate();
    };
    if (needsElevatedConfirmation(result)) {
      Alert.alert(
        'Elevated risk',
        `Server risk: ${result.risk_level || 'unknown'}. Warnings:\n${(result.warnings || []).join('\n') || '(none)'}\n\nTarget path: ${path}\n\nThere is no automatic rollback if something goes wrong.`,
        [
          { text: 'Cancel', style: 'cancel', onPress: () => {} },
          {
            text: 'Continue',
            onPress: () =>
              Alert.alert(
                'Final confirmation',
                `You are about to start a destructive write to:\n${path}\n\nType mentally verified: this erases the device.`,
                [
                  { text: 'Cancel', style: 'cancel', onPress: () => {} },
                  { text: 'Erase device', style: 'destructive', onPress: runBuild },
                ]
              ),
          },
        ]
      );
    } else {
      runBuild();
    }
  };

  const safetyCheckMutation = useMutation({
    mutationFn: () => {
      if (!selectedRecipe || !selectedDevice) throw new Error('Recipe and device required');
      return phoenixClient.safetyCheck(selectedDevice.device_id, selectedRecipe.recipe_id);
    },
    onSuccess: (result) => {
      if (result.safe) {
        proceedAfterSafetyOk(result);
      } else {
        Alert.alert(
          'Safety Check Failed',
          `Errors: ${result.errors.join('\n')}\n\nWarnings: ${result.warnings.join('\n')}`,
          [{ text: 'OK' }]
        );
      }
    },
    onError: (error: unknown) => {
      const msg = error instanceof Error ? error.message : 'Safety check failed';
      Alert.alert('Error', msg);
    },
  });

  // Start build mutation
  const startBuildMutation = useMutation({
    mutationFn: () => {
      if (!selectedRecipe || !selectedDevice) throw new Error('Recipe and device required');
      return phoenixClient.startBuild(selectedDevice.device_id, selectedRecipe.recipe_id);
    },
    onSuccess: (job) => {
      setCurrentJob(job);
    },
    onError: (error: unknown) => {
      const msg = error instanceof Error ? error.message : 'Failed to start build';
      Alert.alert('Error', msg);
      setStep('device-selection');
    },
  });

  // Cancel build mutation
  const cancelBuildMutation = useMutation({
    mutationFn: () => {
      if (!currentJob) throw new Error('No job to cancel');
      return phoenixClient.cancelBuild(currentJob.job_id);
    },
    onSuccess: () => {
      Alert.alert('Success', 'Build cancelled');
      resetWorkflow();
    },
    onError: (error: unknown) => {
      const msg = error instanceof Error ? error.message : 'Failed to cancel build';
      Alert.alert('Error', msg);
    },
  });

  // Update job progress
  useEffect(() => {
    if (jobProgress) {
      setCurrentJob(jobProgress);
      if (jobProgress.status === 'completed') {
        setStep('complete');
      } else if (jobProgress.status === 'failed') {
        const stage = jobProgress.failure_stage ? `\nStage: ${jobProgress.failure_stage}` : '';
        const roll = jobProgress.rollback_available
          ? ''
          : '\n\nNo automatic rollback. Re-scan devices on the host, pick a new USB if needed, or use BootForge desktop. Audit: GET /api/audit/jobs/recent on the host.';
        Alert.alert('Build Failed', `${jobProgress.error_message || 'Unknown error'}${stage}${roll}`);
        resetWorkflow();
      }
    }
  }, [jobProgress]);

  const resetWorkflow = () => {
    setStep('recipe-selection');
    setSelectedRecipe(null);
    setSelectedDevice(null);
    setCurrentJob(null);
  };

  const handleSafetyCheck = () => {
    const path = selectedDevice?.device_id || '';
    Alert.alert(
      'Confirm safety check',
      `Request server validation for:\n${path}\n\nRemovable (host scan): ${selectedDevice?.removable ? 'yes' : 'unknown'}\n\nThis does not start the write yet — a second step runs after the server approves.`,
      [
        { text: 'Cancel', onPress: () => {} },
        { text: 'Run safety check', onPress: () => safetyCheckMutation.mutate(), style: 'destructive' },
      ]
    );
  };

  const formatBytes = (bytes: number) => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i];
  };

  const formatTime = (seconds: number) => {
    if (seconds < 60) return `${Math.round(seconds)}s`;
    if (seconds < 3600) return `${Math.round(seconds / 60)}m`;
    return `${Math.round(seconds / 3600)}h`;
  };

  // Recipe Selection Step
  if (step === 'recipe-selection') {
    if (capsLoading) {
      return (
        <View className="flex-1 bg-slate-900 justify-center items-center p-6">
          <ActivityIndicator size="large" color="#00d4ff" />
          <Text className="text-gray-400 mt-4">Checking host capabilities…</Text>
        </View>
      );
    }
    if (usbWriteBlocked) {
      return (
        <ScrollView className="flex-1 bg-slate-900">
          <View className="p-4">
            <Text className="text-white text-2xl font-bold mb-2">USB build unavailable</Text>
            <Text className="text-amber-200 text-base mb-4">
              This computer's Phoenix Core API reports no native destructive USB write path (Linux with dd/parted required for non-dry-run jobs). Remote USB creation is blocked to avoid false success.
            </Text>
            <Text className="text-gray-400 text-sm mb-4">
              Use BootForge on the desktop (`python3 main.py --gui`) on a supported host, or run the API on Linux with parted and dd installed.
            </Text>
            <Text className="text-gray-500 text-xs">
              See GET /api/health → features.destructive_usb_write_native and docs/CAPABILITY_MATRIX.md.
            </Text>
          </View>
        </ScrollView>
      );
    }
    return (
      <ScrollView className="flex-1 bg-slate-900">
        <View className="p-4">
          <Text className="text-white text-2xl font-bold mb-2">Create Bootable USB</Text>
          <Text className="text-gray-400 mb-6">Select an operating system to create a bootable USB drive</Text>

          {recipesLoading ? (
            <ActivityIndicator size="large" color="#00d4ff" />
          ) : (
            <View>
              {recipes.map((recipe) => (
                <TouchableOpacity
                  key={recipe.recipe_id}
                  onPress={() => {
                    setSelectedRecipe(recipe);
                    setStep('device-selection');
                  }}
                  className="bg-slate-800 rounded-lg p-4 mb-3 border border-slate-700 flex-row items-center"
                >
                  <View className="flex-1">
                    <Text className="text-white font-bold text-base">{recipe.name}</Text>
                    <Text className="text-gray-400 text-xs mt-1">{recipe.description}</Text>
                    <View className="flex-row mt-2 gap-4">
                      <Text className="text-cyan-400 text-xs">
                        <Ionicons name="download" size={12} /> {formatBytes(recipe.image_size_mb * 1024 * 1024)}
                      </Text>
                      <Text className="text-orange-400 text-xs">
                        <Ionicons name="timer" size={12} /> ~{formatTime(recipe.estimated_write_time_seconds)}
                      </Text>
                    </View>
                  </View>
                  <Ionicons name="chevron-forward" size={24} color="#00d4ff" />
                </TouchableOpacity>
              ))}
            </View>
          )}
        </View>
      </ScrollView>
    );
  }

  // Device Selection Step
  if (step === 'device-selection') {
    return (
      <ScrollView className="flex-1 bg-slate-900">
        <View className="p-4">
          <TouchableOpacity onPress={() => setStep('recipe-selection')} className="flex-row items-center mb-4">
            <Ionicons name="chevron-back" size={24} color="#00d4ff" />
            <Text className="text-cyan-400 ml-2">Back</Text>
          </TouchableOpacity>

          <Text className="text-white text-2xl font-bold mb-2">Select USB Device</Text>
          <Text className="text-gray-400 mb-4">Choose the USB drive to write {selectedRecipe?.name} to</Text>

          {selectedRecipe && (
            <View className="bg-slate-800 rounded-lg p-4 mb-4 border border-cyan-500">
              <Text className="text-cyan-400 font-bold">{selectedRecipe.name}</Text>
              <Text className="text-gray-400 text-xs mt-1">{selectedRecipe.description}</Text>
            </View>
          )}

          <Text className="text-white font-bold mb-2">Removable drives (host)</Text>
          <Text className="text-gray-500 text-xs mb-2">
            List is removable_only from the API. Check path matches the physical USB.
          </Text>

          {usbDevices.length === 0 ? (
            <View className="bg-slate-800 rounded-lg p-6 items-center border border-slate-700">
              <Ionicons name="warning" size={32} color="#f59e0b" />
              <Text className="text-gray-400 mt-2">No USB drives detected</Text>
              <Text className="text-gray-500 text-xs mt-1">Connect a USB drive and try again</Text>
            </View>
          ) : (
            usbDevices.map((device) => (
              <TouchableOpacity
                key={device.device_id}
                onPress={() => {
                  setSelectedDevice(device);
                  setStep('safety-check');
                }}
                className={`rounded-lg p-4 mb-3 border flex-row items-center ${
                  selectedDevice?.device_id === device.device_id
                    ? 'bg-cyan-900 border-cyan-500'
                    : 'bg-slate-800 border-slate-700'
                }`}
              >
                <View className="flex-1">
                  <Text className="text-white font-bold">{device.device_name}</Text>
                  <Text className="text-amber-200 text-xs font-mono mt-0.5">{device.device_id}</Text>
                  <Text className="text-gray-400 text-xs">{device.vendor} {device.model}</Text>
                  <Text className="text-cyan-400 text-xs mt-1">{formatBytes(device.size_bytes)}</Text>
                  <Text className="text-gray-500 text-xs mt-0.5">
                    Removable: {device.removable ? 'yes' : 'no'} · Risk: {device.health_status}
                  </Text>
                </View>
                <Ionicons name="chevron-forward" size={24} color="#00d4ff" />
              </TouchableOpacity>
            ))
          )}
        </View>
      </ScrollView>
    );
  }

  // Safety Check Step
  if (step === 'safety-check') {
    return (
      <ScrollView className="flex-1 bg-slate-900">
        <View className="p-4">
          <Text className="text-white text-2xl font-bold mb-4">Review Before Creating</Text>

          {selectedRecipe && (
            <View className="bg-slate-800 rounded-lg p-4 mb-4 border border-slate-700">
              <Text className="text-gray-400 text-xs mb-1">Operating System</Text>
              <Text className="text-white font-bold text-lg">{selectedRecipe.name}</Text>
            </View>
          )}

          {selectedDevice && (
            <View className="bg-slate-800 rounded-lg p-4 mb-4 border border-slate-700">
              <Text className="text-gray-400 text-xs mb-1">Target USB Drive</Text>
              <Text className="text-white font-bold text-lg">{selectedDevice.device_name}</Text>
              <Text className="text-amber-200 text-xs font-mono mt-1">{selectedDevice.device_id}</Text>
              <Text className="text-gray-400 text-xs mt-1">{formatBytes(selectedDevice.size_bytes)}</Text>
              <Text className="text-gray-500 text-xs mt-1">
                Removable: {selectedDevice.removable ? 'yes' : 'no'} · Heuristic risk: {selectedDevice.health_status}
              </Text>
            </View>
          )}

          <View className="bg-red-900 rounded-lg p-4 mb-6 border border-red-700">
            <View className="flex-row">
              <Ionicons name="warning" size={20} color="#fca5a5" />
              <View className="flex-1 ml-3">
                <Text className="text-red-200 font-bold">WARNING</Text>
                <Text className="text-red-100 text-xs mt-1">
                  All data on the selected USB drive will be permanently erased. There is no rollback. If the job fails mid-write, treat the stick as suspect and re-image from BootForge on the desktop if unsure.
                </Text>
              </View>
            </View>
          </View>

          <TouchableOpacity
            onPress={() => setStep('device-selection')}
            className="bg-slate-700 rounded-lg py-3 mb-2 items-center"
          >
            <Text className="text-white font-bold">Cancel</Text>
          </TouchableOpacity>

          <TouchableOpacity
            onPress={handleSafetyCheck}
            disabled={safetyCheckMutation.isPending}
            className="bg-cyan-600 rounded-lg py-3 items-center"
          >
            <Text className="text-white font-bold">
              {safetyCheckMutation.isPending ? 'Validating...' : 'Create Bootable USB'}
            </Text>
          </TouchableOpacity>
        </View>
      </ScrollView>
    );
  }

  // Building Step
  if (step === 'building' && currentJob) {
    const progress = currentJob.progress_percent / 100;
    const timeRemaining = currentJob.estimated_time_remaining;

    return (
      <View className="flex-1 bg-slate-900 justify-center items-center p-4">
        <View className="w-full bg-slate-800 rounded-lg p-6 border border-slate-700">
          <Text className="text-white text-2xl font-bold text-center mb-6">Creating Bootable USB</Text>

          {/* Progress Circle */}
          <View className="items-center mb-8">
            <Progress.Circle
              size={200}
              progress={progress}
              color="#00d4ff"
              unfilledColor="#1e293b"
              thickness={8}
              borderWidth={0}
            />
            <Text className="text-white text-3xl font-bold mt-4">{currentJob.progress_percent}%</Text>
          </View>

          {/* Current Step */}
          <View className="bg-slate-900 rounded-lg p-4 mb-4">
            <Text className="text-gray-400 text-xs mb-1">Current Step</Text>
            <Text className="text-cyan-400 font-semibold">{currentJob.current_step}</Text>
          </View>

          {/* Time Remaining */}
          <View className="bg-slate-900 rounded-lg p-4 mb-6">
            <Text className="text-gray-400 text-xs mb-1">Estimated Time Remaining</Text>
            <Text className="text-orange-400 font-semibold">{formatTime(timeRemaining)}</Text>
          </View>

          {/* Cancel Button */}
          <TouchableOpacity
            onPress={() => {
              Alert.alert('Cancel Build', 'Are you sure you want to cancel?', [
                { text: 'No', onPress: () => {} },
                {
                  text: 'Yes',
                  onPress: () => cancelBuildMutation.mutate(),
                  style: 'destructive',
                },
              ]);
            }}
            disabled={cancelBuildMutation.isPending}
            className="bg-red-600 rounded-lg py-3 items-center"
          >
            <Text className="text-white font-bold">
              {cancelBuildMutation.isPending ? 'Cancelling...' : 'Cancel Build'}
            </Text>
          </TouchableOpacity>
        </View>
      </View>
    );
  }

  // Complete Step
  if (step === 'complete') {
    return (
      <View className="flex-1 bg-slate-900 justify-center items-center p-4">
        <View className="w-full bg-slate-800 rounded-lg p-6 border border-green-700 items-center">
          <Ionicons name="checkmark-circle" size={80} color="#10b981" />
          <Text className="text-white text-2xl font-bold mt-4 text-center">USB Created Successfully!</Text>
          <Text className="text-gray-400 text-center mt-2">
            Your bootable USB drive is ready to use. You can now boot from it on any computer.
          </Text>

          <View className="bg-slate-900 rounded-lg p-4 mt-6 w-full">
            <Text className="text-gray-400 text-xs mb-2">Summary</Text>
            <View className="space-y-2">
              <View className="flex-row justify-between">
                <Text className="text-gray-400">OS</Text>
                <Text className="text-white font-semibold">{selectedRecipe?.name}</Text>
              </View>
              <View className="flex-row justify-between">
                <Text className="text-gray-400">Device</Text>
                <Text className="text-white font-semibold">{selectedDevice?.device_name}</Text>
              </View>
              <View className="flex-row justify-between">
                <Text className="text-gray-400">Status</Text>
                <Text className="text-green-400 font-semibold">Completed</Text>
              </View>
            </View>
          </View>

          <TouchableOpacity
            onPress={resetWorkflow}
            className="bg-cyan-600 rounded-lg py-3 items-center w-full mt-6"
          >
            <Text className="text-white font-bold">Create Another USB</Text>
          </TouchableOpacity>
        </View>
      </View>
    );
  }

  return null;
}
