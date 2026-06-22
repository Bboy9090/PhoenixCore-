# Arcwyre Flex RC1 Release Notes

This document provides the release notes and validation checklists for **Arcwyre Flex** Release Candidate 1 (RC1).

---

## 1. Release Architecture & Boot Targets

- **Boot Support**: **UEFI-only**. Legacy BIOS boot is disabled by design.
- **Login Behavior**: **Console (TTY2) Auto-login passes**. The system automatically logs in the passwordless `arc` user on virtual console TTY2.
- **XFCE Desktop Status**: XFCE desktop validation is not yet the primary pass condition unless proven separately. The LightDM display manager launches successfully on TTY1 but does not auto-login to XFCE without credentials. TTY2 console is the primary verified recovery interface.

---

## 2. Release Artifacts

- **Filename**: `bwos-arcwyre-flex.iso`
- **Path**: `os/phoenix-os/build/bwos-arcwyre-flex.iso`
- **Size**: `3,947,024,384` bytes (~3.7 GB)
- **SHA256**: `123ff51ce4a78d2071f20e5290cf75097f69478afbbaa353e46e6d7d2f56eeed`

---

## 3. Resource Metrics

- **Idle RAM**: ~320 MB (on a 4GB guest)
- **Idle CPU**: < 0.5%
- **RootFS Size**: ~10.4 GB (uncompressed SquashFS estimate)
- **Installed Package Count**: 2,757 packages

---

## 4. Native Application Validation Summary

1. **Recovery Center (`/usr/bin/recovery-center`)**:
   - `sysinfo`: **PASS** (Gathers and displays kernel version, memory, and disk usage).
   - `disk-health`: **PASS** (Invokes `smartctl -H` on storage devices).
   - `network`: **PASS** (Pings 8.8.8.8 to verify connectivity).
   - `export-logs`: **PASS** (Copies core system logs to `/tmp/arcwyre-logs/`).

2. **Web App Center (`/usr/bin/web-app-center`)**:
   - `list`: **PASS** (Lists default productivity and developer web application templates).
   - `install`: **PASS** (Generates desktop launchers pointing to dedicated Firefox instances).
   - `remove`: **PASS** (Removes desktop entries and registers deletion).

---

## 5. Known Limitations

- **Legacy BIOS**: Cannot boot on BIOS-only machines. UEFI is strictly required.
- **LightDM Graphical Autologin**: LightDM displays the user session login greeter card on TTY1 and requires credentials. Switch to TTY2 (`Ctrl+Alt+F2`) for automatic, passwordless console access.

---

## 6. Installation & Testing Instructions

Run the UEFI QEMU boot test using the following command:

```bash
qemu-system-x86_64 \
  -pflash /opt/homebrew/Cellar/qemu/11.0.0/share/qemu/edk2-x86_64-code.fd \
  -m 4096 \
  -drive file=os/phoenix-os/build/bwos-arcwyre-flex.iso,media=cdrom,readonly=on,format=raw \
  -boot d \
  -display none \
  -vnc :1
```

1. Connect to VNC screen at `:1` (port `5901`).
2. Switch to TTY2 terminal using the VNC key combination `Ctrl+Alt+F2`.
3. Auto-login will immediately drop you into the `arc@debian:~$` prompt.
4. Run the smoke test: `/usr/bin/arc-flex-smoke`.
