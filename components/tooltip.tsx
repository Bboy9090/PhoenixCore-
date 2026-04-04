import { Text, View, Pressable, Modal, ActivityIndicator } from 'react-native';
import { useState } from 'react';
import { useColors } from '@/hooks/use-colors';
import { cn } from '@/lib/utils';

export interface TooltipProps {
  id: string;
  title: string;
  description: string;
  icon?: string;
  learnMoreUrl?: string;
  children: React.ReactNode;
  position?: 'top' | 'bottom' | 'center';
}

/**
 * Tooltip component that shows help text on tap
 */
export function Tooltip({
  id,
  title,
  description,
  icon,
  learnMoreUrl,
  children,
  position = 'center',
}: TooltipProps) {
  const colors = useColors();
  const [visible, setVisible] = useState(false);

  return (
    <>
      <Pressable onPress={() => setVisible(true)}>
        {children}
      </Pressable>

      <Modal
        visible={visible}
        transparent
        animationType="fade"
        onRequestClose={() => setVisible(false)}
      >
        <Pressable
          className="flex-1 items-center justify-center bg-black/50"
          onPress={() => setVisible(false)}
        >
          <Pressable
            className="w-11/12 max-w-sm rounded-2xl bg-surface p-6"
            onPress={(e) => e.stopPropagation()}
          >
            {/* Icon */}
            {icon && (
              <Text className="mb-3 text-center text-4xl">{icon}</Text>
            )}

            {/* Title */}
            <Text className="mb-2 text-center text-lg font-bold text-foreground">
              {title}
            </Text>

            {/* Description */}
            <Text className="mb-4 text-center text-sm text-muted leading-relaxed">
              {description}
            </Text>

            {/* Learn More Link */}
            {learnMoreUrl && (
              <Pressable className="mb-4 items-center py-2">
                <Text className="text-sm font-semibold text-primary">
                  Learn More →
                </Text>
              </Pressable>
            )}

            {/* Close Button */}
            <Pressable
              className="rounded-full bg-primary py-3"
              onPress={() => setVisible(false)}
            >
              <Text className="text-center font-semibold text-background">
                Got It
              </Text>
            </Pressable>
          </Pressable>
        </Pressable>
      </Modal>
    </>
  );
}

/**
 * Info badge that shows a tooltip on tap
 */
export function InfoBadge({
  title,
  description,
  icon = 'ℹ️',
}: {
  title: string;
  description: string;
  icon?: string;
}) {
  return (
    <Tooltip
      id={`info-${title}`}
      title={title}
      description={description}
      icon={icon}
    >
      <View className="rounded-full bg-blue-100 p-2">
        <Text className="text-lg">{icon}</Text>
      </View>
    </Tooltip>
  );
}

/**
 * Help text with tooltip
 */
export function HelpText({
  text,
  title,
  description,
}: {
  text: string;
  title: string;
  description: string;
}) {
  return (
    <Tooltip
      id={`help-${title}`}
      title={title}
      description={description}
      icon="❓"
    >
      <Text className="text-sm text-blue-600 underline">{text}</Text>
    </Tooltip>
  );
}
