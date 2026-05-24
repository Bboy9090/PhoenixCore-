/**
 * Real-Time Installation Progress Display Component
 * Shows live progress with component status, speed, and ETA
 */

import React, { useEffect } from 'react';
import { View, Text, ScrollView } from 'react-native';
import { ScreenContainer } from '@/components/screen-container';
import {
  useInstallationProgress,
  useProgressPercentage,
  useETA,
  useFormattedSpeed,
  type InstallationProgress
} from '@/lib/hooks/use-installation-progress';


interface InstallationProgressScreenProps {
  installationId: string;
  onComplete?: () => void;
  onError?: (error: string) => void;
}

/**
 * Component for displaying a single component's progress
 */
function ComponentProgressItem({
  name,
  status,
  progress
}: {
  name: string;
  status: 'pending' | 'in_progress' | 'completed' | 'failed';
  progress: number;
}) {
  const statusColors = {
    pending: '#999999',
    in_progress: '#3498db',
    completed: '#2ecc71',
    failed: '#e74c3c'
  };

  const statusText = {
    pending: 'Pending',
    in_progress: 'Installing...',
    completed: 'Completed',
    failed: 'Failed'
  };

  return (
    <View className="mb-4 p-4 bg-surface rounded-lg border border-border">
      <View className="flex-row justify-between items-center mb-2">
        <Text className="text-sm font-semibold text-foreground">{name}</Text>
        <Text
          className="text-xs font-medium"
          style={{ color: statusColors[status] }}
        >
          {statusText[status]}
        </Text>
      </View>

      <View className="w-full h-2 bg-border rounded-full overflow-hidden">
        <View
          className="h-full bg-primary rounded-full"
          style={{ width: `${progress}%` }}
        />
      </View>

      <Text className="text-xs text-muted mt-1">{progress}%</Text>
    </View>
  );
}

/**
 * Main installation progress screen
 */
