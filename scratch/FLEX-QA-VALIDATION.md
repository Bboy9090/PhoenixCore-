# ARCWYRE Flex SDDM Autologin QA Validation

## Build Status: ✅ PASSED

**ISO:** `bwos-arcwyre-flex.iso`  
**Hash:** `8a51466f53bd6c64a9bad06b751a93fdcc65e6e847b9c4ab73ad53d9bc3e5934`  
**Commit:** `107df229` (fix/flex-live-autologin-serial-boot)  
**Build Date:** 2026-06-24 11:13:55 UTC  

---

## Code Validation: ✅ PASSED

✅ `/etc/sddm.conf` (build-time): Only `[Theme]` section (no autologin config)  
✅ Runtime script `bwos-session-profile-apply`: Writes `/etc/sddm.conf` with correct `[Autologin]` section  
✅ GRUB entries: All use `username=arc`  
✅ User detection: Script checks for `arc` availability  
✅ Logging: Script includes `BWOS_SDDM_AUTOLOGIN_CONFIGURED` marker  

---

## Live Boot Evidence Required

### Option A: Linux VM or Real Hardware (RECOMMENDED)

#### Boot Command
```bash
# On a Linux system with QEMU or KVM
qemu-system-x86_64 -m 4096 -smp 4 -cdrom bwos-arcwyre-flex.iso -display gtk
# OR
virt-manager  # Select ISO, boot, wait for graphical desktop
```

#### Post-Boot Validation (in terminal on booted system)
```bash
# 1. Check journal for SDDM autologin markers
journalctl -b | grep -E "BWOS_SDDM_AUTOLOGIN_CONFIGURED|Unable to find autologin session"

# Expected output:
#   BWOS_SDDM_AUTOLOGIN_CONFIGURED user=arc session=plasmax11.desktop
# Should NOT contain:
#   Unable to find autologin session entry ""

# 2. Verify session is active and using SDDM
loginctl

# Expected output:
#   SESSION UID USER SEAT TTY TYPE CLASS STATE SERVICE
#   1       1001 arc  seat0 vt1 x11  user  active sddm

# 3. Check runtime SDDM config
cat /etc/sddm.conf

# Expected output:
#   [Autologin]
#   User=arc
#   Session=plasmax11.desktop
#   Relogin=true
#   
#   [General]
#   DefaultSession=plasmax11.desktop
#   
#   [Theme]
#   Current=phoenix

# 4. Verify SDDM service status
systemctl status sddm --no-pager

# Expected: active (running)
# NOT: inactive, or showing "Unable to find autologin session" error

# 5. Verify no LightDM fallback was needed
systemctl status lightdm --no-pager 2>/dev/null || echo "LightDM not active (correct)"

# Expected: inactive (dead) or not found
# We want SDDM, not LightDM fallback
```

#### Pass Criteria
```
✅ journalctl shows: BWOS_SDDM_AUTOLOGIN_CONFIGURED user=arc session=plasmax11.desktop
✅ journalctl does NOT show: Unable to find autologin session entry
✅ loginctl shows: active session for arc, service=sddm (not lightdm-autologin)
✅ /etc/sddm.conf contains: [Autologin] with User=arc and valid Session
✅ systemctl status sddm shows: active (running)
✅ systemctl status lightdm shows: inactive or not running
```

---

### Option B: Automated Script (Linux/macOS)

#### Run validation script
```bash
cd /Users/bj90-m1/PhoenixCore-/scratch

# On macOS (limited serial capture):
chmod +x validate-flex-sddm-boot.sh
./validate-flex-sddm-boot.sh /Users/bj90-m1/PhoenixCore-/os/phoenix-os/build/bwos-arcwyre-flex.iso

# On Linux (full serial capture):
chmod +x validate-flex-sddm-boot.sh
./validate-flex-sddm-boot.sh /path/to/bwos-arcwyre-flex.iso 240
```

