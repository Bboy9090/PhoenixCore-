/**
 * React Hook for Real-Time Installation Progress Tracking
 * Subscribes to WebSocket events and manages installation progress state
 */

import { useEffect, useState, useCallback, useRef } from 'react';

// @ts-ignore - socket.io-client may not be installed in all environments
let io: any;

try {
  const socketIO = require('socket.io-client');
  io = socketIO.io;
} catch (e) {
  console.warn('socket.io-client not available');
}

export interface ComponentProgress {
  status: 'pending' | 'in_progress' | 'completed' | 'failed';
  progress: number;
}

export interface InstallationProgress {
  installation_id: string;
  mac_model: string;
  driver_package_id: string;
  status: 'initializing' | 'in_progress' | 'completed' | 'error';
  overall_progress: number;
  stage: string;
  stage_progress: number;
  components: {
    [key: string]: ComponentProgress;
  };
  current_operation: string;
  speed_mbps: number;
  eta_seconds: number;
  started_at: string;
  completed_at?: string;
  error_message?: string;
}

export interface UseInstallationProgressOptions {
  apiUrl?: string;
  autoConnect?: boolean;
  reconnectAttempts?: number;
  reconnectDelay?: number;
}

/**
 * Hook for tracking real-time installation progress via WebSocket
 * 
 * Usage:
 * ```tsx
 * const { progress, isConnected, error, subscribe, unsubscribe } = useInstallationProgress();
 * 
 * useEffect(() => {
 *   subscribe('installation-123');
 * }, []);
 * 
 * return (
 *   <View>
 *     <Text>{progress?.overall_progress}%</Text>
 *     <Text>{progress?.current_operation}</Text>
 *   </View>
 * );
 * ```
 */
export function useInstallationProgress(options: UseInstallationProgressOptions = {}) {
  const {
    apiUrl = process.env.EXPO_PUBLIC_API_URL || 'http://localhost:3000',
    autoConnect = true,
    reconnectAttempts = 5,
    reconnectDelay = 1000
  } = options;

  const [progress, setProgress] = useState<InstallationProgress | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const socketRef = useRef<any>(null);
  const subscriptionRef = useRef<string | null>(null);
  const reconnectAttemptsRef = useRef(0);

  /**
   * Initialize WebSocket connection
   */
  const connect = useCallback(() => {
    if (socketRef.current?.connected) {
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      socketRef.current = io(apiUrl, {
        reconnection: true,
        reconnectionDelay: reconnectDelay,
        reconnectionDelayMax: 10000,
        reconnectionAttempts: reconnectAttempts,
        transports: ['websocket', 'polling']
      });

      // Handle connection
      socketRef.current.on('connect', () => {
        console.log('WebSocket connected');
        setIsConnected(true);
        setError(null);
        reconnectAttemptsRef.current = 0;
        setIsLoading(false);

        // Resubscribe if we were tracking an installation
        if (subscriptionRef.current) {
          subscribe(subscriptionRef.current);
        }
      });

      // Handle disconnection
      socketRef.current.on('disconnect', () => {
        console.log('WebSocket disconnected');
        setIsConnected(false);
      });

      // Handle connection error
      socketRef.current.on('connect_error', (err: any) => {
        console.error('WebSocket connection error:', err);
        setError(err.message || 'Connection failed');
        reconnectAttemptsRef.current += 1;
        setIsLoading(false);
      });

      // Handle progress updates
      socketRef.current.on('progress_update', (data: any) => {
        console.log('Progress update:', data);
        setProgress(data as InstallationProgress);
      });

      // Handle installation started
      socketRef.current.on('installation_started', (data: any) => {
        console.log('Installation started:', data);
        setProgress((prev) => ({
          ...prev,
          ...data,
          status: 'in_progress',
          overall_progress: 0
        } as InstallationProgress));
      });

      // Handle installation completed
      socketRef.current.on('installation_completed', (data: any) => {
        console.log('Installation completed:', data);
        setProgress((prev) => ({
          ...prev,
          status: 'completed',
          overall_progress: 100,
          completed_at: data.timestamp
        } as InstallationProgress));
      });

      // Handle installation error
      socketRef.current.on('installation_error', (data: any) => {
        console.error('Installation error:', data);
        setProgress((prev) => ({
          ...prev,
          status: 'error',
          error_message: data.error_message
        } as InstallationProgress));
        setError(data.error_message);
      });

      // Handle subscription confirmed
      socketRef.current.on('subscription_confirmed', (data: any) => {
        console.log('Subscription confirmed:', data);
      });

      // Handle unsubscription confirmed
      socketRef.current.on('unsubscription_confirmed', (data: any) => {
        console.log('Unsubscription confirmed:', data);
        setProgress(null);
      });

      // Handle generic errors
      socketRef.current.on('error', (data: any) => {
        console.error('WebSocket error:', data);
        setError(data.message || 'Unknown error');
      });

      // Handle connection response
      socketRef.current.on('connection_response', (data: any) => {
        console.log('Connection response:', data);
      });
    } catch (err: any) {
      const errorMsg = err instanceof Error ? err.message : 'Failed to connect';
      console.error('Connection error:', err);
      setError(errorMsg);
      setIsLoading(false);
    }
  }, [apiUrl, reconnectAttempts, reconnectDelay]);

  /**
   * Disconnect WebSocket
   */
  const disconnect = useCallback(() => {
    if (socketRef.current) {
      socketRef.current.disconnect();
      socketRef.current = null;
      setIsConnected(false);
      setProgress(null);
      subscriptionRef.current = null;
    }
  }, []);

  /**
   * Subscribe to installation progress
   */
  const subscribe = useCallback((installationId: string) => {
    if (!socketRef.current?.connected) {
      console.warn('WebSocket not connected, connecting first...');
      connect();
      return;
    }

    subscriptionRef.current = installationId;
    socketRef.current.emit('subscribe_installation', {
      installation_id: installationId
    });

    console.log('Subscribed to installation:', installationId);
  }, [connect]);

  /**
   * Unsubscribe from installation progress
   */
  const unsubscribe = useCallback((installationId?: string) => {
    if (!socketRef.current?.connected) {
      return;
    }

    const id = installationId || subscriptionRef.current;
    if (!id) {
      return;
    }

    socketRef.current.emit('unsubscribe_installation', {
      installation_id: id
    });

    if (id === subscriptionRef.current) {
      subscriptionRef.current = null;
      setProgress(null);
    }

    console.log('Unsubscribed from installation:', id);
  }, []);

  /**
   * Get current progress
   */
  const getProgress = useCallback((installationId: string) => {
    if (!socketRef.current?.connected) {
      console.warn('WebSocket not connected');
      return;
    }

    socketRef.current.emit('get_progress', {
      installation_id: installationId
    });
  }, []);

  /**
   * Auto-connect on mount
   */
  useEffect(() => {
    if (autoConnect) {
      connect();
    }

    return () => {
      // Don't disconnect on unmount - keep connection alive for other components
      // disconnect();
    };
  }, [autoConnect, connect]);

  return {
    progress,
    isConnected,
    isLoading,
    error,
    connect,
    disconnect,
    subscribe,
    unsubscribe,
    getProgress
  };
}

