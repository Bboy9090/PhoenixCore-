# PR29 Phoenix OS Hardened Rebuild & Branding Fix

Date: 2026-05-14

## Summary
PR29 addresses the branding regressions and autologin failures identified during the PR28 Smoke Test. The objective is to transition from "Blue Debian" to the "Sacred Minimal" Phoenix experience and eliminate the live-session lockouts.

## 1. Branding Remediation
- **Plymouth Fix**: Added [0050-set-plymouth-theme.chroot](file:///Users/bj90-m1/PhoenixCore-/os/phoenix-os/live-build/config/hooks/live/0050-set-plymouth-theme.chroot) to force the `phoenix` theme and update the `initramfs`.
- **Logo Redesign**: Created a premium, multi-layered SVG logo for the boot splash: [phoenix-logo-boot.svg](file:///Users/bj90-m1/PhoenixCore-/os/phoenix-os/branding/plymouth/phoenix/phoenix-logo-boot.svg).
- **SDDM Fix**: Added [0060-set-sddm-theme.chroot](file:///Users/bj90-m1/PhoenixCore-/os/phoenix-os/live-build/config/hooks/live/0060-set-sddm-theme.chroot) to apply the Phoenix lock screen and enable **auto-login** for the `phoenix` user.

## 2. Boot Parameter Hardening
- Updated `auto/config` with:
    - `username=phoenix`: Sets the correct live user.
    - `quiet splash`: Enables the Plymouth animation.
    - `plymouth.ignore-serial-consoles`: Prevents logs from breaking the splash animation in VMs.

## 3. Verification Checklist (Post-Build)
- [ ] **Stage E-1**: Verify animated Phoenix logo on boot (no Debian helmet).
- [ ] **Stage E-2**: Verify Phoenix-themed SDDM login screen.
- [ ] **Stage E-3**: Verify auto-login to desktop (no lockout).
- [ ] **Stage F-1**: Verify `/etc/phoenix-version` marker file existence.

## Next Steps
**Trigger Rebuild**: Run `bash os/phoenix-os/scripts/build-iso.sh` to produce the **True Hardened ISO**.
**Final Proof**: Execute one more UTM smoke test to confirm branding success before moving to physical hardware.
