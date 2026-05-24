"""
Phoenix Core - OCLP Integration
OpenCore Legacy Patcher integration for Mac compatibility checking
Integrated from PhoenixCore- backend for production-grade Mac support
"""
import platform
import logging
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)

# Mac model compatibility database
MAC_MODELS = {
    "MacBook1,1": {"name": "MacBook (13-inch, 2006)", "max_macos": "10.7.5", "bootcamp": False},
    "MacBook2,1": {"name": "MacBook (13-inch, 2007)", "max_macos": "10.7.5", "bootcamp": False},
    "MacBook3,1": {"name": "MacBook (13-inch, 2008)", "max_macos": "10.7.5", "bootcamp": True},
    "MacBook4,1": {"name": "MacBook (13-inch, 2008)", "max_macos": "10.7.5", "bootcamp": True},
    "MacBook5,1": {"name": "MacBook (13-inch, 2009)", "max_macos": "10.7.5", "bootcamp": True},
    "MacBook5,2": {"name": "MacBook (13-inch, 2009)", "max_macos": "10.7.5", "bootcamp": True},
    "MacBook6,1": {"name": "MacBook (13-inch, 2010)", "max_macos": "10.7.5", "bootcamp": True},
    "MacBook7,1": {"name": "MacBook (13-inch, 2010)", "max_macos": "10.7.5", "bootcamp": True},
    "MacBook8,1": {"name": "MacBook (12-inch, 2015)", "max_macos": "12.6.9", "bootcamp": False},
    "MacBook9,1": {"name": "MacBook (12-inch, 2016)", "max_macos": "13.5.2", "bootcamp": False},
    "MacBook10,1": {"name": "MacBook (12-inch, 2017)", "max_macos": "14.6.1", "bootcamp": False},
    "MacBookPro1,1": {"name": "MacBook Pro (15-inch, 2006)", "max_macos": "10.7.5", "bootcamp": True},
    "MacBookPro1,2": {"name": "MacBook Pro (17-inch, 2006)", "max_macos": "10.7.5", "bootcamp": True},
    "MacBookPro2,1": {"name": "MacBook Pro (15-inch, 2007)", "max_macos": "10.7.5", "bootcamp": True},
    "MacBookPro2,2": {"name": "MacBook Pro (17-inch, 2007)", "max_macos": "10.7.5", "bootcamp": True},
    "MacBookPro3,1": {"name": "MacBook Pro (15-inch, 2007)", "max_macos": "10.7.5", "bootcamp": True},
    "MacBookPro4,1": {"name": "MacBook Pro (17-inch, 2008)", "max_macos": "10.7.5", "bootcamp": True},
    "MacBookPro5,1": {"name": "MacBook Pro (15-inch, 2008)", "max_macos": "10.7.5", "bootcamp": True},
    "MacBookPro5,2": {"name": "MacBook Pro (17-inch, 2009)", "max_macos": "10.7.5", "bootcamp": True},
    "MacBookPro5,3": {"name": "MacBook Pro (15-inch, 2009)", "max_macos": "10.7.5", "bootcamp": True},
    "MacBookPro5,4": {"name": "MacBook Pro (15-inch, 2009)", "max_macos": "10.7.5", "bootcamp": True},
    "MacBookPro5,5": {"name": "MacBook Pro (13-inch, 2009)", "max_macos": "10.7.5", "bootcamp": True},
    "MacBookPro6,1": {"name": "MacBook Pro (17-inch, 2010)", "max_macos": "10.7.5", "bootcamp": True},
    "MacBookPro6,2": {"name": "MacBook Pro (15-inch, 2010)", "max_macos": "10.7.5", "bootcamp": True},
    "MacBookPro7,1": {"name": "MacBook Pro (13-inch, 2010)", "max_macos": "10.7.5", "bootcamp": True},
    "MacBookPro8,1": {"name": "MacBook Pro (13-inch, 2011)", "max_macos": "10.7.5", "bootcamp": True},
    "MacBookPro8,2": {"name": "MacBook Pro (15-inch, 2011)", "max_macos": "10.7.5", "bootcamp": True},
    "MacBookPro8,3": {"name": "MacBook Pro (17-inch, 2011)", "max_macos": "10.7.5", "bootcamp": True},
    "MacBookPro9,1": {"name": "MacBook Pro (15-inch, 2012)", "max_macos": "10.7.5", "bootcamp": True},
    "MacBookPro9,2": {"name": "MacBook Pro (13-inch, 2012)", "max_macos": "10.7.5", "bootcamp": True},
    "MacBookPro10,1": {"name": "MacBook Pro (15-inch, 2012)", "max_macos": "10.7.5", "bootcamp": True},
    "MacBookPro10,2": {"name": "MacBook Pro (13-inch, 2012)", "max_macos": "10.7.5", "bootcamp": True},
    "MacBookPro11,1": {"name": "MacBook Pro (13-inch, 2013)", "max_macos": "10.7.5", "bootcamp": True},
    "MacBookPro11,2": {"name": "MacBook Pro (15-inch, 2013)", "max_macos": "10.7.5", "bootcamp": True},
    "MacBookPro11,3": {"name": "MacBook Pro (15-inch, 2013)", "max_macos": "10.7.5", "bootcamp": True},
    "MacBookPro11,4": {"name": "MacBook Pro (15-inch, 2014)", "max_macos": "10.7.5", "bootcamp": True},
    "MacBookPro11,5": {"name": "MacBook Pro (15-inch, 2014)", "max_macos": "10.7.5", "bootcamp": True},
    "MacBookPro12,1": {"name": "MacBook Pro (13-inch, 2015)", "max_macos": "12.6.9", "bootcamp": False},
    "MacBookPro13,1": {"name": "MacBook Pro (13-inch, 2016)", "max_macos": "13.5.2", "bootcamp": False},
    "MacBookPro13,2": {"name": "MacBook Pro (13-inch, 2016)", "max_macos": "13.5.2", "bootcamp": False},
    "MacBookPro13,3": {"name": "MacBook Pro (15-inch, 2016)", "max_macos": "13.5.2", "bootcamp": False},
    "MacBookPro14,1": {"name": "MacBook Pro (13-inch, 2017)", "max_macos": "14.6.1", "bootcamp": False},
    "MacBookPro14,2": {"name": "MacBook Pro (15-inch, 2017)", "max_macos": "14.6.1", "bootcamp": False},
    "MacBookPro14,3": {"name": "MacBook Pro (15-inch, 2017)", "max_macos": "14.6.1", "bootcamp": False},
    "MacBookAir1,1": {"name": "MacBook Air (13-inch, 2008)", "max_macos": "10.7.5", "bootcamp": True},
    "MacBookAir2,1": {"name": "MacBook Air (13-inch, 2009)", "max_macos": "10.7.5", "bootcamp": True},
    "MacBookAir3,1": {"name": "MacBook Air (11-inch, 2010)", "max_macos": "10.7.5", "bootcamp": True},
    "MacBookAir3,2": {"name": "MacBook Air (13-inch, 2010)", "max_macos": "10.7.5", "bootcamp": True},
    "MacBookAir4,1": {"name": "MacBook Air (11-inch, 2011)", "max_macos": "10.7.5", "bootcamp": True},
    "MacBookAir4,2": {"name": "MacBook Air (13-inch, 2011)", "max_macos": "10.7.5", "bootcamp": True},
    "MacBookAir5,1": {"name": "MacBook Air (11-inch, 2012)", "max_macos": "10.7.5", "bootcamp": True},
    "MacBookAir5,2": {"name": "MacBook Air (13-inch, 2012)", "max_macos": "10.7.5", "bootcamp": True},
    "MacBookAir6,1": {"name": "MacBook Air (11-inch, 2013)", "max_macos": "10.7.5", "bootcamp": True},
    "MacBookAir6,2": {"name": "MacBook Air (13-inch, 2013)", "max_macos": "10.7.5", "bootcamp": True},
    "MacBookAir7,1": {"name": "MacBook Air (11-inch, 2015)", "max_macos": "12.6.9", "bootcamp": False},
    "MacBookAir7,2": {"name": "MacBook Air (13-inch, 2015)", "max_macos": "12.6.9", "bootcamp": False},
    "MacBookAir8,1": {"name": "MacBook Air (13-inch, 2018)", "max_macos": "14.6.1", "bootcamp": False},
    "MacBookAir8,2": {"name": "MacBook Air (13-inch, 2019)", "max_macos": "14.6.1", "bootcamp": False},
    "MacBookAir9,1": {"name": "MacBook Air (13-inch, 2020)", "max_macos": "14.6.1", "bootcamp": False},
    "MacBookAir10,1": {"name": "MacBook Air (13-inch, 2022)", "max_macos": "14.6.1", "bootcamp": False},
}


