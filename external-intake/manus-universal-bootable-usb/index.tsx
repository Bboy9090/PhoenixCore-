import { ScrollView, Text, View, Pressable, StyleSheet } from "react-native";
import { useRouter } from "expo-router";
import { ScreenContainer } from "@/components/screen-container";
import { IconSymbol } from "@/components/ui/icon-symbol";
import { useColors } from "@/hooks/use-colors";

const FEATURES = [
  {
    title: "Device Wizard",
    description: "Identify your device and see which OSes are compatible",
    icon: "cpu" as const,
    route: "/wizard" as const,
    gradient: "#E85D04",
  },
  {
    title: "USB Builder",
    description: "Build the perfect multi-boot USB recipe for your needs",
    icon: "externaldrive.fill" as const,
    route: "/builder" as const,
    gradient: "#F48C06",
  },
  {
    title: "Knowledge Base",
    description: "Guides for recovery, repair, and OS installation",
    icon: "book.fill" as const,
    route: "/knowledge" as const,
    gradient: "#DC2F02",
  },
];

const STATS = [
  { label: "Operating Systems", value: "10+" },
  { label: "Repair Tools", value: "7+" },
  { label: "Device Types", value: "6" },
  { label: "KB Articles", value: "6+" },
];

export default function HomeScreen() {
  const router = useRouter();
  const colors = useColors();

  return (
    <ScreenContainer>
      <ScrollView
        contentContainerStyle={{ paddingBottom: 32 }}
        showsVerticalScrollIndicator={false}
      >
        {/* Hero Section */}
        <View style={[styles.hero, { backgroundColor: colors.primary }]}>
          <View style={styles.heroContent}>
            <View style={styles.heroIconRow}>
              <IconSymbol name="flame.fill" size={36} color="#FFFFFF" />
              <Text style={styles.heroBadge}>Bobby's PhoenixDrive</Text>
            </View>
            <Text style={styles.heroTitle}>Any Device.{"\n"}Any OS. Fixed.</Text>
            <Text style={styles.heroSubtitle}>
              Bobby's got your back. Plug it in, boot it up,{"\n"}
              problem over in a jiffy.
            </Text>
            <Pressable
              onPress={() => router.push("/wizard" as any)}
              style={({ pressed }) => [
                styles.heroCTA,
                pressed && { opacity: 0.9, transform: [{ scale: 0.97 }] },
              ]}
            >
              <Text style={styles.heroCTAText}>Start Building</Text>
              <IconSymbol name="arrow.right" size={18} color="#E85D04" />
            </Pressable>
          </View>
        </View>

        {/* Stats Row */}
        <View style={styles.statsRow}>
          {STATS.map((stat) => (
            <View key={stat.label} style={[styles.statItem, { backgroundColor: colors.surface, borderColor: colors.border }]}>
              <Text style={[styles.statValue, { color: colors.primary }]}>{stat.value}</Text>
              <Text style={[styles.statLabel, { color: colors.muted }]}>{stat.label}</Text>
            </View>
          ))}
        </View>

        {/* Feature Cards */}
        <View style={styles.section}>
          <Text style={[styles.sectionTitle, { color: colors.foreground }]}>
            What Can Bobby's PhoenixDrive Do?
          </Text>
          {FEATURES.map((feature) => (
            <Pressable
              key={feature.title}
              onPress={() => router.push(feature.route as any)}
              style={({ pressed }) => [
                styles.featureCard,
                { backgroundColor: colors.surface, borderColor: colors.border },
                pressed && { opacity: 0.8, transform: [{ scale: 0.98 }] },
              ]}
            >
              <View style={[styles.featureIcon, { backgroundColor: feature.gradient + "18" }]}>
                <IconSymbol name={feature.icon} size={24} color={feature.gradient} />
              </View>
              <View style={styles.featureText}>
                <Text style={[styles.featureTitle, { color: colors.foreground }]}>
                  {feature.title}
                </Text>
                <Text style={[styles.featureDesc, { color: colors.muted }]}>
                  {feature.description}
                </Text>
              </View>
              <IconSymbol name="chevron.right" size={20} color={colors.muted} />
            </Pressable>
          ))}
        </View>

        {/* Supported OS Grid */}
        <View style={styles.section}>
          <Text style={[styles.sectionTitle, { color: colors.foreground }]}>
            Supported Operating Systems
          </Text>
          <View style={styles.osGrid}>
            {[
              { name: "Windows", color: "#0078D4", icon: "laptopcomputer" as const },
              { name: "macOS", color: "#AC39FF", icon: "desktopcomputer" as const },
              { name: "Linux", color: "#E95420", icon: "terminal" as const },
              { name: "ChromeOS", color: "#4285F4", icon: "globe" as const },
            ].map((os) => (
              <View
                key={os.name}
                style={[styles.osCard, { backgroundColor: colors.surface, borderColor: colors.border }]}
              >
                <View style={[styles.osIconCircle, { backgroundColor: os.color + "18" }]}>
                  <IconSymbol name={os.icon} size={22} color={os.color} />
                </View>
                <Text style={[styles.osName, { color: colors.foreground }]}>{os.name}</Text>
              </View>
            ))}
          </View>
        </View>

        {/* Reality Check Banner */}
        <View style={styles.section}>
          <View style={[styles.realityBanner, { backgroundColor: colors.surface, borderColor: colors.border }]}>
            <IconSymbol name="info.circle.fill" size={22} color={colors.primary} />
            <View style={styles.realityText}>
              <Text style={[styles.realityTitle, { color: colors.foreground }]}>
                The Honest Truth
              </Text>
              <Text style={[styles.realityDesc, { color: colors.muted }]}>
                One USB can boot Windows, Linux, and ChromeOS on x86 devices. macOS requires Apple hardware. Different CPU architectures need separate USBs. Bobby's PhoenixDrive helps you build the smartest USB for YOUR device.
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
    paddingTop: 16,
    paddingBottom: 32,
    borderBottomLeftRadius: 24,
    borderBottomRightRadius: 24,
  },
  heroContent: {
    gap: 12,
  },
  heroIconRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: 10,
  },
  heroBadge: {
    color: "rgba(255,255,255,0.85)",
    fontSize: 15,
    fontWeight: "700",
    letterSpacing: 1,
    textTransform: "uppercase",
  },
  heroTitle: {
    fontSize: 34,
    fontWeight: "800",
    color: "#FFFFFF",
    lineHeight: 40,
  },
  heroSubtitle: {
    fontSize: 15,
    color: "rgba(255,255,255,0.8)",
    lineHeight: 22,
  },
  heroCTA: {
    flexDirection: "row",
    alignItems: "center",
    alignSelf: "flex-start",
    backgroundColor: "#FFFFFF",
    paddingHorizontal: 20,
    paddingVertical: 12,
    borderRadius: 24,
    gap: 8,
    marginTop: 4,
  },
  heroCTAText: {
    fontSize: 16,
    fontWeight: "700",
    color: "#E85D04",
  },
  statsRow: {
    flexDirection: "row",
    paddingHorizontal: 16,
    gap: 8,
    marginTop: -16,
  },
  statItem: {
    flex: 1,
    alignItems: "center",
    paddingVertical: 12,
    borderRadius: 12,
    borderWidth: 1,
  },
  statValue: {
    fontSize: 18,
    fontWeight: "800",
  },
  statLabel: {
    fontSize: 10,
    fontWeight: "600",
    marginTop: 2,
    textAlign: "center",
  },
  section: {
    paddingHorizontal: 16,
    marginTop: 24,
    gap: 12,
  },
  sectionTitle: {
    fontSize: 20,
    fontWeight: "700",
    marginBottom: 4,
  },
  featureCard: {
    flexDirection: "row",
    alignItems: "center",
    padding: 16,
    borderRadius: 14,
    borderWidth: 1,
    gap: 14,
  },
  featureIcon: {
    width: 48,
    height: 48,
    borderRadius: 12,
    alignItems: "center",
    justifyContent: "center",
  },
  featureText: {
    flex: 1,
    gap: 3,
  },
  featureTitle: {
    fontSize: 16,
    fontWeight: "700",
  },
  featureDesc: {
    fontSize: 13,
    lineHeight: 18,
  },
  osGrid: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: 10,
  },
  osCard: {
    width: "48%",
    flexGrow: 1,
    flexDirection: "row",
    alignItems: "center",
    padding: 14,
    borderRadius: 12,
    borderWidth: 1,
    gap: 10,
  },
  osIconCircle: {
    width: 40,
    height: 40,
    borderRadius: 20,
    alignItems: "center",
    justifyContent: "center",
  },
  osName: {
    fontSize: 15,
    fontWeight: "600",
  },
  realityBanner: {
    flexDirection: "row",
    padding: 16,
    borderRadius: 14,
    borderWidth: 1,
    gap: 12,
    alignItems: "flex-start",
  },
  realityText: {
    flex: 1,
    gap: 4,
  },
  realityTitle: {
    fontSize: 15,
    fontWeight: "700",
  },
  realityDesc: {
    fontSize: 13,
    lineHeight: 19,
  },
});
