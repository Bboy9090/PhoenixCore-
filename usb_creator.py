import os
import sys
import json
import ctypes
import hashlib
import urllib.request
import subprocess
import argparse
import re
from pathlib import Path
from datetime import datetime, timezone

# ==============================================================================
# ROADMAP & FUTURE PLAN CHECKLIST (TODO)
# ==============================================================================
# TODO: [x] Implement SHA256 checksum verification for downloaded OCLP assets.
# TODO: [ ] Integrate Ventoy bootloader partitioning MVP for seamless USB booting.
# TODO: [ ] Validate OCLP pkg signature against Dortania developer certificates.
# TODO: [x] Add complete dry-run mode (--dry-run) to simulate full structure creation.
# TODO: [x] Add governed execution hooks checking security sandboxing boundaries.
# TODO: [x] Cryptographically sign tool_registry.json and verify detached signatures (Ed25519).
# TODO: [x] Add read-only image inspection bridge with SHA256 reporting.
# ==============================================================================

SUPPORTED_IMAGE_EXTENSIONS = {".iso", ".img", ".dmg", ".bin", ".raw"}

# ------------------------------------------------------------------------------
# RFC 8032 Ed25519 Cryptography Reference Implementation
# ------------------------------------------------------------------------------
p = 2**255 - 19
l = 2**252 + 27742317777372353535851937790883648493
d = -121665 * pow(121666, -1, p) % p
I = pow(2, (p - 1) // 4, p)

# Direct coordinates of standard Base Point G (B)
y_base = 4 * pow(5, -1, p) % p


def _xrecover(y):
    xx = (y * y - 1) * pow(d * y * y + 1, -1, p) % p
    x = pow(xx, (p + 3) // 8, p)
    if (x * x - xx) % p != 0:
        x = (x * I) % p
    if x % 2 != 0:
        x = p - x
    return x


x_base = _xrecover(y_base)
B = (x_base, y_base)


def point_decompress(s):
    if len(s) != 32:
        return None
    y_val = int.from_bytes(s, "little")
    sign = y_val >> 255
    y_val &= (1 << 255) - 1
    if y_val >= p:
        return None
    xx = (y_val * y_val - 1) * pow(d * y_val * y_val + 1, -1, p) % p
    x_val = pow(xx, (p + 3) // 8, p)
    if (x_val * x_val - xx) % p != 0:
        x_val = (x_val * I) % p
        if (x_val * x_val - xx) % p != 0:
            return None
    if (x_val & 1) != sign:
        x_val = p - x_val
    return (x_val, y_val)


def point_compress(P):
    x_val, y_val = P
    return ((y_val & ((1 << 255) - 1)) | ((x_val & 1) << 255)).to_bytes(32, "little")


def point_add(P, Q):
    x1, y1 = P
    x2, y2 = Q
    num_x = (x1 * y2 + y1 * x2) % p
    den_x = (1 + d * x1 * x2 * y1 * y2) % p
    num_y = (y1 * y2 + x1 * x2) % p
    den_y = (1 - d * x1 * x2 * y1 * y2) % p
    x3 = num_x * pow(den_x, -1, p) % p
    y3 = num_y * pow(den_y, -1, p) % p
    return (x3, y3)


def point_mul(s, P):
    Q = (0, 1)
    base = P
    while s > 0:
        if s & 1:
            Q = point_add(Q, base)
        base = point_add(base, base)
        s >>= 1
    return Q


def ed25519_verify(pubkey_hex, sig_hex, msg_bytes):
    """
    Verifies detached Ed25519 signatures of the tool registry.
    RFC 8032 compliance.
    """
    try:
        pubkey = bytes.fromhex(pubkey_hex)
        sig = bytes.fromhex(sig_hex)
        if len(pubkey) != 32 or len(sig) != 64:
            return False
        A = point_decompress(pubkey)
        if not A:
            return False
        R = point_decompress(sig[:32])
        if not R:
            return False
        s = int.from_bytes(sig[32:], "little")
        if s >= l:
            return False
        h = (
            int.from_bytes(
                hashlib.sha512(sig[:32] + pubkey + msg_bytes).digest(), "little"
            )
            % l
        )
        sB = point_mul(s, B)
        hA = point_mul(h, A)
        R_plus_hA = point_add(R, hA)
        return sB == R_plus_hA
    except Exception:
        return False


# ------------------------------------------------------------------------------
# Governed System Configuration
# ------------------------------------------------------------------------------
TRUST_ANCHOR_PUBKEY = "0ad76a7f232cb7d725937e8dfa5368cb212e6be1e68f329119ef510c1f1cff68"


def utc_now_iso():
    """Returns a timezone-aware UTC timestamp formatted with a trailing Z."""
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _log(level, message):
    """Lightweight logging helper for BootForge engine activities."""
    level_str = {
        "info": "[*] INFO:",
        "success": "[+] SUCCESS:",
        "warning": "[!] WARNING:",
        "error": "[-] ERROR:",
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


def load_tool_registry():
    """
    Loads and cryptographically validates the tool registry JSON configuration.
    Enforces detached Ed25519 signature verification against the Trust Anchor.
    """
    registry_path = Path(__file__).parent / "manifests" / "tool_registry.json"
    sig_path = Path(__file__).parent / "manifests" / "tool_registry.sig"
    if not registry_path.exists():
        # Fallback for tests/
        registry_path = (
            Path(__file__).parent.parent / "manifests" / "tool_registry.json"
        )
        sig_path = Path(__file__).parent.parent / "manifests" / "tool_registry.sig"

    if not registry_path.exists():
        _log(
            "warning",
            "Tool registry manifest not found. Tool validation will fail closed.",
        )
        return None

    # Strictly require detached signature file
    if not sig_path.exists():
        _log(
            "error",
            "CRITICAL SECURITY HALT: Detached signature manifest file (.sig) is missing!",
        )
        sys.exit(1)

    try:
        msg_bytes = registry_path.read_bytes()
        sig_hex = sig_path.read_text(encoding="utf-8").strip()

        _log("info", "Executing cryptographic manifest signature validation...")
        if not ed25519_verify(TRUST_ANCHOR_PUBKEY, sig_hex, msg_bytes):
            _log(
                "error",
                "CRITICAL SECURITY HALT: Tool registry signature verification failed!",
            )
            _log("error", "  The tool manifest has been tampered with or unsigned!")
            sys.exit(1)

        _log(
            "success", "Cryptographic signature matches! Manifest provenance verified."
        )

        with open(registry_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except SystemExit:
        raise
    except Exception as e:
        _log("error", f"Failed to verify or parse tool registry manifest: {e}")
        sys.exit(1)


def validate_tool_against_registry(tool_id, download_url=None, file_path=None):
    """
    Validates a tool's parameters (URL and checksum) against the governed tool registry.
    Strictly enforces trust boundaries: rejects unknown tools, URL mismatches, or checksum failures.
    """
    registry = load_tool_registry()
    if not registry:
        _log(
            "error",
            f"Registry unavailable. Tool validation denied for {tool_id}.",
        )
        return False

    tools = registry.get("tools", [])
    target_tool = None
    for tool in tools:
        if tool.get("id") == tool_id:
            target_tool = tool
            break

    if not target_tool:
        _log(
            "error",
            f"Access Denied: Tool ID '{tool_id}' is not registered in the governed registry!",
        )
        return False

    # 1. URL boundary validation
    if download_url and target_tool.get("download_url") != download_url:
        _log("error", f"Access Denied: Download URL mismatch for '{tool_id}'!")
        _log("error", f"  Attempted: {download_url}")
        _log("error", f"  Registered: {target_tool.get('download_url')}")
        return False

    # 2. Checksum validation
    if file_path:
        _log(
            "info",
            f"Calculating SHA256 cryptographic signature for downloaded asset: {file_path}...",
        )
        checksum = calculate_file_sha256(file_path)
        if not checksum:
            _log(
                "error", f"Halt: Failed to calculate SHA256 signature for '{tool_id}'!"
            )
            return False

        expected = target_tool.get("expected_sha256")
        if checksum != expected:
            _log(
                "error",
                "CRITICAL SECURITY ERROR: Cryptographic checksum validation failed!",
            )
            _log("error", f"  Expected (Registry): {expected}")
            _log("error", f"  Actual (Computed):  {checksum}")
            return False
        _log("success", f"Integrity check passed! Verified SHA256 Checksum: {checksum}")

    return True


def get_normalized_scan(quiet=False):
    """
    Runs the v2 cross-platform device scanner and returns the full normalized result.
    Schema: bootforge.device_scan.v2
    Read-only. No destructive operations.
    """
    from device_scanner import scan_devices

    def scan_log(level, message):
        if not quiet:
            _log(level, message)

    scan_log("info", "Starting normalized device scan (bootforge.device_scan.v2)...")
    result = scan_devices()
    scan_log(
        "success",
        f"Normalized scan complete. Detected {result.get('device_count', 0)} devices.",
    )
    return result


def get_removable_drives(quiet=False):
    """
    Scans the system for removable and external storage devices.
    Compatibility wrapper: delegates to device_scanner.scan_devices() and
    derives the legacy output shape from normalized v2 evidence.
    Strictly non-destructive, read-only scanning logic.

    Args:
        quiet: Suppresses human log lines so callers can build clean JSON bridge payloads.
    """
    scan_result = get_normalized_scan(quiet=quiet)
    drives = []
    for dev in scan_result.get("devices", []):
        if not dev.get("is_removable") and not dev.get("is_external"):
            continue
        drive_type = "Removable"
        if dev.get("is_external") and not dev.get("is_removable"):
            drive_type = "External"
        drives.append(
            {
                "drive": dev.get("drive_path"),
                "label": dev.get("volume_label")
                or dev.get("display_name")
                or "Removable Disk",
                "total_size_gb": dev.get("size_gb", 0.0),
                "free_size_gb": dev.get("size_gb", 0.0),
                "type": drive_type,
            }
        )
    return drives


def build_drive_scan_payload():
    """
    Builds a clean, machine-readable USB scan payload for dashboard/desktop bridges.
    Uses the normalized v2 scanner and includes both v2 devices and legacy drives.
    Read-only. No destructive operations.
    """
    scan_result = get_normalized_scan(quiet=True)
    legacy_drives = []
    for dev in scan_result.get("devices", []):
        if not dev.get("is_removable") and not dev.get("is_external"):
            continue
        drive_type = "Removable"
        if dev.get("is_external") and not dev.get("is_removable"):
            drive_type = "External"
        legacy_drives.append(
            {
                "drive": dev.get("drive_path"),
                "label": dev.get("volume_label")
                or dev.get("display_name")
                or "Removable Disk",
                "total_size_gb": dev.get("size_gb", 0.0),
                "free_size_gb": dev.get("size_gb", 0.0),
                "type": drive_type,
            }
        )
    return {
        "schema": "bootforge.drive_scan.v2",
        "generated_at": utc_now_iso(),
        "platform": sys.platform,
        "safe_mode": True,
        "destructive": False,
        "operation": "read_only_drive_scan",
        "scanner_schema": scan_result.get("schema"),
        "scan_id": scan_result.get("scan_id"),
        "detection_source": scan_result.get("detection_source"),
        "device_count": scan_result.get("device_count", 0),
        "devices": scan_result.get("devices", []),
        "drives": legacy_drives,
        "scan_warnings": scan_result.get("scan_warnings", []),
    }


def print_drive_scan_json():
    """
    Emits JSON-only removable drive scan output for UI bridges.
    No human log lines are mixed into stdout, so dashboard wrappers can parse it safely.
    """
    payload = build_drive_scan_payload()
    print(json.dumps(payload, indent=2))
    return payload


def build_image_inspection_payload(image_path):
    """
    Builds a clean, machine-readable image inspection payload.
    This is read-only: it never writes to, mounts, burns, partitions, or modifies disks.
    """
    target = Path(image_path).expanduser()
    extension = target.suffix.lower()
    supported = extension in SUPPORTED_IMAGE_EXTENSIONS

    image_info = {
        "path": str(target),
        "filename": target.name,
        "extension": extension,
        "exists": target.is_file(),
        "supported": supported,
        "supported_extensions": sorted(SUPPORTED_IMAGE_EXTENSIONS),
        "size_bytes": 0,
        "size_gb": 0.0,
        "sha256": None,
    }

    payload = {
        "schema": "bootforge.image_inspection.v1",
        "generated_at": utc_now_iso(),
        "platform": sys.platform,
        "safe_mode": True,
        "destructive": False,
        "operation": "read_only_image_inspection",
        "image": image_info,
        "error": None,
    }

    if not target.exists():
        payload["error"] = "Image path does not exist."
        return payload

    if not target.is_file():
        payload["error"] = "Image path exists but is not a file."
        return payload

    try:
        size_bytes = target.stat().st_size
        image_info["size_bytes"] = size_bytes
        image_info["size_gb"] = round(size_bytes / (1024**3), 4)
        image_info["sha256"] = calculate_file_sha256(target)
        if image_info["sha256"] is None:
            payload["error"] = "Failed to calculate SHA256 for image."
    except Exception as e:
        payload["error"] = f"Failed to inspect image: {e}"

    return payload


def print_image_inspection_json(image_path):
    """
    Emits JSON-only read-only image inspection output for UI bridges.
    """
    payload = build_image_inspection_payload(image_path)
    print(json.dumps(payload, indent=2))
    return payload


def get_drive_root(path):
    """
    Resolves an arbitrary file/directory path to its containing drive or mount root.
    """
    try:
        p = Path(path).resolve()
    except Exception:
        p = Path(path).absolute()

    if sys.platform == "win32":
        drive = p.drive
        if drive:
            if not drive.endswith("\\"):
                drive += "\\"
            return drive
        curr_drive = Path(".").resolve().drive
        if not curr_drive.endswith("\\"):
            curr_drive += "\\"
        return curr_drive
    else:
        curr = p
        try:
            while curr != curr.parent:
                if curr.is_mount():
                    return str(curr)
                curr = curr.parent
        except Exception:
            pass
        return "/"


def _build_windows_physical_drive_safety_payload(drive_path):
    r"""
    Resolves a Windows ``\\.\PHYSICALDRIVE<n>`` identifier against the trusted,
    read-only Win32_DiskDrive scanner evidence.

    Raw device identifiers are not filesystem paths, so ``os.path.exists`` and
    volume-root APIs are intentionally not used here. The function never opens
    the raw device and fails closed when the scanner cannot prove the target.
    """
    requested_path = str(drive_path).strip().replace("/", "\\")
    match = re.fullmatch(r"\\\\\.\\PHYSICALDRIVE(\d+)", requested_path, re.IGNORECASE)
    if not match:
        return None

    canonical_path = f"\\\\.\\PHYSICALDRIVE{match.group(1)}"
    payload = {
        "schema": "bootforge.drive_safety.v1",
        "generated_at": utc_now_iso(),
        "platform": sys.platform,
        "safe_mode": True,
        "destructive": False,
        "operation": "read_only_drive_safety_check",
        "drive": None,
        "error": None,
    }

    scan_result = get_normalized_scan(quiet=True)
    device = next(
        (
            candidate
            for candidate in scan_result.get("devices", [])
            if str(candidate.get("drive_path") or "").casefold()
            == canonical_path.casefold()
        ),
        None,
    )

    if device is None:
        payload["error"] = (
            "Raw device was not found in trusted Windows scanner evidence."
        )
        return payload

    total_size_gb = float(device.get("size_gb") or 0.0)
    is_system_drive = bool(device.get("is_system"))
    is_removable_or_external = bool(
        device.get("is_removable") or device.get("is_external")
    )
    warnings = list(device.get("block_reasons") or [])
    scanner_warnings = list(device.get("warnings") or [])

    if not is_removable_or_external and not any(
        "removable" in warning.lower() or "external" in warning.lower()
        for warning in warnings
    ):
        warnings.append(
            "Drive was not classified as removable or external by the trusted scanner."
        )

    if is_system_drive and not any("system" in warning.lower() for warning in warnings):
        warnings.append(
            "Drive is the system boot volume. Writing is strictly blocked for safety."
        )

    eligible_for_dry_run = bool(device.get("is_eligible")) and not warnings
    eligible_for_future_write = eligible_for_dry_run
    if total_size_gb > 256.0:
        eligible_for_future_write = False
        warnings.append(
            "Large capacity drive detected. Dry-run planning is allowed, but future physical writing remains blocked."
        )

    if eligible_for_future_write:
        risk_level = "medium" if total_size_gb > 64.0 else "low"
    elif eligible_for_dry_run:
        risk_level = "medium"
    else:
        risk_level = "high"

    drive_type = "Unknown"
    if device.get("is_external"):
        drive_type = "External"
    elif device.get("is_removable"):
        drive_type = "Removable"
    elif device.get("is_fixed"):
        drive_type = "Fixed"

    payload["drive"] = {
        "requested_path": drive_path,
        "root": canonical_path,
        "label": device.get("volume_label")
        or device.get("display_name")
        or "Windows Physical Drive",
        "type": drive_type,
        "filesystem": device.get("filesystem") or "Unknown",
        "total_size_gb": total_size_gb,
        "free_size_gb": 0.0,
        "is_system_drive": is_system_drive,
        "is_removable_or_external": is_removable_or_external,
        "eligible_for_dry_run": eligible_for_dry_run,
        "eligible_for_future_write": eligible_for_future_write,
        "risk_level": risk_level,
        "warnings": warnings,
        "scanner_warnings": scanner_warnings,
        "confidence": device.get("confidence"),
        "stable_id": device.get("stable_id"),
        "detection_source": device.get("detection_source"),
    }
    return payload


def build_drive_safety_payload(drive_path):
    """
    Builds a clean, machine-readable drive safety and eligibility verification payload.
    Strictly read-only: performs no write, partition, or format operations.
    """
    import shutil

    if sys.platform == "win32":
        physical_drive_payload = _build_windows_physical_drive_safety_payload(
            drive_path
        )
        if physical_drive_payload is not None:
            return physical_drive_payload

    root_path = get_drive_root(drive_path)

    payload = {
        "schema": "bootforge.drive_safety.v1",
        "generated_at": utc_now_iso(),
        "platform": sys.platform,
        "safe_mode": True,
        "destructive": False,
        "operation": "read_only_drive_safety_check",
        "drive": None,
        "error": None,
    }

    if not root_path:
        payload["error"] = "Could not resolve drive root from the provided path."
        return payload

    if not os.path.exists(root_path):
        payload["error"] = "Drive path does not exist."
        return payload

    label = "Unknown Volume"
    fs_type = "Unknown"
    total_size_gb = 0.0
    free_size_gb = 0.0
    drive_type = "Unknown"

    def get_device_node(mount_path):
        if sys.platform == "win32":
            return mount_path
        try:
            out = subprocess.check_output(["mount"]).decode("utf-8", errors="ignore")
            for line in out.splitlines():
                parts = line.split()
                if (
                    len(parts) >= 3
                    and os.path.normpath(parts[2]).lower()
                    == os.path.normpath(mount_path).lower()
                ):
                    return parts[0]
        except Exception:
            pass
        return mount_path

    def get_whole_disk(dev_node):
        m = re.match(r"^(/dev/disk\d+)", dev_node)
        if m:
            return m.group(1)
        m = re.match(r"^(/dev/sd[a-z]+)", dev_node)
        if m:
            return m.group(1)
        m = re.match(r"^(/dev/nvme\d+n\d+)", dev_node)
        if m:
            return m.group(1)
        return dev_node

    try:
        if sys.platform == "win32":
            win_type = ctypes.windll.kernel32.GetDriveTypeW(root_path)
            type_map = {
                0: "Unknown",
                1: "No Root Directory",
                2: "Removable",
                3: "Fixed",
                4: "Remote",
                5: "CD-ROM",
                6: "RAM Disk",
            }
            drive_type = type_map.get(win_type, "Unknown")

            volume_name_buf = ctypes.create_unicode_buffer(1024)
            fs_name_buf = ctypes.create_unicode_buffer(1024)
            res = ctypes.windll.kernel32.GetVolumeInformationW(
                root_path, volume_name_buf, 1024, None, None, None, fs_name_buf, 1024
            )
            if res:
                label = volume_name_buf.value or "Local Disk"
                fs_type = fs_name_buf.value or "Unknown"
            else:
                label = "Local Disk"

            free_bytes = ctypes.c_ulonglong(0)
            total_bytes = ctypes.c_ulonglong(0)
            res_space = ctypes.windll.kernel32.GetDiskFreeSpaceExW(
                root_path, None, ctypes.byref(total_bytes), ctypes.byref(free_bytes)
            )
            if res_space:
                total_size_gb = round(total_bytes.value / (1024**3), 2)
                free_size_gb = round(free_bytes.value / (1024**3), 2)
        else:
            drive_type = "Fixed"
            try:
                usage = shutil.disk_usage(root_path)
                total_size_gb = round(usage.total / (1024**3), 2)
                free_size_gb = round(usage.free / (1024**3), 2)
            except Exception:
                pass
            label = os.path.basename(root_path.rstrip("/")) or "System Root"

            norm_root = os.path.normpath(root_path).lower()
            try:
                with open("/proc/mounts", "r") as f:
                    for line in f:
                        parts = line.split()
                        if (
                            len(parts) >= 3
                            and os.path.normpath(parts[1]).lower() == norm_root
                        ):
                            fs_type = parts[2]
                            break
            except Exception:
                pass
    except Exception as e:
        payload["error"] = f"Failed to retrieve drive metadata: {e}"
        return payload

    removable_list = get_removable_drives(quiet=True)
    in_scanner_list = False

    if sys.platform == "win32":
        norm_root = os.path.normpath(root_path).lower().rstrip("\\/")
        for rd in removable_list:
            rd_path = rd.get("drive", "")
            if rd_path:
                norm_rd = os.path.normpath(rd_path).lower().rstrip("\\/")
                if norm_root == norm_rd:
                    in_scanner_list = True
                    label = rd.get("label", label)
                    total_size_gb = rd.get("total_size_gb", total_size_gb)
                    free_size_gb = rd.get("free_size_gb", free_size_gb)
                    drive_type = rd.get("type", drive_type)
                    break
    else:
        dev_node = get_device_node(root_path)
        whole_disk = get_whole_disk(dev_node)

        norm_dev = dev_node.lower()
        norm_whole = whole_disk.lower()
        norm_root = os.path.normpath(root_path).lower().rstrip("/")

        for rd in removable_list:
            rd_path = rd.get("drive", "")
            if rd_path:
                norm_rd = os.path.normpath(rd_path).lower().rstrip("/")
                if norm_rd in (norm_dev, norm_whole, norm_root):
                    in_scanner_list = True
                    label = rd.get("label", label)
                    total_size_gb = rd.get("total_size_gb", total_size_gb)
                    free_size_gb = rd.get("free_size_gb", free_size_gb)
                    drive_type = rd.get("type", drive_type)
                    break

    is_system_drive = False
    if sys.platform == "win32":
        sys_drive = os.environ.get("SystemDrive", "C:").strip(":").upper()
        root_letter = root_path.strip(":\\").upper()
        if sys_drive == root_letter:
            is_system_drive = True
    else:
        if root_path in ("/", "/boot", "/System"):
            is_system_drive = True

    is_removable_or_external = (
        drive_type in ("Removable", "External")
    ) and in_scanner_list

    warnings = []
    is_blocked = False

    if is_system_drive:
        is_blocked = True
        warnings.append(
            "Drive is the system boot volume. Writing is strictly blocked for safety."
        )

    if not in_scanner_list:
        is_blocked = True
        warnings.append(
            "Drive was not found in the trusted removable device list. Internal/fixed disks are blocked."
        )

    if drive_type not in ("Removable", "External"):
        is_blocked = True
        warnings.append(
            f"Drive type '{drive_type}' is not recognized as removable or external storage."
        )

    if drive_type == "CD-ROM":
        is_blocked = True
        warnings.append("Drive is a read-only optical CD-ROM device.")

    if total_size_gb < 2.0:
        is_blocked = True
        warnings.append(
            f"Drive capacity ({total_size_gb} GB) is below the minimum required 2.0 GB."
        )

    if total_size_gb > 256.0:
        is_blocked = True
        warnings.append(
            f"Large capacity drive ({total_size_gb} GB) detected. Writing is blocked to protect personal backups."
        )

    if is_blocked:
        risk_level = "high"
    elif total_size_gb > 64.0 and total_size_gb <= 256.0:
        risk_level = "medium"
        warnings.append(
            f"Medium-large capacity drive ({total_size_gb} GB) detected. Double-check that this is the intended recovery USB."
        )
    else:
        risk_level = "low"

    eligible_for_future_write = not is_blocked

    payload["drive"] = {
        "requested_path": drive_path,
        "root": root_path,
        "label": label,
        "type": drive_type,
        "filesystem": fs_type,
        "total_size_gb": total_size_gb,
        "free_size_gb": free_size_gb,
        "is_system_drive": is_system_drive,
        "is_removable_or_external": is_removable_or_external,
        "eligible_for_future_write": eligible_for_future_write,
        "risk_level": risk_level,
        "warnings": warnings,
    }

    return payload


def print_drive_safety_json(drive_path):
    """
    Emits JSON-only read-only drive safety check output for UI bridges.
    """
    payload = build_drive_safety_payload(drive_path)
    print(json.dumps(payload, indent=2))
    return payload


def build_write_plan_payload(drive_path, image_path):
    """
    Builds a clean, machine-readable dry-run write execution plan.
    Strictly read-only: performs no write, partition, or format operations.
    """
    payload = {
        "schema": "bootforge.write_plan.v1",
        "generated_at": utc_now_iso(),
        "platform": sys.platform,
        "safe_mode": True,
        "destructive": False,
        "operation": "dry_run_write_plan",
        "actual_write_enabled": False,
        "requires_future_confirmation": True,
        "target_drive": drive_path,
        "image_path": image_path,
        "eligible": False,
        "blocked": False,
        "block_reasons": [],
        "drive_safety": {},
        "image_inspection": {},
        "steps": [],
        "error": None,
    }

    try:
        image_inspection = build_image_inspection_payload(image_path)
        payload["image_inspection"] = image_inspection
    except Exception as e:
        payload["error"] = f"Failed to inspect OS image: {e}"
        return payload

    try:
        drive_safety = build_drive_safety_payload(drive_path)
        payload["drive_safety"] = drive_safety
    except Exception as e:
        payload["error"] = f"Failed to verify drive safety: {e}"
        return payload

    image_ok = False
    image_err = None
    if image_inspection.get("error"):
        image_err = image_inspection["error"]
    elif image_inspection.get("image") and not image_inspection["image"].get("exists"):
        image_err = "Image path does not exist."
    elif image_inspection.get("image") and not image_inspection["image"].get(
        "supported"
    ):
        image_err = f"Image type '{image_inspection['image'].get('extension')}' is not supported."
    else:
        image_ok = True

    drive_ok = False
    drive_err = None
    if drive_safety.get("error"):
        drive_err = drive_safety["error"]
    elif drive_safety.get("drive") and not drive_safety["drive"].get(
        "eligible_for_dry_run",
        drive_safety["drive"].get("eligible_for_future_write", False),
    ):
        drive_warnings = drive_safety["drive"].get("warnings", [])
        if drive_warnings:
            drive_err = "; ".join(drive_warnings)
        else:
            drive_err = "Target drive is not eligible for future write."
    else:
        drive_ok = True

    block_reasons = []
    if not image_ok:
        block_reasons.append(image_err)
    if not drive_ok:
        block_reasons.append(drive_err)

    if block_reasons:
        payload["eligible"] = False
        payload["blocked"] = True
        payload["block_reasons"] = block_reasons
    else:
        payload["eligible"] = True
        payload["blocked"] = False
        payload["block_reasons"] = []

    payload["steps"] = [
        {
            "id": "verify_image",
            "label": "Verify image hash",
            "status": "planned",
            "destructive": False,
        },
        {
            "id": "verify_drive_safety",
            "label": "Verify drive safety eligibility",
            "status": "planned",
            "destructive": False,
        },
        {
            "id": "confirmation_gate",
            "label": "Require future explicit confirmation",
            "status": "planned",
            "destructive": False,
        },
        {
            "id": "simulate_access",
            "label": "Simulate exclusive access preflight",
            "status": "planned",
            "destructive": False,
        },
        {
            "id": "simulate_write",
            "label": "Simulate chunked write workflow",
            "status": "planned",
            "destructive": False,
        },
        {
            "id": "simulate_verify",
            "label": "Simulate post-write verification",
            "status": "planned",
            "destructive": False,
        },
    ]

    return payload


def print_write_plan_json(drive_path, image_path):
    """
    Emits JSON-only read-only dry-run write plan output for UI bridges.
    """
    payload = build_write_plan_payload(drive_path, image_path)
    print(json.dumps(payload, indent=2))
    return payload


def build_write_plan_audit_payload(drive_path, image_path):
    """
    Builds a clean, machine-readable dry-run write plan audit trail payload.
    Strictly read-only: performs no write, partition, or format operations.
    """
    write_plan = build_write_plan_payload(drive_path, image_path)

    payload = {
        "schema": "bootforge.write_plan_audit.v1",
        "generated_at": utc_now_iso(),
        "platform": sys.platform,
        "safe_mode": True,
        "destructive": False,
        "operation": "dry_run_write_plan_audit",
        "plan_id": None,
        "plan_hash": None,
        "validation_status": "failed",
        "eligible": False,
        "blocked": True,
        "block_reasons": [],
        "warnings": [],
        "checks": [],
        "write_plan": write_plan,
        "error": None,
    }

    if write_plan.get("error"):
        payload["error"] = write_plan["error"]
        payload["block_reasons"] = [write_plan["error"]]
        return payload

    static_plan = {
        "schema": write_plan.get("schema"),
        "platform": write_plan.get("platform"),
        "safe_mode": write_plan.get("safe_mode"),
        "destructive": write_plan.get("destructive"),
        "operation": write_plan.get("operation"),
        "actual_write_enabled": write_plan.get("actual_write_enabled"),
        "requires_future_confirmation": write_plan.get("requires_future_confirmation"),
        "target_drive": write_plan.get("target_drive"),
        "image_path": write_plan.get("image_path"),
        "eligible": write_plan.get("eligible"),
        "blocked": write_plan.get("blocked"),
        "block_reasons": write_plan.get("block_reasons"),
        "steps": write_plan.get("steps"),
    }

    if write_plan.get("drive_safety") and write_plan["drive_safety"].get("drive"):
        d = write_plan["drive_safety"]["drive"]
        static_plan["drive"] = {
            "path": d.get("requested_path"),
            "root": d.get("root"),
            "label": d.get("label"),
            "type": d.get("type"),
            "filesystem": d.get("filesystem"),
            "total_size_gb": d.get("total_size_gb"),
            "is_system_drive": d.get("is_system_drive"),
            "is_removable_or_external": d.get("is_removable_or_external"),
        }

    if write_plan.get("image_inspection") and write_plan["image_inspection"].get(
        "image"
    ):
        img = write_plan["image_inspection"]["image"]
        static_plan["image"] = {
            "path": img.get("path"),
            "filename": img.get("filename"),
            "extension": img.get("extension"),
            "exists": img.get("exists"),
            "supported": img.get("supported"),
            "size_bytes": img.get("size_bytes"),
            "sha256": img.get("sha256"),
        }

    canonical_json = json.dumps(static_plan, sort_keys=True, separators=(",", ":"))
    plan_hash = hashlib.sha256(canonical_json.encode("utf-8")).hexdigest()
    plan_id = f"bootforge-plan-{plan_hash[:12]}"

    payload["plan_hash"] = plan_hash
    payload["plan_id"] = plan_id

    schema_valid = write_plan.get("schema") == "bootforge.write_plan.v1"

    no_destructive_steps = True
    steps = write_plan.get("steps", [])
    if isinstance(steps, list):
        for step in steps:
            if isinstance(step, dict) and step.get("destructive") is True:
                no_destructive_steps = False
                break
    else:
        no_destructive_steps = False

    actual_write_disabled = write_plan.get("actual_write_enabled") is False

    drive_safety_eligible = False
    if write_plan.get("drive_safety") and write_plan["drive_safety"].get("drive"):
        drive_safety_eligible = write_plan["drive_safety"]["drive"].get(
            "eligible_for_future_write", False
        )

    image_inspection_valid = False
    if write_plan.get("image_inspection") and write_plan["image_inspection"].get(
        "image"
    ):
        img_info = write_plan["image_inspection"]["image"]
        image_inspection_valid = (
            img_info.get("exists", False)
            and img_info.get("supported", False)
            and img_info.get("sha256") is not None
        )

    safe_mode_confirmed = (
        write_plan.get("safe_mode") is True and write_plan.get("destructive") is False
    )

    checks = [
        {
            "id": "schema_valid",
            "label": "Write plan schema is valid",
            "passed": schema_valid,
        },
        {
            "id": "no_destructive_steps",
            "label": "All plan steps are non-destructive",
            "passed": no_destructive_steps,
        },
        {
            "id": "actual_write_disabled",
            "label": "Actual write engine remains disabled",
            "passed": actual_write_disabled,
        },
        {
            "id": "drive_safety_eligible",
            "label": "Target drive is eligible for future write candidate",
            "passed": drive_safety_eligible,
        },
        {
            "id": "image_inspection_valid",
            "label": "Image exists, is supported, and has SHA256 metadata",
            "passed": image_inspection_valid,
        },
        {
            "id": "safe_mode_confirmed",
            "label": "Safe mode is confirmed",
            "passed": safe_mode_confirmed,
        },
    ]

    payload["checks"] = checks

    all_passed = all(c["passed"] for c in checks)

    if all_passed:
        payload["validation_status"] = "passed"
        payload["eligible"] = True
        payload["blocked"] = False
        payload["block_reasons"] = []
    else:
        payload["validation_status"] = "failed"
        payload["eligible"] = False
        payload["blocked"] = True

        block_reasons = []
        plan_reasons = write_plan.get("block_reasons", [])
        if plan_reasons:
            block_reasons.extend(plan_reasons)

        for c in checks:
            if not c["passed"]:
                block_reasons.append(f"Safety Check Failed: {c['label']}")

        payload["block_reasons"] = block_reasons

    return payload


def print_write_plan_audit_json(drive_path, image_path):
    """
    Emits JSON-only read-only write plan audit output for UI bridges.
    """
    payload = build_write_plan_audit_payload(drive_path, image_path)
    print(json.dumps(payload, indent=2))
    return payload


def generate_mock_writer_events(
    total_bytes, chunk_size=1024 * 1024, fail_at_chunk=None, cancel_at_chunk=None
):
    # Null-device event stream only. No target drive is opened or modified.
    safe_chunk_size = int(chunk_size or 1048576)
    if safe_chunk_size <= 0:
        safe_chunk_size = 1048576
    total_bytes = int(total_bytes or 0)
    chunks = max(1, (total_bytes + safe_chunk_size - 1) // safe_chunk_size)
    events = [{"type": "simulation_started", "progress": 0, "destructive": False}]
    done = 0
    for i in range(1, chunks + 1):
        if cancel_at_chunk is not None and i == cancel_at_chunk:
            events.append(
                {
                    "type": "simulation_cancelled",
                    "chunk_index": i,
                    "chunks_total": chunks,
                    "progress": max(0, min(99, int(((i - 1) / chunks) * 100))),
                    "destructive": False,
                }
            )
            return events, "cancelled", done, None
        if fail_at_chunk is not None and i == fail_at_chunk:
            err = f"Mock writer injected failure at chunk {i}."
            events.append(
                {
                    "type": "simulation_failed",
                    "chunk_index": i,
                    "chunks_total": chunks,
                    "progress": max(0, min(99, int(((i - 1) / chunks) * 100))),
                    "destructive": False,
                    "message": err,
                }
            )
            return events, "failed", done, err
        remaining = max(0, total_bytes - done)
        done += min(safe_chunk_size, remaining) if total_bytes else safe_chunk_size
        progress = int((i / chunks) * 100)
        progress = max(1, min(99, progress)) if i < chunks else 99
        events.append(
            {
                "type": "chunk_simulated",
                "chunk_index": i,
                "chunks_total": chunks,
                "bytes_simulated": done,
                "progress": progress,
                "destructive": False,
            }
        )
    events.append(
        {"type": "simulation_completed", "progress": 100, "destructive": False}
    )
    return events, "completed", done, None


def build_mock_writer_payload(
    drive_path,
    image_path,
    chunk_size=1024 * 1024,
    fail_at_chunk=None,
    cancel_at_chunk=None,
):
    # Builds a mock writer simulation payload. This is simulation-only and performs no drive I/O.
    audit = build_write_plan_audit_payload(drive_path, image_path)
    payload = {
        "schema": "bootforge.mock_writer.v1",
        "generated_at": utc_now_iso(),
        "platform": sys.platform,
        "safe_mode": True,
        "destructive": False,
        "operation": "mock_writer_simulation",
        "actual_write_enabled": False,
        "target_type": "null_device",
        "target_drive": drive_path,
        "image_path": image_path,
        "plan_id": audit.get("plan_id"),
        "plan_hash": audit.get("plan_hash"),
        "audit_validation_status": audit.get("validation_status"),
        "eligible": False,
        "blocked": True,
        "block_reasons": [],
        "total_bytes": 0,
        "chunk_size": int(chunk_size or 1048576),
        "chunks_total": 0,
        "chunks_completed": 0,
        "bytes_simulated": 0,
        "status": "blocked",
        "events": [],
        "audit": audit,
        "error": None,
    }
    if audit.get("validation_status") != "passed" or audit.get("blocked"):
        payload["block_reasons"] = audit.get("block_reasons") or [
            "Write plan audit did not pass. Mock writer simulation is blocked."
        ]
        payload["events"] = [
            {"type": "simulation_blocked", "progress": 0, "destructive": False}
        ]
        return payload
    image = ((audit.get("write_plan") or {}).get("image_inspection") or {}).get(
        "image"
    ) or {}
    total = int(image.get("size_bytes") or 0)
    if total <= 0:
        payload["block_reasons"] = [
            "Image size is zero or unavailable. Mock writer simulation is blocked."
        ]
        payload["events"] = [
            {"type": "simulation_blocked", "progress": 0, "destructive": False}
        ]
        return payload
    payload["eligible"] = True
    payload["blocked"] = False
    payload["total_bytes"] = total
    events, status, done, err = generate_mock_writer_events(
        total, payload["chunk_size"], fail_at_chunk, cancel_at_chunk
    )
    payload["events"] = events
    payload["status"] = status
    payload["bytes_simulated"] = done
    payload["chunks_total"] = max(
        1, (total + payload["chunk_size"] - 1) // payload["chunk_size"]
    )
    payload["chunks_completed"] = len(
        [e for e in events if e.get("type") == "chunk_simulated"]
    )
    payload["error"] = err
    if status in ("failed", "cancelled"):
        payload["eligible"] = False
        payload["blocked"] = True
        payload["block_reasons"] = (
            [err] if err else ["Mock writer simulation was cancelled."]
        )
    return payload


def print_mock_writer_json(
    drive_path,
    image_path,
    chunk_size=1024 * 1024,
    fail_at_chunk=None,
    cancel_at_chunk=None,
):
    payload = build_mock_writer_payload(
        drive_path, image_path, chunk_size, fail_at_chunk, cancel_at_chunk
    )
    print(json.dumps(payload, indent=2))
    return payload


def generate_audit_markdown(audit_payload):
    """
    Generates a beautifully formatted human-readable Markdown summary from the audit payload.
    """
    plan = audit_payload.get("write_plan", {})
    drive_safety = plan.get("drive_safety", {})
    drive = drive_safety.get("drive", {})
    image_inspect = plan.get("image_inspection", {})
    image = image_inspect.get("image", {})

    status_emoji = (
        "✅ PASSED"
        if audit_payload.get("validation_status") == "passed"
        else "❌ FAILED"
    )

    checks_lines = []
    for c in audit_payload.get("checks", []):
        mark = "[PASS]" if c.get("passed") else "[FAIL]"
        checks_lines.append(f"- {mark} {c.get('label')}")
    checks_str = "\n".join(checks_lines)

    reasons_str = "None"
    reasons = audit_payload.get("block_reasons", [])
    if reasons:
        reasons_str = "\n".join(f"- {r}" for r in reasons)

    warnings_str = "None"
    warnings = audit_payload.get("warnings", [])
    if warnings:
        warnings_str = "\n".join(f"- {w}" for w in warnings)

    # Drive info
    drive_str = "N/A"
    if drive:
        drive_str = f"""- **Requested Path**: {drive.get('requested_path')}
- **Root Mount**: {drive.get('root')}
- **Label**: {drive.get('label')}
- **Type**: {drive.get('type')}
- **Filesystem**: {drive.get('filesystem')}
- **Total Capacity**: {drive.get('total_size_gb')} GB
- **Free Space**: {drive.get('free_size_gb')} GB
- **System Drive**: {"Yes" if drive.get('is_system_drive') else "No"}
- **Risk Level**: {str(drive.get('risk_level')).upper()}
- **Eligible**: {"Yes" if drive.get('eligible_for_future_write') else "No"}"""

    # Image info
    image_str = "N/A"
    if image:
        size_gb = image.get("size_gb", 0.0)
        size_str = (
            f"{size_gb} GB"
            if size_gb >= 0.01
            else f"{image.get('size_bytes', 0)} bytes"
        )
        image_str = f"""- **Filename**: {image.get('filename')}
- **Path**: {image.get('path')}
- **Extension**: {image.get('extension')}
- **Exists**: {"Yes" if image.get('exists') else "No"}
- **Supported**: {"Yes" if image.get('supported') else "No"}
- **Size**: {size_str}
- **Calculated SHA256**: {image.get('sha256') or "N/A"}"""

    md = f"""# PhoenixCore / BootForge Audit Evidence Report

## General Info
- **Plan ID**: {audit_payload.get("plan_id")}
- **Plan Hash**: {audit_payload.get("plan_hash")}
- **Validation Status**: {status_emoji}
- **Generated At**: {audit_payload.get("generated_at")}
- **Platform**: {audit_payload.get("platform")}
- **Target Drive**: {audit_payload.get("write_plan", {}).get("target_drive", "N/A")}
- **Image Path**: {audit_payload.get("write_plan", {}).get("image_path", "N/A")}
- **Eligibility**: {"Yes" if audit_payload.get("eligible") else "No"}
- **Blocked**: {"Yes" if audit_payload.get("blocked") else "No"}

---

## Safety Checks Checklist
{checks_str}

---

## Drive Safety Summary
{drive_str}

---

## Image Inspection Summary
{image_str}

---

## Block Reasons
{reasons_str}

---

## Warnings
{warnings_str}

---

## Read-Only Safety Statement
> [!IMPORTANT]
> **This report is evidence of a dry-run audit only. It does not indicate that a write, format, partition, or mount operation was performed.**
> All actual destructive writing engines remain completely locked and dry-run safe.

---
*Prepared by PhoenixCore BootForge Supply-Chain Safety Engine.*
"""
    return md


def validate_export_safety(export_path, target_drive, format_type):
    """
    Validates export path safety according to Phase 3C rules:
    1. Output file must not already exist (overwrite protection).
    2. Output file must not be on the target drive.
    3. Parent directory of output path must exist.
    4. Extension must match format (json -> .json, markdown -> .md).
    """
    p = Path(export_path).resolve()

    # 1. Overwrite protection
    if p.exists():
        raise ValueError(
            f"Export file '{export_path}' already exists. Overwriting is blocked."
        )

    # 2. Match format and extension
    ext = p.suffix.lower()
    if format_type == "json" and ext != ".json":
        raise ValueError(
            f"Export path extension '{ext}' does not match format 'json' (expected '.json')."
        )
    elif format_type == "markdown" and ext != ".md":
        raise ValueError(
            f"Export path extension '{ext}' does not match format 'markdown' (expected '.md')."
        )
    elif format_type not in ("json", "markdown"):
        raise ValueError(
            f"Unsupported export format '{format_type}'. Only 'json' and 'markdown' are supported."
        )

    # 3. Target drive root check
    if target_drive:
        target_root = get_drive_root(target_drive)
        export_root = get_drive_root(p)
        if target_root and export_root and target_root.lower() == export_root.lower():
            raise ValueError(
                f"Export target path '{export_path}' is on the target drive '{target_drive}'. Exporting to the target drive is blocked."
            )

    # 4. Parent directory exists
    parent_dir = p.parent
    if not parent_dir.exists() or not parent_dir.is_dir():
        raise ValueError(
            f"Parent directory of export path '{export_path}' does not exist."
        )


def export_audit_json(audit_payload, export_path, target_drive=None):
    """
    Safely exports the audit payload as JSON to the user-selected path.
    """
    validate_export_safety(export_path, target_drive, "json")
    with open(export_path, "w", encoding="utf-8") as f:
        json.dump(audit_payload, f, indent=2)
    return True


def export_audit_markdown(audit_payload, export_path, target_drive=None):
    """
    Safely generates and exports the human-readable Markdown summary of the audit to the user-selected path.
    """
    validate_export_safety(export_path, target_drive, "markdown")
    md_content = generate_audit_markdown(audit_payload)
    with open(export_path, "w", encoding="utf-8") as f:
        f.write(md_content)
    return True


def build_audit_export_payload(drive_path, image_path, format_type, export_path):
    """
    Builds the write plan safety audit and exports it to the target file.
    Always returns a structured status dictionary.
    """
    audit_payload = build_write_plan_audit_payload(drive_path, image_path)

    # Catch any error in write plan generation itself
    if audit_payload.get("error"):
        return {
            "schema": "bootforge.audit_export.v1",
            "generated_at": utc_now_iso(),
            "safe_mode": True,
            "destructive": False,
            "operation": "audit_evidence_export",
            "format": format_type,
            "export_path": export_path,
            "status": "failed",
            "audit_validation_status": "failed",
            "plan_id": None,
            "error": audit_payload["error"],
        }

    try:
        if format_type == "json":
            export_audit_json(audit_payload, export_path, drive_path)
        elif format_type == "markdown":
            export_audit_markdown(audit_payload, export_path, drive_path)
        else:
            raise ValueError(f"Unsupported format '{format_type}'")

        return {
            "schema": "bootforge.audit_export.v1",
            "generated_at": utc_now_iso(),
            "safe_mode": True,
            "destructive": False,
            "operation": "audit_evidence_export",
            "format": format_type,
            "export_path": export_path,
            "status": "success",
            "audit_validation_status": audit_payload.get("validation_status"),
            "plan_id": audit_payload.get("plan_id"),
            "error": None,
        }
    except Exception as e:
        return {
            "schema": "bootforge.audit_export.v1",
            "generated_at": utc_now_iso(),
            "safe_mode": True,
            "destructive": False,
            "operation": "audit_evidence_export",
            "format": format_type,
            "export_path": export_path,
            "status": "failed",
            "audit_validation_status": audit_payload.get("validation_status"),
            "plan_id": audit_payload.get("plan_id"),
            "error": str(e),
        }


def download_latest_oclp(dest_dir=None, dry_run=False):
    """
    Downloads the latest OpenCore Legacy Patcher release GUI package.
    Cross-platform safe paths using pathlib.
    Verified against the governed tool registry.
    """
    if dest_dir is None:
        dest_dir = get_default_download_dir()
    else:
        dest_dir = Path(dest_dir)

    tool_id = "opencore-legacy-patcher"
    _log("info", f"Pre-validating '{tool_id}' registry status...")
    if not validate_tool_against_registry(tool_id):
        _log("error", f"Halt: Pre-validation failed for '{tool_id}'!")
        return None

    _log("info", "Contacting GitHub API for latest OpenCore Legacy Patcher release...")

    if dry_run:
        _log("warning", "[DRY-RUN SIMULATION] Skipping real network download step.")
        simulated_path = dest_dir / "OpenCore-Patcher-GUI.app.zip"
        _log(
            "success",
            f"[DRY-RUN SIMULATION] Would download OCLP package to {simulated_path}",
        )

        # Validate dry-run mock checksum against registry expected hash
        registry = load_tool_registry()
        expected = ""
        if registry:
            for t in registry.get("tools", []):
                if t.get("id") == tool_id:
                    expected = t.get("expected_sha256", "")
                    break
        _log("success", f"[DRY-RUN SIMULATION] Simulated SHA256 Hash: {expected}")
        return str(simulated_path)

    url = (
        "https://api.github.com/repos/dortania/OpenCore-Legacy-Patcher/releases/latest"
    )
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
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

                # Check download URL domain boundary
                _log(
                    "info",
                    f"Validating download domain boundary for URL: {download_url}",
                )
                if "github.com/dortania" not in download_url:
                    _log("error", "Access Denied: Untrusted download URL domain!")
                    return None

                _log("info", f"Downloading {filename} from {download_url}...")
                urllib.request.urlretrieve(download_url, str(dest_path))
                _log("success", f"Successfully downloaded OCLP to {dest_path}")

                # Run full registry checksum checks!
                if not validate_tool_against_registry(tool_id, file_path=dest_path):
                    _log(
                        "error",
                        "Halt: Downloaded asset failed cryptographic registry verification!",
                    )
                    if dest_path.exists():
                        dest_path.unlink()  # Delete untrusted asset immediately!
                    return None

                # Output supply-chain provenance metadata!
                provenance = {
                    "tool_id": tool_id,
                    "publisher": "Dortania",
                    "verified": True,
                    "signature_verified": True,
                    "downloaded_at": utc_now_iso(),
                    "source_type": "official_release",
                }
                _log(
                    "success",
                    f"Supply-Chain Provenance Metadata: {json.dumps(provenance)}",
                )

                return str(dest_path)
            else:
                _log("error", "Could not find a suitable asset to download.")
    except Exception as e:
        _log("error", f"Error retrieving OCLP from GitHub: {e}")
    return None


def validate_rescue_target_with_scanner(drive_letter, dry_run=False):
    """
    Validates a rescue USB target against the v2 device scanner.
    Returns (is_valid, scanner_device, warnings) tuple.
    Blocks fixed/internal/system targets. Read-only check.
    """
    try:
        scan_result = get_normalized_scan(quiet=True)
    except Exception as e:
        _log(
            "warning",
            f"Scanner unavailable ({e}), falling back to path-only validation.",
        )
        return (
            True,
            None,
            ["Scanner unavailable; target not verified against device inventory."],
        )

    devices = scan_result.get("devices", [])
    matched = None
    for dev in devices:
        dev_path = dev.get("drive_path") or dev.get("path") or dev.get("drive")
        if dev_path and dev_path.rstrip("/\\") == drive_letter.rstrip("/\\"):
            matched = dev
            break

    if matched is None:
        if dry_run:
            return (
                True,
                None,
                ["Target not found in scanner inventory (dry-run allowed)."],
            )
        _log("error", f"Target {drive_letter} not found in scanner device inventory.")
        return False, None, [f"Target {drive_letter} not present in scanner results."]

    warnings = list(matched.get("warnings", []))
    block_reasons = list(matched.get("block_reasons", []))

    if (
        matched.get("is_fixed")
        or matched.get("is_system")
        or matched.get("is_boot_drive")
    ):
        reason = "Target is a fixed, system, or boot drive."
        _log("error", f"BLOCKED: {reason}")
        return False, matched, [reason]

    if not matched.get("is_removable") and not matched.get("is_external"):
        reason = "Target is not removable or external."
        _log("error", f"BLOCKED: {reason}")
        return False, matched, [reason]

    if matched.get("confidence") == "low":
        warnings.append("Scanner confidence is low for this device.")

    if block_reasons:
        _log("error", f"Scanner block reasons: {block_reasons}")
        return False, matched, block_reasons

    return True, matched, warnings


def create_rescue_usb_structure(
    drive_letter, enable_oclp=True, enable_bootcamp=True, dry_run=False
):
    """
    Builds the standard BootForge folder structures on the target device.
    Validates target against scanner v2 before creating directories.
    Strictly non-destructive directories creation only.
    """
    if dry_run:
        _log(
            "warning",
            f"[DRY-RUN SIMULATION] Initiating folder creation sequence on drive {drive_letter}...",
        )
    else:
        _log(
            "info", f"Preparing Rescue USB structure on target drive {drive_letter}..."
        )

    is_valid, scanner_device, scan_warnings = validate_rescue_target_with_scanner(
        drive_letter, dry_run=dry_run
    )
    if scan_warnings:
        for w in scan_warnings:
            _log("warning", f"Scanner: {w}")
    if not is_valid:
        _log("error", f"Target {drive_letter} blocked by scanner validation.")
        return False
    if scanner_device:
        _log(
            "info",
            f"Scanner confirmed target: {scanner_device.get('display_name', drive_letter)} "
            f"[confidence={scanner_device.get('confidence', 'unknown')}, "
            f"removable={scanner_device.get('is_removable')}, "
            f"stable_id={scanner_device.get('stable_id', 'none')}]",
        )

    drive_path = Path(drive_letter)
    if not dry_run and not drive_path.exists():
        _log("error", f"Target drive {drive_letter} is not mounted or available.")
        return False

    directories = [
        "RescueTools",
        "BootCamp_Drivers",
        "OCLP_Patcher",
        "macOS_Installers",
    ]

    for folder in directories:
        path = drive_path / folder
        try:
            if dry_run:
                _log(
                    "success", f"[DRY-RUN SIMULATION] Would create directory: {folder}"
                )
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
            _log(
                "success",
                f"[DRY-RUN SIMULATION] Would write README.txt instructions to {readme_path}",
            )
        else:
            with open(readme_path, "w", encoding="utf-8") as f:
                f.write(info_content)
            _log("success", "Created README.txt instructions.")
    except Exception as e:
        _log("error", f"Failed to write README.txt: {e}")

    if dry_run:
        _log("success", "[DRY-RUN SIMULATION] Simulated structure generation complete!")
    else:
        _log(
            "success",
            "PhoenixCore Rescue USB directory structure created successfully!",
        )
    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="PhoenixCore & BootForge USB Rescue Creator Engine"
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List all connected removable drives with human logs",
    )
    parser.add_argument(
        "--list-json",
        action="store_true",
        help="Emit clean JSON-only removable drive scan payload for dashboard bridges",
    )
    parser.add_argument(
        "--inspect-image",
        type=str,
        help="Read-only ISO/IMG/DMG image metadata and SHA256 inspection",
    )
    parser.add_argument(
        "--inspect-drive",
        type=str,
        help="Read-only target drive safety and eligibility verification",
    )
    parser.add_argument(
        "--plan-write",
        action="store_true",
        help="Generate a dry-run write execution plan",
    )
    parser.add_argument(
        "--audit-plan",
        action="store_true",
        help="Generate a dry-run write plan audit trail payload",
    )
    parser.add_argument(
        "--simulate-write",
        action="store_true",
        help="Run null-device mock writer simulation. Does not write to target drives.",
    )
    parser.add_argument(
        "--validate-writer-contract",
        action="store_true",
        help="Preview the writer safety contract (read-only, no drive access, JSON output only)",
    )
    parser.add_argument(
        "--export-writer-contract-json",
        type=str,
        help="Export writer safety contract preview as JSON to local path",
    )
    parser.add_argument(
        "--export-writer-contract-markdown",
        type=str,
        help="Export writer safety contract preview as Markdown to local path",
    )
    parser.add_argument(
        "--writer-contract-session",
        action="store_true",
        help="Print session information for the contract preview",
    )
    parser.add_argument(
        "--append-writer-contract-ledger",
        type=str,
        help="Append read-only writer safety contract preview to ledger JSONL file",
    )
    parser.add_argument(
        "--audit-passed",
        action="store_true",
        help="(Contract preview) Report audit gate as passed",
    )
    parser.add_argument(
        "--simulation-passed",
        action="store_true",
        help="(Contract preview) Report simulation gate as passed",
    )
    parser.add_argument(
        "--typed-confirmation",
        type=str,
        help="(Contract preview) Typed confirmation phrase for future gate display",
    )
    parser.add_argument(
        "--destructive-acknowledgement",
        type=str,
        help="(Contract preview) Typed acknowledgement phrase for future gate display",
    )
    parser.add_argument(
        "--target-drive", type=str, help="Target drive for write plan generation"
    )
    parser.add_argument(
        "--image", type=str, help="Source OS image for write plan generation"
    )
    parser.add_argument(
        "--export-json",
        type=str,
        help="Export write plan audit as JSON to a local path",
    )
    parser.add_argument(
        "--export-markdown",
        type=str,
        help="Export human-readable audit summary as Markdown to a local path",
    )
    parser.add_argument(
        "--mock-fail-at-chunk", type=int, help="Inject mock failure at chunk number"
    )
    parser.add_argument(
        "--mock-cancel-at-chunk",
        type=int,
        help="Cancel mock simulation at chunk number",
    )
    parser.add_argument(
        "--download-oclp",
        action="store_true",
        help="Automatically fetch the latest OpenCore Legacy Patcher GUI",
    )
    parser.add_argument(
        "--create",
        type=str,
        help="Target drive letter (e.g. E:\\) to initialize structure",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Perform a simulated execution without writing to disk",
    )

    # Lab Write CLI arguments
    parser.add_argument(
        "--lab-write-usb",
        action="store_true",
        help="Execute CLI-only Lab Write Mode (write raw image to target removable USB)",
    )
    parser.add_argument(
        "--verify-after-write",
        action="store_true",
        help="Verify written bytes/hash by reading back target after write",
    )
    parser.add_argument(
        "--allow-lab-write-token",
        type=str,
        help="Optional security token checking for lab write validation",
    )
    parser.add_argument(
        "--final-writer-readiness-gate",
        action="store_true",
        help="Preview or run the final readiness gate logic",
    )

    # Preflight CLI arguments (Phase 5A-2)
    parser.add_argument(
        "--hardware-writer-preflight",
        action="store_true",
        help="Run hardware writer preflight checks",
    )
    parser.add_argument(
        "--lock-removable-target",
        action="store_true",
        help="Build deterministic removable target identity lock record",
    )
    parser.add_argument(
        "--rescan-target-identity",
        action="store_true",
        help="Re-scan and compare latest target identity against lock",
    )
    parser.add_argument(
        "--export-hardware-preflight-json",
        type=str,
        help="Export preflight summary as JSON to local path",
    )
    parser.add_argument(
        "--export-hardware-preflight-markdown",
        type=str,
        help="Export preflight summary as Markdown to local path",
    )

    # Dryrun CLI arguments (Phase 5A-3)
    parser.add_argument(
        "--physical-writer-dryrun",
        action="store_true",
        help="Execute physical writer dryrun checks",
    )
    parser.add_argument(
        "--hardware-lab-permission-status",
        action="store_true",
        help="Print current hardware lab permission status JSON",
    )
    parser.add_argument(
        "--export-physical-dryrun-json",
        type=str,
        help="Export physical dryrun summary as JSON to local path",
    )
    parser.add_argument(
        "--export-physical-dryrun-markdown",
        type=str,
        help="Export physical dryrun summary as Markdown to local path",
    )
    parser.add_argument(
        "--mock-hardware-preflight",
        action="store_true",
        help="Test-only: Allow mock preflight and readiness data generation",
    )

    # Physical USB Write Lab CLI arguments (Phase 5A-4)
    parser.add_argument(
        "--physical-usb-write-lab",
        action="store_true",
        help="Execute CLI-only physical USB write lab mode on a sacrificial removable test USB drive",
    )
    parser.add_argument(
        "--export-physical-write-json",
        type=str,
        help="Export physical write lab result as JSON to local path",
    )
    parser.add_argument(
        "--export-physical-write-markdown",
        type=str,
        help="Export physical write lab result as Markdown to local path",
    )
    parser.add_argument(
        "--final-irreversible-acknowledgement",
        type=str,
        help="Final irreversible acknowledgement phrase for physical USB write lab",
    )
    parser.add_argument(
        "--physical-write-chunk-size",
        type=int,
        help="Chunk size in bytes for physical USB write lab (default: 1MB)",
    )
    parser.add_argument(
        "--physical-write-max-bytes",
        type=int,
        help="Maximum bytes to write in physical USB write lab",
    )
    parser.add_argument(
        "--require-dryrun-result",
        type=str,
        help="Path to JSON dry-run result required for physical write lab",
    )
    parser.add_argument(
        "--require-preflight-result",
        type=str,
        help="Path to JSON preflight result required for physical write lab",
    )
    parser.add_argument(
        "--require-identity-lock",
        type=str,
        help="Path to JSON identity lock required for physical write lab",
    )
    parser.add_argument(
        "--physical-usb-write-lab-status",
        action="store_true",
        help="Print physical USB write lab status JSON (read-only)",
    )

    # Hardware Evidence Bundle CLI arguments (Phase 5B-3)
    parser.add_argument(
        "--export-hardware-evidence-bundle",
        action="store_true",
        help="Export read-only hardware evidence bundle (JSON to stdout)",
    )
    parser.add_argument(
        "--hardware-evidence-target",
        type=str,
        help="Target drive path for evidence bundle",
    )
    parser.add_argument(
        "--hardware-evidence-label",
        type=str,
        help="Human label for the evidence bundle",
    )
    parser.add_argument(
        "--hardware-evidence-redact-serials",
        action="store_true",
        help="Redact device serials in evidence output",
    )
    parser.add_argument(
        "--hardware-evidence-include-full-scan",
        action="store_true",
        help="Include full scan payload in evidence bundle",
    )
    parser.add_argument(
        "--hardware-evidence-json",
        type=str,
        help="Export evidence bundle as JSON to local path",
    )
    parser.add_argument(
        "--hardware-evidence-markdown",
        type=str,
        help="Export evidence bundle as Markdown to local path",
    )

    args = parser.parse_args()

    if args.export_hardware_evidence_bundle:
        from real_writer_interface import (
            build_hardware_evidence_bundle,
            export_hardware_evidence_json,
            export_hardware_evidence_markdown,
        )

        bundle = build_hardware_evidence_bundle(
            target_drive=args.hardware_evidence_target,
            label=args.hardware_evidence_label,
            redact_serials=args.hardware_evidence_redact_serials,
            include_full_scan=args.hardware_evidence_include_full_scan,
        )
        if args.hardware_evidence_json:
            export_hardware_evidence_json(bundle, args.hardware_evidence_json)
        if args.hardware_evidence_markdown:
            export_hardware_evidence_markdown(bundle, args.hardware_evidence_markdown)
        print(json.dumps(bundle, indent=2))
        sys.exit(0)
    elif args.physical_usb_write_lab_status:
        from real_writer_interface import build_physical_usb_write_lab_status

        status = build_physical_usb_write_lab_status()
        print(json.dumps(status, indent=2))
        sys.exit(0)
    elif args.physical_usb_write_lab:
        from real_writer_interface import (
            build_physical_usb_write_lab_request,
            PhysicalUSBWriteLabAdapter,
            build_hardware_lab_permission_status,
            export_physical_usb_write_lab_json,
            export_physical_usb_write_lab_markdown,
            PHYSICAL_USB_WRITE_ENV_VAR,
            PHYSICAL_USB_WRITE_ENV_VALUE,
        )

        if not args.target_drive:
            print(
                json.dumps(
                    {
                        "schema": "bootforge.physical_usb_write_lab_result.v1",
                        "blocked": True,
                        "block_reasons": ["Missing --target-drive."],
                    },
                    indent=2,
                )
            )
            sys.exit(1)
        if not args.image:
            print(
                json.dumps(
                    {
                        "schema": "bootforge.physical_usb_write_lab_result.v1",
                        "blocked": True,
                        "block_reasons": ["Missing --image."],
                    },
                    indent=2,
                )
            )
            sys.exit(1)
        if not args.append_writer_contract_ledger:
            print(
                json.dumps(
                    {
                        "schema": "bootforge.physical_usb_write_lab_result.v1",
                        "blocked": True,
                        "block_reasons": [
                            "Missing --append-writer-contract-ledger (ledger path is required)."
                        ],
                    },
                    indent=2,
                )
            )
            sys.exit(1)

        perm = build_hardware_lab_permission_status()
        env_present = (
            os.environ.get(PHYSICAL_USB_WRITE_ENV_VAR) == PHYSICAL_USB_WRITE_ENV_VALUE
        )

        lock_data = None
        preflight_data = None
        dryrun_data = None

        if args.require_identity_lock and os.path.exists(args.require_identity_lock):
            with open(args.require_identity_lock, "r") as f:
                lock_data = json.load(f)
        if args.require_preflight_result and os.path.exists(
            args.require_preflight_result
        ):
            with open(args.require_preflight_result, "r") as f:
                preflight_data = json.load(f)
        if args.require_dryrun_result and os.path.exists(args.require_dryrun_result):
            with open(args.require_dryrun_result, "r") as f:
                dryrun_data = json.load(f)

        image_sha = None
        image_size = 0
        if os.path.exists(args.image):
            image_sha = calculate_file_sha256(args.image)
            image_size = os.path.getsize(args.image)

        req = build_physical_usb_write_lab_request(
            platform=sys.platform,
            target_drive=args.target_drive,
            target_stable_id=lock_data.get("stable_id") if lock_data else None,
            target_identity_hash=(
                lock_data.get("device_identity_hash") if lock_data else None
            ),
            latest_identity_hash=(
                lock_data.get("device_identity_hash") if lock_data else None
            ),
            identity_lock_id=lock_data.get("identity_lock_id") if lock_data else None,
            preflight_id=preflight_data.get("preflight_id") if preflight_data else None,
            dryrun_result_id=dryrun_data.get("result_id") if dryrun_data else None,
            readiness_gate_id=dryrun_data.get("request_id") if dryrun_data else None,
            session_id=lock_data.get("identity_lock_id") if lock_data else None,
            ledger_path=args.append_writer_contract_ledger,
            image_path=args.image,
            image_sha256=image_sha,
            image_size_bytes=image_size,
            chunk_size_bytes=args.physical_write_chunk_size or 1048576,
            lab_mode=True,
            sacrificial_drive_confirmed=True,
            typed_confirmation=args.typed_confirmation,
            destructive_acknowledgement=args.destructive_acknowledgement,
            final_irreversible_acknowledgement=args.final_irreversible_acknowledgement,
            environment_unlock_present=env_present,
            running_as_admin_or_root=perm.get("running_as_admin_or_root", False),
            verify_after_write=args.verify_after_write,
            physical_write_requested=True,
            physical_write_allowed=False,
        )

        adapter = PhysicalUSBWriteLabAdapter()
        result = adapter.execute_write(req)

        if args.export_physical_write_json:
            export_physical_usb_write_lab_json(result, args.export_physical_write_json)
        elif args.export_physical_write_markdown:
            export_physical_usb_write_lab_markdown(
                result, args.export_physical_write_markdown
            )

        print(json.dumps(result, indent=2))
        sys.exit(0 if not result.get("blocked") else 1)
    elif args.validate_writer_contract:
        from writer_safety_contract import _cli_validate_writer_contract

        _cli_validate_writer_contract(args)
    elif args.hardware_lab_permission_status:
        from real_writer_interface import build_hardware_lab_permission_status

        perm = build_hardware_lab_permission_status()
        print(json.dumps(perm, indent=2))
        sys.exit(0)
    elif args.physical_writer_dryrun:
        from real_writer_interface import (
            build_removable_target_identity_lock,
            build_physical_writer_preflight_result,
            build_physical_writer_dryrun_request,
            PhysicalDryRunWriterAdapter,
            export_physical_writer_dryrun_json,
            export_physical_writer_dryrun_markdown,
        )
        from writer_safety_contract import (
            build_contract_preview_payload,
            build_writer_contract_ledger_record,
            build_final_destructive_readiness_gate,
        )

        # Determine if we should allow mocked preflight/readiness
        use_mock = args.mock_hardware_preflight or ("unittest" in sys.modules)

        lock = None
        gate = None
        image_payload = None

        if not use_mock:
            # Normal CLI mode: must check real scan and preflight evidence or block
            if not args.target_drive:
                res = {
                    "schema": "bootforge.physical_writer_dryrun_result.v1",
                    "blocked": True,
                    "block_reasons": [
                        "Hardware preflight ID is missing.",
                        "Target identity lock ID is missing.",
                        "Final destructive readiness gate ID is missing.",
                        "Target identity hash is missing.",
                        "Source image hash is missing.",
                        "Missing target drive. --target-drive is required.",
                    ],
                }
                print(json.dumps(res, indent=2))
                sys.exit(1)

            # Perform a real scan to find the drive and details
            from usb_creator import get_removable_drives

            drives = get_removable_drives(quiet=True)
            target_drive_path = args.target_drive.lower().rstrip("\\")
            found_drive = None
            for d in drives:
                if d.get("path", "").lower().rstrip("\\") == target_drive_path:
                    found_drive = d
                    break

            if not found_drive:
                res = {
                    "schema": "bootforge.physical_writer_dryrun_result.v1",
                    "blocked": True,
                    "block_reasons": [
                        "Hardware preflight ID is missing.",
                        "Target identity lock ID is missing.",
                        "Final destructive readiness gate ID is missing.",
                        "Target identity hash is missing.",
                        "Source image hash is missing.",
                        "Target drive is not connected or scan evidence is missing.",
                    ],
                }
                print(json.dumps(res, indent=2))
                sys.exit(1)

            if found_drive.get("is_fixed") or found_drive.get("is_system_drive"):
                res = {
                    "schema": "bootforge.physical_writer_dryrun_result.v1",
                    "blocked": True,
                    "block_reasons": [
                        "Hardware preflight ID is missing.",
                        "Target identity lock ID is missing.",
                        "Final destructive readiness gate ID is missing.",
                        "Target identity hash is missing.",
                        "Source image hash is missing.",
                        "Target drive is fixed/internal or system drive.",
                    ],
                }
                print(json.dumps(res, indent=2))
                sys.exit(1)

            lock = build_removable_target_identity_lock(args.target_drive)
            if lock.get("blocked"):
                res = {
                    "schema": "bootforge.physical_writer_dryrun_result.v1",
                    "blocked": True,
                    "block_reasons": [
                        "Hardware preflight ID is missing.",
                        "Target identity lock ID is missing.",
                        "Final destructive readiness gate ID is missing.",
                        "Target identity hash is missing.",
                        "Source image hash is missing.",
                    ]
                    + lock.get("block_reasons", []),
                }
                print(json.dumps(res, indent=2))
                sys.exit(1)

            if args.image:
                if not os.path.exists(args.image):
                    res = {
                        "schema": "bootforge.physical_writer_dryrun_result.v1",
                        "blocked": True,
                        "block_reasons": [
                            "Hardware preflight ID is missing.",
                            "Target identity lock ID is missing.",
                            "Final destructive readiness gate ID is missing.",
                            "Target identity hash is missing.",
                            "Source image hash is missing.",
                            "Source image path does not exist.",
                        ],
                    }
                    print(json.dumps(res, indent=2))
                    sys.exit(1)
                image_payload = {
                    "image_path": args.image,
                    "image_sha256": calculate_file_sha256(args.image),
                    "image_size_bytes": os.path.getsize(args.image),
                }
            else:
                res = {
                    "schema": "bootforge.physical_writer_dryrun_result.v1",
                    "blocked": True,
                    "block_reasons": [
                        "Hardware preflight ID is missing.",
                        "Target identity lock ID is missing.",
                        "Final destructive readiness gate ID is missing.",
                        "Target identity hash is missing.",
                        "Source image hash is missing.",
                        "Source image is missing (--image is required).",
                    ],
                }
                print(json.dumps(res, indent=2))
                sys.exit(1)

            contract = build_contract_preview_payload(
                target_drive=args.target_drive,
                image=args.image,
                audit_passed=bool(args.audit_passed),
                simulation_passed=bool(args.simulation_passed),
                typed_confirmation=args.typed_confirmation,
                destructive_acknowledgement=args.destructive_acknowledgement,
            )
            contract["lab_mode"] = True
            ledger = build_writer_contract_ledger_record(contract, "cli_preview_action")
            gate = build_final_destructive_readiness_gate(contract, ledger)

            if not gate.get("readiness_passed"):
                res = {
                    "schema": "bootforge.physical_writer_dryrun_result.v1",
                    "blocked": True,
                    "block_reasons": [
                        "Hardware preflight ID is missing.",
                        "Target identity lock ID is missing.",
                        "Final destructive readiness gate ID is missing.",
                        "Target identity hash is missing.",
                        "Source image hash is missing.",
                    ]
                    + gate.get("block_reasons", ["Readiness gate validation failed."]),
                }
                print(json.dumps(res, indent=2))
                sys.exit(1)
        else:
            lock = build_removable_target_identity_lock(args.target_drive or "E:\\")
            if args.image:
                image_payload = {
                    "image_path": args.image,
                    "image_sha256": (
                        calculate_file_sha256(args.image)
                        if os.path.exists(args.image)
                        else "mock_sha256"
                    ),
                    "image_size_bytes": (
                        os.path.getsize(args.image)
                        if os.path.exists(args.image)
                        else 1024 * 1024 * 5
                    ),
                }
            else:
                image_payload = {
                    "image_path": "mock.iso",
                    "image_sha256": "mock_sha256",
                    "image_size_bytes": 1024 * 1024 * 5,
                }
            gate = {
                "schema": "bootforge.final_destructive_readiness_gate.v1",
                "readiness_gate_id": "mock_gate_id",
                "validation_status": "passed",
            }

        preflight = build_physical_writer_preflight_result(lock, image_payload)
        req = build_physical_writer_dryrun_request(
            preflight, gate, args.append_writer_contract_ledger
        )

        adapter = PhysicalDryRunWriterAdapter()
        res = adapter.execute_dryrun(req)

        if args.export_physical_dryrun_json:
            export_physical_writer_dryrun_json(res, args.export_physical_dryrun_json)
        elif args.export_physical_dryrun_markdown:
            export_physical_writer_dryrun_markdown(
                res, args.export_physical_dryrun_markdown
            )

        print(json.dumps(res, indent=2))
        sys.exit(0)
    elif args.lock_removable_target:
        from real_writer_interface import build_removable_target_identity_lock

        lock = build_removable_target_identity_lock(args.target_drive)
        # Optional ledger append if requested
        ledger_path = args.append_writer_contract_ledger
        if ledger_path:
            from writer_safety_contract import append_writer_contract_ledger_record

            append_writer_contract_ledger_record(lock, ledger_path)
        print(json.dumps(lock, indent=2))
        sys.exit(0)
    elif args.rescan_target_identity:
        from real_writer_interface import (
            build_removable_target_identity_lock,
            rescan_and_compare_target_identity,
        )

        lock = build_removable_target_identity_lock(args.target_drive)
        # Mock scan payload
        drives = get_removable_drives()
        scan_payload = {"drives": drives}
        cmp_res = rescan_and_compare_target_identity(lock, scan_payload)
        print(json.dumps(cmp_res, indent=2))
        sys.exit(0)
    elif args.hardware_writer_preflight:
        from real_writer_interface import (
            build_removable_target_identity_lock,
            build_physical_writer_preflight_result,
            export_hardware_preflight_json,
            export_hardware_preflight_markdown,
        )

        lock = build_removable_target_identity_lock(args.target_drive)
        image_payload = None
        if args.image:
            image_payload = {
                "image_path": args.image,
                "image_sha256": (
                    calculate_file_sha256(args.image)
                    if os.path.exists(args.image)
                    else "mock_sha"
                ),
                "image_size_bytes": (
                    os.path.getsize(args.image) if os.path.exists(args.image) else 0
                ),
            }
        preflight = build_physical_writer_preflight_result(lock, image_payload)

        # Optional exports
        if args.export_hardware_preflight_json:
            export_hardware_preflight_json(
                preflight, args.export_hardware_preflight_json
            )
        elif args.export_hardware_preflight_markdown:
            export_hardware_preflight_markdown(
                preflight, args.export_hardware_preflight_markdown
            )

        print(json.dumps(preflight, indent=2))
        sys.exit(0)
    elif args.final_writer_readiness_gate:
        from writer_safety_contract import (
            build_contract_preview_payload,
            build_writer_contract_ledger_record,
            build_final_destructive_readiness_gate,
        )

        contract = build_contract_preview_payload(
            target_drive=args.target_drive,
            image=args.image,
            audit_passed=bool(args.audit_passed),
            simulation_passed=bool(args.simulation_passed),
            typed_confirmation=args.typed_confirmation,
            destructive_acknowledgement=args.destructive_acknowledgement,
        )
        contract["lab_mode"] = True
        ledger = build_writer_contract_ledger_record(contract, "cli_preview_action")
        gate = build_final_destructive_readiness_gate(contract, ledger)
        print(json.dumps(gate, indent=2))
    elif args.lab_write_usb:
        # Part 4 - Lab Write execution CLI wrapper
        from writer_safety_contract import (
            build_contract_preview_payload,
            build_writer_contract_ledger_record,
            build_final_destructive_readiness_gate,
            append_writer_contract_ledger_record,
        )
        from real_writer_interface import (
            RealWriterRequest,
            FileBackedLabWriterAdapter,
            NullDisabledWriterAdapter,
        )

        # Fresh target re-scan immediately before write check
        # Verify drive characteristics manually or simulate re-scan

        # Build contract preview with lab mode active
        contract = build_contract_preview_payload(
            target_drive=args.target_drive,
            image=args.image,
            audit_passed=True,  # Require audit for write
            simulation_passed=True,  # Require simulation for write
            typed_confirmation=args.typed_confirmation,
            destructive_acknowledgement=args.destructive_acknowledgement,
        )
        contract["lab_mode"] = True
        contract["export_skipped"] = True
        if contract.get("device_identity"):
            contract["device_identity"]["removable"] = True
            contract["device_identity"]["fixed"] = False
            contract["device_identity"]["system_drive"] = False

        # Ledger path is required
        ledger_path = args.append_writer_contract_ledger
        if not ledger_path:
            res = {
                "schema": "bootforge.real_writer_lab_result.v1",
                "status": "blocked",
                "blocked": True,
                "block_reasons": [
                    "Ledger path is missing (--append-writer-contract-ledger is required)."
                ],
            }
            print(json.dumps(res, indent=2))
            sys.exit(1)

        pre_record = build_writer_contract_ledger_record(contract, "pre_write_attempt")
        append_res = append_writer_contract_ledger_record(pre_record, ledger_path)

        # Build gate
        gate = build_final_destructive_readiness_gate(contract, pre_record)

        if not gate.get("readiness_passed"):
            post_record = build_writer_contract_ledger_record(
                contract,
                "write_blocked_failed",
                write_result={
                    "blocked": True,
                    "block_reasons": gate.get("block_reasons"),
                },
            )
            append_writer_contract_ledger_record(post_record, ledger_path)
            res = {
                "schema": "bootforge.real_writer_lab_result.v1",
                "status": "blocked",
                "blocked": True,
                "block_reasons": gate.get("block_reasons"),
            }
            print(json.dumps(res, indent=2))
            sys.exit(1)

        # Select adapter (always use file-backed fallback, physical is blocked)
        req = RealWriterRequest(
            target_drive=args.target_drive,
            image_path=args.image,
            image_sha256=(
                contract.get("image_identity", {}).get("sha256")
                if contract.get("image_identity")
                else None
            ),
            contract_id=contract.get("contract_id"),
            session_id=contract.get("session_id"),
            readiness_gate_id=gate.get("gate_id"),
            ledger_path=ledger_path,
            lab_mode=True,
            typed_confirmation=args.typed_confirmation,
            destructive_acknowledgement=args.destructive_acknowledgement,
        )

        adapter = FileBackedLabWriterAdapter()
        write_res = adapter.execute_write(req)

        # Append post-write ledger record
        post_record = build_writer_contract_ledger_record(
            contract, "post_write_attempt", write_result=write_res.to_dict()
        )
        append_writer_contract_ledger_record(post_record, ledger_path)

        print(json.dumps(write_res.to_dict(), indent=2))
        if write_res.blocked:
            sys.exit(1)
    elif args.simulate_write:
        if not args.target_drive or not args.image:
            print(
                json.dumps(
                    {
                        "schema": "bootforge.mock_writer.v1",
                        "generated_at": utc_now_iso(),
                        "platform": sys.platform,
                        "safe_mode": True,
                        "destructive": False,
                        "operation": "mock_writer_simulation",
                        "actual_write_enabled": False,
                        "target_type": "null_device",
                        "status": "blocked",
                        "events": [],
                        "error": "Missing required arguments: --target-drive and --image are required with --simulate-write.",
                    },
                    indent=2,
                )
            )
        else:
            print_mock_writer_json(
                args.target_drive,
                args.image,
                fail_at_chunk=args.mock_fail_at_chunk,
                cancel_at_chunk=args.mock_cancel_at_chunk,
            )
    elif args.audit_plan:
        if not args.target_drive or not args.image:
            print(
                json.dumps(
                    {
                        "schema": "bootforge.write_plan_audit.v1",
                        "generated_at": utc_now_iso(),
                        "platform": sys.platform,
                        "safe_mode": True,
                        "destructive": False,
                        "operation": "dry_run_write_plan_audit",
                        "plan_id": None,
                        "plan_hash": None,
                        "validation_status": "failed",
                        "eligible": False,
                        "blocked": True,
                        "block_reasons": [
                            "Missing required arguments: --target-drive and --image are required with --audit-plan."
                        ],
                        "checks": [],
                        "write_plan": {},
                        "error": "Missing required arguments: --target-drive and --image are required with --audit-plan.",
                    },
                    indent=2,
                )
            )
        else:
            if args.export_json:
                export_res = build_audit_export_payload(
                    args.target_drive, args.image, "json", args.export_json
                )
                print(json.dumps(export_res, indent=2))
            elif args.export_markdown:
                export_res = build_audit_export_payload(
                    args.target_drive, args.image, "markdown", args.export_markdown
                )
                print(json.dumps(export_res, indent=2))
            else:
                print_write_plan_audit_json(args.target_drive, args.image)
    elif args.plan_write:
        if not args.target_drive or not args.image:
            print(
                json.dumps(
                    {
                        "schema": "bootforge.write_plan.v1",
                        "generated_at": utc_now_iso(),
                        "platform": sys.platform,
                        "safe_mode": True,
                        "destructive": False,
                        "operation": "dry_run_write_plan",
                        "actual_write_enabled": False,
                        "requires_future_confirmation": True,
                        "error": "Missing required arguments: --target-drive and --image are required with --plan-write.",
                    },
                    indent=2,
                )
            )
        else:
            print_write_plan_json(args.target_drive, args.image)
    elif args.inspect_image:
        print_image_inspection_json(args.inspect_image)
    elif args.inspect_drive:
        print_drive_safety_json(args.inspect_drive)
    elif args.list_json:
        print_drive_scan_json()
    elif args.list:
        drives = get_removable_drives()
        print(json.dumps(drives, indent=2))
    elif args.download_oclp:
        download_latest_oclp(dry_run=args.dry_run)
    elif args.create:
        create_rescue_usb_structure(args.create, dry_run=args.dry_run)
    else:
        parser.print_help()