The script will:
1. Boot the ISO for 240 seconds
2. Capture serial output
3. Search for key markers
4. Report on SDDM autologin success or failure

---

### Option C: Docker-based Linux Environment

```bash
cd /Users/bj90-m1/PhoenixCore-/scratch

# Build Docker image with QEMU
docker build -f Dockerfile.flex-test -t flex-test .

# Run validation
docker run -v /Users/bj90-m1/PhoenixCore-/os/phoenix-os/build:/iso \
    flex-test /validation/validate-flex-sddm-boot.sh /iso/bwos-arcwyre-flex.iso
```

---

## Expected First-Boot Sequence

1. UEFI/BIOS → GRUB (loads with `username=arc`)
2. Kernel boot → systemd starts
3. `bwos-session-profile-apply` hook runs
   - Detects user `arc` exists
   - Writes `/etc/sddm.conf` with `[Autologin] User=arc Session=plasmax11.desktop`
   - Logs: `BWOS_SDDM_AUTOLOGIN_CONFIGURED user=arc session=plasmax11.desktop`
4. SDDM starts
   - Reads `/etc/sddm.conf` (runtime config, correct values)
   - Does NOT read stale `/etc/sddm.conf.d/autologin.conf` with empty Session
   - Finds valid Session entry
5. User `arc` autologins
   - X11 session starts
   - Plasma desktop loads
   - systemd user session for arc starts (dbus, systemd --user)
6. Desktop ready (no login prompt)

---

## What We're Proving

```
❌ BEFORE (old ISO):
   SDDM error: "Unable to find autologin session entry """
   → SDDM autologin fails
   → LightDM fallback takes over
   → User arc logs in via LightDM (not SDDM)
   → Diagnostics show: service=lightdm-autologin (fallback)

✅ AFTER (new ISO with fixes):
   No SDDM error
   → SDDM autologin succeeds
   → User arc logs in via SDDM (direct)
   → Diagnostics show: service=sddm (correct)
   → No LightDM fallback needed
```

---

## Files in This ISO

- `/boot/grub/grub.cfg` — Boot entries with `username=arc` ✅
- `/etc/sddm.conf` — Theme only, no stale autologin config ✅
- `/usr/local/bin/bwos-session-profile-apply` — Runtime hook that writes correct autologin config ✅
- `/lib/live/config/1200-arc-user` — Live user creation hook ✅

---

## QA Checklist

- [ ] Boot ISO on Linux VM or hardware
- [ ] Desktop appears (graphical.target reached)
- [ ] User arc is logged in (no login prompt)
- [ ] Terminal available (click activity menu or Ctrl+Alt+T)
- [ ] Run validation commands above
- [ ] Verify all expected outputs match
- [ ] Verify all "should NOT contain" items are absent
- [ ] Confirm service=sddm (not lightdm-autologin)

---

## Reporting

Once validated on Linux/hardware, fill in:

```
ISO Hash:             8a51466f53bd6c64a9bad06b751a93fdcc65e6e847b9c4ab73ad53d9bc3e5934
Boot Environment:     [Linux VM / Hardware / Docker]
Kernel Version:       [6.12.94+deb13-amd64]
Display Manager:      [SDDM or LightDM]
Autologin User:       [arc]
Session Type:         [X11 / Wayland]
SDDM Config Present:  [YES with correct [Autologin] section]
Error "Unable to find": [NOT PRESENT (correct)]
Journal Marker Found:  [BWOS_SDDM_AUTOLOGIN_CONFIGURED user=arc ...]
Loginctl Shows SDDM:   [YES (correct)]
Loginctl Shows LightDM: [NO (correct)]
Final Status:         [PASS / FAIL]
Comments:             [...]
```

---

## Current State

✅ Build: PASS  
✅ ISO Contents: PASS  
✅ Code Validation: PASS  
❌ Live Boot Evidence: PENDING (awaiting Linux/hardware test)  

**Status: READY FOR QA / HARDWARE VALIDATION**
