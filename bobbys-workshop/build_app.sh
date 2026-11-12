#!/bin/zsh
set -e

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
APP_NAME="BobFWTools"
EXEC_NAME="BobFWTools"

# Dynamic --human flag detection: auto-enable on interactive TTY sessions
HUMAN_MODE=false
if [[ "$*" == *"--human"* ]] || ([[ -t 1 ]] && [[ -z "$CI" ]]); then
    HUMAN_MODE=true
fi

if [ "$HUMAN_MODE" = true ]; then
    C_CYAN="\033[1;36m"
    C_GREEN="\033[1;32m"
    C_YELLOW="\033[1;33m"
    C_MAGENTA="\033[1;35m"
    C_BOLD="\033[1m"
    C_DIM="\033[2m"
    C_RESET="\033[0m"
else
    C_CYAN=""
    C_GREEN=""
    C_YELLOW=""
    C_MAGENTA=""
    C_BOLD=""
    C_DIM=""
    C_RESET=""
fi

BUILD_ROOT="/tmp/BobFWTools_build"
rm -rf "${BUILD_ROOT}"
mkdir -p "${BUILD_ROOT}"

APP_BUNDLE="${BUILD_ROOT}/${APP_NAME}.app"
CONTENTS_DIR="${APP_BUNDLE}/Contents"
MACOS_DIR="${CONTENTS_DIR}/MacOS"
FRAMEWORKS_DIR="${CONTENTS_DIR}/Frameworks"
RESOURCES_DIR="${CONTENTS_DIR}/Resources"
mkdir -p /tmp/swift-module-cache
export SWIFT_MODULE_CACHE_PATH="/tmp/swift-module-cache"
export CLANG_MODULE_CACHE_PATH="/tmp/swift-module-cache"
BOOTFORGE_BIN="${PROJECT_DIR}/tools/bootforgeusb"
ENTITLEMENTS_PLIST="${PROJECT_DIR}/entitlements.plist"

rm -rf "${APP_BUNDLE}"
mkdir -p "${MACOS_DIR}" "${FRAMEWORKS_DIR}" "${RESOURCES_DIR}"

echo "[1/5] Generating Store-Compliant Info.plist & entitlements.plist..."
cat > "${CONTENTS_DIR}/Info.plist" <<PLIST_EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleDevelopmentRegion</key>
    <string>en</string>
    <key>CFBundleExecutable</key>
    <string>${EXEC_NAME}</string>
    <key>CFBundleIconFile</key>
    <string>AppIcon</string>
    <key>CFBundleIdentifier</key>
    <string>com.bobbyblanco.bobfwtools.studio</string>
    <key>CFBundleInfoDictionaryVersion</key>
    <string>6.0</string>
    <key>CFBundleName</key>
    <string>BobFWTools</string>
    <key>CFBundleDisplayName</key>
    <string>BobFWTools Studio</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>CFBundleShortVersionString</key>
    <string>5.0.0</string>
    <key>CFBundleVersion</key>
    <string>500</string>
    <key>LSApplicationCategoryType</key>
    <string>public.app-category.utilities</string>
    <key>LSMinimumSystemVersion</key>
    <string>12.0</string>
    <key>NSHighResolutionCapable</key>
    <true/>
    <key>ITSAppUsesNonExemptEncryption</key>
    <false/>
    <key>NSHumanReadableCopyright</key>
    <string>Copyright © 2026 Bobby's Workshop — Phoenix Forge. All rights reserved.</string>
    <key>NSUSBUsageDescription</key>
    <string>BobFWTools communicates with connected USB mobile devices for hardware diagnostics, telemetry verification, and authorized firmware servicing.</string>
    <key>NSDownloadsFolderUsageDescription</key>
    <string>BobFWTools inspects official firmware archives in your Downloads folder for SHA-256 verification and anti-rollback binary matching.</string>
</dict>
</plist>
PLIST_EOF

