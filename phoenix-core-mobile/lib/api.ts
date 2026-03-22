/**
 * API client for BootForge web server (web_server.py)
 */

import { useState, useEffect } from 'react';
import { API_BASE_URL } from './config';

export interface HealthResponse {
  status: string;
  app?: string;
  base_url?: string;
  supported_architectures?: Record<string, string[]>;
}

export interface ApiHealthResponse {
  status: string;
  message?: string;
  service?: string;
}

export interface Recipe {
  id: string;
  name: string;
  description: string;
  target_os: string;
  min_storage_gb: number;
  difficulty: string;
  estimated_minutes: number;
}

export interface UsbToolkitInfo {
  available: boolean;
  download_url?: string | null;
  filename?: string;
  message?: string;
}

export async function checkHealth(): Promise<HealthResponse> {
  const res = await fetch(`${API_BASE_URL}/health`);
  if (!res.ok) throw new Error(`Health check failed: ${res.status}`);
  return res.json();
}

export async function checkApiHealth(): Promise<ApiHealthResponse> {
  const res = await fetch(`${API_BASE_URL}/api/health`);
  if (!res.ok) throw new Error(`API health check failed: ${res.status}`);
  return res.json();
}

export async function getRecipes(): Promise<Recipe[]> {
  const res = await fetch(`${API_BASE_URL}/api/recipes`);
  if (!res.ok) throw new Error(`Recipes failed: ${res.status}`);
  const data = await res.json();
  return data.recipes || [];
}

export async function getUsbToolkit(): Promise<UsbToolkitInfo> {
  const res = await fetch(`${API_BASE_URL}/api/usb-toolkit`);
  if (!res.ok) throw new Error(`USB toolkit check failed: ${res.status}`);
  return res.json();
}

export function getApiBaseUrl(): string {
  return API_BASE_URL;
}

export function useApiHealth(): { status: string | null; error: Error | null; loading: boolean } {
  const [status, setStatus] = useState<string | null>(null);
  const [error, setError] = useState<Error | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const data = await checkApiHealth();
        if (!cancelled) setStatus(data.service || data.status || 'ok');
      } catch (e) {
        if (!cancelled) setError(e instanceof Error ? e : new Error(String(e)));
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => { cancelled = true; };
  }, []);

  return { status, error, loading };
}
