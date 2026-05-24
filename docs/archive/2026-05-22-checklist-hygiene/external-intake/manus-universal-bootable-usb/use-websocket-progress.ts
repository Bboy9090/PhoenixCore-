/**
 * WebSocket hook for real-time USB build progress streaming
 * Connects to Flask-SocketIO backend for live updates
 */

import { useEffect, useState, useCallback, useRef } from 'react';
import { BuildProgress } from '@/hooks/use-phoenix-api';

// Dynamic import to avoid bundling socket.io-client on mobile
let io: any = null;
let Socket: any = null;

if (typeof window !== 'undefined') {
  try {
    const socketIO = require('socket.io-client');
    io = socketIO.io;
    Socket = socketIO.Socket;
  } catch (e) {
    console.warn('socket.io-client not available, using polling fallback');
  }
}

const WS_URL = process.env.EXPO_PUBLIC_API_URL?.replace('/api/v1', '') || 'http://localhost:5000';

interface WebSocketProgressHook {
  progress: BuildProgress | null;
  isConnected: boolean;
  error: string | null;
  subscribe: (buildId: string) => void;
  unsubscribe: () => void;
}

export function useWebSocketProgress(): WebSocketProgressHook {
  const [progress, setProgress] = useState<BuildProgress | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const socketRef = useRef<any>(null);
  const currentBuildIdRef = useRef<string | null>(null);

  // Initialize WebSocket connection
  useEffect(() => {
    try {
      socketRef.current = io(WS_URL, {
        transports: ['websocket', 'polling'],
        reconnection: true,
        reconnectionDelay: 1000,
        reconnectionDelayMax: 5000,
        reconnectionAttempts: 5,
      });

      socketRef.current.on('connect', () => {
        console.log('WebSocket connected');
        setIsConnected(true);
        setError(null);
      });

      socketRef.current.on('disconnect', () => {
        console.log('WebSocket disconnected');
        setIsConnected(false);
      });

      socketRef.current.on('error', (err: any) => {
        console.error('WebSocket error:', err);
        setError(err?.message || 'WebSocket error');
      });

      socketRef.current.on('progress', (data: BuildProgress) => {
        console.log('Build progress:', data);
        setProgress(data);
      });

      socketRef.current.on('complete', (data: BuildProgress) => {
        console.log('Build complete:', data);
        setProgress(data);
      });

      socketRef.current.on('error_event', (data: BuildProgress) => {
        console.error('Build error:', data);
        setProgress(data);
        setError(data.error_message || 'Build failed');
      });

      return () => {
        if (socketRef.current) {
          socketRef.current.disconnect();
        }
      };
    } catch (err) {
      console.error('Failed to initialize WebSocket:', err);
      setError(err instanceof Error ? err.message : 'Failed to connect to WebSocket');
    }
  }, []);

  const subscribe = useCallback((buildId: string) => {
    if (!socketRef.current || !socketRef.current.connected) {
      setError('WebSocket not connected');
      return;
    }

    console.log('Subscribing to build:', buildId);
    currentBuildIdRef.current = buildId;
    socketRef.current.emit('subscribe_build', { build_id: buildId });
  }, []);

  const unsubscribe = useCallback(() => {
    if (!socketRef.current || !currentBuildIdRef.current) {
      return;
    }

    console.log('Unsubscribing from build:', currentBuildIdRef.current);
    socketRef.current.emit('unsubscribe_build', { build_id: currentBuildIdRef.current });
    currentBuildIdRef.current = null;
    setProgress(null);
  }, []);

  return {
    progress,
    isConnected,
    error,
    subscribe,
    unsubscribe,
  };
}

/**
 * Alternative hook using polling instead of WebSocket
 * Useful for environments where WebSocket is not available
 */
export function usePollingProgress(buildId: string | null, pollInterval: number = 1000) {
  const [progress, setProgress] = useState<BuildProgress | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const intervalRef = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    if (!buildId) {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
      return;
    }

    const pollProgress = async () => {
      try {
        setIsLoading(true);
        const response = await fetch(
          `${process.env.EXPO_PUBLIC_API_URL}/usb/build/${buildId}/status`
        );

        if (!response.ok) {
          throw new Error(`API error: ${response.statusText}`);
        }

        const data = await response.json();
        setProgress(data);
        setError(null);

        // Stop polling if build is complete or errored
        if (data.state === 'complete' || data.state === 'error' || data.state === 'cancelled') {
          if (intervalRef.current) {
            clearInterval(intervalRef.current);
            intervalRef.current = null;
          }
        }
      } catch (err) {
        console.error('Polling error:', err);
        setError(err instanceof Error ? err.message : 'Polling failed');
      } finally {
        setIsLoading(false);
      }
    };

    // Poll immediately
    pollProgress();

    // Set up interval
    intervalRef.current = setInterval(pollProgress, pollInterval) as any;

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, [buildId, pollInterval]);

  return { progress, isLoading, error };
}
