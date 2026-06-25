# Arcwyre Flex Live Validation Handoff

## ISO Artifact

**Path:**
```
os/phoenix-os/build/phoenix-os-release-amd64.iso
```

**SHA-256:**
```
a7e5135b546cf194da7b6ab15c5d97192043a0aa1161a62c45253b1a523e47a4
```

**Size:** 3.7G

**Format:** ISO 9660 CD-ROM (bootable, hybrid EFI)

---

## Linux KVM Boot

### Prerequisites
- Linux host with KVM support
- QEMU installed
- ISO copied to test host

### Boot Command
```bash
qemu-system-x86_64 \
  -enable-kvm \
  -m 4096 \
  -smp 2 \
  -cdrom phoenix-os-release-amd64.iso \
  -boot d \
  -serial stdio \
  -display gtk \
  -no-reboot
```

---

## USB Hardware Boot

### Prerequisites
- USB drive (4GB+)
- Linux host with USB write capability
- `dd` or similar USB write tool

### Create Bootable USB
```bash
sudo dd if=phoenix-os-release-amd64.iso of=/dev/sdX bs=4M status=progress
sudo sync
```

### Boot from USB
1. Insert USB into target machine
2. Power on, select USB boot (typically F12, Del, or Esc at POST)
3. SDDM should start automatically

---

## Inside Live Session: Validation Commands

Run these commands after SDDM boots and autologin completes:

```bash
# Check current user (should be 'arc')
whoami

# Check SDDM status
systemctl status sddm --no-pager

# Check active sessions
loginctl list-sessions

# Check SDDM configuration
cat /etc/sddm.conf | grep -A5 "\[Autologin\]"

# Check for autologin success marker
journalctl -b -u bwos-session-profile.service

# Verify no session-entry error (should produce no output)
journalctl -b | grep -i "Unable to find autologin session entry"

# Check Arcwyre Flex identity
cat /etc/os-release | grep -E "ID|NAME|VERSION"

# Verify runtime hook log
cat /run/arcwyre-flex-session-profile.log

# Check desktop environment
echo $DESKTOP_SESSION
```

---

## PASS / FAIL Checklist

### ✅ PASS Criteria (All Must Be True)

- [ ] ISO boots to SDDM login screen
- [ ] Auto-logs in as `arc` user (no manual password entry required)
- [ ] Desktop environment loads without manual intervention
- [ ] Active session shows SDDM service (not LightDM)
- [ ] `/etc/sddm.conf` has `[Autologin]` section with `User=arc`
- [ ] `journalctl -b -u bwos-session-profile.service` shows success marker
- [ ] No "Unable to find autologin session entry" error in journal
- [ ] `/run/arcwyre-flex-session-profile.log` exists and contains success marker
- [ ] Arcwyre Flex branding/identity visible in live session
- [ ] Desktop is usable (mouse, keyboard, basic UI responsive)

### ❌ FAIL Criteria (Any One Fails The Test)

- [ ] ISO fails to boot
- [ ] SDDM fails to start
- [ ] Autologin does not trigger (stuck at login prompt)
- [ ] Error: "Unable to find autologin session entry"
- [ ] Session shows LightDM fallback (not SDDM)
- [ ] `/etc/sddm.conf` missing or has wrong [Autologin] section
- [ ] No success marker in journalctl or runtime log
- [ ] Kernel panic or hardware/driver errors
- [ ] Desktop does not load after successful login
- [ ] Arcwyre Flex identity not present (wrong branding/hostname)

---

## Known Blocker: macOS QEMU

**Issue:** QEMU on macOS (HVF) does not support CD/DVD device emulation.

**Error:** `Boot failed: Could not read from CDROM (code 0009)`

**Workaround:** Use Linux KVM host or real USB hardware boot instead.

**Status:** Not a blocker for Linux KVM or USB hardware paths.

---

## Related Documentation

- Full validation report: `docs/ARCWYRE_FLEX_SDDM_AUTOLOGIN_VALIDATION.md`
- Build details: `os/phoenix-os/build/` (ISO, kernel, initrd)
- Hook implementation: `os/phoenix-os/live-build/config/hooks/live/0068-session-failure-telemetry.chroot`

---

## Handoff Complete

This document provides everything needed to validate Arcwyre Flex SDDM autologin
in a live environment without reopening the build and test infrastructure.

**Next validator:** Pick a Linux KVM host or USB hardware machine, follow the boot
commands, and run the validation checklist inside the live session.

---

**Created:** 2026-06-25  
**Branch:** fix/flex-live-autologin-serial-boot  
**Commit:** f53c4152
