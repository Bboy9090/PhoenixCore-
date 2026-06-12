/**
 * Recipe Export — Standalone screen, no required props.
 * Generates a shareable recipe from local state or shows placeholder.
 */
import { useState } from 'react';
import { ScrollView, Text, View, TouchableOpacity } from 'react-native';
import { ScreenContainer } from '@/components/screen-container';
import { useColors } from '@/hooks/use-colors';
import { buildRecipe, scanUSBDevices, SelectedOSItem, SelectedToolItem } from '@/lib/phoenix-engine';

const SAMPLE_OS: SelectedOSItem[] = [
  { id: 'win10', name: 'Windows 10', version: '22H2', sizeGB: 5.8, color: '#0078D4', category: 'windows' },
];
const SAMPLE_TOOLS: SelectedToolItem[] = [
  { id: 'medicat', name: 'MediCat USB', sizeGB: 25, color: '#E53935', category: 'recovery' },
];

export default function RecipeExportScreen() {
  const colors = useColors();
  const [copied, setCopied] = useState(false);

  const devices = scanUSBDevices();
  const recipe = buildRecipe('pc-laptop', devices[0] ?? null, SAMPLE_OS, SAMPLE_TOOLS);

  const recipeJSON = JSON.stringify({
    id: recipe.id,
    name: recipe.name,
    created: recipe.createdAt,
    device: recipe.deviceType,
    target: recipe.targetDevice?.name ?? 'No device',
    os: recipe.selectedOS.map(o => o.name),
    tools: recipe.selectedTools.map(t => t.name),
    totalSizeGB: recipe.totalSizeGB.toFixed(2),
    estimatedMinutes: recipe.estimatedMinutes,
    partitionScheme: recipe.partitionScheme,
    bootloader: recipe.bootloader,
  }, null, 2);

  const handleCopy = async () => {
    try {
      if (typeof navigator !== 'undefined' && navigator.clipboard) {
        await navigator.clipboard.writeText(recipeJSON);
      }
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      /* silently fail on native */
    }
  };

  return (
    <ScreenContainer>
      <ScrollView contentContainerStyle={{ padding: 20, paddingBottom: 40 }} showsVerticalScrollIndicator={false}>
        {/* Header */}
        <View style={{ marginBottom: 24 }}>
          <Text style={{ fontSize: 28, fontWeight: '800', color: colors.primary, marginBottom: 4 }}>
            ⚡ Export Recipe
          </Text>
          <Text style={{ color: colors.muted, fontSize: 14 }}>
            Share your USB build recipe
          </Text>
        </View>

        {/* Recipe Card */}
        <View style={{
          backgroundColor: colors.surface,
          borderRadius: 16,
          borderWidth: 1,
          borderColor: 'rgba(255, 255, 255, 0.05)',
          padding: 20,
          marginBottom: 20,
        }}>
          <Text style={{ color: colors.primary, fontSize: 12, fontWeight: '700', letterSpacing: 1, marginBottom: 12 }}>
            RECIPE SUMMARY
          </Text>
          {[
            { label: 'Name', value: recipe.name },
            { label: 'Device Type', value: recipe.deviceType },
            { label: 'Target USB', value: recipe.targetDevice?.name ?? 'None selected' },
            { label: 'OS Images', value: recipe.selectedOS.map(o => o.name).join(', ') || 'None' },
            { label: 'Tools', value: recipe.selectedTools.map(t => t.name).join(', ') || 'None' },
            { label: 'Total Size', value: `${recipe.totalSizeGB.toFixed(1)} GB` },
            { label: 'Est. Time', value: `~${recipe.estimatedMinutes} min` },
            { label: 'Partition', value: recipe.partitionScheme.toUpperCase() },
            { label: 'Bootloader', value: recipe.bootloader.toUpperCase() },
          ].map(({ label, value }) => (
            <View key={label} style={{ flexDirection: 'row', justifyContent: 'space-between', paddingVertical: 8, borderBottomWidth: 1, borderBottomColor: 'rgba(255,255,255,0.06)' }}>
              <Text style={{ color: colors.muted, fontSize: 13 }}>{label}</Text>
              <Text style={{ color: '#fff', fontSize: 13, fontWeight: '600', maxWidth: '60%', textAlign: 'right' }}>{value}</Text>
            </View>
          ))}
        </View>

        {/* JSON Preview */}
        <View style={{
          backgroundColor: 'rgba(0,0,0,0.15)',
          borderRadius: 12,
          borderWidth: 1,
          borderColor: 'rgba(255, 255, 255, 0.05)',
          padding: 16,
          marginBottom: 20,
        }}>
          <Text style={{ color: colors.primary, fontSize: 11, fontWeight: '700', letterSpacing: 1, marginBottom: 10 }}>
            JSON RECIPE
          </Text>
          <Text style={{ color: '#94a3b8', fontFamily: 'monospace', fontSize: 11, lineHeight: 18 }}>
            {recipeJSON}
          </Text>
        </View>

        {/* Copy Button */}
        <TouchableOpacity
          onPress={handleCopy}
          style={{
            backgroundColor: copied ? colors.success : colors.primary,
            borderRadius: 14,
            paddingVertical: 16,
            alignItems: 'center',
            marginBottom: 12,
          }}
        >
          <Text style={{ color: '#050811', fontWeight: '800', fontSize: 16 }}>
            {copied ? '✅ Copied!' : '📋 Copy to Clipboard'}
          </Text>
        </TouchableOpacity>

        <View style={{
          backgroundColor: 'rgba(157,78,221,0.1)',
          borderRadius: 12,
          borderWidth: 1,
          borderColor: 'rgba(157,78,221,0.3)',
          padding: 16,
        }}>
          <Text style={{ color: '#9d4edd', fontWeight: '700', marginBottom: 6 }}>💡 How to Use</Text>
          <Text style={{ color: colors.muted, fontSize: 13, lineHeight: 20 }}>
            Copy this recipe and import it in the Phoenix Core desktop app. The desktop app will flash your USB drive with all selected OS images and tools.
          </Text>
        </View>
      </ScrollView>
    </ScreenContainer>
  );
}
