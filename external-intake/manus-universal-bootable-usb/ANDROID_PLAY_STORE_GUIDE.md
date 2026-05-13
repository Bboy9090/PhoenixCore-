# Android Play Store Submission Guide

**Status:** Production Ready  
**Last Updated:** May 5, 2026  
**Version:** 2.0.0

---

## Overview

Complete guide for submitting Bobby's PhoenixDrive to Google Play Store.

**Timeline:** 1-3 hours from submission to approval (usually)

---

## Prerequisites

1. **Google Play Developer Account** — $25 one-time (https://play.google.com/console)
2. **Google Account** — For Play Store Connect
3. **EAS Build** — Expo's build service (already configured)
4. **Android Signing Key** — For app signing

---

## Step 1: Set Up Google Play Developer Account

### 1.1 Create Google Account

1. Go to https://accounts.google.com
2. Create new account or use existing
3. Enable two-factor authentication
4. Verify phone number

### 1.2 Enroll in Google Play Developer Program

1. Go to https://play.google.com/console
2. Click "Create account"
3. Accept Developer Agreement
4. Pay $25 enrollment fee
5. Complete registration

### 1.3 Set Up Merchant Account

1. Go to Play Console → Settings → Payments
2. Add payment method
3. Verify payment information
4. Complete merchant setup

---

## Step 2: Create App Entry

### 2.1 Create New App

1. Go to Play Console → All apps
2. Click "Create app"
3. Enter:
   - **App name:** Bobby's PhoenixDrive
   - **Default language:** English
   - **App or game:** App
   - **Free or paid:** Free
4. Click "Create app"

### 2.2 Fill in Store Listing

1. Go to Store listing
2. Fill in:
   - **Short description:** (50 characters max)
     "Universal OS Deployment Tool"
   
   - **Full description:** (4000 characters max)
     ```
     Bobby's PhoenixDrive is your ultimate companion for creating universal bootable USB drives.
     
     Features:
     • Device Wizard: Identify your device and see compatible operating systems
     • USB Builder: Create multi-boot USB drives with your choice of OS and tools
     • Real-time Monitoring: Watch build progress in real-time
     • Boot Camp Support: Install Windows drivers on Mac automatically
     • Knowledge Base: Comprehensive guides for recovery and installation
     • QR Code Import: Seamlessly import recipes from desktop app
     
     Perfect for:
     - System recovery and repair
     - Multi-OS testing
     - IT professionals
     - Power users
     - Device troubleshooting
     
     Supported Operating Systems:
     - Windows 10/11
     - Ubuntu 20.04+
     - Debian 11+
     - Fedora 35+
     - CentOS 8+
     - And many more!
     
     No technical knowledge required. PhoenixDrive guides you through every step.
     
     Privacy: We don't collect any personal data. All builds are processed locally on your device.
     ```
   
   - **Promotional text:** (80 characters max)
     "Create bootable USB drives with ease"

### 2.3 Add Graphics

**App Icon:**
- Size: 512 × 512 pixels
- Format: PNG
- File: `assets/images/icon.png`

**Feature Graphic:**
- Size: 1024 × 500 pixels
- Format: PNG or JPEG
- Create in Figma or Photoshop

**Screenshots:**
- Size: 1080 × 1920 pixels (phone) or 2560 × 1440 pixels (tablet)
- Format: PNG or JPEG
- Count: 2-8 screenshots
- Create 5 screenshots:
  1. Home screen
  2. Device Wizard
  3. USB Builder
  4. Build Progress
  5. Success Screen

**Video Preview (Optional):**
- Duration: 30 seconds max
- Format: MP4
- Resolution: 1080p

### 2.4 Configure Content Rating

1. Go to Content rating
2. Fill out questionnaire:
   - Violence: None
   - Sexual content: None
   - Profanity: None
   - Alcohol/Tobacco: None
   - Gambling: None
3. Get rating certificate
4. Select appropriate rating (likely PEGI 3 / ESRB Everyone)

### 2.5 Add Privacy Policy

1. Go to App content
2. Add Privacy Policy URL:
   https://phoenixdrive.app/privacy
3. Add Terms of Service URL:
   https://phoenixdrive.app/terms
4. Select data collection:
   - Personal data: No
   - Sensitive data: No
   - Ad personalization: No

### 2.6 Configure Target Audience

1. Go to Target audience
2. Select:
   - **Target age:** 13+
   - **Content rating:** Appropriate for all ages
   - **Restricted content:** None

---

## Step 3: Generate Android Signing Key

### 3.1 Create Keystore

```bash
keytool -genkey -v -keystore phoenixdrive.keystore \
  -keyalg RSA -keysize 2048 -validity 10000 \
  -alias phoenixdrive-key
```

When prompted:
- **Keystore password:** Create strong password
- **Key password:** Same as keystore password
- **First and last name:** Bobby
- **Organization:** PhoenixDrive
- **City:** Your City
- **State/Province:** Your State
- **Country code:** US

### 3.2 Store Keystore Safely

```bash
# Backup keystore
cp phoenixdrive.keystore ~/.android/

# Store password securely
echo "password" > ~/.android/phoenixdrive.keystore.password
chmod 600 ~/.android/phoenixdrive.keystore.password
```

**Important:** Keep this keystore safe. You'll need it for all future updates!

---

## Step 4: Configure Build Settings

### 4.1 Update app.config.ts

```typescript
const env = {
  appName: "Bobby's PhoenixDrive",
  appSlug: "phoenix-drive",
  scheme: "manus20240115103045",
  iosBundleId: "space.manus.phoenix.drive",
  androidPackage: "space.manus.phoenix.drive",
  version: "2.0.0",
  android: {
    package: "space.manus.phoenix.drive",
    versionCode: 1,
    permissions: ["POST_NOTIFICATIONS"],
  },
};
```

### 4.2 Update eas.json

```json
{
  "build": {
    "production": {
      "android": {
        "release": {
          "workflow": "generic",
          "gradleCommand": ":app:bundleRelease"
        }
      }
    }
  },
  "submit": {
    "production": {
      "android": {
        "serviceAccountKeyPath": "./service-account-key.json",
        "track": "internal"
      }
    }
  }
}
```

### 4.3 Create Service Account Key

1. Go to Google Cloud Console
2. Create new project: "PhoenixDrive"
3. Enable Google Play Android Developer API
4. Create service account
5. Create key (JSON format)
6. Download and save as `service-account-key.json`

---

## Step 5: Build for Android

### 5.1 Build with EAS

```bash
eas build --platform android --auto-submit
```

Or without auto-submit:

```bash
eas build --platform android
```

### 5.2 Monitor Build

1. Go to https://expo.dev/builds
2. Monitor build progress
3. Download APK when complete

### 5.3 Test Build

```bash
# Install on connected device
adb install app-release.apk

# Or use Android Emulator
emulator -avd Pixel_5_API_31 &
adb install app-release.apk
```

Test:
- [ ] App launches without crashing
- [ ] All screens load correctly
- [ ] Navigation works
- [ ] API connections work
- [ ] WebSocket connections work
- [ ] Permissions work (if any)

---

## Step 6: Submit to Play Store

### 6.1 Create Release

1. Go to Play Console → Release management → Releases
2. Click "Create new release"
3. Select "Production"
4. Upload AAB (Android App Bundle) from EAS build

### 6.2 Add Release Notes

```
Version 2.0.0 - Initial Release

Features:
• Device Wizard for OS compatibility checking
• USB Builder for creating bootable drives
• Real-time build progress monitoring
• Boot Camp driver installation for Mac
• Comprehensive Knowledge Base
• QR code recipe import from desktop app

Bug fixes:
• Fixed WebSocket connection stability
• Improved error handling
• Optimized memory usage

Performance:
• Faster app startup
• Smoother animations
• Better battery efficiency
```

### 6.3 Review and Submit

1. Review all information:
   - [ ] Store listing complete
   - [ ] Graphics uploaded
   - [ ] Privacy policy added
   - [ ] Content rating set
   - [ ] Target audience set
   - [ ] Release notes added
   - [ ] Build uploaded

2. Click "Review release"
3. Click "Start rollout to Production"
4. Confirm submission

---

## Step 7: Monitor Submission

### 7.1 Check Status

1. Go to Play Console → Release management
2. Monitor release status
3. Receive email updates

**Typical Timeline:**
- Queued: 5-30 minutes
- Reviewing: 1-3 hours
- Published: Automatic release

### 7.2 Monitor After Launch

1. Check Play Store analytics
2. Monitor crash reports
3. Monitor user ratings
4. Respond to reviews

---

## Step 8: Post-Launch

### 8.1 Announce Release

1. Update website
2. Social media announcement
3. Email newsletter
4. Press release

### 8.2 Monitor Performance

1. Check Play Store analytics
2. Monitor crash reports
3. Monitor user ratings
4. Respond to reviews

### 8.3 Plan Updates

1. Collect user feedback
2. Plan features
3. Schedule next release
4. Submit updates

---

## Troubleshooting

### Issue: Build Fails

**Check logs:**
```bash
eas build:view --id <BUILD_ID>
```

**Common causes:**
- Gradle build errors
- Dependency issues
- Signing key issues

### Issue: App Rejected

**Common reasons:**
1. **Crashes on Launch**
   - Test on multiple Android versions
   - Check crash logs

2. **Missing Privacy Policy**
   - Add privacy policy URL
   - Make it comprehensive

3. **Permissions Not Justified**
   - Only request necessary permissions
   - Explain why each permission is needed

4. **Performance Issues**
   - Optimize app startup
   - Reduce memory usage
   - Fix crashes

### Issue: Cannot Find App on Play Store

**Solution:**
1. Wait 2-3 hours for indexing
2. Search by exact app name
3. Check if app is restricted in your region
4. Verify app is published (not draft)

---

## Updating Your App

### Update Version

1. Update version in `app.config.ts`:
   ```typescript
   version: "2.0.1",
   android: {
     versionCode: 2,  // Increment for each release
   }
   ```

2. Build and submit:
   ```bash
   eas build --platform android --auto-submit
   ```

3. Monitor release status

---

## Checklist

- [ ] Google Play Developer Account created
- [ ] App entry created in Play Console
- [ ] Store listing completed
- [ ] App icon uploaded (512×512)
- [ ] Feature graphic uploaded (1024×500)
- [ ] Screenshots created and uploaded (5-8)
- [ ] Video preview created (optional)
- [ ] Privacy policy added
- [ ] Terms of service added
- [ ] Content rating completed
- [ ] Target audience configured
- [ ] Android signing key created
- [ ] app.config.ts updated
- [ ] eas.json configured
- [ ] Service account key created
- [ ] Build created and tested
- [ ] App submitted for review
- [ ] Review status monitored
- [ ] App published to Play Store
- [ ] Post-launch monitoring started

---

## Next Steps

1. Monitor user reviews and ratings
2. Collect feedback
3. Plan next update
4. Implement improvements
5. Submit updates regularly

---

**Status:** ✅ Ready for Submission

For questions, contact: support@phoenixdrive.app
