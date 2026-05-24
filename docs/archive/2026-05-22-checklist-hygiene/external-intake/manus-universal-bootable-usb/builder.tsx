import { ScrollView, Text, View, Pressable, StyleSheet, Alert, Platform } from "react-native";
import { useState, useMemo, useCallback } from "react";
import { ScreenContainer } from "@/components/screen-container";
import { IconSymbol } from "@/components/ui/icon-symbol";
import { useColors } from "@/hooks/use-colors";
import { OS_CATALOG, TOOL_CATALOG, type OSItem, type ToolItem } from "@/lib/data/catalog";

type TabFilter = "all" | "os" | "tools";

export default function BuilderScreen() {
  const colors = useColors();
  const [selectedOSIds, setSelectedOSIds] = useState<Set<string>>(new Set());
  const [selectedToolIds, setSelectedToolIds] = useState<Set<string>>(new Set());
  const [activeTab, setActiveTab] = useState<TabFilter>("all");

  const toggleOS = useCallback((id: string) => {
    setSelectedOSIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  }, []);

  const toggleTool = useCallback((id: string) => {
    setSelectedToolIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  }, []);

  const totalSize = useMemo(() => {
    let size = 0;
    OS_CATALOG.forEach((os) => {
      if (selectedOSIds.has(os.id)) size += os.sizeGB;
    });
    TOOL_CATALOG.forEach((tool) => {
      if (selectedToolIds.has(tool.id)) size += tool.sizeGB;
    });
    return size;
  }, [selectedOSIds, selectedToolIds]);

  const totalItems = selectedOSIds.size + selectedToolIds.size;

  const recommendedUSB = useMemo(() => {
    if (totalSize <= 8) return "8 GB";
    if (totalSize <= 16) return "16 GB";
    if (totalSize <= 32) return "32 GB";
    if (totalSize <= 64) return "64 GB";
    if (totalSize <= 128) return "128 GB";
    return "256 GB+";
  }, [totalSize]);

  const handleExport = () => {
    const recipe = {
      name: "Bobby's PhoenixDrive USB Recipe",
      createdAt: new Date().toISOString(),
      estimatedSizeGB: Math.round(totalSize * 10) / 10,
      recommendedUSB,
      operatingSystems: OS_CATALOG.filter((os) => selectedOSIds.has(os.id)).map((os) => ({
        id: os.id,
        name: os.name,
        version: os.version,
        sizeGB: os.sizeGB,
        bootMethod: os.bootMethod,
      })),
      tools: TOOL_CATALOG.filter((t) => selectedToolIds.has(t.id)).map((t) => ({
        id: t.id,
        name: t.name,
        version: t.version,
        sizeGB: t.sizeGB,
      })),
    };

    if (Platform.OS === "web") {
      alert("Recipe exported! In the full app, this would generate a JSON file for Bobby's PhoenixDrive desktop builder.\n\n" + JSON.stringify(recipe, null, 2).substring(0, 500));
    } else {
      Alert.alert(
        "Recipe Exported",
        `Your USB recipe with ${totalItems} items (${Math.round(totalSize * 10) / 10} GB) is ready. Sync with Bobby's PhoenixDrive desktop builder to create your USB.`,
        [{ text: "OK" }]
      );
    }
  };

  const selectAllOS = () => {
    setSelectedOSIds(new Set(OS_CATALOG.map((os) => os.id)));
  };

  const selectAllTools = () => {
    setSelectedToolIds(new Set(TOOL_CATALOG.map((t) => t.id)));
  };

  const clearAll = () => {
    setSelectedOSIds(new Set());
    setSelectedToolIds(new Set());
  };

  const renderOSItem = (os: OSItem) => {
    const isSelected = selectedOSIds.has(os.id);
    return (
      <Pressable
        key={os.id}
        onPress={() => toggleOS(os.id)}
        style={({ pressed }) => [
          styles.itemCard,
          {
            backgroundColor: isSelected ? colors.primary + "10" : colors.surface,
            borderColor: isSelected ? colors.primary + "40" : colors.border,
          },
          pressed && { opacity: 0.8 },
        ]}
      >
        <View style={[styles.itemCheck, { borderColor: isSelected ? colors.primary : colors.border, backgroundColor: isSelected ? colors.primary : "transparent" }]}>
          {isSelected && <IconSymbol name="checkmark.circle.fill" size={16} color="#FFFFFF" />}
        </View>
        <View style={[styles.itemIcon, { backgroundColor: os.color + "18" }]}>
          <IconSymbol name={os.iconName as any} size={20} color={os.color} />
        </View>
        <View style={styles.itemText}>
          <Text style={[styles.itemName, { color: colors.foreground }]}>
            {os.name}
          </Text>
          <Text style={[styles.itemVersion, { color: colors.muted }]}>
            {os.version} · {os.sizeGB} GB · {os.architectures.join(", ")}
          </Text>
        </View>
        <View style={[styles.categoryBadge, { backgroundColor: getCategoryColor(os.category) + "18" }]}>
          <Text style={[styles.categoryText, { color: getCategoryColor(os.category) }]}>
            {os.category}
          </Text>
        </View>
      </Pressable>
    );
  };

  const renderToolItem = (tool: ToolItem) => {
    const isSelected = selectedToolIds.has(tool.id);
    return (
      <Pressable
        key={tool.id}
        onPress={() => toggleTool(tool.id)}
        style={({ pressed }) => [
          styles.itemCard,
          {
            backgroundColor: isSelected ? colors.primary + "10" : colors.surface,
            borderColor: isSelected ? colors.primary + "40" : colors.border,
          },
          pressed && { opacity: 0.8 },
        ]}
      >
        <View style={[styles.itemCheck, { borderColor: isSelected ? colors.primary : colors.border, backgroundColor: isSelected ? colors.primary : "transparent" }]}>
          {isSelected && <IconSymbol name="checkmark.circle.fill" size={16} color="#FFFFFF" />}
        </View>
        <View style={[styles.itemIcon, { backgroundColor: tool.color + "18" }]}>
          <IconSymbol name={tool.iconName as any} size={20} color={tool.color} />
        </View>
        <View style={styles.itemText}>
          <Text style={[styles.itemName, { color: colors.foreground }]}>
            {tool.name}
          </Text>
          <Text style={[styles.itemVersion, { color: colors.muted }]}>
            v{tool.version} · {tool.sizeGB >= 1 ? tool.sizeGB + " GB" : Math.round(tool.sizeGB * 1024) + " MB"}
          </Text>
        </View>
        <View style={[styles.categoryBadge, { backgroundColor: tool.color + "18" }]}>
          <Text style={[styles.categoryText, { color: tool.color }]}>
            {tool.category}
          </Text>
        </View>
      </Pressable>
    );
  };

  return (
    <ScreenContainer>
      <ScrollView
        contentContainerStyle={{ paddingBottom: 120 }}
        showsVerticalScrollIndicator={false}
      >
        {/* Header */}
        <View style={styles.header}>
          <Text style={[styles.screenTitle, { color: colors.foreground }]}>
            USB Builder
          </Text>
          <Text style={[styles.screenSubtitle, { color: colors.muted }]}>
            Select operating systems and tools to include on your universal USB
          </Text>
        </View>

        {/* Size Summary Bar */}
        <View style={[styles.summaryBar, { backgroundColor: colors.surface, borderColor: colors.border }]}>
          <View style={styles.summaryLeft}>
            <Text style={[styles.summaryLabel, { color: colors.muted }]}>Selected</Text>
            <Text style={[styles.summaryValue, { color: colors.foreground }]}>{totalItems} items</Text>
          </View>
          <View style={styles.summaryDivider} />
          <View style={styles.summaryLeft}>
            <Text style={[styles.summaryLabel, { color: colors.muted }]}>Total Size</Text>
            <Text style={[styles.summaryValue, { color: colors.primary }]}>
              {Math.round(totalSize * 10) / 10} GB
            </Text>
          </View>
          <View style={styles.summaryDivider} />
          <View style={styles.summaryLeft}>
            <Text style={[styles.summaryLabel, { color: colors.muted }]}>USB Needed</Text>
            <Text style={[styles.summaryValue, { color: colors.foreground }]}>{recommendedUSB}</Text>
          </View>
        </View>

        {/* Filter Tabs */}
        <View style={styles.tabRow}>
          {(["all", "os", "tools"] as TabFilter[]).map((tab) => (
            <Pressable
              key={tab}
              onPress={() => setActiveTab(tab)}
              style={({ pressed }) => [
                styles.tabBtn,
                {
                  backgroundColor: activeTab === tab ? colors.primary : colors.surface,
                  borderColor: activeTab === tab ? colors.primary : colors.border,
                },
                pressed && { opacity: 0.8 },
              ]}
            >
              <Text
                style={[
                  styles.tabBtnText,
                  { color: activeTab === tab ? "#FFFFFF" : colors.muted },
                ]}
              >
                {tab === "all" ? "All" : tab === "os" ? "Operating Systems" : "Repair Tools"}
              </Text>
            </Pressable>
          ))}
        </View>

        {/* Quick Actions */}
        <View style={styles.quickActions}>
          <Pressable
            onPress={selectAllOS}
            style={({ pressed }) => [styles.quickBtn, pressed && { opacity: 0.7 }]}
          >
            <Text style={[styles.quickBtnText, { color: colors.primary }]}>Select All OS</Text>
          </Pressable>
          <Pressable
            onPress={selectAllTools}
            style={({ pressed }) => [styles.quickBtn, pressed && { opacity: 0.7 }]}
          >
            <Text style={[styles.quickBtnText, { color: colors.primary }]}>Select All Tools</Text>
          </Pressable>
          <Pressable
            onPress={clearAll}
            style={({ pressed }) => [styles.quickBtn, pressed && { opacity: 0.7 }]}
          >
            <Text style={[styles.quickBtnText, { color: colors.error }]}>Clear All</Text>
          </Pressable>
        </View>

        {/* OS List */}
        {(activeTab === "all" || activeTab === "os") && (
          <View style={styles.section}>
            <Text style={[styles.sectionTitle, { color: colors.foreground }]}>
              Operating Systems
            </Text>
            {OS_CATALOG.map(renderOSItem)}
          </View>
        )}

        {/* Tools List */}
        {(activeTab === "all" || activeTab === "tools") && (
          <View style={styles.section}>
            <Text style={[styles.sectionTitle, { color: colors.foreground }]}>
              Repair & Diagnostic Tools
            </Text>
            {TOOL_CATALOG.map(renderToolItem)}
          </View>
        )}
      </ScrollView>

      {/* Floating Export Button */}
      {totalItems > 0 && (
        <View style={[styles.floatingBar, { backgroundColor: colors.background, borderTopColor: colors.border }]}>
          <View style={{ flex: 1 }}>
            <Text style={[styles.floatingText, { color: colors.foreground }]}>
              {totalItems} items · {Math.round(totalSize * 10) / 10} GB
            </Text>
            <Text style={[styles.floatingSubtext, { color: colors.muted }]}>
              Recommended: {recommendedUSB} USB 3.0 drive
            </Text>
          </View>
          <Pressable
            onPress={handleExport}
            style={({ pressed }) => [
              styles.exportBtn,
              { backgroundColor: colors.primary },
              pressed && { opacity: 0.9, transform: [{ scale: 0.97 }] },
            ]}
          >
            <IconSymbol name="square.and.arrow.up" size={18} color="#FFFFFF" />
            <Text style={styles.exportBtnText}>Export</Text>
          </Pressable>
        </View>
      )}
    </ScreenContainer>
  );
}

