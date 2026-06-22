# Arcwyre Flex Failure Testing Report

This document registers the failure test simulations and behavior logs for **Arcwyre Flex** release candidate 1 (RC1).

---

## 1. Simulated Failure Modes & Behaviors

### Failure 1: No Network
- **Simulation Method**: Disabled network adapter interface inside QEMU.
- **Boot Behavior**: Successful. Boot time remains unchanged. Network target initialization does not block local display target loading.
- **Application Behavior**: Firefox displays standard offline error page. `web-app-center` CLI functions (list/install/remove) execute successfully as they are local metadata manipulations. `recovery-center network` correctly diagnoses and reports `FAIL — Cannot reach 8.8.8.8. Check network settings.`

### Failure 2: Missing User Profile
- **Simulation Method**: Deleted `/home/arc` directory at startup.
- **Boot Behavior**: Successful.
- **Self-Healing Behavior**: The dynamic user-creation live-config hook (`1200-arc-user`) detects the absence of the home directory structure and automatically recreates `/home/arc` using `/etc/skel` templates, re-applying proper ownership (`chown arc:arc`).

### Failure 3: Read-Only Disk
- **Simulation Method**: Booted ISO with write protection enabled on the storage layer.
- **Boot Behavior**: Successful.
- **Overlay Behavior**: Debian Live overlayfs layer redirects all physical writes to volatile memory (`tmpfs`). System write requests (logs, temporary files, package registry updates) execute without error, but do not persist across reboots.

### Failure 4: Broken Desktop Session
- **Simulation Method**: Simulated corrupted XFCE desktop session config.
- **Display Behavior**: LightDM fails to launch XFCE desktop target.
- **Recovery Behavior**: The system remains operational via virtual console TTY2. Switching to TTY2 (`ctrl-alt-f2`) provides a working, passwordless interactive bash shell for user `arc`, allowing console-based system repair and log export.
