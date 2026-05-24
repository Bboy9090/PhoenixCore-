import { ScrollView, Text, View, Pressable, StyleSheet } from "react-native";
import { useState, useMemo } from "react";
import { ScreenContainer } from "@/components/screen-container";
import { IconSymbol } from "@/components/ui/icon-symbol";
import { useColors } from "@/hooks/use-colors";
import { DEVICE_TYPES, OS_CATALOG, getCompatibility } from "@/lib/data/catalog";

type Step = "device" | "result";

export default function WizardScreen() {
  const colors = useColors();
  const [step, setStep] = useState<Step>("device");
  const [selectedDevice, setSelectedDevice] = useState<string | null>(null);

  const compatibility = useMemo(() => {
    if (!selectedDevice) return [];
    return getCompatibility(selectedDevice);
  }, [selectedDevice]);

  const device = DEVICE_TYPES.find((d) => d.id === selectedDevice);

  const handleSelectDevice = (deviceId: string) => {
    setSelectedDevice(deviceId);
    setStep("result");
  };

  const handleReset = () => {
    setStep("device");
    setSelectedDevice(null);
  };

  return (
    <ScreenContainer>
      <ScrollView
        contentContainerStyle={{ paddingBottom: 32 }}
        showsVerticalScrollIndicator={false}
      >
        {/* Header */}
        <View style={styles.header}>
          <Text style={[styles.screenTitle, { color: colors.foreground }]}>
            Device Wizard
          </Text>
          <Text style={[styles.screenSubtitle, { color: colors.muted }]}>
            {step === "device"
              ? "Select your device type to see compatible operating systems"
              : `Compatibility results for ${device?.name}`}
          </Text>
        </View>

        {/* Step Indicator */}
        <View style={styles.stepRow}>
          <View style={[styles.stepDot, { backgroundColor: colors.primary }]} />
          <View style={[styles.stepLine, { backgroundColor: step === "result" ? colors.primary : colors.border }]} />
          <View style={[styles.stepDot, { backgroundColor: step === "result" ? colors.primary : colors.border }]} />
        </View>

        {step === "device" ? (
          <View style={styles.section}>
            <Text style={[styles.sectionLabel, { color: colors.muted }]}>
              WHAT TYPE OF DEVICE ARE YOU WORKING WITH?
            </Text>
            {DEVICE_TYPES.map((dt) => (
              <Pressable
                key={dt.id}
                onPress={() => handleSelectDevice(dt.id)}
                style={({ pressed }) => [
                  styles.deviceCard,
                  { backgroundColor: colors.surface, borderColor: colors.border },
                  pressed && { opacity: 0.8, transform: [{ scale: 0.98 }] },
                ]}
              >
                <View style={[styles.deviceIcon, { backgroundColor: colors.primary + "15" }]}>
                  <IconSymbol name={dt.icon as any} size={28} color={colors.primary} />
                </View>
                <View style={styles.deviceText}>
                  <Text style={[styles.deviceName, { color: colors.foreground }]}>
                    {dt.name}
                  </Text>
                  <Text style={[styles.deviceDesc, { color: colors.muted }]} numberOfLines={2}>
                    {dt.description}
                  </Text>
                  <View style={styles.archRow}>
                    {dt.architectures.map((arch) => (
                      <View key={arch} style={[styles.archBadge, { backgroundColor: colors.primary + "18" }]}>
                        <Text style={[styles.archText, { color: colors.primary }]}>{arch}</Text>
                      </View>
                    ))}
                  </View>
                </View>
                <IconSymbol name="chevron.right" size={20} color={colors.muted} />
              </Pressable>
            ))}
          </View>
        ) : (
          <View style={styles.section}>
            {/* Selected Device Summary */}
            <View style={[styles.selectedDevice, { backgroundColor: colors.primary + "10", borderColor: colors.primary + "30" }]}>
              <IconSymbol name={device?.icon as any || "laptopcomputer"} size={24} color={colors.primary} />
              <View style={{ flex: 1 }}>
                <Text style={[styles.selectedDeviceName, { color: colors.foreground }]}>
                  {device?.name}
                </Text>
                <Text style={[styles.selectedDeviceArch, { color: colors.muted }]}>
                  Architecture: {device?.architectures.join(", ")}
                </Text>
              </View>
              <Pressable
                onPress={handleReset}
                style={({ pressed }) => [
                  styles.changeBtn,
                  { backgroundColor: colors.surface, borderColor: colors.border },
                  pressed && { opacity: 0.7 },
                ]}
              >
                <Text style={[styles.changeBtnText, { color: colors.primary }]}>Change</Text>
              </Pressable>
            </View>

            {/* Compatibility Results */}
            <Text style={[styles.sectionLabel, { color: colors.muted }]}>
              OS COMPATIBILITY
            </Text>

            {/* Supported */}
            {compatibility.filter((c) => c.status === "supported").length > 0 && (
              <View style={styles.compatGroup}>
                <View style={styles.compatHeader}>
                  <IconSymbol name="checkmark.circle.fill" size={18} color={colors.success} />
                  <Text style={[styles.compatHeaderText, { color: colors.success }]}>
                    Fully Supported
                  </Text>
                </View>
                {compatibility
                  .filter((c) => c.status === "supported")
                  .map((c) => {
                    const os = OS_CATALOG.find((o) => o.id === c.osId);
                    if (!os) return null;
                    return (
                      <View key={c.osId} style={[styles.compatItem, { backgroundColor: colors.surface, borderColor: colors.border }]}>
                        <View style={[styles.compatDot, { backgroundColor: colors.success }]} />
                        <View style={{ flex: 1 }}>
                          <Text style={[styles.compatName, { color: colors.foreground }]}>
                            {os.name} {os.version}
                          </Text>
                          <Text style={[styles.compatNote, { color: colors.muted }]}>{c.notes}</Text>
                        </View>
                        <Text style={[styles.compatSize, { color: colors.muted }]}>{os.sizeGB} GB</Text>
                      </View>
                    );
                  })}
              </View>
            )}

            {/* Partial */}
            {compatibility.filter((c) => c.status === "partial").length > 0 && (
              <View style={styles.compatGroup}>
                <View style={styles.compatHeader}>
                  <IconSymbol name="exclamationmark.triangle.fill" size={18} color={colors.warning} />
                  <Text style={[styles.compatHeaderText, { color: colors.warning }]}>
                    Partial Support
                  </Text>
                </View>
                {compatibility
                  .filter((c) => c.status === "partial")
                  .map((c) => {
                    const os = OS_CATALOG.find((o) => o.id === c.osId);
                    if (!os) return null;
                    return (
                      <View key={c.osId} style={[styles.compatItem, { backgroundColor: colors.surface, borderColor: colors.border }]}>
                        <View style={[styles.compatDot, { backgroundColor: colors.warning }]} />
                        <View style={{ flex: 1 }}>
                          <Text style={[styles.compatName, { color: colors.foreground }]}>
                            {os.name} {os.version}
                          </Text>
                          <Text style={[styles.compatNote, { color: colors.muted }]}>{c.notes}</Text>
                        </View>
                        <Text style={[styles.compatSize, { color: colors.muted }]}>{os.sizeGB} GB</Text>
                      </View>
                    );
                  })}
              </View>
            )}

            {/* Unsupported */}
            {compatibility.filter((c) => c.status === "unsupported").length > 0 && (
              <View style={styles.compatGroup}>
                <View style={styles.compatHeader}>
                  <IconSymbol name="xmark.circle.fill" size={18} color={colors.error} />
                  <Text style={[styles.compatHeaderText, { color: colors.error }]}>
                    Not Supported
                  </Text>
                </View>
                {compatibility
                  .filter((c) => c.status === "unsupported")
                  .map((c) => {
                    const os = OS_CATALOG.find((o) => o.id === c.osId);
                    if (!os) return null;
                    return (
                      <View key={c.osId} style={[styles.compatItem, { backgroundColor: colors.surface, borderColor: colors.border }]}>
                        <View style={[styles.compatDot, { backgroundColor: colors.error }]} />
                        <View style={{ flex: 1 }}>
                          <Text style={[styles.compatName, { color: colors.foreground }]}>
                            {os.name} {os.version}
                          </Text>
                          <Text style={[styles.compatNote, { color: colors.muted }]}>{c.notes}</Text>
                        </View>
                      </View>
                    );
                  })}
              </View>
            )}

            {/* Build USB CTA */}
            <Pressable
              onPress={() => {/* Navigate to builder with pre-selected items */}}
              style={({ pressed }) => [
                styles.buildCTA,
                { backgroundColor: colors.primary },
                pressed && { opacity: 0.9, transform: [{ scale: 0.97 }] },
              ]}
            >
              <IconSymbol name="externaldrive.fill" size={20} color="#FFFFFF" />
              <Text style={styles.buildCTAText}>Build USB for This Device</Text>
            </Pressable>
          </View>
        )}
      </ScrollView>
    </ScreenContainer>
  );
}

