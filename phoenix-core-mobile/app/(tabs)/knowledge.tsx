import { View, Text, StyleSheet, Linking, TouchableOpacity } from 'react-native';
import { getApiBaseUrl } from '../../lib/api';

const LINKS = [
  { label: 'BootForge Docs', path: '/', desc: 'Install & quick start' },
  { label: 'Install Guides', path: '/install', desc: 'Linux, macOS, Windows' },
  { label: 'PhoenixCore Architecture', path: null, desc: 'See docs/ARCHITECTURE.md in repo' },
];

export default function KnowledgeScreen() {
  const base = getApiBaseUrl();

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Knowledge</Text>
      <Text style={styles.subtitle}>
        PhoenixDocs, recovery guides, and troubleshooting
      </Text>

      <View style={styles.card}>
        <Text style={styles.cardTitle}>Backend resources</Text>
        <Text style={styles.cardDesc}>
          Open these links in your browser (same network as backend).
        </Text>
        {LINKS.filter((l) => l.path).map((link) => (
          <TouchableOpacity
            key={link.label}
            style={styles.link}
            onPress={() => Linking.openURL(`${base}${link.path}`)}
          >
            <Text style={styles.linkLabel}>{link.label}</Text>
            <Text style={styles.linkDesc}>{link.desc}</Text>
          </TouchableOpacity>
        ))}
      </View>

      <Text style={styles.hint}>
        Run BootForge GUI: python3 main.py --gui
      </Text>
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
    fontWeight: '600',
    color: '#00d4ff',
    marginBottom: 10,
  },
  cardDesc: {
    color: '#aaa',
    fontSize: 14,
    marginBottom: 16,
  },
  link: {
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: 'rgba(255,255,255,0.06)',
  },
  linkLabel: { color: '#00d4ff', fontSize: 16, fontWeight: '500' },
  linkDesc: { color: '#666', fontSize: 12, marginTop: 2 },
  hint: { color: '#666', fontSize: 13 },
});
