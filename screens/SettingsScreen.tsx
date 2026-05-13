/**
 * Phoenix Core - Settings Screen
 * Backend configuration, diagnostics, and app settings
 */

import React, { useEffect, useState } from 'react';
import {
  View,
  Text,
  ScrollView,
  StyleSheet,
  TouchableOpacity,
  TextInput,
  ActivityIndicator,
  Alert,
} from 'react-native';
import { Colors, Spacing, Typography, BorderRadius, Shadows } from '../utils/theme';
import api, { DiagnosticsResult } from '../services/api';

export default function SettingsScreen() {
  const [backendUrl, setBackendUrl] = useState(api.getBaseURL());
  const [isConnected, setIsConnected] = useState(false);
  const [testing, setTesting] = useState(false);
  const [diagnostics, setDiagnostics] = useState<DiagnosticsResult | null>(null);
  const [showDiagnostics, setShowDiagnostics] = useState(false);

  useEffect(() => {
    testConnection();
  }, []);

  const testConnection = async () => {
    setTesting(true);
    try {
      const connected = await api.ping();
      setIsConnected(connected);
    } catch (err) {
      setIsConnected(false);
    } finally {
      setTesting(false);
    }
  };

  const handleUpdateBackendUrl = () => {
    if (!backendUrl.startsWith('http')) {
      Alert.alert('Invalid URL', 'URL must start with http:// or https://');
      return;
    }
    api.setBaseURL(backendUrl);
    testConnection();
    Alert.alert('Success', 'Backend URL updated');
  };

  const handleRunDiagnostics = async () => {
    setTesting(true);
    try {
      const result = await api.runDiagnostics();
      setDiagnostics(result);
      setShowDiagnostics(true);
    } catch (err) {
      Alert.alert('Error', 'Failed to run diagnostics');
    } finally {
      setTesting(false);
    }
  };

  return (
    <ScrollView style={styles.container}>
      {/* Header */}
      <View style={styles.header}>
        <Text style={styles.headerTitle}>Settings</Text>
      </View>

      {/* Backend Configuration */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Backend Configuration</Text>

        {/* Connection Status */}
        <View style={styles.statusCard}>
          <View style={styles.statusIndicator}>
            <View
              style={[
                styles.statusDot,
                { backgroundColor: isConnected ? Colors.status.success : Colors.status.error },
              ]}
            />
            <Text style={styles.statusLabel}>
              {isConnected ? 'Connected' : 'Disconnected'}
            </Text>
          </View>
          <TouchableOpacity
            style={styles.testButton}
            onPress={testConnection}
            disabled={testing}
          >
            <Text style={styles.testButtonText}>
              {testing ? '⏳' : '🔄'} Test
            </Text>
          </TouchableOpacity>
        </View>

        {/* Backend URL Input */}
        <View style={styles.inputGroup}>
          <Text style={styles.inputLabel}>Backend URL</Text>
          <TextInput
            style={styles.textInput}
            value={backendUrl}
            onChangeText={setBackendUrl}
            placeholder="http://localhost:8000"
            placeholderTextColor={Colors.text.muted}
          />
          <TouchableOpacity
            style={styles.updateButton}
            onPress={handleUpdateBackendUrl}
          >
            <Text style={styles.updateButtonText}>Update URL</Text>
          </TouchableOpacity>
        </View>
      </View>

      {/* System Diagnostics */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>System Diagnostics</Text>
        <TouchableOpacity
          style={styles.diagnosticsButton}
          onPress={handleRunDiagnostics}
          disabled={testing}
        >
          <Text style={styles.diagnosticsButtonText}>
            {testing ? '⏳ Running...' : '🔧 Run Diagnostics'}
          </Text>
        </TouchableOpacity>
      </View>

      {/* Diagnostics Results */}
      {showDiagnostics && diagnostics && (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Diagnostics Results</Text>

          {/* Overall Status */}
          <View style={styles.diagnosticsCard}>
            <Text style={styles.diagnosticsLabel}>Overall Status</Text>
            <Text
              style={[
                styles.diagnosticsValue,
                {
                  color:
                    diagnostics.overall_status === 'healthy'
                      ? Colors.status.success
                      : Colors.status.warning,
                },
              ]}
            >
              {diagnostics.overall_status.toUpperCase()}
            </Text>
          </View>

          {/* Platform */}
          <View style={styles.diagnosticsCard}>
            <Text style={styles.diagnosticsLabel}>Platform</Text>
            <Text style={styles.diagnosticsValue}>{diagnostics.platform}</Text>
          </View>

          {/* Checks */}
          <View style={styles.checksSection}>
            <Text style={styles.checksTitle}>System Checks</Text>
            {Object.entries(diagnostics.checks).map(([key, value]) => (
              <CheckItem key={key} name={key} data={value} />
            ))}
          </View>
        </View>
      )}

      {/* About */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>About</Text>
        <View style={styles.aboutCard}>
          <Text style={styles.aboutText}>Phoenix Core Mobile</Text>
          <Text style={styles.aboutVersion}>Version 2.0.0</Text>
          <Text style={styles.aboutDescription}>
            Professional cross-platform OS deployment tool with real USB creation capabilities
          </Text>
        </View>
      </View>

      <View style={{ height: Spacing.xl }} />
    </ScrollView>
  );
}

interface CheckItemProps {
  name: string;
  data: any;
}

function CheckItem({ name, data }: CheckItemProps) {
  const isOk = data.status === 'ok' || data.status === 'available';

  return (
    <View style={styles.checkItem}>
      <View style={styles.checkHeader}>
        <Text style={styles.checkIcon}>{isOk ? '✓' : '⚠'}</Text>
        <Text style={styles.checkName}>{name}</Text>
      </View>
      <Text style={styles.checkStatus}>
        {data.status || data.message || 'OK'}
      </Text>
    </View>
  );
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
  },
  section: {
    padding: Spacing.base,
    marginBottom: Spacing.md,
  },
  sectionTitle: {
    fontSize: Typography.size.lg,
    fontWeight: Typography.weight.bold,
    color: Colors.text.primary,
    marginBottom: Spacing.md,
    marginLeft: Spacing.sm,
  },
  statusCard: {
    backgroundColor: Colors.bg.card,
    borderRadius: BorderRadius.md,
    padding: Spacing.base,
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: Spacing.md,
    borderWidth: 1,
    borderColor: Colors.border.default,
    ...Shadows.md,
  },
  statusIndicator: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: Spacing.sm,
  },
  statusDot: {
    width: 12,
    height: 12,
    borderRadius: 6,
  },
  statusLabel: {
    fontSize: Typography.size.md,
    fontWeight: Typography.weight.semibold,
    color: Colors.text.primary,
  },
  testButton: {
    paddingHorizontal: Spacing.md,
    paddingVertical: Spacing.sm,
    backgroundColor: Colors.bg.tertiary,
    borderRadius: BorderRadius.sm,
  },
  testButtonText: {
    fontSize: Typography.size.md,
    fontWeight: Typography.weight.semibold,
    color: Colors.accent.primary,
  },
  inputGroup: {
    marginBottom: Spacing.md,
  },
  inputLabel: {
    fontSize: Typography.size.sm,
    color: Colors.text.tertiary,
    marginBottom: Spacing.sm,
    marginLeft: Spacing.sm,
  },
  textInput: {
    backgroundColor: Colors.bg.card,
    borderRadius: BorderRadius.md,
    borderWidth: 1,
    borderColor: Colors.border.default,
    padding: Spacing.base,
    color: Colors.text.primary,
    fontSize: Typography.size.md,
    marginBottom: Spacing.sm,
  },
  updateButton: {
    backgroundColor: Colors.accent.primary,
    borderRadius: BorderRadius.md,
    padding: Spacing.base,
  },
  updateButtonText: {
    color: Colors.bg.primary,
    fontWeight: Typography.weight.bold,
    fontSize: Typography.size.md,
    textAlign: 'center',
  },
  diagnosticsButton: {
    backgroundColor: Colors.accent.primary,
    borderRadius: BorderRadius.md,
    padding: Spacing.base,
    marginBottom: Spacing.md,
  },
  diagnosticsButtonText: {
    color: Colors.bg.primary,
    fontWeight: Typography.weight.bold,
    fontSize: Typography.size.md,
    textAlign: 'center',
  },
  diagnosticsCard: {
    backgroundColor: Colors.bg.card,
    borderRadius: BorderRadius.md,
    padding: Spacing.base,
    marginBottom: Spacing.md,
    borderWidth: 1,
    borderColor: Colors.border.default,
  },
  diagnosticsLabel: {
    fontSize: Typography.size.sm,
    color: Colors.text.tertiary,
    marginBottom: Spacing.xs,
  },
  diagnosticsValue: {
    fontSize: Typography.size.lg,
    fontWeight: Typography.weight.bold,
    color: Colors.accent.primary,
  },
  checksSection: {
    marginBottom: Spacing.md,
  },
  checksTitle: {
    fontSize: Typography.size.md,
    fontWeight: Typography.weight.bold,
    color: Colors.text.primary,
    marginBottom: Spacing.md,
  },
  checkItem: {
    backgroundColor: Colors.bg.card,
    borderRadius: BorderRadius.md,
    padding: Spacing.base,
    marginBottom: Spacing.sm,
    borderWidth: 1,
    borderColor: Colors.border.default,
  },
  checkHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: Spacing.sm,
    marginBottom: Spacing.xs,
  },
  checkIcon: {
    fontSize: Typography.size.lg,
  },
  checkName: {
    fontSize: Typography.size.md,
    fontWeight: Typography.weight.semibold,
    color: Colors.text.primary,
  },
  checkStatus: {
    fontSize: Typography.size.sm,
    color: Colors.text.tertiary,
    marginLeft: Spacing.lg,
  },
  aboutCard: {
    backgroundColor: Colors.bg.card,
    borderRadius: BorderRadius.md,
    padding: Spacing.base,
    borderWidth: 1,
    borderColor: Colors.border.accent,
    alignItems: 'center',
  },
  aboutText: {
    fontSize: Typography.size.lg,
    fontWeight: Typography.weight.bold,
    color: Colors.accent.primary,
    marginBottom: Spacing.xs,
  },
  aboutVersion: {
    fontSize: Typography.size.sm,
    color: Colors.text.tertiary,
    marginBottom: Spacing.md,
  },
  aboutDescription: {
    fontSize: Typography.size.sm,
    color: Colors.text.secondary,
    textAlign: 'center',
    lineHeight: 20,
  },
});

