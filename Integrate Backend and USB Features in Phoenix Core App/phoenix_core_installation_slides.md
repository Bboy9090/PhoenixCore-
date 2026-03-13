# Phoenix Core Mobile App: Installation Guide

## Slide 1: Title Slide

# Phoenix Core Mobile App
## Installation Guide for iOS, Android & ChromeOS

**Presented by: Manus AI**
**Date: March 13, 2026**

---

## Slide 2: Introduction to Phoenix Core Mobile

### What is Phoenix Core Mobile?

Phoenix Core Mobile is a powerful companion app for the Phoenix Core desktop engine, enabling remote management and monitoring of OS deployment and USB creation tasks. It provides a modern, intuitive interface for controlling complex operations on a host machine from your iOS, Android, or ChromeOS device.

### Key Capabilities:

*   **Remote Control:** Initiate and manage USB creation workflows.
*   **Real-time Monitoring:** Track build progress, system metrics, and device status.
*   **Device Management:** Scan and select target USB devices.
*   **Hardware Profiling:** View detailed host system hardware information.
*   **OCLP Integration:** Manage OpenCore Legacy Patcher operations for macOS.

---

## Slide 3: System Requirements & Prerequisites

### Host Machine (Running Phoenix Core Backend):

*   **Operating System:** macOS, Windows, Linux (Ubuntu 22.04+ recommended), or ChromeOS (with Linux development environment enabled).
*   **Python:** Python 3.11+.
*   **Dependencies:** `fastapi`, `uvicorn`, `psutil`, `aiofiles`, `pydantic`.
*   **Network:** Must be on the same local network as the mobile device, or accessible via a public IP/domain.
*   **USB Ports:** Available USB 2.0/3.0/3.1/3.2 ports for target drives.

### Mobile Device (iOS/Android/ChromeOS):

*   **iOS:** iOS 13.4+ (iPhone 6s or newer, iPad Air 2+).
*   **Android:** Android 6.0 (API 23)+.
*   **ChromeOS:** Any Chromebook with a modern web browser (for Expo Web PWA).
*   **Network:** Wi-Fi or cellular data connection to reach the host machine.
*   **Storage:** Minimum 100MB free space for the app (iOS/Android) or minimal browser cache (ChromeOS Web App).

---

## Slide 4: Backend Setup (Host Machine) - Essential First Step

### 1. Clone the Phoenix Core Repository:

```bash
gh repo clone Bboy9090/PhoenixCore- /home/ubuntu/PhoenixCore
```

### 2. Navigate to the Backend Directory:

```bash
cd /home/ubuntu/phoenix-core-backend
```

### 3. Install Python Dependencies:

```bash
sudo pip3 install fastapi uvicorn psutil aiofiles pydantic
```

### 4. Start the FastAPI Backend Server:

```bash
python3.11 main.py
```

*   The backend will start on `http://localhost:8000`.
*   Ensure port 8000 is open on your host machine's firewall.

---

## Slide 5: Mobile App Installation - Developer/Testing (Expo Go)

### For Quick Testing & Development:

This method uses the **Expo Go** app, ideal for rapid iteration and testing without building a standalone app.

1.  **Install Node.js & npm:** Ensure Node.js (v18+) and npm are installed on your development machine.
2.  **Install Expo CLI:**
    ```bash
    npm install -g expo-cli
    ```
3.  **Navigate to Mobile App Directory:**
    ```bash
    cd /home/ubuntu/phoenix-core-mobile
    ```
4.  **Install Project Dependencies:**
    ```bash
    npm install
    ```
5.  **Start Expo Development Server:**
    ```bash
    npm start
    ```
    *   This will open a browser tab with a QR code.
6.  **Install Expo Go App:** Download and install the **Expo Go** app from the App Store (iOS) or Google Play Store (Android) on your mobile device.
7.  **Scan QR Code:** Open Expo Go on your phone and scan the QR code displayed in your browser. The Phoenix Core app will load.

---

## Slide 6: Mobile App Installation - Production (iOS - TestFlight/App Store)

### For Public Distribution or Beta Testing:

1.  **Apple Developer Account:** You need an active Apple Developer Program membership.
2.  **Install EAS CLI:**
    ```bash
    npm install -g eas-cli
    ```
3.  **Login to EAS:**
    ```bash
    eas login
    ```
4.  **Configure `app.json`:** Ensure your `app.json` (in `phoenix-core-mobile/`) has the correct `bundleIdentifier` and `projectId`.
5.  **Build for iOS:**
    ```bash
    cd /home/ubuntu/phoenix-core-mobile
    eas build --platform ios --profile production
    ```
    *   This command builds an `.ipa` file and uploads it to Apple for distribution via TestFlight or the App Store.
6.  **Distribute:** Follow Apple's guidelines to distribute your app through TestFlight for beta testing or submit it to the App Store for public release.

---

## Slide 7: Mobile App Installation - Production (Android - Google Play Store)

### For Public Distribution or Internal Use:

