"""Chrome OS recovery recipe is registered on StorageBuilderEngine."""

import sys
from pathlib import Path

DESKTOP = Path(__file__).resolve().parent.parent / "desktop"
if str(DESKTOP) not in sys.path:
    sys.path.insert(0, str(DESKTOP))

from src.core.models import DeploymentType
from src.core.usb_builder import StorageBuilderEngine


def test_chromeos_recovery_recipe_registered():
    eng = StorageBuilderEngine()
    r = eng.recipes.get("Chrome OS Recovery (download)")
    assert r is not None
    assert r.deployment_type == DeploymentType.CHROMEOS_RECOVERY
    assert "chromeos_recovery.zip" in r.required_files
