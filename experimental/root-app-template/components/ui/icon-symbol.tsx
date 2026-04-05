import MaterialIcons from "@expo/vector-icons/MaterialIcons";
import { SymbolWeight, SymbolViewProps } from "expo-symbols";
import { ComponentProps } from "react";
import { OpaqueColorValue, type StyleProp, type TextStyle } from "react-native";

type IconMapping = Record<string, ComponentProps<typeof MaterialIcons>["name"]>;
type IconSymbolName = keyof typeof MAPPING;

const MAPPING = {
  // Tab bar icons
  "house.fill": "home",
  "cpu": "memory",
  "externaldrive.fill": "usb",
  "book.fill": "menu-book",
  // Navigation
  "chevron.right": "chevron-right",
  "chevron.left": "chevron-left",
  "arrow.right": "arrow-forward",
  "arrow.left": "arrow-back",
  // Status icons
  "checkmark.circle.fill": "check-circle",
  "exclamationmark.triangle.fill": "warning",
  "xmark.circle.fill": "cancel",
  "info.circle.fill": "info",
  // Content icons
  "paperplane.fill": "send",
  "magnifyingglass": "search",
  "star.fill": "star",
  "bookmark.fill": "bookmark",
  "square.and.arrow.up": "share",
  "doc.on.doc": "content-copy",
  "trash.fill": "delete",
  "plus.circle.fill": "add-circle",
  "minus.circle.fill": "remove-circle",
  // Device icons
  "laptopcomputer": "laptop",
  "desktopcomputer": "desktop-mac",
  "terminal": "terminal",
  "globe": "public",
  "wrench.fill": "build",
  "hammer.fill": "construction",
  "shield.fill": "security",
  "bolt.fill": "flash-on",
  "flame.fill": "local-fire-department",
  // OS category icons
  "window": "laptop",
  "penguin": "terminal",
  "apple": "desktop-mac",
  "chrome": "public",
  // Tool category icons
  "healing": "healing",
  "build": "build",
  "storage": "storage",
  "memory": "memory",
  "restore": "restore",
  "content-copy": "content-copy",
  "delete-forever": "delete-forever",
  "developer-board": "developer-board",
} as IconMapping;

export function IconSymbol({
  name,
  size = 24,
  color,
  style,
}: {
  name: IconSymbolName;
  size?: number;
  color: string | OpaqueColorValue;
  style?: StyleProp<TextStyle>;
  weight?: SymbolWeight;
}) {
  const mappedName = MAPPING[name as string] || "help-outline";
  return <MaterialIcons color={color} size={size} name={mappedName} style={style} />;
}
