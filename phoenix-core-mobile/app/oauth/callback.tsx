import { useEffect } from 'react';
import { View, Text, StyleSheet, ActivityIndicator } from 'react-native';
import { useRouter } from 'expo-router';

/**
 * OAuth callback handler. Receives auth redirects and processes tokens.
 * Extend this when you add OAuth (e.g. Cloudflare, GitHub) integration.
 */
export default function OAuthCallbackScreen() {
  const router = useRouter();

  useEffect(() => {
    // Placeholder: redirect back to home after a short delay
    const t = setTimeout(() => router.replace('/'), 1500);
    return () => clearTimeout(t);
  }, [router]);

  return (
    <View style={styles.container}>
      <ActivityIndicator size="large" color="#00d4ff" />
      <Text style={styles.text}>Processing sign-in...</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#0f1419',
    gap: 16,
  },
  text: {
    color: '#94a3b8',
    fontSize: 16,
  },
});
