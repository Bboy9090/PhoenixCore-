# PR41A Evidence Capture Template

Use one copy of this template per physical boot attempt.

## Run Metadata

- Slot ID: `[HW-01/HW-06/HW-03/HW-04/HW-05]`
- Operator: `[name or handle]`
- Execution timestamp UTC: `[YYYY-MM-DDTHH:MM:SSZ]`
- Booted edition: `Home Aurelia`
- Artifact path: `iso/outputs/bwos-home.iso`
- Artifact SHA256: `463e8273b24ef851b64c5b7388ebaafe639f6632b62ddea64e81aff7f43f5686`

## Target Machine

- Manufacturer:
- Model:
- CPU:
- RAM:
- Firmware type:
- Secure Boot status:
- Boot picker hotkey:

## USB Media

- USB make/model:
- USB capacity:
- USB device path used for imaging:
- USB write command used:
- ISO SHA256 verified before write: `[yes/no]`

## Boot Evidence

- photo_01_boot_menu:
- photo_02_grub:
- photo_03_desktop:
- photo_fail_01:
- failure_notes.txt:

## Guest Evidence If Desktop Reached

```text
uname -a:
```

```text
cat /proc/cmdline:
```

```text
lsblk:
```

```text
journalctl -b | tail -200:
```

## App Smoke Test

| App | Result | Notes |
| --- | --- | --- |
| Firefox | `NOT_TESTED` | |
| Dolphin | `NOT_TESTED` | |
| Konsole | `NOT_TESTED` | |

## Classification

Choose one:

- `PHYSICAL_BOOT_PASS`
- `PHYSICAL_BOOT_PARTIAL`
- `PHYSICAL_BOOT_FAIL_NO_PICKER`
- `PHYSICAL_BOOT_FAIL_BOOTLOADER`
- `PHYSICAL_BOOT_FAIL_KERNEL`
- `PHYSICAL_BOOT_FAIL_DESKTOP`

Final classification:

```text
PENDING
```

## Operator Notes

```text

```
