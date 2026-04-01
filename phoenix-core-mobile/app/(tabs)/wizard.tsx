import { useState, useEffect } from 'react';
import { View, Text, StyleSheet, ScrollView, ActivityIndicator } from 'react-native';
import { getRecipes, Recipe } from '../../lib/api';

export default function WizardScreen() {
  const [recipes, setRecipes] = useState<Recipe[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getRecipes()
      .then(setRecipes)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Wizard</Text>
      <Text style={styles.subtitle}>
        Step-by-step USB creation and recovery flows
      </Text>

      {loading && <ActivityIndicator color="#00d4ff" style={styles.loader} />}
      {error && (
        <Text style={styles.error}>
          Cannot reach backend: {error}. Start web_server.py and set EXPO_PUBLIC_API_URL.
        </Text>
      )}

      {!loading && !error && (
        <ScrollView style={styles.list}>
          {recipes.map((r) => (
            <View key={r.id} style={styles.card}>
              <Text style={styles.cardTitle}>{r.name}</Text>
              <Text style={styles.cardDesc}>{r.description}</Text>
              <View style={styles.meta}>
                <Text style={styles.badge}>{r.target_os}</Text>
                <Text style={styles.metaText}>{r.min_storage_gb}GB+ • {r.estimated_minutes}min • {r.difficulty}</Text>
              </View>
            </View>
          ))}
        </ScrollView>
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
  list: { flex: 1 },
  card: {
    backgroundColor: 'rgba(255,255,255,0.08)',
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    borderWidth: 1,
    borderColor: 'rgba(0,212,255,0.3)',
  },
  cardTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#00d4ff',
    marginBottom: 6,
  },
  cardDesc: {
    color: '#aaa',
    fontSize: 14,
    marginBottom: 10,
  },
  meta: { flexDirection: 'row', alignItems: 'center', gap: 8 },
  badge: {
    backgroundColor: 'rgba(0,212,255,0.2)',
    color: '#00d4ff',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 6,
    fontSize: 12,
  },
  metaText: { color: '#666', fontSize: 12 },
});
