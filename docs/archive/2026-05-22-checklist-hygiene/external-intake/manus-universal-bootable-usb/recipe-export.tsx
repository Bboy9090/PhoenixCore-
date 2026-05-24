import { useState, useEffect } from 'react';
import { ScrollView, Text, View, TouchableOpacity, ActivityIndicator, Image } from 'react-native';
import { ScreenContainer } from '@/components/screen-container';
import { useColors } from '@/hooks/use-colors';
import { generateRecipeQRCode, exportRecipeAsJSON as exportToJSON, getRecipeFilename as getFilename } from '@/lib/qr-utils';
import { DeploymentRecipe } from '@/hooks/use-phoenix-api';

interface RecipeExportScreenProps {
  recipe: DeploymentRecipe;
  onClose: () => void;
}

export default function RecipeExportScreen({ recipe, onClose }: RecipeExportScreenProps) {
  const colors = useColors();
  const [qrCodeUrl, setQrCodeUrl] = useState<string | null>(null);
  const [isGenerating, setIsGenerating] = useState(false);
  const [exportFormat, setExportFormat] = useState<'qr' | 'json'>('qr');

  useEffect(() => {
    generateQRCode();
  }, []);

  const generateQRCode = async () => {
    setIsGenerating(true);
    try {
      const url = await generateRecipeQRCode(recipe);
      setQrCodeUrl(url);
    } catch (error) {
      console.error('QR code generation failed:', error);
    } finally {
      setIsGenerating(false);
    }
  };

  const handleDownloadJSON = () => {
    const json = exportToJSON(recipe);
    const filename = getFilename(recipe);

    // Create blob and download
    const blob = new Blob([json], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    link.click();
    URL.revokeObjectURL(url);
  };

  const handleCopyToClipboard = async () => {
    const json = exportToJSON(recipe);
    try {
      await navigator.clipboard.writeText(json);
      alert('Recipe copied to clipboard!');
    } catch (error) {
      console.error('Failed to copy:', error);
    }
  };

  return (
    <ScreenContainer className="p-6">
      <ScrollView contentContainerStyle={{ flexGrow: 1 }}>
        {/* Header */}
        <View className="mb-6">
          <Text className="text-3xl font-bold text-foreground mb-2">Export Recipe</Text>
          <Text className="text-muted">
            Share your USB recipe with others or use on desktop
          </Text>
        </View>

        {/* Format Selector */}
        <View className="flex-row gap-3 mb-6">
          <TouchableOpacity
            onPress={() => setExportFormat('qr')}
            className={`flex-1 py-3 rounded-lg border-2 items-center ${
              exportFormat === 'qr'
                ? 'border-primary bg-primary/10'
                : 'border-border bg-surface'
            }`}
          >
            <Text className={`font-semibold ${exportFormat === 'qr' ? 'text-primary' : 'text-muted'}`}>
              QR Code
            </Text>
          </TouchableOpacity>

          <TouchableOpacity
            onPress={() => setExportFormat('json')}
            className={`flex-1 py-3 rounded-lg border-2 items-center ${
              exportFormat === 'json'
                ? 'border-primary bg-primary/10'
                : 'border-border bg-surface'
            }`}
          >
            <Text className={`font-semibold ${exportFormat === 'json' ? 'text-primary' : 'text-muted'}`}>
              JSON File
            </Text>
          </TouchableOpacity>
        </View>

        {/* QR Code Export */}
        {exportFormat === 'qr' && (
          <View className="items-center mb-8">
            {isGenerating ? (
              <View className="w-64 h-64 items-center justify-center bg-surface rounded-xl border-2 border-border">
                <ActivityIndicator size="large" color={colors.primary} />
                <Text className="mt-4 text-muted">Generating QR code...</Text>
              </View>
            ) : qrCodeUrl ? (
              <View className="items-center">
                <Image
                  source={{ uri: qrCodeUrl }}
                  style={{ width: 256, height: 256 }}
                  className="rounded-xl border-2 border-border mb-4"
                />
                <Text className="text-center text-muted text-sm max-w-xs">
                  Scan this QR code on your desktop to import the recipe
                </Text>
              </View>
            ) : (
              <TouchableOpacity
                onPress={generateQRCode}
                className="w-64 h-64 items-center justify-center bg-surface rounded-xl border-2 border-border"
              >
                <Text className="text-4xl mb-2">📱</Text>
                <Text className="text-foreground font-semibold">Tap to Generate QR Code</Text>
              </TouchableOpacity>
            )}

            {qrCodeUrl && (
              <TouchableOpacity
                onPress={() => {
                  // TODO: Implement QR code download
                  alert('QR code download coming soon');
                }}
                className="mt-6 w-full py-3 rounded-full bg-primary items-center"
              >
                <Text className="text-background font-semibold">Download QR Code</Text>
              </TouchableOpacity>
            )}
          </View>
        )}

        {/* JSON Export */}
        {exportFormat === 'json' && (
          <View className="mb-8">
            <View className="bg-surface rounded-xl p-4 border-2 border-border mb-4">
              <Text className="text-sm text-muted mb-2">Recipe Filename</Text>
              <Text className="text-foreground font-mono text-sm break-all">
                {getFilename(recipe)}
              </Text>
            </View>

            <View className="bg-surface rounded-xl p-4 border-2 border-border mb-6">
              <Text className="text-sm text-muted mb-2">Recipe Size</Text>
              <Text className="text-foreground font-semibold">
                {(exportToJSON(recipe).length / 1024).toFixed(2)} KB
              </Text>
            </View>

            <TouchableOpacity
              onPress={handleDownloadJSON}
              className="w-full py-3 rounded-full bg-primary items-center mb-3"
            >
              <Text className="text-background font-semibold">📥 Download JSON</Text>
            </TouchableOpacity>

            <TouchableOpacity
              onPress={handleCopyToClipboard}
              className="w-full py-3 rounded-full border-2 border-primary items-center"
            >
              <Text className="text-primary font-semibold">📋 Copy to Clipboard</Text>
            </TouchableOpacity>
          </View>
        )}

        {/* Recipe Summary */}
        <View className="bg-surface rounded-xl p-4 border-2 border-border mb-6">
          <Text className="text-lg font-semibold text-foreground mb-4">Recipe Summary</Text>

          <View className="mb-3 pb-3 border-b border-border">
            <Text className="text-xs text-muted mb-1">Name</Text>
            <Text className="text-foreground font-semibold">{recipe.name}</Text>
          </View>

          <View className="mb-3 pb-3 border-b border-border">
            <Text className="text-xs text-muted mb-1">Type</Text>
            <Text className="text-foreground font-semibold">{recipe.deployment_type}</Text>
          </View>

          <View className="mb-3 pb-3 border-b border-border">
            <Text className="text-xs text-muted mb-1">Operating Systems</Text>
            <Text className="text-foreground font-semibold">{recipe.os_images.length} selected</Text>
          </View>

          <View className="mb-3 pb-3 border-b border-border">
            <Text className="text-xs text-muted mb-1">Tools</Text>
            <Text className="text-foreground font-semibold">{recipe.tools.length} selected</Text>
          </View>

          <View>
            <Text className="text-xs text-muted mb-1">Total Size</Text>
            <Text className="text-foreground font-semibold">
              {recipe.metadata.total_size_gb.toFixed(1)} GB
            </Text>
          </View>
        </View>

        {/* Instructions */}
        <View className="bg-primary/10 rounded-xl p-4 border-2 border-primary/20 mb-6">
          <Text className="text-sm font-semibold text-foreground mb-2">💡 How to Use</Text>
          <Text className="text-sm text-muted leading-relaxed">
            {exportFormat === 'qr'
              ? 'On your desktop, run: python PhoenixDrive_Desktop_Consumer.py --scan-qr'
              : 'On your desktop, run: python PhoenixDrive_Desktop_Consumer.py recipe.json --device /dev/sdb'}
          </Text>
        </View>

        {/* Close Button */}
        <TouchableOpacity
          onPress={onClose}
          className="w-full py-3 rounded-full border-2 border-border items-center"
        >
          <Text className="text-foreground font-semibold">Done</Text>
        </TouchableOpacity>
      </ScrollView>
    </ScreenContainer>
  );
}


