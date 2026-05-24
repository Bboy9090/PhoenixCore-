/**
 * Admin Notification Preferences Settings Component
 * Allows admins to configure notification channels, thresholds, and quiet hours
 */

import React, { useState, useEffect } from 'react';
import { View, Text, ScrollView, Pressable, Switch, TextInput } from 'react-native';
import { ScreenContainer } from '@/components/screen-container';

interface NotificationPreferences {
  email_addresses: string[];
  notification_types: {
    installation_started: boolean;
    installation_completed: boolean;
    installation_failed: boolean;
    system_health_warning: boolean;
    system_health_critical: boolean;
    api_health_check: boolean;
  };
  alert_thresholds: {
    error_rate: number;
    api_response_time: number;
    failed_installations: number;
    disk_space: number;
  };
  quiet_hours: {
    enabled: boolean;
    start_time: string;
    end_time: string;
    timezone: string;
  };
  digest_options: {
    daily_digest: boolean;
    weekly_digest: boolean;
    digest_time: string;
  };
  notification_channels: {
    email: boolean;
    dashboard: boolean;
    sms: boolean;
  };
}

interface NotificationPreferencesScreenProps {
  onSave?: (preferences: NotificationPreferences) => void;
  onCancel?: () => void;
}

/**
 * Notification type toggle component
 */
function NotificationTypeToggle({
  label,
  value,
  onChange
}: {
  label: string;
  value: boolean;
  onChange: (value: boolean) => void;
}) {
  return (
    <View className="flex-row justify-between items-center p-3 bg-surface rounded-lg border border-border mb-2">
      <Text className="text-sm font-medium text-foreground">{label}</Text>
      <Switch
        value={value}
        onValueChange={onChange}
        trackColor={{ false: '#999', true: '#3498db' }}
      />
    </View>
  );
}

/**
 * Alert threshold slider component
 */
function ThresholdInput({
  label,
  value,
  unit,
  min,
  max,
  onChange
}: {
  label: string;
  value: number;
  unit: string;
  min: number;
  max: number;
  onChange: (value: number) => void;
}) {
  return (
    <View className="p-3 bg-surface rounded-lg border border-border mb-3">
      <View className="flex-row justify-between items-center mb-2">
        <Text className="text-sm font-medium text-foreground">{label}</Text>
        <Text className="text-sm font-bold text-primary">
          {value}{unit}
        </Text>
      </View>

      <View className="flex-row items-center gap-2">
        <Pressable
          onPress={() => onChange(Math.max(min, value - 1))}
          className="px-3 py-2 bg-primary rounded"
        >
          <Text className="text-white font-bold">−</Text>
        </Pressable>

        <TextInput
          value={String(value)}
          onChangeText={(text) => {
            const num = parseInt(text) || min;
            onChange(Math.min(max, Math.max(min, num)));
          }}
          keyboardType="numeric"
          className="flex-1 p-2 bg-background border border-border rounded text-center text-foreground"
        />

        <Pressable
          onPress={() => onChange(Math.min(max, value + 1))}
          className="px-3 py-2 bg-primary rounded"
        >
          <Text className="text-white font-bold">+</Text>
        </Pressable>
      </View>
    </View>
  );
}

/**
 * Time input component
 */
function TimeInput({
  label,
  value,
  onChange
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
}) {
  return (
    <View className="p-3 bg-surface rounded-lg border border-border mb-3">
      <Text className="text-sm font-medium text-foreground mb-2">{label}</Text>
      <TextInput
        value={value}
        onChangeText={onChange}
        placeholder="HH:MM"
        placeholderTextColor="#999"
        className="p-2 bg-background border border-border rounded text-foreground"
      />
    </View>
  );
}

/**
 * Email input component
 */
function EmailInput({
  emails,
  onAdd,
  onRemove
}: {
  emails: string[];
  onAdd: (email: string) => void;
  onRemove: (index: number) => void;
}) {
  const [newEmail, setNewEmail] = useState('');

  const handleAdd = () => {
    if (newEmail && newEmail.includes('@')) {
      onAdd(newEmail);
      setNewEmail('');
    }
  };

  return (
    <View className="mb-4">
      <Text className="text-sm font-semibold text-foreground mb-2">
        Email Addresses
      </Text>

      {/* Email list */}
      {emails.map((email, index) => (
        <View
          key={index}
          className="flex-row justify-between items-center p-3 bg-surface rounded-lg border border-border mb-2"
        >
          <Text className="text-sm text-foreground">{email}</Text>
          <Pressable
            onPress={() => onRemove(index)}
            className="px-3 py-1 bg-error rounded"
          >
            <Text className="text-white text-xs font-bold">Remove</Text>
          </Pressable>
        </View>
      ))}

      {/* Add new email */}
      <View className="flex-row gap-2">
        <TextInput
          value={newEmail}
          onChangeText={setNewEmail}
          placeholder="admin@example.com"
          placeholderTextColor="#999"
          keyboardType="email-address"
          className="flex-1 p-3 bg-background border border-border rounded text-foreground"
        />
        <Pressable
          onPress={handleAdd}
          className="px-4 py-3 bg-primary rounded"
        >
          <Text className="text-white font-bold">Add</Text>
        </Pressable>
      </View>
    </View>
  );
}

