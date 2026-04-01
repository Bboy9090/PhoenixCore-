# Bobby's PhoenixDrive — iOS Quick Start (Mac)

Fast track to building and testing Bobby's PhoenixDrive on your Mac.

## 5-Minute Setup

### 1. Install Prerequisites

```bash
# Install Xcode (if not already installed)
# Download from App Store or: xcode-select --install

# Install Node.js & pnpm (if not already installed)
brew install node pnpm

# Install Expo & EAS CLI globally
npm install -g expo-cli eas-cli
```

### 2. Authenticate with Expo

```bash
# Create free Expo account at https://expo.dev
eas login
# Follow prompts to sign in
```

### 3. Build for iOS

```bash
cd /home/ubuntu/phoenix-core-mobile

# Option A: Build for testing (fastest)
eas build --platform ios --profile preview

# Option B: Build for App Store submission
eas build --platform ios --profile production
```

The build will:
- Upload your code to Expo's cloud servers
- Compile for iOS
- Generate an `.ipa` file
- Sign it automatically

**Build time:** 10-20 minutes

### 4. Download & Test

1. Go to https://expo.dev/builds
2. Find your build in the list
3. Click **Download** to get the `.ipa` file
4. Open in Xcode or use Transporter to test/submit

## For App Store Submission

### Step 1: Create App Store Connect Entry

1. Go to [App Store Connect](https://appstoreconnect.apple.com)
2. Click **My Apps** → **+** → **New App**
3. Fill in:
   - **Platform:** iOS
   - **Name:** Bobby's PhoenixDrive
   - **Bundle ID:** `space.manus.phoenix.core.mobile.t20260312210432`
   - **SKU:** `BOBBYS-PHOENIXDRIVE-001`
4. Click **Create**

### Step 2: Upload Build

```bash
# Build for App Store
eas build --platform ios --profile production

# After build completes, submit directly
eas submit --platform ios --latest
```

**Or manually submit:**
1. Download the `.ipa` file
2. Open **Transporter** app on Mac
3. Drag & drop the `.ipa` file
4. Click **Deliver**

### Step 3: Fill App Store Metadata

In App Store Connect:
1. Click **Version 1.0**
2. Add **Screenshots** (required):
   - iPhone 6.7": Home screen, Device Wizard, USB Builder, Success screen
   - iPad 12.9": Same screens in landscape
3. Add **Description** (see iOS_BUILD_GUIDE.md for template)
4. Add **Keywords**: bootable usb, os installation, windows, linux, macos
5. Click **Save**

### Step 4: Submit for Review

1. Click **Submit for Review**
2. Answer compliance questions
3. Click **Submit**

**Review time:** 24-48 hours typically

## Troubleshooting

### Build Fails
```bash
# Clear cache and retry
eas credentials --platform ios --clear
eas build --platform ios --profile production
```

### Need to Test Locally First?
```bash
# Build for Simulator (Mac only)
eas build --platform ios --profile preview --simulator

# Or use Expo Go app
expo start --ios
```

### App Rejected?
- Check rejection email for specific reason
- Update metadata in App Store Connect
- Resubmit with changes

## File Reference

- **app.config.ts** — iOS configuration (bundle ID, permissions, etc.)
- **eas.json** — Build profiles and settings
- **iOS_BUILD_GUIDE.md** — Detailed step-by-step guide
- **iOS_QUICK_START.md** — This file

## Next Steps

1. ✅ Install prerequisites
2. ✅ Authenticate with Expo
3. ✅ Build for iOS
4. ✅ Test on device or simulator
5. ✅ Create App Store Connect entry
6. ✅ Fill metadata & screenshots
7. ✅ Submit for review
8. ✅ Monitor review status
9. ✅ Launch on App Store!

## Support

- **Expo Docs:** https://docs.expo.dev/build/setup/
- **App Store Connect Help:** https://help.apple.com/app-store-connect/
- **PhoenixCore Issues:** https://github.com/Bboy9090/PhoenixCore-/issues
