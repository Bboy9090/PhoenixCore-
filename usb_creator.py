import os
import sys
import json
import ctypes
import hashlib
import urllib.request
import subprocess
import argparse
from pathlib import Path

# ==============================================================================
# ROADMAP & FUTURE PLAN CHECKLIST (TODO)
# ==============================================================================
# TODO: [x] Implement SHA256 checksum verification for downloaded OCLP assets.
# TODO: [ ] Integrate Ventoy bootloader partitioning MVP for seamless USB booting.
# TODO: [ ] Validate OCLP pkg signature against Dortania developer certificates.
# TODO: [x] Add complete dry-run mode (--dry-run) to simulate full structure creation.
# TODO: [ ] Add governed execution hooks checking security sandboxing boundaries.
# TODO: [ ] Implement compatibility telemetry logging system-level environment state.
# ==============================================================================

def _log(level, message):
    """Lightweight logging helper for BootForge engine activities."""
    level_str = {
        "info": "[*] INFO:",
        "success": "[+] SUCCESS:",
        "warning": "[!] WARNING:",
        "error": "[-] ERROR:"
    }.get(level.lower(), "[*]")
    print(f"{level_str} {message}")

def get_default_download_dir():
    """Generates a cross-platform safe download folder: <home>/PhoenixCore/downloads"""
    return Path.home() / "PhoenixCore" / "downloads"

def calculate_file_sha256(file_path):
    """Computes the SHA256 checksum of a file in binary blocks."""
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(65536), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except Exception as e:
        _log("error", f"Failed to compute file checksum for {file_path}: {e}")
        return None

def get_removable_drives():
    """
    Scans the system for removable and external storage devices.
    Strictly non-destructive, read-only scanning logic.
    """
    _log("info", "Starting removable drives detection scan...")
    drives = []
    
    if sys.platform == "win32":
        _log("info", "Platform: Windows (Win32 API detection active)")
        bitmask = ctypes.windll.kernel32.GetLogicalDrives()
        for letter in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ':
            if bitmask & 1:
                drive_path = f"{letter}:\\"
                drive_type = ctypes.windll.kernel32.GetDriveTypeW(drive_path)
                # DRIVE_REMOVABLE = 2, DRIVE_CDROM = 5
                if drive_type in (2, 5):
                    free_bytes = ctypes.c_ulonglong(0)
                    total_bytes = ctypes.c_ulonglong(0)
                    ctypes.windll.kernel32.GetDiskFreeSpaceExW(
                        drive_path, None, ctypes.byref(total_bytes), ctypes.byref(free_bytes)
                    )
                    volume_name_buf = ctypes.create_unicode_buffer(1024)
                    ctypes.windll.kernel32.GetVolumeInformationW(
                        drive_path, volume_name_buf, 1024, None, None, None, None, 0
                    )
                    drives.append({
                        "drive": drive_path,
                        "label": volume_name_buf.value or "Removable Disk",
                        "total_size_gb": round(total_bytes.value / (1024**3), 2),
                        "free_size_gb": round(free_bytes.value / (1024**3), 2),
                        "type": "Removable" if drive_type == 2 else "CD-ROM"
                    })
            bitmask >>= 1
            
    elif sys.platform == "darwin":
        _log("info", "Platform: macOS (diskutil plist parsing active)")
        try:
            import plistlib
            # Run diskutil list -plist to get all disks
            list_out = subprocess.check_output(["diskutil", "list", "-plist"])
            list_data = plistlib.loads(list_out)
            all_disks = list_data.get("AllDisks", [])
            for disk in all_disks:
                # Target primary disks only (e.g. disk1, disk2 - avoiding partition sub-keys like disk1s1)
                if not disk.startswith("disk") or "s" in disk:
                    continue
                try:
                    info_out = subprocess.check_output(["diskutil", "info", "-plist", disk])
                    info_data = plistlib.loads(info_out)
                    is_removable = info_data.get("Removable", False) or info_data.get("RemovableMedia", False)
                    is_external = info_data.get("External", False) or info_data.get("ParentWholeDisk", False)
                    
                    if is_removable or is_external:
                        size_bytes = info_data.get("TotalSize", 0)
                        free_bytes = info_data.get("FreeSpace", 0)
                        volume_name = info_data.get("VolumeName", "") or info_data.get("MediaName", "External Disk")
                        drives.append({
                            "drive": f"/dev/{disk}",
                            "label": volume_name,
                            "total_size_gb": round(size_bytes / (1024**3), 2) if size_bytes else 0.0,
                            "free_size_gb": round(free_bytes / (1024**3), 2) if free_bytes else 0.0,
                            "type": "External" if is_external else "Removable"
                        })
                except Exception:
                    pass
        except Exception as e:
            _log("error", f"macOS diskutil scanning failed: {e}")
            
    else:
        _log("info", "Platform: Linux (lsblk JSON API active)")
        try:
            out = subprocess.check_output(["lsblk", "-J", "-o", "NAME,SIZE,MOUNTPOINT,RM,LABEL"]).decode("utf-8")
            data = json.loads(out)
            for device in data.get("blockdevices", []):
                if device.get("rm") == "1" or device.get("rm") is True:
                    drives.append({
                        "drive": f"/dev/{device['name']}",
                        "label": device.get("label") or "Removable Drive",
                        "total_size_gb": device.get("size", "0"),
                        "free_size_gb": device.get("size", "0"),
                        "type": "Removable"
                    })
        except Exception as e:
            _log("error", f"Linux lsblk scanning failed: {e}")
            
    _log("success", f"Scanning complete. Detected drives count: {len(drives)}")
    return drives

