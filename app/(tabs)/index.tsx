import { ScrollView, Text, View, Pressable, StyleSheet, Animated } from "react-native";
import { useRouter } from "expo-router";
import { useEffect, useRef, useState } from "react";
import { ScreenContainer } from "@/components/screen-container";
import { IconSymbol } from "@/components/ui/icon-symbol";
import { useColors } from "@/hooks/use-colors";
import { checkAPIHealth } from '@/lib/phoenix-engine';

const FEATURES = [
  {
    title: "Device Wizard",
    description: "Detect your hardware and see which OS builds are compatible",
    icon: "cpu" as const,
    route: "/wizard" as const,
    color: "#00d2ff",
    glow: "rgba(0, 210, 255, 0.12)",
  },
  {
    title: "USB Builder",
    description: "Flash premium OS builds to any USB drive with full safety checks",
    icon: "externaldrive.fill" as const,
    route: "/builder" as const,
    color: "#ffd700",
    glow: "rgba(255, 215, 0, 0.12)",
  },
  {
    title: "Knowledge Base",
    description: "Deep guides for boot repair, OS recovery, and legacy hardware",
    icon: "book.fill" as const,
    route: "/knowledge" as const,
    color: "#9d4edd",
    glow: "rgba(157, 78, 221, 0.12)",
  },
];

const OS_SUITE = [
  { name: "Home Aurelia", subtitle: "Legacy 32-bit", color: "#ffd700", bgColor: "rgba(255, 215, 0, 0.1)", icon: "flame.fill" as const },
  { name: "Blue Phoenix", subtitle: "Modern x64", color: "#00d2ff", bgColor: "rgba(0, 210, 255, 0.1)", icon: "bolt.fill" as const },
  { name: "Arcwyre", subtitle: "Pro Dev Build", color: "#9d4edd", bgColor: "rgba(157, 78, 221, 0.1)", icon: "sparkles" as const },
  { name: "Thunder God", subtitle: "Performance", color: "#00ffff", bgColor: "rgba(0, 255, 255, 0.08)", icon: "waveform" as const },
];

const STATS = [
  { label: "OS Builds", value: "4+" },
  { label: "Repair Tools", value: "7+" },
  { label: "Device Types", value: "6" },
  { label: "Architectures", value: "3" },
];

