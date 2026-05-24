/**
 * QR Code utilities for Bobby's PhoenixDrive
 * Handles generation and parsing of QR codes for recipe export/import
 */

import { DeploymentRecipe } from '@/hooks/use-phoenix-api';

const MAX_QR_CAPACITY = 2953; // Maximum alphanumeric characters in QR code

export interface QRRecipeData {
  v: string; // version
  id: string; // recipe_id
  n: string; // name (truncated)
  t: string; // deployment_type
  os: string[]; // os_selections (IDs only)
  tl: string[]; // tool_selections (IDs only)
  d: number; // target_device_size_gb
  s: number; // total_size_gb
}

/**
 * Compress recipe into QR-friendly format
 * Reduces size by using abbreviated field names and removing unnecessary data
 */
export function compressRecipe(recipe: DeploymentRecipe): QRRecipeData {
  return {
    v: '1', // version
    id: recipe.recipe_id,
    n: recipe.name.substring(0, 30), // truncate name
    t: recipe.deployment_type,
    os: recipe.os_images.map((img) => img.image_id),
    tl: recipe.tools,
    d: recipe.target_device.size_gb,
    s: recipe.metadata.total_size_gb,
  };
}

/**
 * Generate QR code data URL
 * Uses a simple QR code generation approach
 */
export async function generateQRCode(data: string): Promise<string> {
  try {
    // Dynamic import to avoid bundling qrcode on mobile
    const QRCode = (await import('qrcode')).default;

    const dataUrl = await QRCode.toDataURL(data, {
      errorCorrectionLevel: 'H',
      type: 'image/png',
      width: 300,
      margin: 2,
      color: {
        dark: '#000000',
        light: '#FFFFFF',
      },
    });

    return dataUrl;
  } catch (error) {
    console.error('QR code generation failed:', error);
    throw error;
  }
}

/**
 * Generate QR code for recipe export
 */
export async function generateRecipeQRCode(recipe: DeploymentRecipe): Promise<string> {
  const compressed = compressRecipe(recipe);
  const json = JSON.stringify(compressed);

  // Check if fits in QR code
  if (json.length > MAX_QR_CAPACITY) {
    throw new Error(
      `Recipe too large for QR code (${json.length} > ${MAX_QR_CAPACITY} characters). Use JSON export instead.`
    );
  }

  return generateQRCode(json);
}

/**
 * Parse QR code data back into recipe format
 */
export function parseQRRecipeData(qrData: string): QRRecipeData {
  try {
    return JSON.parse(qrData);
  } catch (error) {
    throw new Error('Invalid QR code data');
  }
}

/**
 * Expand compressed QR data back into full recipe
 */
export function expandQRRecipe(qrData: QRRecipeData): Partial<DeploymentRecipe> {
  return {
    recipe_id: qrData.id,
    name: qrData.n,
    deployment_type: qrData.t as any,
    os_images: qrData.os.map((osId) => ({
      image_id: osId,
      name: osId.replace(/_/g, ' ').toUpperCase(),
      os_family: 'linux',
      version: 'latest',
      architecture: 'x86_64',
      size_gb: 3.5,
      status: 'available',
    })),
    tools: qrData.tl,
    target_device: {
      device_id: 'unknown',
      size_gb: qrData.d,
      confirm_erase: true,
    },
    metadata: {
      total_size_gb: qrData.s,
      estimated_write_time_minutes: 15,
      target_platform: 'x86_64',
      tags: [],
    },
  };
}

/**
 * Export recipe as JSON string (for file download)
 */
export function exportRecipeAsJSON(recipe: DeploymentRecipe): string {
  return JSON.stringify(recipe, null, 2);
}

/**
 * Import recipe from JSON string
 */
export function importRecipeFromJSON(jsonString: string): DeploymentRecipe {
  try {
    return JSON.parse(jsonString);
  } catch (error) {
    throw new Error('Invalid recipe JSON');
  }
}

/**
 * Generate recipe download filename
 */
export function getRecipeFilename(recipe: DeploymentRecipe): string {
  const timestamp = new Date().toISOString().slice(0, 10);
  const safeName = recipe.name.replace(/[^a-z0-9]/gi, '_').toLowerCase();
  return `phoenixdrive_${safeName}_${timestamp}.json`;
}

/**
 * Generate recipe sharing URL (for cloud sharing)
 */
export function generateRecipeSharingURL(recipe: DeploymentRecipe, baseURL: string = 'https://phoenixdrive.bobby'): string {
  const compressed = compressRecipe(recipe);
  const encoded = btoa(JSON.stringify(compressed)); // Base64 encode
  return `${baseURL}/recipe/${encoded}`;
}

/**
 * Parse recipe from sharing URL
 */
export function parseRecipeFromURL(url: string): Partial<DeploymentRecipe> {
  try {
    const encoded = url.split('/recipe/')[1];
    const decoded = atob(encoded);
    const qrData = JSON.parse(decoded);
    return expandQRRecipe(qrData);
  } catch (error) {
    throw new Error('Invalid recipe URL');
  }
}