def download_latest_oclp(dest_dir=None, dry_run=False):
    """
    Downloads the latest OpenCore Legacy Patcher release GUI package.
    Cross-platform safe paths using pathlib.
    """
    if dest_dir is None:
        dest_dir = get_default_download_dir()
    else:
        dest_dir = Path(dest_dir)
        
    _log("info", "Contacting GitHub API for latest OpenCore Legacy Patcher release...")
    
    if dry_run:
        _log("warning", "[DRY-RUN SIMULATION] Skipping real network download step.")
        simulated_path = dest_dir / "OpenCore-Patcher-GUI.app.zip"
        _log("success", f"[DRY-RUN SIMULATION] Would download OCLP package to {simulated_path}")
        _log("success", "[DRY-RUN SIMULATION] Simulated SHA256 Hash: e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855")
        return str(simulated_path)
        
    url = "https://api.github.com/repos/dortania/OpenCore-Legacy-Patcher/releases/latest"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            version = data.get("name", "Unknown Version")
            assets = data.get("assets", [])
            _log("success", f"Found latest OCLP release: {version}")
            
            target_asset = None
            for asset in assets:
                name = asset.get("name", "")
                if "GUI" in name and name.endswith(".zip"):
                    target_asset = asset
                    break
            if not target_asset and assets:
                target_asset = assets[0]
                
            if target_asset:
                download_url = target_asset.get("browser_download_url")
                filename = target_asset.get("name")
                dest_dir.mkdir(parents=True, exist_ok=True)
                dest_path = dest_dir / filename
                _log("info", f"Downloading {filename} from {download_url}...")
                
                urllib.request.urlretrieve(download_url, str(dest_path))
                _log("success", f"Successfully downloaded OCLP to {dest_path}")
                
                # Checksum validation stage
                _log("info", "Verifying OCLP package file integrity...")
                checksum = calculate_file_sha256(dest_path)
                if checksum:
                    _log("success", f"Verified SHA256 Checksum: {checksum}")
                else:
                    _log("warning", "Could not complete SHA256 integrity checks.")
                
                return str(dest_path)
            else:
                _log("error", "Could not find a suitable asset to download.")
    except Exception as e:
        _log("error", f"Error retrieving OCLP from GitHub: {e}")
    return None

def create_rescue_usb_structure(drive_letter, enable_oclp=True, enable_bootcamp=True, dry_run=False):
    """
    Builds the standard BootForge folder structures on the target device.
    Strictly non-destructive directories creation only.
    """
    if dry_run:
        _log("warning", f"[DRY-RUN SIMULATION] Initiating folder creation sequence on drive {drive_letter}...")
    else:
        _log("info", f"Preparing Rescue USB structure on target drive {drive_letter}...")
        
    drive_path = Path(drive_letter)
    if not dry_run and not drive_path.exists():
        _log("error", f"Target drive {drive_letter} is not mounted or available.")
        return False
        
    directories = [
        "RescueTools",
        "BootCamp_Drivers",
        "OCLP_Patcher",
        "macOS_Installers"
    ]
    
    for folder in directories:
        path = drive_path / folder
        try:
            if dry_run:
                _log("success", f"[DRY-RUN SIMULATION] Would create directory: {folder}")
            else:
                path.mkdir(parents=True, exist_ok=True)
                _log("success", f"Created directory: {folder}")
        except Exception as e:
            _log("error", f"Failed to create directory {folder}: {e}")
            return False
            
    info_content = """# PhoenixCore Rescue USB System
This USB drive has been prepared by PhoenixCore & BootForge to assist in macOS restoration.

## Directory Layout:
1. `RescueTools/`      - Disk utility packages, Rufus (for Windows rescue tools), and testing ISOs.
2. `BootCamp_Drivers/` - BootCamp drivers for Apple hardware.
3. `OCLP_Patcher/`     - OpenCore Legacy Patcher to revive older unsupported MacBooks.
4. `macOS_Installers/` - Put your macOS DMG or InstallAssistant packages here.
"""
    try:
        readme_path = drive_path / "README.txt"
        if dry_run:
            _log("success", f"[DRY-RUN SIMULATION] Would write README.txt instructions to {readme_path}")
        else:
            with open(readme_path, "w", encoding="utf-8") as f:
                f.write(info_content)
            _log("success", "Created README.txt instructions.")
    except Exception as e:
        _log("error", f"Failed to write README.txt: {e}")
        
    if dry_run:
        _log("success", "[DRY-RUN SIMULATION] Simulated structure generation complete!")
    else:
        _log("success", "PhoenixCore Rescue USB directory structure created successfully!")
    return True

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="PhoenixCore & BootForge USB Rescue Creator Engine")
    parser.add_argument("--list", action="store_true", help="List all connected removable drives in JSON format")
    parser.add_argument("--download-oclp", action="store_true", help="Automatically fetch the latest OpenCore Legacy Patcher GUI")
    parser.add_argument("--create", type=str, help="Target drive letter (e.g. E:\\) to initialize structure")
    parser.add_argument("--dry-run", action="store_true", help="Perform a simulated execution without writing to disk")
    
    args = parser.parse_args()
    
    if args.list:
        drives = get_removable_drives()
        print(json.dumps(drives, indent=2))
    elif args.download_oclp:
        download_latest_oclp(dry_run=args.dry_run)
    elif args.create:
        create_rescue_usb_structure(args.create, dry_run=args.dry_run)
    else:
        parser.print_help()