export default function HomeScreen() {
  const router = useRouter();
  const colors = useColors();
  const [apiOnline, setApiOnline] = useState<boolean | null>(null);
  useEffect(() => {
    checkAPIHealth().then(r => setApiOnline(r.online));
    const interval = setInterval(() => checkAPIHealth().then(r => setApiOnline(r.online)), 30000);
    return () => clearInterval(interval);
  }, []);
  const pulseAnim = useRef(new Animated.Value(0.8)).current;
  const glowAnim = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    // Pulsing glow animation for hero badge
    Animated.loop(
      Animated.sequence([
        Animated.timing(pulseAnim, { toValue: 1, duration: 2000, useNativeDriver: true }),
        Animated.timing(pulseAnim, { toValue: 0.8, duration: 2000, useNativeDriver: true }),
      ])
    ).start();
    // Subtle glow shift
    Animated.loop(
      Animated.sequence([
        Animated.timing(glowAnim, { toValue: 1, duration: 3000, useNativeDriver: true }),
        Animated.timing(glowAnim, { toValue: 0, duration: 3000, useNativeDriver: true }),
      ])
    ).start();
  }, []);

  return (
    <ScreenContainer>
      <ScrollView
        contentContainerStyle={{ paddingBottom: 40 }}
        showsVerticalScrollIndicator={false}
      >
        {/* ── Hero Section ── */}
        <View style={styles.hero}>
          {/* Live API Status Badge */}
          <View style={{
            flexDirection: 'row',
            alignItems: 'center',
            alignSelf: 'flex-start',
            backgroundColor: apiOnline === true ? 'rgba(16,185,129,0.15)' : apiOnline === false ? 'rgba(244,63,94,0.15)' : 'rgba(148,163,184,0.15)',
            borderRadius: 20,
            paddingHorizontal: 12,
            paddingVertical: 6,
            borderWidth: 1,
            borderColor: apiOnline === true ? 'rgba(16,185,129,0.4)' : apiOnline === false ? 'rgba(244,63,94,0.4)' : 'rgba(148,163,184,0.3)',
            marginBottom: 16,
          }}>
            <View style={{
              width: 8, height: 8, borderRadius: 4,
              backgroundColor: apiOnline === true ? '#10b981' : apiOnline === false ? '#f43f5e' : '#94a3b8',
              marginRight: 8,
            }} />
            <Text style={{
              fontSize: 12, fontWeight: '700', letterSpacing: 0.5,
              color: apiOnline === true ? '#10b981' : apiOnline === false ? '#f43f5e' : '#94a3b8',
            }}>
              {apiOnline === true ? 'PHOENIX ONLINE' : apiOnline === false ? 'SERVER OFFLINE' : 'CHECKING...'}
            </Text>
          </View>
          {/* Background glow effect */}
          <Animated.View
            style={[
              styles.heroGlow,
              { opacity: glowAnim },
            ]}
          />

          <View style={styles.heroContent}>
            {/* Brand badge */}
            <View style={styles.heroBadgeRow}>
              <Animated.View style={[styles.heroPulse, { transform: [{ scale: pulseAnim }] }]} />
              <Text style={styles.heroBadge}>⚡ PHOENIX CORE</Text>
            </View>

            <Text style={styles.heroTitle}>Any Device.{"\n"}Any OS.{"\n"}Deployed.</Text>
            <Text style={styles.heroSubtitle}>
              Premium OS deployment suite with real USB creation, hardware detection, and our exclusive OS lineup — built different.
            </Text>

            <Pressable
              onPress={() => router.push("/wizard" as any)}
              style={({ pressed }) => [
                styles.heroCTA,
                pressed && { opacity: 0.9, transform: [{ scale: 0.97 }] },
              ]}
            >
              <Text style={styles.heroCTAText}>Start Building</Text>
              <IconSymbol name="arrow.right" size={18} color="#050811" />
            </Pressable>
          </View>
        </View>

        {/* ── Stats Row ── */}
        <View style={styles.statsRow}>
          {STATS.map((stat) => (
            <View
              key={stat.label}
              style={[styles.statItem, { backgroundColor: colors.surface, borderColor: "rgba(0, 210, 255, 0.2)" }]}
            >
              <Text style={[styles.statValue, { color: "#00d2ff" }]}>{stat.value}</Text>
              <Text style={[styles.statLabel, { color: colors.muted }]}>{stat.label}</Text>
            </View>
          ))}
        </View>

        {/* ── Phoenix OS Suite ── */}
        <View style={styles.section}>
          <Text style={[styles.sectionTitle, { color: colors.foreground }]}>
            Phoenix OS Suite
          </Text>
          <Text style={[styles.sectionSubtitle, { color: colors.muted }]}>
            Our exclusive OS lineup — built from the ground up
          </Text>
          <View style={styles.osGrid}>
            {OS_SUITE.map((os) => (
              <View
                key={os.name}
                style={[
                  styles.osCard,
                  {
                    backgroundColor: colors.surface,
                    borderColor: `${os.color}40`,
                    borderLeftColor: os.color,
                  },
                ]}
              >
                <View style={[styles.osIconCircle, { backgroundColor: os.bgColor }]}>
                  <IconSymbol name={os.icon} size={20} color={os.color} />
                </View>
                <View style={styles.osInfo}>
                  <Text style={[styles.osName, { color: colors.foreground }]}>{os.name}</Text>
                  <Text style={[styles.osSubtitle, { color: os.color }]}>{os.subtitle}</Text>
                </View>
              </View>
            ))}
          </View>
        </View>

        {/* ── Feature Cards ── */}
        <View style={styles.section}>
          <Text style={[styles.sectionTitle, { color: colors.foreground }]}>
            What Can Phoenix Core Do?
          </Text>
          {FEATURES.map((feature) => (
            <Pressable
              key={feature.title}
              onPress={() => router.push(feature.route as any)}
              style={({ pressed }) => [
                styles.featureCard,
                { backgroundColor: colors.surface, borderColor: `${feature.color}30` },
                pressed && { opacity: 0.85, transform: [{ scale: 0.98 }] },
              ]}
            >
              <View style={[styles.featureIcon, { backgroundColor: feature.glow }]}>
                <IconSymbol name={feature.icon} size={24} color={feature.color} />
              </View>
              <View style={styles.featureText}>
                <Text style={[styles.featureTitle, { color: colors.foreground }]}>
                  {feature.title}
                </Text>
                <Text style={[styles.featureDesc, { color: colors.muted }]}>
                  {feature.description}
                </Text>
              </View>
              <IconSymbol name="chevron.right" size={18} color={feature.color} />
            </Pressable>
          ))}
        </View>

        {/* ── Power Banner ── */}
        <View style={styles.section}>
          <View style={[styles.powerBanner, { borderColor: "rgba(0, 210, 255, 0.25)" }]}>
            <View style={styles.powerBannerGlow} />
            <IconSymbol name="bolt.fill" size={22} color="#00d2ff" />
            <View style={styles.powerText}>
              <Text style={[styles.powerTitle, { color: "#ffffff" }]}>
                Built Different
              </Text>
              <Text style={[styles.powerDesc, { color: colors.muted }]}>
                Phoenix Core supports our own OS suite (Home Aurelia, Blue Phoenix, Arcwyre, Thunder God) plus Windows, Linux, and macOS — no limits, no compromise.
              </Text>
            </View>
          </View>
        </View>
      </ScrollView>
    </ScreenContainer>
  );
}

