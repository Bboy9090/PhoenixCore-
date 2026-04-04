import { useState, useEffect } from 'react';
import { View, Text, StyleSheet, Linking, TouchableOpacity, ActivityIndicator } from 'react-native';
import { getUsbToolkit, getApiBaseUrl, UsbToolkitInfo } from '../../lib/api';

export default function BuilderScreen() {
  const [toolkit, setToolkit] = useState<UsbToolkitInfo | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getUsbToolkit()
      .then(setToolkit)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  const handleDownload = () => {
    if (toolkit?.download_url) {
      const url = toolkit.download_url.startsWith('http')
        ? toolkit.download_url
        : `${getApiBaseUrl()}${toolkit.download_url}`;
      Linking.openURL(url);
    }
  };

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Builder</Text>
      <Text style={styles.subtitle}>
        Create and manage bootable media configs
      </Text>

      {loading && <ActivityIndicator color="#00d4ff" style={styles.loader} />}
      {error && (
        <Text style={styles.error}>
          Cannot reach backend: {error}. Start web_server.py and set EXPO_PUBLIC_API_URL.
        </Text>
      )}

      {!loading && !error && toolkit && (
        <View style={styles.card}>
          <Text style={styles.cardTitle}>BootForge USB Toolkit</Text>
          <Text style={styles.cardDesc}>
            {toolkit.available
              ? 'Ready to download. Extract to a FAT32 USB and run Start-BootForge-Mac.command.'
              : 'Run "python3 create_recovery_usb.py --yes" on your computer to build the toolkit.'}
          </Text>
          {toolkit.available ? (
            <TouchableOpacity style={styles.button} onPress={handleDownload}>
              <Text style={styles.buttonText}>Download {toolkit.filename ?? 'USB Toolkit'}</Text>
            </TouchableOpacity>
          ) : (
            <Text style={styles.hint}>{toolkit.message}</Text>
          )}
        </View>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#1e1e1e',
    padding: 24,
  },
  title: {
    fontSize: 24,
    fontWeight: '700',
    color: '#00d4ff',
    marginBottom: 8,
  },
  subtitle: {
    fontSize: 16,
    color: '#aaa',
    marginBottom: 24,
  },
  loader: { marginVertical: 24 },
  error: { color: '#ff6b6b', fontSize: 14, marginBottom: 16 },
  card: {
    backgroundColor: 'rgba(255,255,255,0.08)',
    borderRadius: 12,
    padding: 20,
    borderWidth: 1,
    borderColor: 'rgba(0,212,255,0.3)',
  },
  cardTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#00d4ff',
    marginBottom: 10,
  },
  cardDesc: {
    color: '#aaa',
    fontSize: 14,
    marginBottom: 16,
  },
  button: {
    backgroundColor: '#00d4ff',
    paddingVertical: 12,
    paddingHorizontal: 20,
    borderRadius: 8,
    alignSelf: 'flex-start',
  },
  buttonText: {
    color: '#1e1e1e',
    fontWeight: '600',
    fontSize: 16,
  },
  hint: {
    color: '#666',
    fontSize: 13,
    fontFamily: 'monospace',
  },
});