cat > "${RESOURCES_DIR}/PrivacyInfo.xcprivacy" <<PRIV_EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>NSPrivacyTracking</key>
    <false/>
    <key>NSPrivacyTrackingDomains</key>
    <array/>
    <key>NSPrivacyCollectedDataTypes</key>
    <array/>
    <key>NSPrivacyAccessedAPITypes</key>
    <array>
        <dict>
            <key>NSPrivacyAccessedAPIType</key>
            <string>NSPrivacyAccessedAPICategoryDiskSpace</string>
            <key>NSPrivacyAccessedAPITypeReasons</key>
            <array>
                <string>E174.1</string>
            </array>
        </dict>
        <dict>
            <key>NSPrivacyAccessedAPIType</key>
            <string>NSPrivacyAccessedAPICategoryFileTimestamp</string>
            <key>NSPrivacyAccessedAPITypeReasons</key>
            <array>
                <string>DDA9.1</string>
            </array>
        </dict>
    </array>
</dict>
</plist>
PRIV_EOF

cat > "${ENTITLEMENTS_PLIST}" <<ENT_EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>com.apple.security.cs.allow-unsigned-executable-memory</key>
    <true/>
    <key>com.apple.security.cs.disable-library-validation</key>
    <true/>
    <key>com.apple.security.device.usb</key>
    <true/>
    <key>com.apple.security.device.serial</key>
    <true/>
    <key>com.apple.security.files.user-selected.read-write</key>
    <true/>
    <key>com.apple.security.files.downloads.read-write</key>
    <true/>
    <key>com.apple.security.network.client</key>
    <true/>
</dict>
</plist>
ENT_EOF

ENTITLEMENTS_STORE_PLIST="${PROJECT_DIR}/entitlements.store.plist"
ENTITLEMENTS_HELPER_PLIST="${PROJECT_DIR}/entitlements.helper.plist"

cat > "${ENTITLEMENTS_STORE_PLIST}" <<STORE_ENT_EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>com.apple.security.app-sandbox</key>
    <true/>
    <key>com.apple.security.device.usb</key>
    <true/>
    <key>com.apple.security.device.serial</key>
    <true/>
    <key>com.apple.security.files.user-selected.read-write</key>
    <true/>
    <key>com.apple.security.files.downloads.read-write</key>
    <true/>
    <key>com.apple.security.network.client</key>
    <true/>
</dict>
</plist>
STORE_ENT_EOF

cat > "${ENTITLEMENTS_HELPER_PLIST}" <<HELPER_ENT_EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>com.apple.security.app-sandbox</key>
    <true/>
    <key>com.apple.security.inherit</key>
    <true/>
</dict>
</plist>
HELPER_ENT_EOF

echo "[2/5] Installing AppIcon.icns & Bundled Resources..."
if [ -f "${PROJECT_DIR}/store_packaging/macos/AppIcon.icns" ]; then
    cp "${PROJECT_DIR}/store_packaging/macos/AppIcon.icns" "${RESOURCES_DIR}/AppIcon.icns"
fi
if [ -f "${PROJECT_DIR}/Resources/AppIcon_1024.png" ]; then
    cp "${PROJECT_DIR}/Resources/AppIcon_1024.png" "${RESOURCES_DIR}/AppIcon_1024.png"
fi
if [ -f "${PROJECT_DIR}/Resources/SplashHero.png" ]; then
    cp "${PROJECT_DIR}/Resources/SplashHero.png" "${RESOURCES_DIR}/SplashHero.png"
fi
if [ -f "${PROJECT_DIR}/Resources/chipset_signatures.json" ]; then
    cp "${PROJECT_DIR}/Resources/chipset_signatures.json" "${RESOURCES_DIR}/chipset_signatures.json"
fi

echo "[3/5] Bundling native Rust BootForge USB engine, ADB/Fastboot/Heimdall & self-contained libusb dylib..."
if [ -f "${PROJECT_DIR}/tools/bootforgeusb" ]; then
    cp "${PROJECT_DIR}/tools/bootforgeusb" "${MACOS_DIR}/bootforgeusb"
    chmod +x "${MACOS_DIR}/bootforgeusb"
elif [ -f "${BOOTFORGE_BIN}" ]; then
    cp "${BOOTFORGE_BIN}" "${MACOS_DIR}/bootforgeusb"
    chmod +x "${MACOS_DIR}/bootforgeusb"
fi

if [ -f "${PROJECT_DIR}/tools/libusb-1.0.0.dylib" ]; then
    cp "${PROJECT_DIR}/tools/libusb-1.0.0.dylib" "${FRAMEWORKS_DIR}/libusb-1.0.0.dylib"
    chmod 755 "${FRAMEWORKS_DIR}/libusb-1.0.0.dylib"