/**
 * Hook for managing multiple installations
 */
export function useMultipleInstallations(options: UseInstallationProgressOptions = {}) {
  const [installations, setInstallations] = useState<Map<string, InstallationProgress>>(new Map());
  const { subscribe, unsubscribe, isConnected, error } = useInstallationProgress(options);

  const subscribeToInstallation = useCallback((installationId: string) => {
    subscribe(installationId);
  }, [subscribe]);

  const unsubscribeFromInstallation = useCallback((installationId: string) => {
    unsubscribe(installationId);
    setInstallations((prev) => {
      const next = new Map(prev);
      next.delete(installationId);
      return next;
    });
  }, [unsubscribe]);

  const updateInstallation = useCallback((progress: InstallationProgress) => {
    setInstallations((prev) => {
      const next = new Map(prev);
      next.set(progress.installation_id, progress);
      return next;
    });
  }, []);

  return {
    installations,
    isConnected,
    error,
    subscribe: subscribeToInstallation,
    unsubscribe: unsubscribeFromInstallation,
    updateInstallation
  };
}

/**
 * Hook for progress percentage calculation
 */
export function useProgressPercentage(progress: InstallationProgress | null) {
  const [percentage, setPercentage] = useState(0);
  const [displayText, setDisplayText] = useState('0%');

  useEffect(() => {
    if (!progress) {
      setPercentage(0);
      setDisplayText('0%');
      return;
    }

    const percent = Math.round(progress.overall_progress);
    setPercentage(percent);
    setDisplayText(`${percent}%`);
  }, [progress?.overall_progress]);

  return { percentage, displayText };
}

/**
 * Hook for ETA calculation
 */
export function useETA(progress: InstallationProgress | null) {
  const [etaText, setEtaText] = useState('Calculating...');
  const [etaSeconds, setEtaSeconds] = useState(0);

  useEffect(() => {
    if (!progress || progress.eta_seconds <= 0) {
      setEtaText('Calculating...');
      setEtaSeconds(0);
      return;
    }

    setEtaSeconds(progress.eta_seconds);

    const minutes = Math.floor(progress.eta_seconds / 60);
    const seconds = progress.eta_seconds % 60;

    if (minutes > 0) {
      setEtaText(`${minutes}m ${seconds}s remaining`);
    } else {
      setEtaText(`${seconds}s remaining`);
    }
  }, [progress?.eta_seconds]);

  return { etaText, etaSeconds };
}

/**
 * Hook for speed formatting
 */
export function useFormattedSpeed(progress: InstallationProgress | null) {
  const [speedText, setSpeedText] = useState('0 MB/s');

  useEffect(() => {
    if (!progress) {
      setSpeedText('0 MB/s');
      return;
    }

    const speed = progress.speed_mbps || 0;
    if (speed > 1000) {
      setSpeedText(`${(speed / 1024).toFixed(1)} GB/s`);
    } else {
      setSpeedText(`${speed.toFixed(1)} MB/s`);
    }
  }, [progress?.speed_mbps]);

  return speedText;
}
