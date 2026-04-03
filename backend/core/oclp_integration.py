"""
Phoenix Core - OCLP Integration
OpenCore Legacy Patcher compatibility and configuration
"""
import platform
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

# Known OCLP-compatible Mac models with supported macOS versions
OCLP_COMPATIBILITY_DB = {
    "iMac14,1": {"name": "iMac (21.5-inch, Late 2013)", "max_native": "10.15", "oclp_max": "15.0", "kexts": ["graphics", "audio", "wifi", "usb"]},
    "iMac14,2": {"name": "iMac (27-inch, Late 2013)", "max_native": "10.15", "oclp_max": "15.0", "kexts": ["graphics", "audio", "wifi", "usb"]},
    "iMac15,1": {"name": "iMac (Retina 5K, 27-inch, Late 2014)", "max_native": "12.0", "oclp_max": "15.0", "kexts": ["graphics", "audio", "wifi"]},
    "iMac16,1": {"name": "iMac (21.5-inch, Late 2015)", "max_native": "12.0", "oclp_max": "15.0", "kexts": ["graphics", "audio", "wifi"]},
    "iMac16,2": {"name": "iMac (21.5-inch 4K, Late 2015)", "max_native": "12.0", "oclp_max": "15.0", "kexts": ["graphics", "audio", "wifi"]},
    "iMac17,1": {"name": "iMac (Retina 5K, 27-inch, Late 2015)", "max_native": "12.0", "oclp_max": "15.0", "kexts": ["graphics", "audio"]},
    "iMac18,1": {"name": "iMac (21.5-inch, 2017)", "max_native": "13.0", "oclp_max": "15.0", "kexts": ["graphics", "wifi"]},
    "iMac18,2": {"name": "iMac (Retina 4K, 21.5-inch, 2017)", "max_native": "13.0", "oclp_max": "15.0", "kexts": ["graphics", "wifi"]},
    "iMac18,3": {"name": "iMac (Retina 5K, 27-inch, 2017)", "max_native": "13.0", "oclp_max": "15.0", "kexts": ["graphics"]},
    "iMac19,1": {"name": "iMac (Retina 5K, 27-inch, 2019)", "max_native": "14.0", "oclp_max": "15.0", "kexts": []},
    "iMac19,2": {"name": "iMac (Retina 4K, 21.5-inch, 2019)", "max_native": "14.0", "oclp_max": "15.0", "kexts": []},
    "MacBookPro11,1": {"name": "MacBook Pro (Retina, 13-inch, Late 2013)", "max_native": "12.0", "oclp_max": "15.0", "kexts": ["graphics", "wifi"]},
    "MacBookPro11,2": {"name": "MacBook Pro (Retina, 15-inch, Late 2013)", "max_native": "12.0", "oclp_max": "15.0", "kexts": ["graphics", "wifi"]},
    "MacBookPro11,3": {"name": "MacBook Pro (Retina, 15-inch, Late 2013)", "max_native": "12.0", "oclp_max": "15.0", "kexts": ["graphics", "wifi"]},
    "MacBookPro12,1": {"name": "MacBook Pro (Retina, 13-inch, Early 2015)", "max_native": "12.0", "oclp_max": "15.0", "kexts": ["wifi"]},
    "MacBookPro13,1": {"name": "MacBook Pro (13-inch, Late 2016)", "max_native": "13.0", "oclp_max": "15.0", "kexts": []},
    "MacBookPro14,1": {"name": "MacBook Pro (13-inch, 2017)", "max_native": "14.0", "oclp_max": "15.0", "kexts": []},
    "MacBookAir6,1": {"name": "MacBook Air (11-inch, Mid 2013)", "max_native": "11.0", "oclp_max": "15.0", "kexts": ["graphics", "wifi", "audio"]},
    "MacBookAir6,2": {"name": "MacBook Air (13-inch, Mid 2013)", "max_native": "11.0", "oclp_max": "15.0", "kexts": ["graphics", "wifi", "audio"]},
    "MacBookAir7,1": {"name": "MacBook Air (11-inch, Early 2015)", "max_native": "12.0", "oclp_max": "15.0", "kexts": ["wifi"]},
    "MacBookAir7,2": {"name": "MacBook Air (13-inch, Early 2015)", "max_native": "12.0", "oclp_max": "15.0", "kexts": ["wifi"]},
    "MacPro5,1": {"name": "Mac Pro (Mid 2010)", "max_native": "10.14", "oclp_max": "15.0", "kexts": ["graphics", "audio", "wifi", "usb"]},
    "MacPro6,1": {"name": "Mac Pro (Late 2013)", "max_native": "12.0", "oclp_max": "15.0", "kexts": ["graphics", "wifi"]},
    "Macmini6,1": {"name": "Mac mini (Late 2012)", "max_native": "10.15", "oclp_max": "15.0", "kexts": ["graphics", "wifi", "audio"]},
    "Macmini6,2": {"name": "Mac mini (Late 2012)", "max_native": "10.15", "oclp_max": "15.0", "kexts": ["graphics", "wifi", "audio"]},
    "Macmini7,1": {"name": "Mac mini (Late 2014)", "max_native": "12.0", "oclp_max": "15.0", "kexts": ["wifi"]},
    "Macmini8,1": {"name": "Mac mini (Late 2018)", "max_native": "14.0", "oclp_max": "15.0", "kexts": []},
}

