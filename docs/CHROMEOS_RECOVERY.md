# Chrome OS recovery (download automation)

BootForge can **download** official Chrome OS recovery images by **board name** (hardware codename), using a public metadata index that maps boards to **Google-hosted** recovery ZIP URLs (`dl.google.com`).

## What this is

- **Not** a replacement for the Chromebook Recovery Utility for every workflow.
- **Is** a deterministic, scriptable way to fetch the same recovery binaries the ecosystem indexes from Google’s CDN.

## Data source and attribution

- **Metadata index**: [MercuryWorkshop/chromeos-releases-data](https://github.com/MercuryWorkshop/chromeos-releases-data) (JSON, **Creative Commons Attribution**). If you use this data in your own product, **include attribution** as required by that license.
- **Image files**: Served by **Google** from `https://dl.google.com/dl/edgedl/chromeos/recovery/…`. Phoenix Core does not host or redistribute those binaries.

Default index URL (override with `CHROMEOS_RECOVERY_INDEX_URL`):

`https://cdn.jsdelivr.net/gh/MercuryWorkshop/chromeos-releases-data@main/data.json`

## Operator safety

- **Wrong board = wrong recovery** and can fail or damage the device. Always confirm the **board** matches the Chromebook (recovery screen, `chrome://system`, or manufacturer documentation).
- Download automation **does not write to USB by default**. Writing a raw recovery image to a USB is **destructive**. BootForge can optionally perform a **gated raw** write (extract `.bin` from the ZIP, then write to a whole **removable** USB block device) only after explicit confirmations and the same prerequisite checks as other destructive flows.

## CLI

From the repository root (with `desktop/` on `PYTHONPATH` as in other BootForge scripts):

```bash
python3 scripts/chromeos_recovery_download.py --list-boards
python3 scripts/chromeos_recovery_download.py --board octopus -o ./recovery_octopus.zip
```

JSON output:

```bash
python3 scripts/chromeos_recovery_download.py --board octopus --json
```

## Python API

```python
from src.core.chromeos_recovery import fetch_index, select_recovery_for_board

index = fetch_index()
sel = select_recovery_for_board(index, "octopus")
# sel.url -> dl.google.com recovery ZIP
```

## BootForge GUI

1. Open **USB Deployment Builder** (from the app menu that shows the recipe manager, or wherever `USBRecipeManagerWidget` is exposed).
2. Tab **1. Recipe** → select **Chrome OS Recovery (download)**.
3. Tab **Chrome OS recovery** → enter **board** codename → **Download recovery ZIP**.
4. **Default (no USB write):** tab **5. Device** → leave **flash** unchecked → **Confirm recovery ZIP** shows the path and manual recovery steps.
5. **Optional raw write from BootForge:** tab **5. Device** → check **“Chrome OS: … flash recovery .bin to selected USB”** → select the correct **removable** USB → **Flash recovery to USB** → complete confirmations (device name + final token). BootForge extracts the single `.bin` from the ZIP, checks size against the USB when possible, then runs a raw block write (with optional verify). You need **root/sudo** (Linux/macOS) or **Administrator** (Windows) per `SafetyValidator` prerequisites.

## Unzipping and writing to USB

Recovery downloads are **`.zip`** files containing a `.bin` image. You can unzip manually and use your platform’s **verified** imaging flow, or use BootForge’s gated flash path above. The Python helper `extract_chromeos_recovery_bin()` extracts the lone `.bin` when the ZIP contains exactly one `.bin` member.