const styles = StyleSheet.create({
  hero: {
    paddingHorizontal: 20,
    paddingTop: 20,
    paddingBottom: 40,
    backgroundColor: "#050811",
    borderBottomLeftRadius: 28,
    borderBottomRightRadius: 28,
    borderBottomWidth: 2,
    borderBottomColor: "rgba(255, 215, 0, 0.3)",
    overflow: "hidden",
    position: "relative",
    minHeight: 280,
  },
  heroGlow: {
    position: "absolute",
    top: -40,
    right: -40,
    width: 220,
    height: 220,
    borderRadius: 110,
    backgroundColor: "rgba(0, 210, 255, 0.08)",
  },
  heroContent: {
    gap: 14,
    zIndex: 1,
  },
  heroBadgeRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: 10,
  },
  heroPulse: {
    width: 10,
    height: 10,
    borderRadius: 5,
    backgroundColor: "#00d2ff",
    shadowColor: "#00d2ff",
    shadowOffset: { width: 0, height: 0 },
    shadowOpacity: 0.8,
    shadowRadius: 6,
  },
  heroBadge: {
    color: "#00d2ff",
    fontSize: 13,
    fontWeight: "800",
    letterSpacing: 2,
    textTransform: "uppercase",
  },
  heroTitle: {
    fontSize: 36,
    fontWeight: "800",
    color: "#ffffff",
    lineHeight: 44,
    letterSpacing: -0.5,
  },
  heroSubtitle: {
    fontSize: 14,
    color: "rgba(255,255,255,0.6)",
    lineHeight: 22,
  },
  heroCTA: {
    flexDirection: "row",
    alignItems: "center",
    alignSelf: "flex-start",
    backgroundColor: "#00d2ff",
    paddingHorizontal: 22,
    paddingVertical: 13,
    borderRadius: 26,
    gap: 8,
    marginTop: 4,
    shadowColor: "#00d2ff",
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.4,
    shadowRadius: 10,
    elevation: 8,
  },
  heroCTAText: {
    fontSize: 15,
    fontWeight: "700",
    color: "#050811",
  },
  statsRow: {
    flexDirection: "row",
    paddingHorizontal: 16,
    gap: 8,
    marginTop: -18,
  },
  statItem: {
    flex: 1,
    alignItems: "center",
    paddingVertical: 12,
    borderRadius: 12,
    borderWidth: 1,
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.3,
    shadowRadius: 6,
    elevation: 4,
  },
  statValue: {
    fontSize: 18,
    fontWeight: "800",
  },
  statLabel: {
    fontSize: 9,
    fontWeight: "600",
    marginTop: 2,
    textAlign: "center",
    textTransform: "uppercase",
    letterSpacing: 0.5,
  },
  section: {
    paddingHorizontal: 16,
    marginTop: 26,
    gap: 12,
  },
  sectionTitle: {
    fontSize: 20,
    fontWeight: "700",
    letterSpacing: -0.3,
  },
  sectionSubtitle: {
    fontSize: 13,
    marginTop: -6,
    lineHeight: 18,
  },
  osGrid: {
    gap: 10,
  },
  osCard: {
    flexDirection: "row",
    alignItems: "center",
    padding: 14,
    borderRadius: 12,
    borderWidth: 1,
    borderLeftWidth: 3,
    gap: 12,
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.2,
    shadowRadius: 4,
    elevation: 3,
  },
  osIconCircle: {
    width: 38,
    height: 38,
    borderRadius: 10,
    alignItems: "center",
    justifyContent: "center",
  },
  osInfo: {
    flex: 1,
  },
  osName: {
    fontSize: 14,
    fontWeight: "700",
    marginBottom: 1,
  },
  osSubtitle: {
    fontSize: 11,
    fontWeight: "600",
    textTransform: "uppercase",
    letterSpacing: 0.5,
  },
  featureCard: {
    flexDirection: "row",
    alignItems: "center",
    padding: 16,
    borderRadius: 14,
    borderWidth: 1,
    gap: 14,
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.2,
    shadowRadius: 6,
    elevation: 3,
  },
  featureIcon: {
    width: 50,
    height: 50,
    borderRadius: 14,
    alignItems: "center",
    justifyContent: "center",
  },
  featureText: {
    flex: 1,
    gap: 4,
  },
  featureTitle: {
    fontSize: 16,
    fontWeight: "700",
  },
  featureDesc: {
    fontSize: 13,
    lineHeight: 18,
  },
  powerBanner: {
    flexDirection: "row",
    padding: 18,
    borderRadius: 16,
    borderWidth: 1,
    backgroundColor: "#080c16",
    gap: 14,
    alignItems: "flex-start",
    overflow: "hidden",
    position: "relative",
  },
  powerBannerGlow: {
    position: "absolute",
    top: -30,
    left: -30,
    width: 120,
    height: 120,
    borderRadius: 60,
    backgroundColor: "rgba(0, 210, 255, 0.05)",
  },
  powerText: {
    flex: 1,
    gap: 5,
  },
  powerTitle: {
    fontSize: 15,
    fontWeight: "700",
  },
  powerDesc: {
    fontSize: 13,
    lineHeight: 19,
  },
});