/**
 * Main notification preferences screen
 */
export default function NotificationPreferencesScreen({
  onSave,
  onCancel
}: NotificationPreferencesScreenProps) {
  const [preferences, setPreferences] = useState<NotificationPreferences>({
    email_addresses: ['admin@example.com'],
    notification_types: {
      installation_started: true,
      installation_completed: true,
      installation_failed: true,
      system_health_warning: true,
      system_health_critical: true,
      api_health_check: false
    },
    alert_thresholds: {
      error_rate: 5,
      api_response_time: 5000,
      failed_installations: 3,
      disk_space: 10
    },
    quiet_hours: {
      enabled: false,
      start_time: '22:00',
      end_time: '08:00',
      timezone: 'UTC'
    },
    digest_options: {
      daily_digest: true,
      weekly_digest: false,
      digest_time: '09:00'
    },
    notification_channels: {
      email: true,
      dashboard: true,
      sms: false
    }
  });

  const handleSave = () => {
    if (onSave) {
      onSave(preferences);
    }
  };

  return (
    <ScreenContainer>
      <ScrollView
        contentContainerStyle={{ flexGrow: 1 }}
        showsVerticalScrollIndicator={false}
      >
        <View className="gap-6 pb-6">
          {/* Header */}
          <View className="gap-2">
            <Text className="text-2xl font-bold text-foreground">
              Notification Preferences
            </Text>
            <Text className="text-sm text-muted">
              Configure how you receive installation and system alerts
            </Text>
          </View>

          {/* Email Addresses */}
          <View className="gap-3">
            <Text className="text-base font-semibold text-foreground">
              Email Addresses
            </Text>
            <EmailInput
              emails={preferences.email_addresses}
              onAdd={(email) => {
                setPreferences({
                  ...preferences,
                  email_addresses: [...preferences.email_addresses, email]
                });
              }}
              onRemove={(index) => {
                setPreferences({
                  ...preferences,
                  email_addresses: preferences.email_addresses.filter(
                    (_, i) => i !== index
                  )
                });
              }}
            />
          </View>

          {/* Notification Types */}
          <View className="gap-3">
            <Text className="text-base font-semibold text-foreground">
              Notification Types
            </Text>
            <NotificationTypeToggle
              label="Installation Started"
              value={preferences.notification_types.installation_started}
              onChange={(value) => {
                setPreferences({
                  ...preferences,
                  notification_types: {
                    ...preferences.notification_types,
                    installation_started: value
                  }
                });
              }}
            />
            <NotificationTypeToggle
              label="Installation Completed"
              value={preferences.notification_types.installation_completed}
              onChange={(value) => {
                setPreferences({
                  ...preferences,
                  notification_types: {
                    ...preferences.notification_types,
                    installation_completed: value
                  }
                });
              }}
            />
            <NotificationTypeToggle
              label="Installation Failed"
              value={preferences.notification_types.installation_failed}
              onChange={(value) => {
                setPreferences({
                  ...preferences,
                  notification_types: {
                    ...preferences.notification_types,
                    installation_failed: value
                  }
                });
              }}
            />
            <NotificationTypeToggle
              label="System Health Warning"
              value={preferences.notification_types.system_health_warning}
              onChange={(value) => {
                setPreferences({
                  ...preferences,
                  notification_types: {
                    ...preferences.notification_types,
                    system_health_warning: value
                  }
                });
              }}
            />
            <NotificationTypeToggle
              label="System Health Critical"
              value={preferences.notification_types.system_health_critical}
              onChange={(value) => {
                setPreferences({
                  ...preferences,
                  notification_types: {
                    ...preferences.notification_types,
                    system_health_critical: value
                  }
                });
              }}
            />
            <NotificationTypeToggle
              label="API Health Check"
              value={preferences.notification_types.api_health_check}
              onChange={(value) => {
                setPreferences({
                  ...preferences,
                  notification_types: {
                    ...preferences.notification_types,
                    api_health_check: value
                  }
                });
              }}
            />
          </View>

          {/* Alert Thresholds */}
          <View className="gap-3">
            <Text className="text-base font-semibold text-foreground">
              Alert Thresholds
            </Text>
            <ThresholdInput
              label="Error Rate"
              value={preferences.alert_thresholds.error_rate}
              unit="%"
              min={1}
              max={100}
              onChange={(value) => {
                setPreferences({
                  ...preferences,
                  alert_thresholds: {
                    ...preferences.alert_thresholds,
                    error_rate: value
                  }
                });
              }}
            />
            <ThresholdInput
              label="API Response Time"
              value={preferences.alert_thresholds.api_response_time}
              unit="ms"
              min={100}
              max={30000}
              onChange={(value) => {
                setPreferences({
                  ...preferences,
                  alert_thresholds: {
                    ...preferences.alert_thresholds,
                    api_response_time: value
                  }
                });
              }}
            />
            <ThresholdInput
              label="Failed Installations"
              value={preferences.alert_thresholds.failed_installations}
              unit=""
              min={1}
              max={100}
              onChange={(value) => {
                setPreferences({
                  ...preferences,
                  alert_thresholds: {
                    ...preferences.alert_thresholds,
                    failed_installations: value
                  }
                });
              }}
            />
            <ThresholdInput
              label="Disk Space"
              value={preferences.alert_thresholds.disk_space}
              unit="%"
              min={1}
              max={100}
              onChange={(value) => {
                setPreferences({
                  ...preferences,
                  alert_thresholds: {
                    ...preferences.alert_thresholds,
                    disk_space: value
                  }
                });
              }}
            />
          </View>

          {/* Quiet Hours */}
          <View className="gap-3">
            <View className="flex-row justify-between items-center">
              <Text className="text-base font-semibold text-foreground">
                Quiet Hours
              </Text>
              <Switch
                value={preferences.quiet_hours.enabled}
                onValueChange={(value) => {
                  setPreferences({
                    ...preferences,
                    quiet_hours: {
                      ...preferences.quiet_hours,
                      enabled: value
                    }
                  });
                }}
              />
            </View>

            {preferences.quiet_hours.enabled && (
              <>
                <TimeInput
                  label="Start Time"
                  value={preferences.quiet_hours.start_time}
                  onChange={(value) => {
                    setPreferences({
                      ...preferences,
                      quiet_hours: {
                        ...preferences.quiet_hours,
                        start_time: value
                      }
                    });
                  }}
                />
                <TimeInput
                  label="End Time"
                  value={preferences.quiet_hours.end_time}
                  onChange={(value) => {
                    setPreferences({
                      ...preferences,
                      quiet_hours: {
                        ...preferences.quiet_hours,
                        end_time: value
                      }
                    });
                  }}
                />
              </>
            )}
          </View>

          {/* Digest Options */}
          <View className="gap-3">
            <Text className="text-base font-semibold text-foreground">
              Digest Options
            </Text>
            <NotificationTypeToggle
              label="Daily Digest"
              value={preferences.digest_options.daily_digest}
              onChange={(value) => {
                setPreferences({
                  ...preferences,
                  digest_options: {
                    ...preferences.digest_options,
                    daily_digest: value
                  }
                });
              }}
            />
            <NotificationTypeToggle
              label="Weekly Digest"
              value={preferences.digest_options.weekly_digest}
              onChange={(value) => {
                setPreferences({
                  ...preferences,
                  digest_options: {
                    ...preferences.digest_options,
                    weekly_digest: value
                  }
                });
              }}
            />
            {(preferences.digest_options.daily_digest ||
              preferences.digest_options.weekly_digest) && (
              <TimeInput
                label="Digest Time"
                value={preferences.digest_options.digest_time}
                onChange={(value) => {
                  setPreferences({
                    ...preferences,
                    digest_options: {
                      ...preferences.digest_options,
                      digest_time: value
                    }
                  });
                }}
              />
            )}
          </View>

          {/* Notification Channels */}
          <View className="gap-3">
            <Text className="text-base font-semibold text-foreground">
              Notification Channels
            </Text>
            <NotificationTypeToggle
              label="Email"
              value={preferences.notification_channels.email}
              onChange={(value) => {
                setPreferences({
                  ...preferences,
                  notification_channels: {
                    ...preferences.notification_channels,
                    email: value
                  }
                });
              }}
            />
            <NotificationTypeToggle
              label="Dashboard"
              value={preferences.notification_channels.dashboard}
              onChange={(value) => {
                setPreferences({
                  ...preferences,
                  notification_channels: {
                    ...preferences.notification_channels,
                    dashboard: value
                  }
                });
              }}
            />
            <NotificationTypeToggle
              label="SMS"
              value={preferences.notification_channels.sms}
              onChange={(value) => {
                setPreferences({
                  ...preferences,
                  notification_channels: {
                    ...preferences.notification_channels,
                    sms: value
                  }
                });
              }}
            />
          </View>

          {/* Action Buttons */}
          <View className="flex-row gap-3 mt-4">
            <Pressable
              onPress={onCancel}
              className="flex-1 py-3 bg-muted rounded-lg"
            >
              <Text className="text-center text-foreground font-semibold">
                Cancel
              </Text>
            </Pressable>
            <Pressable
              onPress={handleSave}
              className="flex-1 py-3 bg-primary rounded-lg"
            >
              <Text className="text-center text-white font-semibold">
                Save Preferences
              </Text>
            </Pressable>
          </View>
        </View>
      </ScrollView>
    </ScreenContainer>
  );
}
