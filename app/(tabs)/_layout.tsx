import { Tabs } from "expo-router";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { Platform } from "react-native";

import { HapticTab } from "@/components/haptic-tab";
import { IconSymbol } from "@/components/ui/icon-symbol";

// Phoenix Core premium tab bar — Electric Blue active tint, Gold border, Deep Navy background
export default function TabLayout() {
  const insets = useSafeAreaInsets();
  const bottomPadding = Platform.OS === "web" ? 12 : Math.max(insets.bottom, 8);
  const tabBarHeight = 60 + bottomPadding;

  return (
    <Tabs
      screenOptions={{
        tabBarActiveTintColor: "#00d2ff",    // Electric Blue for active
        tabBarInactiveTintColor: "rgba(255,255,255,0.35)",
        headerShown: false,
        tabBarButton: HapticTab,
        tabBarStyle: {
          paddingTop: 10,
          paddingBottom: bottomPadding,
          height: tabBarHeight,
          backgroundColor: "#050811",
          borderTopColor: "rgba(255, 215, 0, 0.25)",
          borderTopWidth: 1,
          // Subtle shadow/glow upward
          shadowColor: "#00d2ff",
          shadowOffset: { width: 0, height: -2 },
          shadowOpacity: 0.08,
          shadowRadius: 8,
          elevation: 12,
        },
        tabBarLabelStyle: {
          fontSize: 10,
          fontWeight: "700",
          letterSpacing: 0.5,
          textTransform: "uppercase",
          marginTop: 2,
        },
      }}
    >
      <Tabs.Screen
        name="index"
        options={{
          title: "Home",
          tabBarIcon: ({ color }) => (
            <IconSymbol size={24} name="house.fill" color={color} />
          ),
        }}
      />
      <Tabs.Screen
        name="wizard"
        options={{
          title: "Device",
          tabBarIcon: ({ color }) => (
            <IconSymbol size={24} name="cpu" color={color} />
          ),
        }}
      />
      <Tabs.Screen
        name="builder"
        options={{
          title: "USB Builder",
          tabBarIcon: ({ color }) => (
            <IconSymbol size={26} name="externaldrive.fill" color={color} />
          ),
        }}
      />
      <Tabs.Screen
        name="knowledge"
        options={{
          title: "Knowledge",
          tabBarIcon: ({ color }) => (
            <IconSymbol size={24} name="book.fill" color={color} />
          ),
        }}
      />
    </Tabs>
  );
}