MACOS_VERSIONS = {
    "11.0": "Big Sur",
    "12.0": "Monterey",
    "13.0": "Ventura",
    "13.6": "Ventura 13.6",
    "14.0": "Sonoma",
    "14.5": "Sonoma 14.5",
    "15.0": "Sequoia",
}


def check_oclp_compatibility(model: str) -> Dict[str, Any]:
    """Check OCLP compatibility for a Mac model."""
    if model in OCLP_COMPATIBILITY_DB:
        info = OCLP_COMPATIBILITY_DB[model]
        supported_versions = [
            f"{ver} ({name})"
            for ver, name in MACOS_VERSIONS.items()
            if float(ver) > float(info["max_native"])
        ]
        return {
            "model": model,
            "compatible": True,
            "model_name": info["name"],
            "max_native_macos": info["max_native"],
            "oclp_max_macos": info["oclp_max"],
            "supported_macos_versions": supported_versions,
            "required_kexts": info["kexts"],
            "warnings": _get_warnings(model, info),
            "notes": f"OCLP can extend {info['name']} support to macOS {info['oclp_max']}",
        }
    else:
        # Check if it's a newer model that doesn't need OCLP
        return {
            "model": model,
            "compatible": False,
            "model_name": f"Unknown Mac ({model})",
            "max_native_macos": "15.0",
            "oclp_max_macos": "15.0",
            "supported_macos_versions": list(MACOS_VERSIONS.values()),
            "required_kexts": [],
            "warnings": [],
            "notes": "This model may not require OCLP or is not in the compatibility database.",
        }


def _get_warnings(model: str, info: Dict[str, Any]) -> List[str]:
    """Get OCLP warnings for a specific model."""
    warnings = []
    kexts = info.get("kexts", [])

    if "graphics" in kexts:
        warnings.append("Graphics acceleration requires Metal GPU patch — some effects may be slower")
    if "wifi" in kexts:
        warnings.append("WiFi requires Broadcom kext injection — AirDrop may have limited functionality")
    if "usb" in kexts:
        warnings.append("USB requires legacy USB controller patch")
    if model.startswith("MacPro5"):
        warnings.append("Mac Pro 5,1 requires GPU upgrade for Metal support")

    return warnings


def get_all_compatible_models() -> List[Dict[str, Any]]:
    """Get all OCLP-compatible Mac models."""
    models = []
    for model_id, info in OCLP_COMPATIBILITY_DB.items():
        models.append({
            "model_id": model_id,
            "name": info["name"],
            "max_native_macos": info["max_native"],
            "oclp_max_macos": info["oclp_max"],
            "required_kexts": info["kexts"],
        })
    return sorted(models, key=lambda x: x["model_id"])


def get_macos_versions() -> Dict[str, str]:
    """Get supported macOS versions."""
    return MACOS_VERSIONS


def detect_current_mac_model() -> Optional[str]:
    """Detect the current Mac model identifier."""
    if platform.system() != "Darwin":
        return None
    try:
        import subprocess
        result = subprocess.run(
            ["sysctl", "-n", "hw.model"],
            capture_output=True, text=True, timeout=3
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except Exception:
        pass
    return None
