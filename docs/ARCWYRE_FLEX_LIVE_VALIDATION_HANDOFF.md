# Arcwyre Flex Live Validation Handoff

## ISO Path

```text
os/phoenix-os/build/phoenix-os-release-amd64.iso
```

## ISO SHA-256

```text
a7e5135b546cf194da7b6ab15c5d97192043a0aa1161a62c45253b1a523e47a4
```

## Linux KVM QEMU Command

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

## USB Hardware Boot Option

```bash
sudo dd if=phoenix-os-release-amd64.iso of=/dev/sdX bs=4M status=progress
sudo sync
```

Boot the target machine from the USB device and validate the same live-session criteria.

## Inside-Live-Session Validation Commands

```bash
whoami
systemctl status sddm --no-pager
loginctl list-sessions
cat /etc/sddm.conf
journalctl -b -u bwos-session-profile.service --no-pager
journalctl -b --no-pager | grep -i "Unable to find autologin session entry"
cat /etc/os-release
cat /run/arcwyre-flex-session-profile.log
echo "$DESKTOP_SESSION"
```

## PASS / FAIL Checklist

PASS only if all are true:

- ISO boots to the live environment.
- SDDM starts in the live environment.
- The system autologins as `arc`.
- `loginctl list-sessions` shows an active live session.
- `journalctl -b -u bwos-session-profile.service --no-pager` shows the runtime marker.
- No runtime journal line contains `Unable to find autologin session entry`.
- Arcwyre Flex identity markers are present.
- The live desktop is usable.

FAIL if any are true:

- ISO does not boot.
- SDDM does not start.
- Autologin does not enter the `arc` session.
- Runtime journal contains `Unable to find autologin session entry`.
- Required runtime marker is missing.
- Arcwyre Flex identity markers are missing.
- The live desktop is not usable.

## Known Blocker

Live boot validation could not be completed in the current macOS QEMU setup.
The attempted QEMU CDROM path failed with CDROM read error 0009.
Live validation is deferred to Linux KVM or direct hardware boot.
