import { Stack } from 'expo-router';

export default function RootLayout() {
  return (
    <Stack screenOptions={{ headerShown: false }}>
      <Stack.Screen name="(tabs)" />
      <Stack.Screen name="dev/theme-lab" options={{ presentation: 'modal' }} />
      <Stack.Screen name="oauth/callback" />
    </Stack>
  );
}
