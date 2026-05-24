// Load environment variables with proper priority (system > .env)
import "./scripts/load-env.js";
import type { ExpoConfig } from "expo/config";

// Bundle ID format: space.manus.<project_name_dots>.<timestamp>
// e.g., "my-app" created at 2024-01-15 10:30:45 -> "space.manus.my.app.t20240115103045"
// Bundle ID can only contain letters, numbers, and dots
// Android requires each dot-separated segment to start with a letter
const rawBundleId = "space.manus.phoenix.core.mobile.t20260312210432";
const bundleId =
  rawBundleId
    .replace(/[-_]/g, ".") // Replace hyphens/underscores with dots
    .replace(/[^a-zA-Z0-9.]/g, "") // Remove invalid chars
    .replace(/\.+/g, ".") // Collapse consecutive dots
    .replace(/^\.+|\.+$/g, "") // Trim leading/trailing dots
    .toLowerCase()
    .split(".")
    .map((segment) => {
      // Android requires each segment to start with a letter
      // Prefix with 'x' if segment starts with a digit
      return /^[a-zA-Z]/.test(segment) ? segment : "x" + segment;
    })
    .join(".") || "space.manus.app";
// Extract timestamp from bundle ID and prefix with "manus" for deep link scheme
// e.g., "space.manus.my.app.t20240115103045" -> "manus20240115103045"
const timestamp = bundleId.split(".").pop()?.replace(/^t/, "") ?? "";
const schemeFromBundleId = `manus${timestamp}`;

const env = {
  // App branding - update these values directly (do not use env vars)
  appName: "Bobby's PhoenixDrive",
  appSlug: "phoenix-core-mobile",
  // S3 URL of the app logo - set this to the URL returned by generate_image when creating custom logo
  // Leave empty to use the default icon from assets/images/icon.png
  logoUrl: "",
  scheme: schemeFromBundleId,
  iosBundleId: bundleId,
  androidPackage: bundleId,
  // Production API URL - update when deploying to production
  apiUrl: process.env.EXPO_PUBLIC_API_URL || "https://phoenixdrive-api.herokuapp.com",
  // WebSocket URL for real-time progress tracking
  wsUrl: process.env.EXPO_PUBLIC_WS_URL || "wss://phoenixdrive-api.herokuapp.com",
};

const config: ExpoConfig = {
  name: env.appName,
  slug: env.appSlug,
  description: "Bobby's PhoenixDrive: Create bootable USB drives for Windows, Linux, ChromeOS, and macOS. Simple planning tool that works with PhoenixCore for safe, reliable OS deployment.",
  version: "1.0.0",
  runtimeVersion: "1.0.0",
  orientation: "portrait",
  icon: "./assets/images/icon.png",
  primaryColor: "#FF6B35",
  scheme: env.scheme,
  userInterfaceStyle: "automatic",
  newArchEnabled: true,
  platforms: ["ios", "android", "web"],
  ios: {
    supportsTablet: true,
    bundleIdentifier: env.iosBundleId,
    buildNumber: "1",
    infoPlist: {
      ITSAppUsesNonExemptEncryption: false,
      NSLocalNetworkUsageDescription: "Bobby's PhoenixDrive needs local network access to detect USB devices and communicate with your computer.",
      NSBonjourServiceTypes: ["_http._tcp", "_ws._tcp"],
      NSMicrophoneUsageDescription: "Not used by Bobby's PhoenixDrive.",
      NSPhotoLibraryUsageDescription: "Not used by Bobby's PhoenixDrive.",
      NSCameraUsageDescription: "Not used by Bobby's PhoenixDrive."
    },
    entitlements: {
      "com.apple.developer.networking.local-network": true,
      "com.apple.developer.networking.multicast": true
    }
  },
  android: {
    adaptiveIcon: {
      backgroundColor: "#0D1117",
      foregroundImage: "./assets/images/android-icon-foreground.png",
      backgroundImage: "./assets/images/android-icon-background.png",
      monochromeImage: "./assets/images/android-icon-monochrome.png",
    },
    edgeToEdgeEnabled: true,
    predictiveBackGestureEnabled: false,
    package: env.androidPackage,
    permissions: ["POST_NOTIFICATIONS"],
    intentFilters: [
      {
        action: "VIEW",
        autoVerify: true,
        data: [
          {
            scheme: env.scheme,
            host: "*",
          },
        ],
        category: ["BROWSABLE", "DEFAULT"],
      },
    ],
  },
  web: {
    bundler: "metro",
    output: "static",
    favicon: "./assets/images/favicon.png",
  },
  plugins: [
    "expo-router",
    [
      "expo-audio",
      {
        microphonePermission: "Allow $(PRODUCT_NAME) to access your microphone.",
      },
    ],
    [
      "expo-video",
      {
        supportsBackgroundPlayback: true,
        supportsPictureInPicture: true,
      },
    ],
    [
      "expo-splash-screen",
      {
        image: "./assets/images/splash-icon.png",
        imageWidth: 200,
        resizeMode: "contain",
        backgroundColor: "#ffffff",
        dark: {
          backgroundColor: "#000000",
        },
      },
    ],
    [
      "expo-build-properties",
      {
        ios: {
          deploymentTarget: "15.1",
          useFrameworks: "static",
        },
        android: {
          buildArchs: ["armeabi-v7a", "arm64-v8a"],
          minSdkVersion: 24,
        },
      },
    ],
  ],
  experiments: {
    typedRoutes: true,
    reactCompiler: true,
  },
  extra: {
    eas: {
      projectId: "Ckayyn9SVaz8UPGNyasERW",
    },
  },
};

// Privacy policy URL - add to app store metadata
config.extra = config.extra || {};
config.extra.privacyUrl = "https://example.com/privacy";

export default config;