def detect_current_mac_model() -> Optional[str]:
    """Detect current Mac model identifier."""
    if platform.system() != "Darwin":
        return None
    
    try:
        import subprocess
        result = subprocess.run(
            ["sysctl", "-n", "hw.model"],
            capture_output=True, text=True, timeout=5
        )
        return result.stdout.strip()
    except Exception as e:
        logger.error(f"Failed to detect Mac model: {e}")
        return None


def check_oclp_compatibility(mac_model: str) -> Dict[str, Any]:
    """Check if a Mac model is compatible with OCLP."""
    if mac_model not in MAC_MODELS:
        return {
            "compatible": False,
            "reason": "Mac model not recognized",
            "model": mac_model,
        }
    
    model_info = MAC_MODELS[mac_model]
    
    return {
        "compatible": True,
        "model": mac_model,
        "name": model_info["name"],
        "max_macos": model_info["max_macos"],
        "bootcamp_supported": model_info["bootcamp"],
        "oclp_required": True,  # All models in this DB need OCLP for newer macOS
    }


def get_all_compatible_models() -> List[Dict[str, Any]]:
    """Get all compatible Mac models."""
    return [
        {
            "model": model_id,
            "name": info["name"],
            "max_macos": info["max_macos"],
            "bootcamp": info["bootcamp"],
        }
        for model_id, info in MAC_MODELS.items()
    ]


def get_macos_versions() -> List[Dict[str, Any]]:
    """Get list of macOS versions with Windows compatibility."""
    return [
        {"version": "10.5", "name": "Leopard", "bootcamp": True},
        {"version": "10.6", "name": "Snow Leopard", "bootcamp": True},
        {"version": "10.7", "name": "Lion", "bootcamp": True},
        {"version": "10.8", "name": "Mountain Lion", "bootcamp": True},
        {"version": "10.9", "name": "Mavericks", "bootcamp": True},
        {"version": "10.10", "name": "Yosemite", "bootcamp": True},
        {"version": "10.11", "name": "El Capitan", "bootcamp": True},
        {"version": "10.12", "name": "Sierra", "bootcamp": True},
        {"version": "10.13", "name": "High Sierra", "bootcamp": True},
        {"version": "10.14", "name": "Mojave", "bootcamp": True},
        {"version": "10.15", "name": "Catalina", "bootcamp": True},
        {"version": "11", "name": "Big Sur", "bootcamp": False},
        {"version": "12", "name": "Monterey", "bootcamp": False},
        {"version": "13", "name": "Ventura", "bootcamp": False},
        {"version": "14", "name": "Sonoma", "bootcamp": False},
        {"version": "15", "name": "Sequoia", "bootcamp": False},
    ]