1.  **Google Play Developer Account:** You need an active Google Play Developer account.
2.  **Install EAS CLI:** (If not already installed)
    ```bash
    npm install -g eas-cli
    ```
3.  **Login to EAS:** (If not already logged in)
    ```bash
    eas login
    ```
4.  **Configure `app.json`:** Ensure your `app.json` (in `phoenix-core-mobile/`) has the correct `package` name.
5.  **Build for Android:**
    ```bash
    cd /home/ubuntu/phoenix-core-mobile
    eas build --platform android --profile production
    ```
    *   This command builds an `.apk` or `.aab` file and provides a link to download it.
6.  **Distribute:** Upload the `.aab` file to the Google Play Console for distribution on the Google Play Store, or distribute the `.apk` directly for internal testing or side-loading.

---

## Slide 8: Mobile App Installation - ChromeOS (Web App / PWA)

### For Chromebook Users:

Phoenix Core Mobile can be accessed directly via a web browser on ChromeOS, functioning as a Progressive Web App (PWA).

1.  **Ensure Backend is Running:** Follow the Backend Setup instructions (Slide 4) to start the Phoenix Core backend on your ChromeOS device (within the Linux development environment).
2.  **Open Chrome Browser:** On your Chromebook, open the Chrome browser.
3.  **Navigate to Backend URL:** Enter the address of your Phoenix Core backend (e.g., `http://localhost:8000` or the host machine's IP address) in the browser's address bar.
4.  **Access Mobile App:** The Phoenix Core mobile app interface will load directly in your browser.
5.  **Install as PWA (Optional):** For a native app-like experience, click the "Install app" icon (usually a plus sign in a circle) in the browser's address bar and follow the prompts to install Phoenix Core as a PWA.

*   **Note on USB Writing:** Due to ChromeOS security restrictions, direct USB writing from the Linux container is not possible. The Phoenix Core backend will guide you to use the native **Chromebook Recovery Utility** for the final writing step. Remember to rename `.iso` files to `.bin` before using the utility.

---

## Slide 9: Connecting the Mobile App to the Backend

### Post-Installation Configuration:

1.  **Open Phoenix Core Mobile App:** Launch the app on your iOS or Android device, or access the PWA on ChromeOS.
2.  **Navigate to Settings:** Tap on the "Settings" tab in the bottom navigation bar.
3.  **Enter Backend URL:** In the "Backend Configuration" section, enter the IP address or hostname of your host machine where the Phoenix Core backend is running, followed by the port (e.g., `http://192.168.1.100:8000`).
    *   **Important:** Use the host machine's local IP address if on the same network.
4.  **Test Connection:** Tap the "Test" button to verify connectivity. A "Connected" status should appear.
5.  **Update URL:** Tap "Update URL" to save the configuration.

*   **Troubleshooting:** If connection fails, ensure the backend is running, firewall is configured, and IP address is correct.

---

## Slide 10: Usage & Workflow Overview

### Once Connected:

1.  **Dashboard:** Monitor real-time system metrics and overall health of your host machine.
2.  **Devices:** View connected USB devices. Select a target device for OS deployment.
3.  **Build USB:** Choose an OS recipe (e.g., Ubuntu, macOS OCLP), confirm safety checks, and initiate the USB creation process. Monitor progress and logs.
4.  **Settings:** Reconfigure backend connection or run system diagnostics.

### Example Workflow:

1.  Plug a blank USB drive into your host machine.
2.  Open Phoenix Core Mobile, go to "Devices" and select the USB drive.
3.  Navigate to "Build USB", choose the "Ubuntu 22.04" recipe.
4.  Review the safety check and start the build (optionally in dry-run mode).
5.  Monitor the progress and logs from your mobile device.

---

## Slide 11: Troubleshooting & Support

### Common Issues:

*   **Backend Not Reachable:**
    *   Verify backend server is running (`python3.11 main.py`).
    *   Check host machine's firewall (port 8000).
    *   Ensure correct IP address/hostname in app settings.
*   **USB Device Not Detected:**
    *   Ensure the USB drive is properly connected to the host machine.
    *   Check host machine's permissions for `/dev/sdX` devices.
    *   Refresh device list in the app.
*   **Build Errors:**
    *   Review build logs in the app for specific error messages.
    *   Ensure sufficient disk space on the target USB drive.
    *   Check OS image integrity.
*   **ChromeOS USB Writing:**
    *   Remember direct writing is not supported. Follow instructions to use the Chromebook Recovery Utility.
    *   Rename `.iso` to `.bin` if using the Recovery Utility.

### Further Assistance:

*   Refer to the `PHOENIX_CORE_COMPLETE.md` and `INTEGRATION_ANALYSIS.md` files for detailed technical documentation.
*   Contact support at `https://help.manus.im` for technical assistance.

---

## Slide 12: Thank You & Q&A

# Thank You!

## Questions & Answers

**Phoenix Core - Empowering OS Deployment**

---
