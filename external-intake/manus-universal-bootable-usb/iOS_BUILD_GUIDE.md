# Bobby's PhoenixDrive — iOS Build & App Store Submission Guide

This guide walks you through building Bobby's PhoenixDrive for iOS and submitting it to the Apple App Store.

## Prerequisites

Before starting, ensure you have:

- **Mac with Xcode 15+** installed (download from App Store)
- **Apple Developer Account** ($99/year) - [Join here](https://developer.apple.com/programs/)
- **Node.js 18+** and **pnpm** installed
- **Expo CLI** installed globally: `npm install -g expo-cli`
- **EAS CLI** installed: `npm install -g eas-cli`

## Step 1: Set Up Apple Developer Account & Certificates

### 1.1 Create App ID in Apple Developer Portal

1. Go to [Apple Developer Portal](https://developer.apple.com/account)
2. Navigate to **Certificates, Identifiers & Profiles** → **Identifiers**
3. Click the **+** button to create a new App ID
4. Select **App IDs** and click **Continue**
5. Choose **App** and click **Continue**
6. Fill in:
   - **Description:** Bobby's PhoenixDrive
   - **Bundle ID:** Use Explicit ID: `space.manus.phoenix.core.mobile.t20260312210432`
7. Select capabilities:
   - ✅ Local Network
   - ✅ Multicast DNS
   - ✅ Network Extension
8. Click **Register** and **Continue**

### 1.2 Create Development & Distribution Certificates

**For Development:**
1. Go to **Certificates, Identifiers & Profiles** → **Certificates**
2. Click **+** to create a new certificate
3. Select **Apple Development** and click **Continue**
4. Follow the prompts to upload a Certificate Signing Request (CSR)
5. Download the certificate and double-click to install

**For Distribution (App Store):**
1. Repeat the process but select **Apple Distribution** instead
2. Download and install the distribution certificate

### 1.3 Create Provisioning Profiles

**Development Profile:**
1. Go to **Provisioning Profiles** → **Development**
2. Click **+** to create new profile
3. Select **iOS App Development** and click **Continue**
4. Select the App ID you created (`space.manus.phoenix.core.mobile.t20260312210432`)
5. Select your development certificate
6. Select your development device (or leave empty for all devices)
7. Name it: `Bobby-PhoenixDrive-Dev`
8. Download and install

**Distribution Profile (App Store):**
1. Go to **Provisioning Profiles** → **Distribution**
2. Click **+** to create new profile
3. Select **App Store Connect** and click **Continue**
4. Select the App ID
5. Select your distribution certificate
6. Name it: `Bobby-PhoenixDrive-AppStore`
7. Download and install

## Step 2: Configure EAS Build (Recommended for App Store)

EAS Build is Expo's cloud build service - it handles signing and building for you.

### 2.1 Initialize EAS

```bash
cd /home/ubuntu/phoenix-core-mobile
eas login
# Sign in with your Expo account (create one if needed at expo.dev)
eas init --id Ckayyn9SVaz8UPGNyasERW
```

### 2.2 Create eas.json

Create a file `eas.json` in the project root:

```json
{
  "cli": {
    "version": ">= 5.0.0",
    "promptToConfigurePushNotifications": false
  },
  "build": {
    "development": {
      "developmentClient": true,
      "distribution": "internal",
      "ios": {
        "resourceClass": "default"
      }
    },
    "preview": {
      "distribution": "internal",
      "ios": {
        "resourceClass": "default"
      }
    },
    "production": {
      "distribution": "store",
      "ios": {
        "resourceClass": "default"
      }
    }
  },
  "submit": {
    "production": {
      "ios": {
        "ascProvider": "YOUR_ASC_PROVIDER_ID"
      }
    }
  }
}
```

### 2.3 Set Up App Store Connect

1. Go to [App Store Connect](https://appstoreconnect.apple.com)
2. Click **My Apps** → **+** to create a new app
3. Select **New App**
4. Fill in:
   - **Platform:** iOS
   - **Name:** Bobby's PhoenixDrive
   - **Primary Language:** English
   - **Bundle ID:** Select `space.manus.phoenix.core.mobile.t20260312210432`
   - **SKU:** `BOBBYS-PHOENIXDRIVE-001`
5. Click **Create**

## Step 3: Build for iOS

### Option A: Using EAS Build (Recommended)

```bash
cd /home/ubuntu/phoenix-core-mobile

# Build for App Store
eas build --platform ios --auto-submit

# Or build without auto-submit (for testing first)
eas build --platform ios
```

The build will:
1. Upload your code to EAS servers
2. Build the app on Apple's infrastructure
3. Sign it with your distribution certificate
4. Generate an `.ipa` file

### Option B: Local Build with Xcode

```bash
cd /home/ubuntu/phoenix-core-mobile

# Generate Xcode project
expo prebuild --clean

# Open in Xcode
open ios/PhoenixCoreMobile.xcworkspace

# In Xcode:
# 1. Select "Product" → "Scheme" → "PhoenixCoreMobile"
# 2. Select "Product" → "Destination" → "Generic iOS Device"
# 3. Select "Product" → "Archive"
# 4. Wait for archive to complete
# 5. Click "Distribute App" → "App Store Connect"
```

## Step 4: Prepare App Store Metadata

In App Store Connect, fill in:

### 4.1 App Information
- **App Name:** Bobby's PhoenixDrive
- **Subtitle:** Create Bootable USB Drives
- **Privacy Policy URL:** https://example.com/privacy (update this)
- **Category:** Utilities
- **Content Rights:** Select appropriate option

### 4.2 Pricing & Availability
- **Pricing Tier:** Free (or select paid if preferred)
- **Availability:** Select countries where app will be available

### 4.3 App Preview & Screenshots

You need to provide:
- **App Preview:** 30-second video showing app in action (optional but recommended)
- **Screenshots:** 
  - iPhone 6.7" (required)
  - iPhone 5.5" (required)
  - iPad 12.9" (required)
  
**Screenshot Recommendations:**
1. Home screen with "Start Building" button
2. Device Wizard showing device detection
3. USB Builder with OS selection
4. Knowledge Base with helpful guides
5. Success screen with celebration animation

### 4.4 Description

```
Bobby's PhoenixDrive is your simple, friendly tool for creating bootable USB drives for any operating system.

Whether you need to:
- Install Windows, Linux, ChromeOS, or macOS
- Repair a broken computer
- Create a multi-boot USB with multiple operating systems
- Set up a recovery drive

Bobby's got your back. Plug it in, boot it up, problem over in a jiffy.

Features:
✓ Automatic device detection - identifies your computer's hardware
✓ Smart OS recommendations - see which operating systems are compatible
✓ Simple USB builder - create multi-boot USBs in just a few taps
✓ Repair toolkit - access recovery and repair tools
✓ Knowledge base - learn how to use your USB drive
✓ Works with PhoenixCore - seamless integration with the desktop app

Bobby's PhoenixDrive is the planning tool. The actual USB creation happens on your computer using PhoenixCore.

Supported Operating Systems:
- Windows 10, 11, Server editions
- Ubuntu, Fedora, Debian, and other Linux distributions
- ChromeOS Flex
- macOS (Intel Macs)

Supported Repair Tools:
- Windows Recovery Environment
- Linux Live Systems
- Disk Repair Utilities
- System Diagnostics

Privacy & Security:
- No data collection or tracking
- All processing happens locally on your device
- Open source and auditable
```

### 4.5 Keywords

```
bootable usb, os installation, windows, linux, macos, chromeos, recovery, repair, system tools, disk utility
```

### 4.6 Support URL & Marketing URL

- **Support URL:** https://github.com/Bboy9090/PhoenixCore-/issues
- **Marketing URL:** https://github.com/Bboy9090/PhoenixCore-

## Step 5: Submit for Review

1. In App Store Connect, click **Version 1.0** (or your current version)
2. Scroll to **Build** section and select your build
3. Fill in **Release Notes:**
   ```
   Initial release of Bobby's PhoenixDrive!
   
   - Device Wizard for automatic hardware detection
   - USB Builder for creating bootable drives
   - Support for Windows, Linux, ChromeOS, and macOS
   - Knowledge Base with helpful guides
   - QR code recipe export/import
   - Dark mode support
   ```
4. Click **Save**
5. Scroll to top and click **Submit for Review**
6. Answer the compliance questions:
   - **Encryption:** No (unless you're using encryption)
   - **Content Rights:** Yes, you own the rights
   - **IDFA:** No (we don't use advertising)
7. Click **Submit**

## Step 6: Monitor Review Status

1. Go to **App Store Connect** → **My Apps** → **Bobby's PhoenixDrive**
2. Check the **Version** section for review status
3. Apple typically reviews apps within 24-48 hours
4. You'll receive email notifications about approval or rejection

### If Rejected:
- Read the rejection reason carefully
- Make required changes
- Click **Resubmit** to send updated version

### If Approved:
- Your app will appear on the App Store within a few hours
- Share the link: `https://apps.apple.com/app/bobbys-phoenixdrive/id[YOUR_APP_ID]`

## Troubleshooting

### Build Fails with Certificate Error
```bash
# Clear cached credentials
eas credentials --platform ios --clear

# Reconfigure credentials
eas credentials --platform ios
```

### App Rejected for Privacy Issues
- Ensure all privacy descriptions are filled in `app.config.ts`
- Update privacy policy URL to valid page
- Resubmit with updated metadata

### Build Takes Too Long
- EAS builds typically take 10-20 minutes
- Check build status at https://expo.dev/builds
- Contact Expo support if build hangs

### Local Build Fails in Xcode
```bash
# Clean build folder
rm -rf ios/Pods ios/Podfile.lock

# Reinstall dependencies
cd ios && pod install && cd ..

# Try building again
expo prebuild --clean
```

## Next Steps After Approval

1. **Monitor Reviews:** Check App Store reviews and respond to user feedback
2. **Update Regularly:** Submit new versions with improvements and bug fixes
3. **Analytics:** Set up analytics to track app usage
4. **Marketing:** Share your app on social media and relevant communities
5. **Support:** Provide support for users via GitHub issues

## Resources

- [Expo iOS Build Documentation](https://docs.expo.dev/build/setup/)
- [App Store Connect Help](https://help.apple.com/app-store-connect/)
- [Apple Developer Program](https://developer.apple.com/programs/)
- [PhoenixCore Repository](https://github.com/Bboy9090/PhoenixCore-)

## Support

For issues with the build process:
1. Check the [Expo Discord](https://discord.gg/expo)
2. Review [Expo GitHub Issues](https://github.com/expo/expo/issues)
3. Contact [Expo Support](https://support.expo.dev)

For app-specific issues:
- Create an issue on [PhoenixCore GitHub](https://github.com/Bboy9090/PhoenixCore-/issues)
