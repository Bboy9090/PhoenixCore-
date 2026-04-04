import { Text, View, Pressable, Animated } from 'react-native';
import { useEffect, useRef } from 'react';
import { ScreenContainer } from '@/components/screen-container';
import { useColors } from '@/hooks/use-colors';

export interface SuccessScreenProps {
  icon?: string;
  title: string;
  description: string;
  actionText?: string;
  onAction?: () => void;
  secondaryActionText?: string;
  onSecondaryAction?: () => void;
}

/**
 * Success screen with celebration animation
 */
export function SuccessScreen({
  icon = '🎉',
  title,
  description,
  actionText = 'Continue',
  onAction,
  secondaryActionText,
  onSecondaryAction,
}: SuccessScreenProps) {
  const colors = useColors();
  const scaleAnim = useRef(new Animated.Value(0)).current;
  const opacityAnim = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    // Celebration animation
    Animated.sequence([
      Animated.parallel([
        Animated.timing(scaleAnim, {
          toValue: 1,
          duration: 600,
          useNativeDriver: true,
        }),
        Animated.timing(opacityAnim, {
          toValue: 1,
          duration: 400,
          useNativeDriver: true,
        }),
      ]),
    ]).start();
  }, [scaleAnim, opacityAnim]);

  return (
    <ScreenContainer className="items-center justify-center p-6">
      <View className="w-full gap-6">
        {/* Celebration Icon */}
        <Animated.View
          style={{
            transform: [{ scale: scaleAnim }],
            opacity: opacityAnim,
            alignItems: 'center',
          }}
        >
          <Text className="text-7xl">{icon}</Text>
        </Animated.View>

        {/* Title */}
        <View className="items-center gap-2">
          <Text className="text-center text-3xl font-bold text-foreground">
            {title}
          </Text>
          <Text className="text-center text-base text-muted leading-relaxed">
            {description}
          </Text>
        </View>

        {/* Primary Action */}
        {onAction && (
          <Pressable
            className="rounded-full bg-primary py-4"
            onPress={onAction}
          >
            <Text className="text-center font-semibold text-background text-lg">
              {actionText}
            </Text>
          </Pressable>
        )}

        {/* Secondary Action */}
        {secondaryActionText && onSecondaryAction && (
          <Pressable
            className="rounded-full border border-border py-4"
            onPress={onSecondaryAction}
          >
            <Text className="text-center font-semibold text-foreground">
              {secondaryActionText}
            </Text>
          </Pressable>
        )}
      </View>
    </ScreenContainer>
  );
}

/**
 * Error screen with helpful next steps
 */
export function ErrorScreen({
  icon = '❌',
  title,
  description,
  errorDetails,
  actionText = 'Try Again',
  onAction,
  helpText,
}: {
  icon?: string;
  title: string;
  description: string;
  errorDetails?: string;
  actionText?: string;
  onAction?: () => void;
  helpText?: string;
}) {
  const colors = useColors();

  return (
    <ScreenContainer className="items-center justify-center p-6">
      <View className="w-full gap-6">
        {/* Error Icon */}
        <View className="items-center">
          <Text className="text-6xl">{icon}</Text>
        </View>

        {/* Title */}
        <View className="items-center gap-2">
          <Text className="text-center text-2xl font-bold text-error">
            {title}
          </Text>
          <Text className="text-center text-base text-muted leading-relaxed">
            {description}
          </Text>
        </View>

        {/* Error Details */}
        {errorDetails && (
          <View className="rounded-lg bg-red-50 p-4">
            <Text className="text-sm text-red-700">{errorDetails}</Text>
          </View>
        )}

        {/* Help Text */}
        {helpText && (
          <View className="rounded-lg bg-blue-50 p-4">
            <Text className="text-sm text-blue-700">
              <Text className="font-semibold">💡 Tip:</Text> {helpText}
            </Text>
          </View>
        )}

        {/* Action Button */}
        {onAction && (
          <Pressable
            className="rounded-full bg-primary py-4"
            onPress={onAction}
          >
            <Text className="text-center font-semibold text-background text-lg">
              {actionText}
            </Text>
          </Pressable>
        )}

        {/* Help Link */}
        <Pressable className="items-center py-2">
          <Text className="text-sm text-primary underline">
            Get Help →
          </Text>
        </Pressable>
      </View>
    </ScreenContainer>
  );
}

/**
 * Loading screen with progress
 */
export function LoadingScreen({
  icon = '⏳',
  title,
  description,
  progress,
  status,
}: {
  icon?: string;
  title: string;
  description: string;
  progress?: number;
  status?: string;
}) {
  return (
    <ScreenContainer className="items-center justify-center p-6">
      <View className="w-full gap-6">
        {/* Icon */}
        <View className="items-center">
          <Text className="text-6xl">{icon}</Text>
        </View>

        {/* Title */}
        <View className="items-center gap-2">
          <Text className="text-center text-2xl font-bold text-foreground">
            {title}
          </Text>
          <Text className="text-center text-base text-muted">
            {description}
          </Text>
        </View>

        {/* Progress Bar */}
        {progress !== undefined && (
          <View className="gap-2">
            <View className="h-3 w-full overflow-hidden rounded-full bg-border">
              <View
                className="h-full bg-primary"
                style={{ width: `${progress}%` }}
              />
            </View>
            <Text className="text-center text-lg font-bold text-primary">
              {Math.round(progress)}%
            </Text>
          </View>
        )}

        {/* Status */}
        {status && (
          <View className="rounded-lg bg-surface p-4">
            <Text className="text-center text-sm text-muted">{status}</Text>
          </View>
        )}
      </View>
    </ScreenContainer>
  );
}
