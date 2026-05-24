# iOS App Store Submission Guide

**Status:** Production Ready  
**Last Updated:** May 5, 2026  
**Version:** 2.0.0

---

## Overview

Complete guide for submitting Bobby's PhoenixDrive to the Apple App Store.

**Timeline:** 2-4 weeks from submission to approval

---

## Prerequisites

1. **Apple Developer Account** — $99/year (https://developer.apple.com)
2. **Mac with Xcode** — macOS 12+
3. **App Store Connect** — Apple's app management platform
4. **TestFlight** — Beta testing platform (included with App Store Connect)
5. **EAS Build** — Expo's build service (already configured)

---

## Step 1: Set Up Apple Developer Account

### 1.1 Create Apple ID

1. Go to https://appleid.apple.com
2. Create new Apple ID (use business email)
3. Enable two-factor authentication
4. Verify email

### 1.2 Enroll in Apple Developer Program

1. Go to https://developer.apple.com/programs/enroll/
2. Click "Enroll"
3. Sign in with Apple ID
4. Complete enrollment process ($99)
5. Verify business information
6. Wait for approval (1-2 days)

### 1.3 Accept Legal Agreements

1. Go to https://appstoreconnect.apple.com
2. Sign in with Apple ID
3. Go to Agreements, Tax, and Banking
4. Accept latest agreements
5. Complete tax information
6. Add banking information

---

## Step 2: Create App Store Connect Entry

### 2.1 Register App ID

1. Go to https://appstoreconnect.apple.com
2. Click "Apps" → "New App"
3. Select "iOS"
4. Fill in:
   - **App Name:** Bobby's PhoenixDrive
   - **Bundle ID:** space.manus.phoenix.drive
   - **SKU:** PHOENIXDRIVE001
   - **Primary Language:** English
5. Click "Create"

### 2.2 Fill in App Information

1. Go to App Information
2. Fill in:
   - **Subtitle:** Universal OS Deployment Tool
   - **Category:** Utilities
   - **Content Rights:** Select appropriate options
   - **Age Rating:** Complete questionnaire (likely 4+)

### 2.3 Configure Pricing and Availability

1. Go to Pricing and Availability
2. Select:
   - **Price Tier:** Free
   - **Availability:** All countries
   - **Release Date:** Automatic (upon approval)

---

## Step 3: Create Certificates and Provisioning Profiles

### 3.1 Create Development Certificate

1. Go to Developer → Certificates, IDs & Profiles
2. Click "Certificates"
3. Click "+" to create new
4. Select "iOS App Development"
5. Follow instructions to create CSR (Certificate Signing Request)
6. Upload CSR
7. Download certificate
8. Double-click to install in Keychain

### 3.2 Create Distribution Certificate

1. Repeat above but select "Apple Distribution"
2. This is used for App Store submissions

### 3.3 Create App ID

1. Go to "Identifiers"
2. Click "+" to create new
3. Select "App IDs"
4. Enter:
   - **Description:** PhoenixDrive
   - **Bundle ID:** space.manus.phoenix.drive
5. Select capabilities:
   - Push Notifications (if needed)
   - HealthKit (if needed)
6. Click "Continue" → "Register"

### 3.4 Create Provisioning Profiles

**Development Profile:**
1. Go to "Profiles"
2. Click "+" to create new
3. Select "iOS App Development"
4. Select App ID: space.manus.phoenix.drive
5. Select development certificate
6. Select test devices (optional)
7. Download profile

**Distribution Profile:**
1. Repeat above but select "App Store Connect"
2. Select distribution certificate
3. Download profile

---

## Step 4: Prepare App Assets

### 4.1 Create App Screenshots

Requirements:
- **iPhone 6.7":** 1284 × 2778 pixels (required)
- **iPad 12.9":** 2048 × 2732 pixels (optional)
- **Format:** PNG or JPEG
- **Count:** 2-10 screenshots per device

Create 5 screenshots showing:
1. Home screen with features
2. Device Wizard flow
3. USB Builder interface
4. Build progress monitoring
5. Success completion screen

**Tools:**
- Figma (design)
- Screenshot tools (capture)
- Preview (edit)

### 4.2 Create App Preview Video (Optional but Recommended)

Requirements:
- **Duration:** 15-30 seconds
- **Format:** MOV or MP4
- **Resolution:** 1080p
- **Aspect Ratio:** 16:9 or 9:16

Content:
1. Show app opening (2 sec)
2. Demonstrate main features (10 sec)
3. Show build process (5 sec)
4. Show completion (3 sec)

**Tools:**
- ScreenFlow (macOS)
- Final Cut Pro
- Adobe Premiere

### 4.3 Create App Icon

Requirements:
- **Size:** 1024 × 1024 pixels
- **Format:** PNG
- **No rounded corners** (iOS adds them automatically)
- **No transparency** (use solid background)

Already created: `assets/images/icon.png`

### 4.4 Write App Description

**App Name:** Bobby's PhoenixDrive

**Subtitle:** Universal OS Deployment Tool

**Description:**
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

**Keywords:** bootable, USB, OS, deployment, recovery, Windows, Linux, Mac, tools, installation

**Support URL:** https://phoenixdrive.app/support

**Privacy Policy URL:** https://phoenixdrive.app/privacy

**Terms of Service URL:** https://phoenixdrive.app/terms

---

## Step 5: Configure Build Settings

### 5.1 Update app.config.ts

```typescript
const env = {
  appName: "Bobby's PhoenixDrive",
  appSlug: "phoenix-drive",
  scheme: "manus20240115103045",
  iosBundleId: "space.manus.phoenix.drive",
  androidPackage: "space.manus.phoenix.drive",
  version: "2.0.0",
  ios: {
    bundleIdentifier: "space.manus.phoenix.drive",
    buildNumber: "1",
    supportsTablet: true,
  },
};
```

### 5.2 Update eas.json

```json
{
  "build": {
    "production": {
      "ios": {
        "distribution": "app-store",
        "buildType": "release"
      }
    }
  },
  "submit": {
    "production": {
      "ios": {
        "ascAppId": "1234567890"
      }
    }
  }
}
```

---

## Step 6: Build for iOS

### 6.1 Build with EAS

```bash
eas build --platform ios --auto-submit
```

Or without auto-submit:

```bash
eas build --platform ios
```

### 6.2 Monitor Build

1. Go to https://expo.dev/builds
2. Monitor build progress
3. Download IPA when complete

### 6.3 Test with TestFlight

1. Go to App Store Connect → TestFlight
2. Add internal testers (your email)
3. Download TestFlight app on iOS device
4. Install build and test
5. Fix any issues
6. Rebuild if needed

---

## Step 7: Submit to App Store

### 7.1 Add Build to App Store Connect

1. Go to App Store Connect → Builds
2. Select build from TestFlight
3. Click "Add to App Store"

### 7.2 Add App Review Information

1. Go to App Review Information
2. Fill in:
   - **Contact Email:** your-email@example.com
   - **Phone Number:** +1-555-0123
   - **Demo Account:** (if needed)
   - **Notes:** Any special instructions for reviewers

### 7.3 Add Pricing and Availability

1. Go to Pricing and Availability
2. Verify settings
3. Select release date (usually "Automatic")

### 7.4 Submit for Review

1. Go to Version Release
2. Click "Submit for Review"
3. Answer compliance questions:
   - **Encryption:** No
   - **Third-party SDKs:** List any
   - **Advertising:** No
4. Click "Submit"

---

## Step 8: Monitor Review Status

### 8.1 Check Review Status

1. Go to App Store Connect → Activity
2. Monitor submission status
3. Receive email updates

**Typical Timeline:**
- In Review: 1-3 days
- Approved: Automatic release
- Rejected: Fix issues and resubmit

### 8.2 Respond to Feedback

If rejected:
1. Read rejection reason carefully
2. Fix issues
3. Update app version
4. Resubmit

Common rejection reasons:
- Crashes on launch
- Missing privacy policy
- Misleading description
- Inappropriate content

### 8.3 Monitor After Launch

1. Monitor crash reports
2. Monitor user ratings
3. Respond to reviews
4. Plan updates

---

## Step 9: Post-Launch

### 9.1 Announce Release

1. Update website
2. Social media announcement
3. Email newsletter
4. Press release

### 9.2 Monitor Performance

1. Check App Store analytics
2. Monitor crash reports
3. Monitor user ratings
4. Respond to reviews

### 9.3 Plan Updates

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
- Xcode version mismatch
- Certificate issues
- Provisioning profile issues

### Issue: App Rejected

**Common reasons:**
1. **Crashes on Launch**
   - Test on multiple iOS versions
   - Check crash logs

2. **Missing Privacy Policy**
   - Add privacy policy URL
   - Make it comprehensive

3. **Misleading Description**
   - Ensure description matches functionality
   - Don't make false claims

4. **Performance Issues**
   - Optimize app startup
   - Reduce memory usage
   - Fix crashes

### Issue: TestFlight Build Not Available

**Solution:**
1. Wait 30 minutes for processing
2. Check build status in EAS
3. Rebuild if necessary

---

## Checklist

- [ ] Apple Developer Account created
- [ ] App Store Connect entry created
- [ ] Certificates created and installed
- [ ] Provisioning profiles created
- [ ] App icons created (1024×1024)
- [ ] Screenshots created (5-10 per device)
- [ ] App preview video created (optional)
- [ ] App description written
- [ ] Privacy policy created
- [ ] Terms of service created
- [ ] app.config.ts updated
- [ ] eas.json configured
- [ ] Build created and tested
- [ ] TestFlight testing completed
- [ ] App submitted for review
- [ ] Review status monitored
- [ ] App approved and released
- [ ] Post-launch monitoring started

---

## Next Steps

1. Create Google Play Store entry for Android
2. Monitor App Store reviews and ratings
3. Plan next update
4. Collect user feedback
5. Implement improvements

---

**Status:** ✅ Ready for Submission

For questions, contact: support@phoenixdrive.app
