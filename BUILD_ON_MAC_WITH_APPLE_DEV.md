# Building Bobby's PhoenixDrive on Mac with Apple Developer Account

This guide provides step-by-step instructions for building the desktop app on macOS and deploying the iOS app to the App Store using your Apple Developer account.

## Part 1: Desktop App Build on macOS

### Prerequisites

- macOS 10.13 or later
- Python 3.8+
- Xcode Command Line Tools
- Apple Developer Account (for code signing)

### Step 1: Install Build Tools

```bash
# Install Xcode Command Line Tools
xcode-select --install

# Install Python (if not already installed)
brew install python3

# Install PyInstaller and dependencies
pip3 install PyInstaller PyQt6 opencv-python requests python-socketio jsonschema
```

### Step 2: Clone and Navigate to Project

```bash
cd /path/to/phoenix-drive-desktop
```

### Step 3: Create App Icon

Ensure you have `assets/icon.icns` for macOS. If not, convert from PNG:

```bash
# Convert PNG to ICNS (requires ImageMagick)
brew install imagemagick
convert assets/icon.png -define icon:auto-resize=256,128,96,64,48,32,16 assets/icon.icns
```

### Step 4: Build macOS App Bundle

```bash
pyinstaller --onefile \
  --windowed \
  --icon=assets/icon.icns \
  --name=phoenix-drive \
  --add-data "assets:assets" \
  --add-data "src:src" \
  --osx-bundle-identifier=com.phoenixdrive.app \
  main.py
```

### Step 5: Code Sign the App

```bash
# Get your Team ID from Apple Developer account
TEAM_ID="XXXXXXXXXX"  # Replace with your Team ID

# Sign the app bundle
codesign --deep --force --verify --verbose \
  --sign "Developer ID Application: Your Name ($TEAM_ID)" \
  dist/phoenix-drive.app

# Verify signature
codesign --verify --verbose dist/phoenix-drive.app
```

### Step 6: Create DMG Installer

```bash
# Create DMG
hdiutil create -volname "PhoenixDrive" \
  -srcfolder dist/phoenix-drive.app \
  -ov -format UDZO \
  dist/PhoenixDrive.dmg

# Sign DMG
codesign --sign "Developer ID Application: Your Name ($TEAM_ID)" \
  dist/PhoenixDrive.dmg

# Verify DMG
codesign --verify --verbose dist/PhoenixDrive.dmg
```

### Step 7: Notarize the App (Required for Distribution)

```bash
# Submit for notarization
xcrun altool --notarize-app \
  --file dist/PhoenixDrive.dmg \
  --primary-bundle-id com.phoenixdrive.app \
  --username "your-apple-id@example.com" \
  --password "@keychain:AC_PASSWORD"

# Wait for notarization (check status with RequestUUID)
xcrun altool --notarization-info REQUEST_UUID \
  --username "your-apple-id@example.com" \
  --password "@keychain:AC_PASSWORD"

# Once approved, staple the notarization ticket
xcrun stapler staple dist/PhoenixDrive.dmg
```

### Step 8: Generate Checksums

```bash
sha256sum dist/phoenix-drive.app > dist/phoenix-drive.app.sha256
sha256sum dist/PhoenixDrive.dmg > dist/PhoenixDrive.dmg.sha256
```

### Step 9: Create GitHub Release

```bash
# Create release with assets
gh release create v1.0.0 \
  dist/PhoenixDrive.dmg \
  dist/PhoenixDrive.dmg.sha256 \
  dist/phoenix-drive.app.sha256 \
  --title "PhoenixDrive v1.0.0" \
  --notes "See RELEASE_NOTES.md for details"
```

---

## Part 2: iOS App Store Deployment

### Prerequisites

- Apple Developer Account ($99/year)
- Mac with Xcode 14+
- EAS CLI installed: `npm install -g eas-cli`

### Step 1: Create App Store Connect Entry

