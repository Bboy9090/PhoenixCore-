/**
 * Redirects to the main builder/wizard tab.
 * This file is kept for routing compatibility only.
 */
import { useEffect } from 'react';
import { View, Text } from 'react-native';
import { useRouter } from 'expo-router';

export default function RedirectScreen() {
  const router = useRouter();
  useEffect(() => {
    router.replace('/(tabs)/builder');
  }, []);
  return (
    <View style={{ flex: 1, backgroundColor: '#050811', alignItems: 'center', justifyContent: 'center' }}>
      <Text style={{ color: '#00d2ff', fontSize: 16 }}>Loading...</Text>
    </View>
  );
}