elif [ -f "/usr/local/opt/libusb/lib/libusb-1.0.0.dylib" ]; then
    cp "/usr/local/opt/libusb/lib/libusb-1.0.0.dylib" "${FRAMEWORKS_DIR}/libusb-1.0.0.dylib" 2>/dev/null || true
    chmod 755 "${FRAMEWORKS_DIR}/libusb-1.0.0.dylib" 2>/dev/null || true
fi

if [ -f "${FRAMEWORKS_DIR}/libusb-1.0.0.dylib" ] && [ -f "${MACOS_DIR}/bootforgeusb" ]; then
    install_name_tool -id "@executable_path/../Frameworks/libusb-1.0.0.dylib" "${FRAMEWORKS_DIR}/libusb-1.0.0.dylib" 2>/dev/null || true
    install_name_tool -change "/usr/local/opt/libusb/lib/libusb-1.0.0.dylib" "@executable_path/../Frameworks/libusb-1.0.0.dylib" "${MACOS_DIR}/bootforgeusb" 2>/dev/null || true
fi

for TOOL in adb fastboot heimdall samloader; do
    if [ -f "${PROJECT_DIR}/tools/${TOOL}" ]; then
        cp "${PROJECT_DIR}/tools/${TOOL}" "${MACOS_DIR}/${TOOL}"
        chmod +x "${MACOS_DIR}/${TOOL}"
    elif [ -f "/usr/local/bin/${TOOL}" ]; then
        cp -L "/usr/local/bin/${TOOL}" "${MACOS_DIR}/${TOOL}" 2>/dev/null || true
        chmod +x "${MACOS_DIR}/${TOOL}" 2>/dev/null || true
    fi
done

if [ -f "${PROJECT_DIR}/tools/payload_dumper.py" ]; then
    cp "${PROJECT_DIR}/tools/payload_dumper.py" "${RESOURCES_DIR}/payload_dumper.py"
    chmod +x "${RESOURCES_DIR}/payload_dumper.py"
fi

echo "[4/5] Compiling Swift sources into Universal 2 (x86_64 + arm64) native macOS binary..."
rm -rf "${BUILD_ROOT}/Sources"
cp -R -X "${PROJECT_DIR}/Sources" "${BUILD_ROOT}/Sources"
swiftc \
    -O \
    -module-cache-path /tmp/swift-module-cache \
    -target x86_64-apple-macos12.0 \
    -parse-as-library \
    "${BUILD_ROOT}/Sources/DeviceMasterRegistry.swift" \
    "${BUILD_ROOT}/Sources/ServicingEngine.swift" \
    "${BUILD_ROOT}/Sources/MainViews.swift" \
    "${BUILD_ROOT}/Sources/AppMain.swift" \
    -o "${MACOS_DIR}/${EXEC_NAME}_x86_64"

swiftc \
    -O \
    -module-cache-path /tmp/swift-module-cache \
    -target arm64-apple-macos12.0 \
    -parse-as-library \
    "${BUILD_ROOT}/Sources/DeviceMasterRegistry.swift" \
    "${BUILD_ROOT}/Sources/ServicingEngine.swift" \
    "${BUILD_ROOT}/Sources/MainViews.swift" \
    "${BUILD_ROOT}/Sources/AppMain.swift" \
    -o "${MACOS_DIR}/${EXEC_NAME}_arm64"

lipo -create -output "${MACOS_DIR}/${EXEC_NAME}" "${MACOS_DIR}/${EXEC_NAME}_x86_64" "${MACOS_DIR}/${EXEC_NAME}_arm64"
rm -f "${MACOS_DIR}/${EXEC_NAME}_x86_64" "${MACOS_DIR}/${EXEC_NAME}_arm64"