export default function InstallationProgressScreen({
  installationId,
  onComplete,
  onError
}: InstallationProgressScreenProps) {
  const {
    progress,
    isConnected,
    error,
    subscribe,
    unsubscribe,
    isLoading
  } = useInstallationProgress({
    autoConnect: true
  });

  const { percentage, displayText } = useProgressPercentage(progress);
  const { etaText } = useETA(progress);
  const speedText = useFormattedSpeed(progress);

  // Subscribe to installation on mount
  useEffect(() => {
    if (isConnected) {
      subscribe(installationId);
    }

    return () => {
      unsubscribe(installationId);
    };
  }, [isConnected, installationId, subscribe, unsubscribe]);

  // Handle completion
  useEffect(() => {
    if (progress?.status === 'completed' && onComplete) {
      onComplete();
    }
  }, [progress?.status, onComplete]);

  // Handle errors
  useEffect(() => {
    if (progress?.status === 'error' && progress.error_message && onError) {
      onError(progress.error_message);
    }
  }, [progress?.status, progress?.error_message, onError]);

  if (!isConnected || isLoading) {
    return (
      <ScreenContainer className="justify-center items-center">
        <Text className="text-lg font-semibold text-foreground mb-2">
          Connecting...
        </Text>
        <Text className="text-sm text-muted">
          Establishing real-time connection
        </Text>
      </ScreenContainer>
    );
  }

  if (error && !progress) {
    return (
      <ScreenContainer className="justify-center items-center">
        <Text className="text-lg font-semibold text-error mb-2">
          Connection Error
        </Text>
        <Text className="text-sm text-muted text-center">{error}</Text>
      </ScreenContainer>
    );
  }

  if (!progress) {
    return (
      <ScreenContainer className="justify-center items-center">
        <Text className="text-lg font-semibold text-foreground mb-2">
          No Installation Data
        </Text>
        <Text className="text-sm text-muted">
          Installation ID: {installationId}
        </Text>
      </ScreenContainer>
    );
  }

  return (
    <ScreenContainer>
      <ScrollView
        contentContainerStyle={{ flexGrow: 1 }}
        showsVerticalScrollIndicator={false}
      >
        <View className="gap-6">
          {/* Header */}
          <View className="gap-2">
            <Text className="text-2xl font-bold text-foreground">
              Installing Drivers
            </Text>
            <Text className="text-sm text-muted">
              {progress.mac_model}
            </Text>
          </View>

          {/* Overall Progress */}
          <View className="gap-3 p-4 bg-surface rounded-lg border border-border">
            <View className="flex-row justify-between items-center">
              <Text className="text-base font-semibold text-foreground">
                Overall Progress
              </Text>
              <Text className="text-lg font-bold text-primary">
                {displayText}
              </Text>
            </View>

            <View className="w-full h-3 bg-border rounded-full overflow-hidden">
              <View
                className="h-full bg-primary rounded-full"
                style={{ width: `${percentage}%` }}
              />
            </View>

            {/* Stage Info */}
            <View className="flex-row justify-between items-center mt-2">
              <Text className="text-sm text-muted">
                Stage: {progress.stage}
              </Text>
              <Text className="text-sm text-muted">
                {progress.stage_progress}%
              </Text>
            </View>
          </View>

          {/* Current Operation */}
          <View className="p-3 bg-primary/10 rounded-lg border border-primary/20">
            <Text className="text-xs font-semibold text-primary mb-1">
              CURRENT OPERATION
            </Text>
            <Text className="text-sm text-foreground">
              {progress.current_operation}
            </Text>
          </View>

          {/* Speed and ETA */}
          <View className="flex-row gap-3">
            <View className="flex-1 p-3 bg-surface rounded-lg border border-border">
              <Text className="text-xs font-semibold text-muted mb-1">
                SPEED
              </Text>
              <Text className="text-lg font-bold text-foreground">
                {speedText}
              </Text>
            </View>

            <View className="flex-1 p-3 bg-surface rounded-lg border border-border">
              <Text className="text-xs font-semibold text-muted mb-1">
                ETA
              </Text>
              <Text className="text-sm font-semibold text-foreground">
                {etaText}
              </Text>
            </View>
          </View>

          {/* Components */}
          <View className="gap-2">
            <Text className="text-base font-semibold text-foreground">
              Components
            </Text>

            {Object.entries(progress.components).map(([name, comp]) => (
              <ComponentProgressItem
                key={name}
                name={name}
                status={comp.status}
                progress={comp.progress}
              />
            ))}
          </View>

          {/* Status Messages */}
          {progress.status === 'completed' && (
            <View className="p-4 bg-success/10 rounded-lg border border-success/20">
              <Text className="text-base font-semibold text-success">
                ✓ Installation Complete
              </Text>
              <Text className="text-sm text-foreground mt-1">
                All drivers have been successfully installed.
              </Text>
            </View>
          )}

          {progress.status === 'error' && progress.error_message && (
            <View className="p-4 bg-error/10 rounded-lg border border-error/20">
              <Text className="text-base font-semibold text-error">
                ✗ Installation Failed
              </Text>
              <Text className="text-sm text-foreground mt-1">
                {progress.error_message}
              </Text>
            </View>
          )}

          {/* Debug Info */}
          <View className="p-3 bg-muted/10 rounded-lg">
            <Text className="text-xs font-mono text-muted">
              Installation ID: {progress.installation_id}
            </Text>
            <Text className="text-xs font-mono text-muted mt-1">
              Started: {new Date(progress.started_at).toLocaleTimeString()}
            </Text>
            {progress.completed_at && (
              <Text className="text-xs font-mono text-muted mt-1">
                Completed: {new Date(progress.completed_at).toLocaleTimeString()}
              </Text>
            )}
          </View>
        </View>
      </ScrollView>
    </ScreenContainer>
  );
}
