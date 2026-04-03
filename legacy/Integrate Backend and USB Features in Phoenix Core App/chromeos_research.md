# ChromeOS Linux (Crostini) USB Support Findings

## Summary
ChromeOS Linux (Crostini) supports USB device pass-through, but it is primarily intended for developer tools like ADB or serial devices. Direct block device access (required for `dd` and raw USB writing) is restricted for security reasons within the default container.

## Key Details
- **Permissions:** USB access is not enabled by default. Users must go to **Settings > Developers > Linux development environment > Manage USB devices** to toggle access for specific devices.
- **Block Device Access:** Crostini does *not* typically allow raw access to `/dev/sdX` block devices. This means tools like `dd` or Phoenix Core's direct writing engine will likely fail to see the USB drive as a writable disk.
- **Workaround 1 (Native ChromeOS):** Use the **Chromebook Recovery Utility**. Rename `.iso` to `.bin` to allow selection.
- **Workaround 2 (Phoenix Core Integration):** The Phoenix Core backend can run on ChromeOS, but for the actual *writing* phase, it should guide users to use the native recovery utility or provide a specialized "ChromeOS Mode" that handles the file renaming and provides instructions for the recovery utility.
- **Mobile App Role:** The mobile app can still monitor the ChromeOS host's metrics and manage recipes, but the "Build" step on ChromeOS will require a manual final step using the native utility.

## Conclusion for Phoenix Core
Phoenix Core is **compatible** with ChromeOS as a host for the backend (metrics, recipe management, hardware profiling), but the raw USB writing capability is restricted by the ChromeOS sandbox. I will update the installation guide and slides to reflect this "Hybrid" approach for ChromeOS users.
