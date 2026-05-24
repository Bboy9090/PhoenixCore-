import { Text, View, Pressable, Modal } from 'react-native';
import { useState } from 'react';
import { useColors } from '@/hooks/use-colors';

export interface ConfirmationDialogProps {
  title: string;
  description: string;
  icon?: string;
  confirmText?: string;
  cancelText?: string;
  isDangerous?: boolean;
  onConfirm: () => void;
  onCancel?: () => void;
  children: React.ReactNode;
}

/**
 * Confirmation dialog that prevents accidental destructive actions
 */
export function ConfirmationDialog({
  title,
  description,
  icon,
  confirmText = 'Confirm',
  cancelText = 'Cancel',
  isDangerous = false,
  onConfirm,
  onCancel,
  children,
}: ConfirmationDialogProps) {
  const colors = useColors();
  const [visible, setVisible] = useState(false);

  const handleConfirm = () => {
    setVisible(false);
    onConfirm();
  };

  const handleCancel = () => {
    setVisible(false);
    onCancel?.();
  };

  return (
    <>
      <Pressable onPress={() => setVisible(true)}>
        {children}
      </Pressable>

      <Modal
        visible={visible}
        transparent
        animationType="fade"
        onRequestClose={handleCancel}
      >
        <Pressable
          className="flex-1 items-center justify-center bg-black/50"
          onPress={handleCancel}
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
            <Text className={`mb-2 text-center text-lg font-bold ${isDangerous ? 'text-error' : 'text-foreground'}`}>
              {title}
            </Text>

            {/* Description */}
            <Text className="mb-6 text-center text-sm text-muted leading-relaxed">
              {description}
            </Text>

            {/* Buttons */}
            <View className="gap-3">
              {/* Confirm Button */}
              <Pressable
                className={`rounded-full py-3 ${isDangerous ? 'bg-error' : 'bg-primary'}`}
                onPress={handleConfirm}
              >
                <Text className="text-center font-semibold text-background">
                  {confirmText}
                </Text>
              </Pressable>

              {/* Cancel Button */}
              <Pressable
                className="rounded-full border border-border py-3"
                onPress={handleCancel}
              >
                <Text className="text-center font-semibold text-foreground">
                  {cancelText}
                </Text>
              </Pressable>
            </View>
          </Pressable>
        </Pressable>
      </Modal>
    </>
  );
}

/**
 * Dangerous action button with confirmation
 */
export function DangerousActionButton({
  title,
  confirmTitle,
  confirmDescription,
  onConfirm,
  children,
}: {
  title: string;
  confirmTitle: string;
  confirmDescription: string;
  onConfirm: () => void;
  children: React.ReactNode;
}) {
  return (
    <ConfirmationDialog
      title={confirmTitle}
      description={confirmDescription}
      icon="⚠️"
      confirmText="Yes, I'm Sure"
      cancelText="Cancel"
      isDangerous
      onConfirm={onConfirm}
    >
      <Pressable className="rounded-full border border-error bg-red-50 py-3">
        <Text className="text-center font-semibold text-error">
          {title}
        </Text>
      </Pressable>
    </ConfirmationDialog>
  );
}
