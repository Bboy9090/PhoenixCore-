import { View, Text, StyleSheet, Linking } from 'react-native';
import { useApiHealth } from '../../lib/api';

export default function HomeScreen() {
  const { status, error, loading } = useApiHealth();

  return (
    <View style={styles.container}>
      <Text style={styles.title}>PhoenixCore Mobile</Text>
      <Text style={styles.subtitle}>
        BootForge & recovery workflows on the go
      </Text>

      <View style={styles.card}>
        <Text style={styles.cardTitle}>Backend Status</Text>
        {loading && <Text style={styles.status}>Checking…</Text>}
        {error && (
          <Text style={styles.error}>
            Offline or wrong URL. Set EXPO_PUBLIC_API_URL to your web server
            (e.g. http://YOUR_IP:5000).
          </Text>
        )}
        {status && (
          <Text style={styles.connected}>Connected – {status}</Text>
        )}
      </View>

      <Text style={styles.hint}>
        Use the tabs: Wizard, Builder, Knowledge
      </Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#1e1e1e',
    padding: 24,
    justifyContent: 'center',
  },
  title: {
    fontSize: 28,
    fontWeight: '700',
    color: '#00d4ff',
    marginBottom: 8,
  },
  subtitle: {
    fontSize: 16,
    color: '#aaa',
    marginBottom: 32,
  },
  card: {
    backgroundColor: 'rgba(255,255,255,0.08)',
    borderRadius: 12,
    padding: 20,
    borderWidth: 1,
    borderColor: 'rgba(0,212,255,0.3)',
    marginBottom: 24,
  },
  cardTitle: {
    fontSize: 18,
    color: '#00d4ff',
    marginBottom: 12,
  },
  status: { color: '#999', fontSize: 14 },
  error: { color: '#ff6b6b', fontSize: 14 },
  connected: { color: '#51cf66', fontSize: 14 },
  hint: {
    color: '#666',
    fontSize: 14,
  },
});