const styles = StyleSheet.create({
  header: {
    paddingHorizontal: 20,
    paddingTop: 16,
    gap: 6,
  },
  screenTitle: {
    fontSize: 28,
    fontWeight: "800",
  },
  screenSubtitle: {
    fontSize: 15,
    lineHeight: 21,
  },
  stepRow: {
    flexDirection: "row",
    alignItems: "center",
    paddingHorizontal: 20,
    marginTop: 16,
    marginBottom: 8,
  },
  stepDot: {
    width: 12,
    height: 12,
    borderRadius: 6,
  },
  stepLine: {
    flex: 1,
    height: 2,
    marginHorizontal: 4,
  },
  section: {
    paddingHorizontal: 16,
    marginTop: 16,
    gap: 10,
  },
  sectionLabel: {
    fontSize: 12,
    fontWeight: "700",
    letterSpacing: 0.8,
    marginTop: 8,
    marginBottom: 4,
  },
  deviceCard: {
    flexDirection: "row",
    alignItems: "center",
    padding: 16,
    borderRadius: 14,
    borderWidth: 1,
    gap: 14,
  },
  deviceIcon: {
    width: 52,
    height: 52,
    borderRadius: 14,
    alignItems: "center",
    justifyContent: "center",
  },
  deviceText: {
    flex: 1,
    gap: 4,
  },
  deviceName: {
    fontSize: 16,
    fontWeight: "700",
  },
  deviceDesc: {
    fontSize: 13,
    lineHeight: 18,
  },
  archRow: {
    flexDirection: "row",
    gap: 6,
    marginTop: 4,
  },
  archBadge: {
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 6,
  },
  archText: {
    fontSize: 11,
    fontWeight: "700",
  },
  selectedDevice: {
    flexDirection: "row",
    alignItems: "center",
    padding: 14,
    borderRadius: 12,
    borderWidth: 1,
    gap: 12,
  },
  selectedDeviceName: {
    fontSize: 15,
    fontWeight: "700",
  },
  selectedDeviceArch: {
    fontSize: 12,
    marginTop: 2,
  },
  changeBtn: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 8,
    borderWidth: 1,
  },
  changeBtnText: {
    fontSize: 13,
    fontWeight: "600",
  },
  compatGroup: {
    gap: 8,
  },
  compatHeader: {
    flexDirection: "row",
    alignItems: "center",
    gap: 8,
    marginTop: 4,
  },
  compatHeaderText: {
    fontSize: 14,
    fontWeight: "700",
  },
  compatItem: {
    flexDirection: "row",
    alignItems: "center",
    padding: 14,
    borderRadius: 12,
    borderWidth: 1,
    gap: 10,
  },
  compatDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
  },
  compatName: {
    fontSize: 15,
    fontWeight: "600",
  },
  compatNote: {
    fontSize: 12,
    lineHeight: 17,
    marginTop: 2,
  },
  compatSize: {
    fontSize: 12,
    fontWeight: "600",
  },
  buildCTA: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    padding: 16,
    borderRadius: 14,
    gap: 10,
    marginTop: 8,
  },
  buildCTAText: {
    color: "#FFFFFF",
    fontSize: 16,
    fontWeight: "700",
  },
});
