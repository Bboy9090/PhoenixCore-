import { View, Text, StyleSheet } from 'react-native';

export default function ThemeLabScreen() {
  return (
    <View style={styles.container}>
      <Text style={styles.title}>Theme Lab</Text>
      <Text style={styles.subtitle}>
        Dev screen for theme and UI testing
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
    fontSize: 24,
    fontWeight: '700',
    color: '#00d4ff',
    marginBottom: 8,
  },
  subtitle: {
    fontSize: 16,
    color: '#aaa',
  },
});