function getCategoryColor(category: string): string {
  switch (category) {
    case "windows": return "#0078D4";
    case "linux": return "#E95420";
    case "macos": return "#AC39FF";
    case "chromeos": return "#4285F4";
    default: return "#656D76";
  }
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
  summaryBar: {
    flexDirection: "row",
    marginHorizontal: 16,
    marginTop: 16,
    padding: 14,
    borderRadius: 14,
    borderWidth: 1,
    alignItems: "center",
  },
  summaryLeft: {
    flex: 1,
    alignItems: "center",
    gap: 2,
  },
  summaryLabel: {
    fontSize: 11,
    fontWeight: "600",
  },
  summaryValue: {
    fontSize: 16,
    fontWeight: "800",
  },
  summaryDivider: {
    width: 1,
    height: 30,
    backgroundColor: "#D0D7DE30",
    marginHorizontal: 4,
  },
  tabRow: {
    flexDirection: "row",
    paddingHorizontal: 16,
    marginTop: 16,
    gap: 8,
  },
  tabBtn: {
    paddingHorizontal: 14,
    paddingVertical: 8,
    borderRadius: 20,
    borderWidth: 1,
  },
  tabBtnText: {
    fontSize: 13,
    fontWeight: "600",
  },
  quickActions: {
    flexDirection: "row",
    paddingHorizontal: 16,
    marginTop: 12,
    gap: 12,
  },
  quickBtn: {
    paddingVertical: 4,
  },
  quickBtnText: {
    fontSize: 13,
    fontWeight: "600",
  },
  section: {
    paddingHorizontal: 16,
    marginTop: 20,
    gap: 8,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: "700",
    marginBottom: 4,
  },
  itemCard: {
    flexDirection: "row",
    alignItems: "center",
    padding: 14,
    borderRadius: 12,
    borderWidth: 1,
    gap: 10,
  },
  itemCheck: {
    width: 24,
    height: 24,
    borderRadius: 12,
    borderWidth: 2,
    alignItems: "center",
    justifyContent: "center",
  },
  itemIcon: {
    width: 40,
    height: 40,
    borderRadius: 10,
    alignItems: "center",
    justifyContent: "center",
  },
  itemText: {
    flex: 1,
    gap: 2,
  },
  itemName: {
    fontSize: 15,
    fontWeight: "600",
  },
  itemVersion: {
    fontSize: 12,
  },
  categoryBadge: {
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 6,
  },
  categoryText: {
    fontSize: 10,
    fontWeight: "700",
    textTransform: "uppercase",
  },
  floatingBar: {
    position: "absolute",
    bottom: 0,
    left: 0,
    right: 0,
    flexDirection: "row",
    alignItems: "center",
    paddingHorizontal: 16,
    paddingVertical: 14,
    paddingBottom: 28,
    borderTopWidth: 1,
    gap: 12,
  },
  floatingText: {
    fontSize: 15,
    fontWeight: "700",
  },
  floatingSubtext: {
    fontSize: 12,
    marginTop: 2,
  },
  exportBtn: {
    flexDirection: "row",
    alignItems: "center",
    paddingHorizontal: 20,
    paddingVertical: 12,
    borderRadius: 12,
    gap: 8,
  },
  exportBtnText: {
    color: "#FFFFFF",
    fontSize: 15,
    fontWeight: "700",
  },
});
