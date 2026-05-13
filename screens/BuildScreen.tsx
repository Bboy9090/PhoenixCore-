/**
 * Phoenix Core - Build Screen
 * USB creation workflow with recipe selection and progress tracking
 */

import React, { useEffect, useState } from 'react';
import {
  View,
  Text,
  ScrollView,
  StyleSheet,
  TouchableOpacity,
  ActivityIndicator,
  Alert,
  Dimensions,
} from 'react-native';
import { Colors, Spacing, Typography, BorderRadius, Shadows, getStatusColor } from '../utils/theme';
import api, { BuildRecipe, BuildProgress, SafetyCheckResponse } from '../services/api';

const { width } = Dimensions.get('window');

type BuildStep = 'recipe' | 'device' | 'safety' | 'building' | 'complete';

export default function BuildScreen() {
  const [step, setStep] = useState<BuildStep>('recipe');
  const [loading, setLoading] = useState(true);
  const [recipes, setRecipes] = useState<BuildRecipe[]>([]);
  const [selectedRecipe, setSelectedRecipe] = useState<BuildRecipe | null>(null);
  const [selectedDevice, setSelectedDevice] = useState<string | null>(null);
  const [safety, setSafety] = useState<SafetyCheckResponse | null>(null);
  const [jobId, setJobId] = useState<string | null>(null);
  const [progress, setProgress] = useState<BuildProgress | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [dryRun, setDryRun] = useState(true);

  useEffect(() => {
    loadRecipes();
  }, []);

  const loadRecipes = async () => {
    try {
      const response = await api.listRecipes();
      setRecipes(response.recipes);
      setLoading(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load recipes');
      setLoading(false);
    }
  };

  const handleSelectRecipe = (recipe: BuildRecipe) => {
    setSelectedRecipe(recipe);
    setStep('device');
  };

  const handleSelectDevice = async (devicePath: string) => {
    setSelectedDevice(devicePath);
    setLoading(true);
    try {
      const safetyResult = await api.safetyCheck(devicePath, selectedRecipe!.id);
      setSafety(safetyResult);
      setStep('safety');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Safety check failed');
    } finally {
      setLoading(false);
    }
  };

  const handleStartBuild = async () => {
    if (!selectedRecipe || !selectedDevice || !safety) return;

    setLoading(true);
    try {
      const result = await api.startBuild({
        recipe_id: selectedRecipe.id,
        target_device_path: selectedDevice,
        dry_run: dryRun,
        confirmation_token: safety.confirmation_token,
      });

      setJobId(result.job_id);
      setStep('building');

      // Poll for progress
      const pollInterval = setInterval(async () => {
        try {
          const progressData = await api.getBuildProgress(result.job_id);
          setProgress(progressData);

          if (progressData.status === 'complete' || progressData.status === 'failed') {
            clearInterval(pollInterval);
            setStep('complete');
          }
        } catch (err) {
          console.error('Progress poll error:', err);
        }
      }, 1000);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Build failed to start');
    } finally {
      setLoading(false);
    }
  };

  if (loading && step === 'recipe') {
    return (
      <View style={styles.container}>
        <ActivityIndicator size="large" color={Colors.accent.primary} />
      </View>
    );
  }

  return (
    <ScrollView style={styles.container}>
      {/* Header */}
      <View style={styles.header}>
        <Text style={styles.headerTitle}>Create Bootable USB</Text>
        <Text style={styles.stepIndicator}>
          Step {['recipe', 'device', 'safety', 'building', 'complete'].indexOf(step) + 1} of 5
        </Text>
      </View>

      {/* Step: Recipe Selection */}
      {step === 'recipe' && (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Choose Operating System</Text>
          {recipes.map((recipe) => (
            <RecipeCard
              key={recipe.id}
              recipe={recipe}
              onSelect={() => handleSelectRecipe(recipe)}
            />
          ))}
        </View>
      )}

      {/* Step: Device Selection */}
      {step === 'device' && selectedRecipe && (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Select USB Device</Text>
          <Text style={styles.recipeInfo}>
            {selectedRecipe.name} • {selectedRecipe.required_size_gb}GB minimum
          </Text>
          <TouchableOpacity
            style={styles.deviceSelectButton}
            onPress={() => {
              // Navigate to device selection
              Alert.alert('Select Device', 'Choose a USB device from the Devices tab');
            }}
          >
            <Text style={styles.deviceSelectButtonText}>
              {selectedDevice ? `Selected: ${selectedDevice}` : 'Select Device'}
            </Text>
          </TouchableOpacity>
          {selectedDevice && (
            <TouchableOpacity
              style={styles.proceedButton}
              onPress={() => handleSelectDevice(selectedDevice)}
            >
              <Text style={styles.proceedButtonText}>Continue →</Text>
            </TouchableOpacity>
          )}
        </View>
      )}

      {/* Step: Safety Check */}
      {step === 'safety' && safety && (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Safety Check</Text>

          {/* Risk Assessment */}
          <View style={styles.riskCard}>
            <Text style={styles.riskLabel}>Risk Level</Text>
            <Text style={[styles.riskValue, { color: getRiskColor(safety.risk_level) }]}>
              {safety.risk_level.toUpperCase()}
            </Text>
          </View>

          {/* Warnings */}
          {safety.warnings.length > 0 && (
            <View style={styles.warningsSection}>
              <Text style={styles.warningsTitle}>⚠️ Warnings</Text>
              {safety.warnings.map((warning, idx) => (
                <Text key={idx} style={styles.warningItem}>
                  • {warning}
                </Text>
              ))}
            </View>
          )}

          {/* Errors */}
          {safety.errors.length > 0 && (
            <View style={styles.errorsSection}>
              <Text style={styles.errorsTitle}>❌ Errors</Text>
              {safety.errors.map((error, idx) => (
                <Text key={idx} style={styles.errorItem}>
                  • {error}
                </Text>
              ))}
            </View>
          )}

          {/* Device Info */}
          {safety.device_info && (
            <View style={styles.deviceInfoCard}>
              <Text style={styles.deviceInfoTitle}>Device Information</Text>
              <Text style={styles.deviceInfoText}>
                {safety.device_info.friendly_name}
              </Text>
              <Text style={styles.deviceInfoText}>
                {safety.device_info.size_human} • {safety.device_info.filesystem}
              </Text>
            </View>
          )}

          {/* Dry Run Toggle */}
          <TouchableOpacity
            style={styles.dryRunToggle}
            onPress={() => setDryRun(!dryRun)}
          >
            <Text style={styles.dryRunLabel}>
              {dryRun ? '✓' : '○'} Dry Run Mode (Simulation)
            </Text>
          </TouchableOpacity>

          {/* Start Button */}
          <TouchableOpacity
            style={[
              styles.startButton,
              safety.errors.length > 0 && styles.startButtonDisabled,
            ]}
            onPress={handleStartBuild}
            disabled={safety.errors.length > 0}
          >
            <Text style={styles.startButtonText}>
              {dryRun ? '🔄 Start Dry Run' : '⚡ Start Build'}
            </Text>
          </TouchableOpacity>
        </View>
      )}

      {/* Step: Building */}
      {step === 'building' && progress && (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Building USB...</Text>

          {/* Progress Bar */}
          <View style={styles.progressContainer}>
            <View style={styles.progressBar}>
              <View
                style={[
                  styles.progressBarFill,
                  { width: `${progress.progress_percent}%` },
                ]}
              />
            </View>
            <Text style={styles.progressPercent}>{progress.progress_percent.toFixed(1)}%</Text>
          </View>

          {/* Current Step */}
          <View style={styles.currentStepCard}>
            <Text style={styles.currentStepLabel}>Current Step</Text>
            <Text style={styles.currentStepValue}>{progress.current_step}</Text>
            <Text style={styles.stepsInfo}>
              {progress.steps_completed} of {progress.steps_total} steps
            </Text>
          </View>

          {/* Speed & Time */}
          {progress.speed_mbps && (
            <View style={styles.statsGrid}>
              <StatCard label="Speed" value={`${progress.speed_mbps.toFixed(1)} MB/s`} />
              <StatCard label="Elapsed" value={`${progress.elapsed_seconds.toFixed(0)}s`} />
            </View>
          )}

          {/* Logs */}
          {progress.log_messages.length > 0 && (
            <View style={styles.logsSection}>
              <Text style={styles.logsTitle}>Build Log</Text>
              <View style={styles.logsList}>
                {progress.log_messages.slice(-10).map((msg, idx) => (
                  <Text key={idx} style={styles.logItem}>
                    {msg}
                  </Text>
                ))}
              </View>
            </View>
          )}

          {/* Error */}
          {progress.error && (
            <View style={styles.buildErrorCard}>
              <Text style={styles.buildErrorText}>❌ {progress.error}</Text>
            </View>
          )}
        </View>
      )}

      {/* Step: Complete */}
      {step === 'complete' && progress && (
        <View style={styles.section}>
          <View style={styles.completeCard}>
            <Text style={styles.completeIcon}>
              {progress.status === 'complete' ? '✅' : '❌'}
            </Text>
            <Text style={styles.completeTitle}>
              {progress.status === 'complete' ? 'Build Complete!' : 'Build Failed'}
            </Text>
            <Text style={styles.completeMessage}>
              {progress.status === 'complete'
                ? 'Your USB drive is ready to use'
                : progress.error || 'Build did not complete successfully'}
            </Text>
          </View>

          <TouchableOpacity
            style={styles.restartButton}
            onPress={() => {
              setStep('recipe');
              setSelectedRecipe(null);
              setSelectedDevice(null);
              setSafety(null);
              setJobId(null);
              setProgress(null);
            }}
          >
            <Text style={styles.restartButtonText}>Create Another USB</Text>
          </TouchableOpacity>
        </View>
      )}

      {/* Error Message */}
      {error && (
        <View style={styles.errorCard}>
          <Text style={styles.errorText}>⚠️ {error}</Text>
        </View>
      )}

      <View style={{ height: Spacing.xl }} />
    </ScrollView>
  );
}

interface RecipeCardProps {
  recipe: BuildRecipe;
  onSelect: () => void;
}

function RecipeCard({ recipe, onSelect }: RecipeCardProps) {
  return (
    <TouchableOpacity style={styles.recipeCard} onPress={onSelect}>
      <View style={styles.recipeHeader}>
        <Text style={styles.recipeName}>{recipe.name}</Text>
        <Text style={styles.recipeArrow}>→</Text>
      </View>
      <Text style={styles.recipeDescription}>{recipe.description}</Text>
      <View style={styles.recipeDetails}>
        <RecipeDetailBadge label="Size" value={`${recipe.required_size_gb}GB`} />
        <RecipeDetailBadge label="Time" value={`~${recipe.estimated_time_minutes}m`} />
        {recipe.supports_oclp && <RecipeDetailBadge label="OCLP" value="✓" />}
      </View>
    </TouchableOpacity>
  );
}

interface RecipeDetailBadgeProps {
  label: string;
  value: string;
}

function RecipeDetailBadge({ label, value }: RecipeDetailBadgeProps) {
  return (
    <View style={styles.recipeDetailBadge}>
      <Text style={styles.recipeDetailLabel}>{label}:</Text>
      <Text style={styles.recipeDetailValue}>{value}</Text>
    </View>
  );
}

interface StatCardProps {
  label: string;
  value: string;
}

function StatCard({ label, value }: StatCardProps) {
  return (
    <View style={styles.statCard}>
      <Text style={styles.statLabel}>{label}</Text>
      <Text style={styles.statValue}>{value}</Text>
    </View>
  );
}

function getRiskColor(risk: string): string {
  switch (risk) {
    case 'low': return Colors.status.success;
    case 'medium': return Colors.status.warning;
    case 'high': return Colors.status.error;
    case 'critical': return Colors.status.error;
    default: return Colors.text.tertiary;
  }
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: Colors.bg.primary,
  },
  header: {
    padding: Spacing.xl,
    paddingBottom: Spacing.base,
  },
  headerTitle: {
    fontSize: Typography.size['2xl'],
    fontWeight: Typography.weight.bold,
    color: Colors.text.primary,
    marginBottom: Spacing.sm,
  },
  stepIndicator: {
    fontSize: Typography.size.sm,
    color: Colors.text.tertiary,
  },
  section: {
    padding: Spacing.base,
    gap: Spacing.md,
  },
  sectionTitle: {
    fontSize: Typography.size.lg,
    fontWeight: Typography.weight.bold,
    color: Colors.text.primary,
    marginBottom: Spacing.sm,
  },
  recipeInfo: {
    fontSize: Typography.size.sm,
    color: Colors.text.tertiary,
    marginBottom: Spacing.md,
  },
  recipeCard: {
    backgroundColor: Colors.bg.card,
    borderRadius: BorderRadius.lg,
    borderWidth: 1,
    borderColor: Colors.border.accent,
    padding: Spacing.base,
    marginBottom: Spacing.md,
    ...Shadows.md,
  },
  recipeHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: Spacing.sm,
  },
  recipeName: {
    fontSize: Typography.size.md,
    fontWeight: Typography.weight.bold,
    color: Colors.accent.primary,
  },
  recipeArrow: {
    fontSize: Typography.size.lg,
    color: Colors.accent.primary,
  },
  recipeDescription: {
    fontSize: Typography.size.sm,
    color: Colors.text.secondary,
    marginBottom: Spacing.md,
    lineHeight: 20,
  },
  recipeDetails: {
    flexDirection: 'row',
    gap: Spacing.sm,
    flexWrap: 'wrap',
  },
  recipeDetailBadge: {
    backgroundColor: Colors.bg.tertiary,
    paddingHorizontal: Spacing.sm,
    paddingVertical: Spacing.xs,
    borderRadius: BorderRadius.sm,
    flexDirection: 'row',
    gap: Spacing.xs,
  },
  recipeDetailLabel: {
    fontSize: Typography.size.xs,
    color: Colors.text.tertiary,
  },
  recipeDetailValue: {
    fontSize: Typography.size.xs,
    fontWeight: Typography.weight.semibold,
    color: Colors.accent.primary,
  },
  deviceSelectButton: {
    padding: Spacing.base,
    backgroundColor: Colors.bg.card,
    borderRadius: BorderRadius.md,
    borderWidth: 2,
    borderColor: Colors.border.accent,
    marginBottom: Spacing.md,
  },
  deviceSelectButtonText: {
    fontSize: Typography.size.md,
    color: Colors.accent.primary,
    fontWeight: Typography.weight.semibold,
    textAlign: 'center',
  },
  proceedButton: {
    padding: Spacing.base,
    backgroundColor: Colors.accent.primary,
    borderRadius: BorderRadius.md,
    marginBottom: Spacing.md,
  },
  proceedButtonText: {
    color: Colors.bg.primary,
    fontWeight: Typography.weight.bold,
    fontSize: Typography.size.md,
    textAlign: 'center',
  },
  riskCard: {
    backgroundColor: Colors.bg.card,
    borderRadius: BorderRadius.md,
    padding: Spacing.base,
    marginBottom: Spacing.md,
    borderWidth: 1,
    borderColor: Colors.border.default,
  },
  riskLabel: {
    fontSize: Typography.size.sm,
    color: Colors.text.tertiary,
    marginBottom: Spacing.xs,
  },
  riskValue: {
    fontSize: Typography.size.xl,
    fontWeight: Typography.weight.bold,
  },
  warningsSection: {
    backgroundColor: Colors.status.warningBg,
    borderRadius: BorderRadius.md,
    padding: Spacing.base,
    marginBottom: Spacing.md,
    borderWidth: 1,
    borderColor: Colors.status.warning,
  },
  warningsTitle: {
    fontSize: Typography.size.md,
    fontWeight: Typography.weight.bold,
    color: Colors.status.warning,
    marginBottom: Spacing.sm,
  },
  warningItem: {
    fontSize: Typography.size.sm,
    color: Colors.status.warning,
    marginBottom: Spacing.xs,
  },
  errorsSection: {
    backgroundColor: Colors.status.errorBg,
    borderRadius: BorderRadius.md,
    padding: Spacing.base,
    marginBottom: Spacing.md,
    borderWidth: 1,
    borderColor: Colors.status.error,
  },
  errorsTitle: {
    fontSize: Typography.size.md,
    fontWeight: Typography.weight.bold,
    color: Colors.status.error,
    marginBottom: Spacing.sm,
  },
  errorItem: {
    fontSize: Typography.size.sm,
    color: Colors.status.error,
    marginBottom: Spacing.xs,
  },
  deviceInfoCard: {
    backgroundColor: Colors.bg.card,
    borderRadius: BorderRadius.md,
    padding: Spacing.base,
    marginBottom: Spacing.md,
    borderWidth: 1,
    borderColor: Colors.border.default,
  },
  deviceInfoTitle: {
    fontSize: Typography.size.sm,
    color: Colors.text.tertiary,
    marginBottom: Spacing.xs,
  },
  deviceInfoText: {
    fontSize: Typography.size.md,
    color: Colors.text.primary,
    fontWeight: Typography.weight.semibold,
    marginBottom: Spacing.xs,
  },
  dryRunToggle: {
    padding: Spacing.base,
    backgroundColor: Colors.bg.card,
    borderRadius: BorderRadius.md,
    borderWidth: 1,
    borderColor: Colors.border.default,
    marginBottom: Spacing.md,
  },
  dryRunLabel: {
    fontSize: Typography.size.md,
    color: Colors.accent.primary,
    fontWeight: Typography.weight.semibold,
  },
  startButton: {
    padding: Spacing.lg,
    backgroundColor: Colors.accent.primary,
    borderRadius: BorderRadius.md,
    marginBottom: Spacing.md,
  },
  startButtonDisabled: {
    opacity: 0.5,
  },
  startButtonText: {
    color: Colors.bg.primary,
    fontWeight: Typography.weight.bold,
    fontSize: Typography.size.lg,
    textAlign: 'center',
  },
  progressContainer: {
    marginBottom: Spacing.md,
  },
  progressBar: {
    height: 12,
    backgroundColor: Colors.bg.card,
    borderRadius: BorderRadius.full,
    overflow: 'hidden',
    marginBottom: Spacing.sm,
  },
  progressBarFill: {
    height: '100%',
    backgroundColor: Colors.accent.primary,
    borderRadius: BorderRadius.full,
  },
  progressPercent: {
    fontSize: Typography.size.lg,
    fontWeight: Typography.weight.bold,
    color: Colors.accent.primary,
    textAlign: 'center',
  },
  currentStepCard: {
    backgroundColor: Colors.bg.card,
    borderRadius: BorderRadius.md,
    padding: Spacing.base,
    marginBottom: Spacing.md,
    borderWidth: 1,
    borderColor: Colors.border.accent,
  },
  currentStepLabel: {
    fontSize: Typography.size.sm,
    color: Colors.text.tertiary,
    marginBottom: Spacing.xs,
  },
  currentStepValue: {
    fontSize: Typography.size.lg,
    fontWeight: Typography.weight.bold,
    color: Colors.accent.primary,
    marginBottom: Spacing.xs,
  },
  stepsInfo: {
    fontSize: Typography.size.sm,
    color: Colors.text.tertiary,
  },
  statsGrid: {
    flexDirection: 'row',
    gap: Spacing.md,
    marginBottom: Spacing.md,
  },
  statCard: {
    flex: 1,
    backgroundColor: Colors.bg.card,
    borderRadius: BorderRadius.md,
    padding: Spacing.base,
    borderWidth: 1,
    borderColor: Colors.border.default,
  },
  statLabel: {
    fontSize: Typography.size.xs,
    color: Colors.text.tertiary,
    marginBottom: Spacing.xs,
  },
  statValue: {
    fontSize: Typography.size.md,
    fontWeight: Typography.weight.bold,
    color: Colors.accent.primary,
  },
  logsSection: {
    marginBottom: Spacing.md,
  },
  logsTitle: {
    fontSize: Typography.size.md,
    fontWeight: Typography.weight.bold,
    color: Colors.text.primary,
    marginBottom: Spacing.sm,
  },
  logsList: {
    backgroundColor: Colors.bg.card,
    borderRadius: BorderRadius.md,
    padding: Spacing.base,
    borderWidth: 1,
    borderColor: Colors.border.default,
    maxHeight: 200,
  },
  logItem: {
    fontSize: Typography.size.xs,
    color: Colors.text.tertiary,
    fontFamily: 'Courier',
    marginBottom: Spacing.xs,
  },
  buildErrorCard: {
    backgroundColor: Colors.status.errorBg,
    borderRadius: BorderRadius.md,
    padding: Spacing.base,
    borderWidth: 1,
    borderColor: Colors.status.error,
  },
  buildErrorText: {
    color: Colors.status.error,
    fontWeight: Typography.weight.semibold,
  },
  completeCard: {
    backgroundColor: Colors.bg.card,
    borderRadius: BorderRadius.lg,
    padding: Spacing.xl,
    alignItems: 'center',
    borderWidth: 2,
    borderColor: Colors.accent.primary,
    marginBottom: Spacing.lg,
  },
  completeIcon: {
    fontSize: 64,
    marginBottom: Spacing.md,
  },
  completeTitle: {
    fontSize: Typography.size.xl,
    fontWeight: Typography.weight.bold,
    color: Colors.accent.primary,
    marginBottom: Spacing.sm,
    textAlign: 'center',
  },
  completeMessage: {
    fontSize: Typography.size.md,
    color: Colors.text.secondary,
    textAlign: 'center',
  },
  restartButton: {
    padding: Spacing.lg,
    backgroundColor: Colors.accent.primary,
    borderRadius: BorderRadius.md,
  },
  restartButtonText: {
    color: Colors.bg.primary,
    fontWeight: Typography.weight.bold,
    fontSize: Typography.size.md,
    textAlign: 'center',
  },
  errorCard: {
    margin: Spacing.base,
    padding: Spacing.base,
    backgroundColor: Colors.status.errorBg,
    borderRadius: BorderRadius.md,
    borderWidth: 1,
    borderColor: Colors.status.error,
  },
  errorText: {
    color: Colors.status.error,
    fontSize: Typography.size.sm,
    fontWeight: Typography.weight.semibold,
  },
});