1. Go to [App Store Connect](https://appstoreconnect.apple.com)
2. Click "My Apps" → "+"
3. Select "New App"
4. Fill in:
   - **Platform**: iOS
   - **Name**: Bobby's PhoenixDrive
   - **Bundle ID**: space.manus.phoenix.core.mobile (from app.config.ts)
   - **SKU**: phoenixdrive-001
   - **User Access**: Full Access

### Step 2: Create App Store Certificates

```bash
# Login to EAS
eas login

# Create certificates (interactive)
eas credentials
# Select: iOS
# Select: Create new
# Follow prompts for App Store Connect API key
```

### Step 3: Configure app.config.ts

Update your `app.config.ts` with production settings:

```typescript
const env = {
  appName: "Bobby's PhoenixDrive",
  appSlug: "phoenix-core-mobile",
  logoUrl: "https://your-s3-bucket.s3.amazonaws.com/icon.png",
  scheme: "manus20240115103045",
  iosBundleId: "space.manus.phoenix.core.mobile",
  androidPackage: "space.manus.phoenix.core.mobile",
};

const config: ExpoConfig = {
  name: env.appName,
  slug: env.appSlug,
  version: "1.0.0",
  ios: {
    supportsTablet: true,
    bundleIdentifier: env.iosBundleId,
    buildNumber: "1",
  },
  // ... rest of config
};
```

### Step 4: Build for App Store

```bash
# Build for App Store
eas build --platform ios --profile production

# This will:
# 1. Build on Expo's servers
# 2. Create an .ipa file
# 3. Upload to App Store Connect (if configured)
# 4. Show build URL and status
```

### Step 5: Fill App Store Metadata

In App Store Connect, fill in:

**General Information:**
- **Category**: Utilities
- **Content Rating**: Complete questionnaire
- **Pricing**: Free

**App Information:**
- **Subtitle**: Boot Camp driver installer for Mac
- **Description**: 
  ```
  Bobby's PhoenixDrive automatically detects your Mac model and provides 
  the correct Windows drivers for Boot Camp with automated installation.
  
  Features:
  - Automatic Mac model detection
  - Boot Camp driver installation
  - Real-time progress tracking
  - WebSocket integration
  - Email notifications
  ```
- **Keywords**: bootcamp, drivers, mac, windows, installer
- **Support URL**: https://github.com/Bboy9090/PhoenixCore-
- **Privacy Policy URL**: https://your-domain.com/privacy

**Screenshots:**
- Upload 5-6 screenshots (1242×2208 or 1284×2778)
- Show: Home screen, Device Wizard, USB Builder, Success screen, Settings

**App Preview:**
- Optional: Upload 15-30 second preview video

### Step 6: Set Up In-App Purchases (if needed)

Skip this if your app is free with no in-app purchases.

### Step 7: Review Information

- **App Review Information**:
  - **Contact Email**: your-email@example.com
  - **Demo Account**: (if needed)
  - **Notes for Reviewers**: "This app helps Mac users install Boot Camp drivers"

### Step 8: Submit for Review

1. Click "Version" in left sidebar
2. Scroll to bottom
3. Click "Submit for Review"
4. Answer compliance questions
5. Confirm submission

### Step 9: Monitor Review Status

```bash
# Check build status
eas build:list

# View in App Store Connect dashboard
# Expected review time: 24-48 hours
```

### Step 10: Post-Approval

Once approved:

1. **Release to App Store**:
   - Go to App Store Connect
   - Click "Release"
   - Select "Release this Version"

2. **Announce Release**:
   - Update GitHub releases
   - Post on social media
   - Email users

---

## Troubleshooting

### macOS Build Issues

**PyInstaller errors:**
```bash
# Clear cache and rebuild
rm -rf build dist *.spec
pyinstaller --onefile --windowed --icon=assets/icon.icns main.py
```

**Code signing issues:**
```bash
# List available certificates
security find-identity -v -p codesigning

# Remove invalid certificates
security delete-certificate -c "Developer ID Application"
```

**Notarization failures:**
```bash
# Check notarization status
xcrun altool --notarization-info REQUEST_UUID \
  --username "your-apple-id@example.com" \
  --password "@keychain:AC_PASSWORD"

# View detailed logs
xcrun altool --notarization-info REQUEST_UUID \
  --username "your-apple-id@example.com" \
  --password "@keychain:AC_PASSWORD" \
  --output-format json | jq '.NotarizationInfo.LogFileURL'
```

### iOS Build Issues

**EAS Build failures:**
```bash
# Check build logs
eas build:view BUILD_ID

# Rebuild with verbose output
eas build --platform ios --profile production --verbose
```

**App Store Connect issues:**
- Verify Bundle ID matches app.config.ts
- Ensure certificates are valid
- Check provisioning profiles are active

---

## Next Steps

1. **Desktop App**: Follow Part 1 to build and distribute on macOS
2. **iOS App**: Follow Part 2 to submit to App Store
3. **Android App**: Similar process for Google Play Store (separate guide)
4. **Monitoring**: Set up Sentry/Datadog to track crashes and performance

---

## Resources

- [Apple Developer Documentation](https://developer.apple.com/documentation/)
- [App Store Connect Help](https://help.apple.com/app-store-connect/)
- [EAS Build Documentation](https://docs.expo.dev/build/setup/)
- [Code Signing Guide](https://developer.apple.com/support/code-signing/)
- [Notarization Guide](https://developer.apple.com/documentation/security/notarizing_macos_software_before_distribution)

---

**Last Updated**: April 2026  
**Version**: 1.0.0
