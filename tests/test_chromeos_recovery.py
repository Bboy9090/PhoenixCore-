"""Tests for Chrome OS recovery metadata selection (no network)."""

import tempfile
import zipfile
from pathlib import Path

from src.core.chromeos_recovery.extract import extract_chromeos_recovery_bin
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


def test_extract_chromeos_recovery_bin_single_member():
    with tempfile.TemporaryDirectory() as tmp:
        zpath = Path(tmp) / "rec.zip"
        inner = Path(tmp) / "payload.bin"
        inner.write_bytes(b"chromeos-bin-test-bytes" * 100)
        with zipfile.ZipFile(zpath, "w") as zf:
            zf.write(inner, "chromeos_123_recovery_stable-channel.bin")

        out_dir = Path(tmp) / "out"
        got = extract_chromeos_recovery_bin(zpath, out_dir, safe_stem="octopus")
        assert got.name == "octopus_recovery.bin"
        assert got.read_bytes() == inner.read_bytes()


def test_extract_raises_on_multiple_bin():
    with tempfile.TemporaryDirectory() as tmp:
        zpath = Path(tmp) / "rec.zip"
        with zipfile.ZipFile(zpath, "w") as zf:
            zf.writestr("a.bin", b"a")
            zf.writestr("b.bin", b"b")
        try:
            extract_chromeos_recovery_bin(zpath, Path(tmp) / "out", safe_stem="x")
            assert False, "expected ChromeosRecoveryError"
        except ChromeosRecoveryError as e:
            assert "Multiple" in str(e)