echo "[5/6] Signing (inside-out Hardened Runtime + Unrestricted Owner Entitlements) and packaging YOUR Private Standalone Owner Copy..."
find "${APP_BUNDLE}" -name "._*" -delete 2>/dev/null || true
xattr -c "${APP_BUNDLE}" 2>/dev/null || true
xattr -cr "${APP_BUNDLE}" 2>/dev/null || true
xattr -d com.apple.FinderInfo "${APP_BUNDLE}" 2>/dev/null || true
xattr -d com.apple.fileprovider.fpfs#P "${APP_BUNDLE}" 2>/dev/null || true
if [ -f "${FRAMEWORKS_DIR}/libusb-1.0.0.dylib" ]; then
    codesign --force --sign - --options runtime "${FRAMEWORKS_DIR}/libusb-1.0.0.dylib"
fi
for TOOL in bootforgeusb adb fastboot heimdall samloader; do
    if [ -f "${MACOS_DIR}/${TOOL}" ]; then
        codesign --force --sign - --options runtime "${MACOS_DIR}/${TOOL}"
    fi
done
find "${APP_BUNDLE}" -name "._*" -delete 2>/dev/null || true
xattr -c "${APP_BUNDLE}" 2>/dev/null || true
xattr -cr "${APP_BUNDLE}" 2>/dev/null || true
codesign --force --sign - --options runtime --entitlements "${ENTITLEMENTS_PLIST}" "${APP_BUNDLE}"

OWNER_DIST_DIR="${PROJECT_DIR}/dist/Owner-Private-Only"
rm -rf "${OWNER_DIST_DIR}" "${PROJECT_DIR}/${APP_NAME}.app"
mkdir -p "${OWNER_DIST_DIR}"
chmod 700 "${OWNER_DIST_DIR}"
cp -R "${APP_BUNDLE}" "${OWNER_DIST_DIR}/${APP_NAME}.app"
cp -R "${APP_BUNDLE}" "${PROJECT_DIR}/${APP_NAME}.app"
ditto -c -k --sequesterRsrc --keepParent "${APP_BUNDLE}" "${OWNER_DIST_DIR}/BobFWTools-Owner-Private-macOS.zip"
chmod 600 "${OWNER_DIST_DIR}/BobFWTools-Owner-Private-macOS.zip"

killall "${APP_NAME}" 2>/dev/null || true
sleep 1
if rm -rf "/Applications/${APP_NAME}.app" 2>/dev/null && cp -R "${APP_BUNDLE}" "/Applications/${APP_NAME}.app" 2>/dev/null; then
    echo ""
    echo "${C_GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${C_RESET}"
    echo "${C_BOLD} 🚀 PRIMARY AGENT HOST & OPERATOR RUNTIME: ${C_CYAN}/Applications/${APP_NAME}.app${C_RESET}"
    echo "${C_GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${C_RESET}"
    echo "  ${C_BOLD}Status:${C_RESET}       ${C_GREEN}● INSTALLED & READY FOR IMMEDIATE USE${C_RESET}"
    echo "  ${C_BOLD}Architecture:${C_RESET} Universal 2 (Native Apple Silicon arm64 + Intel x86_64)"
    echo "  ${C_BOLD}Permissions:${C_RESET}  Hardened Runtime + Direct USB/Modem/Fastboot Access"
    echo "  ${C_BOLD}Launch Now:${C_RESET}   ${C_CYAN}open /Applications/${APP_NAME}.app${C_RESET}"
    echo "${C_GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${C_RESET}"
    echo ""
else
    echo "Preserved local app in ${OWNER_DIST_DIR}/${APP_NAME}.app"
fi

echo "[6/6] Compiling & packaging SEPARATE Public Store Submission Edition (-DSTORE_EDITION, zero Owner code)..."
STORE_DIST_DIR="${PROJECT_DIR}/dist/Store-Submission"
STORE_BUILD_DIR="${BUILD_ROOT}/store_build"
STORE_BUNDLE="${STORE_BUILD_DIR}/${APP_NAME}.app"
rm -rf "${STORE_DIST_DIR}" "${STORE_BUILD_DIR}"
mkdir -p "${STORE_DIST_DIR}" "${STORE_BUILD_DIR}"
cp -R "${APP_BUNDLE}" "${STORE_BUNDLE}"

swiftc \
    -O \
    -module-cache-path /tmp/swift-module-cache \
    -DSTORE_EDITION \
    -target x86_64-apple-macos12.0 \
    -parse-as-library \
    "${BUILD_ROOT}/Sources/DeviceMasterRegistry.swift" \
    "${BUILD_ROOT}/Sources/ServicingEngine.swift" \
    "${BUILD_ROOT}/Sources/MainViews.swift" \
    "${BUILD_ROOT}/Sources/AppMain.swift" \
    -o "${STORE_BUNDLE}/Contents/MacOS/${EXEC_NAME}_x86_64"

