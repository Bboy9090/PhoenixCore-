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
- Download automation **does not write to USB**. Writing a raw recovery image to a USB is still a **destructive** operation and must go through your normal safety + audit path.

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
4. When the download finishes, **Build USB Drive** confirms the ZIP path and reminds you to unzip and write the `.bin` (BootForge does not run the full partition pipeline for this recipe).

## Unzipping and writing to USB

Recovery downloads are **`.zip`** files containing a `.bin` image. Unzip, then use your platform’s **verified** imaging flow (same rules as other raw disk images). Automating `dd` to a removable device is intentionally **not** bundled in this download-only step.
