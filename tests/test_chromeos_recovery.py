"""Tests for Chrome OS recovery metadata selection (no network)."""

from src.core.chromeos_recovery.index import (
    ChromeosRecoveryError,
    pick_latest_stable_image,
    select_recovery_for_board,
)


def test_pick_latest_stable_prefers_highest_platform_version():
    images = [
        {
            "platform_version": "0.0.0",
            "chrome_version": "0.0.0.0",
            "channel": "Credit: github.com/MercuryWorkshop/chromeos-releases-data",
            "url": "https://github.com/MercuryWorkshop/chromeos-releases-data",
        },
        {
            "platform_version": "10000.0.0",
            "chrome_version": "90.0.0.0",
            "channel": "stable-channel",
            "url": "https://dl.google.com/dl/edgedl/chromeos/recovery/chromeos_10000.0.0_foo_recovery_stable-channel_mp.bin.zip",
        },
        {
            "platform_version": "9999.0.0",
            "chrome_version": "89.0.0.0",
            "channel": "stable-channel",
            "url": "https://dl.google.com/dl/edgedl/chromeos/recovery/chromeos_9999.0.0_foo_recovery_stable-channel_mp.bin.zip",
        },
    ]
    picked = pick_latest_stable_image(images)
    assert picked is not None
    assert picked["platform_version"] == "10000.0.0"


def test_select_recovery_for_board():
    index = {
        "testboard": {
            "brand_names": ["Example Chromebook"],
            "images": [
                {
                    "platform_version": "0.0.0",
                    "channel": "meta",
                    "url": "https://github.com/MercuryWorkshop/chromeos-releases-data",
                },
                {
                    "platform_version": "15000.1.0",
                    "chrome_version": "100.0.0.0",
                    "channel": "stable-channel",
                    "last_modified": 1,
                    "url": "https://dl.google.com/dl/edgedl/chromeos/recovery/chromeos_15000.1.0_testboard_recovery_stable-channel_x.bin.zip",
                },
            ],
        }
    }
    sel = select_recovery_for_board(index, "testboard")
    assert sel.board == "testboard"
    assert "dl.google.com" in sel.url
    assert sel.platform_version == "15000.1.0"


def test_unknown_board_raises():
    try:
        select_recovery_for_board({}, "missing")
        assert False, "expected ChromeosRecoveryError"
    except ChromeosRecoveryError as e:
        assert "Unknown board" in str(e)