swiftc \
    -O \
    -module-cache-path /tmp/swift-module-cache \
    -DSTORE_EDITION \
    -target arm64-apple-macos12.0 \
    -parse-as-library \
    "${BUILD_ROOT}/Sources/DeviceMasterRegistry.swift" \
    "${BUILD_ROOT}/Sources/ServicingEngine.swift" \
    "${BUILD_ROOT}/Sources/MainViews.swift" \
    "${BUILD_ROOT}/Sources/AppMain.swift" \
    -o "${STORE_BUNDLE}/Contents/MacOS/${EXEC_NAME}_arm64"

lipo -create -output "${STORE_BUNDLE}/Contents/MacOS/${EXEC_NAME}" "${STORE_BUNDLE}/Contents/MacOS/${EXEC_NAME}_x86_64" "${STORE_BUNDLE}/Contents/MacOS/${EXEC_NAME}_arm64"
rm -f "${STORE_BUNDLE}/Contents/MacOS/${EXEC_NAME}_x86_64" "${STORE_BUNDLE}/Contents/MacOS/${EXEC_NAME}_arm64"

find "${STORE_BUNDLE}" -name "._*" -delete 2>/dev/null || true
xattr -c "${STORE_BUNDLE}" 2>/dev/null || true
xattr -cr "${STORE_BUNDLE}" 2>/dev/null || true
xattr -d com.apple.FinderInfo "${STORE_BUNDLE}" 2>/dev/null || true
xattr -d com.apple.fileprovider.fpfs#P "${STORE_BUNDLE}" 2>/dev/null || true
for TOOL in bootforgeusb adb fastboot heimdall samloader; do
    if [ -f "${STORE_BUNDLE}/Contents/MacOS/${TOOL}" ]; then
        codesign --force --sign - --options runtime --entitlements "${ENTITLEMENTS_HELPER_PLIST}" "${STORE_BUNDLE}/Contents/MacOS/${TOOL}"
    fi
done
find "${STORE_BUNDLE}" -name "._*" -delete 2>/dev/null || true
xattr -c "${STORE_BUNDLE}" 2>/dev/null || true
xattr -cr "${STORE_BUNDLE}" 2>/dev/null || true
xattr -d com.apple.FinderInfo "${STORE_BUNDLE}" 2>/dev/null || true
xattr -d com.apple.fileprovider.fpfs#P "${STORE_BUNDLE}" 2>/dev/null || true
codesign --force --sign - --options runtime --entitlements "${ENTITLEMENTS_STORE_PLIST}" "${STORE_BUNDLE}"
cp -R "${STORE_BUNDLE}" "${STORE_DIST_DIR}/${APP_NAME}.app"
ditto -c -k --sequesterRsrc --keepParent "${STORE_BUNDLE}" "${STORE_DIST_DIR}/BobFWTools-Store-Submission-macOS.zip"

echo ""
echo "${C_CYAN}══════════════════════════════════════════════════════════════════════${C_RESET}"
echo "${C_BOLD}  BOBFWTOOLS STUDIO · BUILD & DEPLOYMENT SUMMARY${C_RESET}"
echo "${C_CYAN}══════════════════════════════════════════════════════════════════════${C_RESET}"
echo "  1. ${C_BOLD}Agent Host Target (Installed):${C_RESET} ${C_GREEN}/Applications/${APP_NAME}.app${C_RESET}"
echo "  2. ${C_BOLD}Owner Private Standalone Zip :${C_RESET}  ${C_MAGENTA}${OWNER_DIST_DIR}/BobFWTools-Owner-Private-macOS.zip${C_RESET} ${C_DIM}(mode 600)${C_RESET}"
echo "  3. ${C_BOLD}Public Store Submission Zip  :${C_RESET}  ${C_YELLOW}${STORE_DIST_DIR}/BobFWTools-Store-Submission-macOS.zip${C_RESET}"
echo "${C_CYAN}══════════════════════════════════════════════════════════════════════${C_RESET}"
