# PR41A Operator Quickstart

## Current Artifact

```text
iso/outputs/bwos-home.iso
SHA256: 463e8273b24ef851b64c5b7388ebaafe639f6632b62ddea64e81aff7f43f5686
```

## Recommended Path For The Seagate Ventoy Drive

Because the external drive is a Ventoy drive, do not raw-image it unless you intend to erase Ventoy.

Use file-copy mode:

```sh
cd /Users/bj90-m1/PhoenixCore-
scripts/pr41a/host-preflight-macos.sh
ls /Volumes
scripts/pr41a/ventoy-copy-iso-macos.sh --volume /Volumes/Ventoy
```

If the volume name is different, replace `/Volumes/Ventoy` with the actual mounted path.

If macOS mounted NTFS read-only, copy the ISO from Windows/Linux or use an NTFS write driver. Do not fall back to raw imaging unless you accept erasing Ventoy.

## Raw USB Imaging Path

Only for a disposable USB, not the Ventoy drive:

```sh
cd /Users/bj90-m1/PhoenixCore-
scripts/pr41a/host-preflight-macos.sh
scripts/pr41a/raw-image-usb-macos.sh --disk diskN
```

The script refuses internal disks and requires exact confirmation.

## Physical Boot Test Steps

1. Boot target machine from the Ventoy/Phoenix USB.
2. Capture `photo_01_boot_menu`.
3. Select `bwos-home.iso` in Ventoy.
4. Capture `photo_02_grub`.
5. Boot Phoenix OS.
6. If desktop loads, capture `photo_03_desktop`.
7. If it fails, capture `photo_fail_01` and write `failure_notes.txt`.

## If Desktop Loads

Run this inside the Phoenix live session:

```sh
mkdir -p /tmp/pr41a-live-evidence
sh /path/to/live-collect-evidence.sh /tmp/pr41a-live-evidence
```

If the script is not available in the live session, manually run:

```sh
uname -a > uname-a.txt
cat /proc/cmdline > proc-cmdline.txt
lsblk > lsblk.txt
journalctl -b | tail -200 > journalctl-tail-200.txt
```

Then launch and record:

- Firefox
- Dolphin
- Konsole

## Classification

Run locally for the classification definitions:

```sh
scripts/pr41a/classify-attempt.sh
```

Do not record `PHYSICAL_BOOT_PASS` unless the desktop photo and guest evidence exist.
