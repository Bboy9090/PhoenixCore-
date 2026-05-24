import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.core import usb_low_level


def test_parse_hexish_variants():
    assert usb_low_level._parse_hexish("0x05ac") == 0x05AC
    assert usb_low_level._parse_hexish("05ac") == 0x05AC
    assert usb_low_level._parse_hexish("09") == 0x09
    assert usb_low_level._parse_hexish("0x05ac  (Apple Inc.)") == 0x05AC
    assert usb_low_level._parse_hexish(None) is None


def test_bootforge_mode_classification_matches_known_profiles():
    assert usb_low_level._classify_mode(0x05AC, 0x1227) == "dfu"
    assert usb_low_level._classify_mode(0x05AC, 0x1281) == "recovery"
    assert usb_low_level._classify_mode(0x18D1, 0x4EE7) == "fastboot"
    assert usb_low_level._classify_mode(0x04E8, 0x6860) == "adb"
    assert usb_low_level._classify_mode(0x0781, 0x1234) == "mass_storage"


def test_transport_classification_from_speed():
    assert usb_low_level._classify_transport(speed="Up to 5 Gb/s") == "usb3"
    assert usb_low_level._classify_transport(speed="Up to 480 Mb/s") == "usb2"
    assert usb_low_level._classify_transport(speed="Up to 12 Mb/s") == "usb1"
    assert usb_low_level._classify_transport(speed="5000") == "usb3"
    assert usb_low_level._classify_transport(speed="480") == "usb2"


def test_extract_macos_usb_devices_from_system_profiler_payload():
    payload = {
        "SPUSBDataType": [
            {
                "_name": "USB 3.0 Bus",
                "_items": [
                    {
                        "_name": "iPhone",
                        "vendor_id": "0x05ac  (Apple Inc.)",
                        "product_id": "0x12a8",
                        "manufacturer": "Apple Inc.",
                        "serial_num": "TEST-SERIAL",
                        "speed": "Up to 480 Mb/s",
                        "version": "2.00",
                        "location_id": "0x00100000 / 3",
                    }
                ],
            }
        ]
    }

    devices = usb_low_level._extract_macos_usb_devices(payload)
    assert len(devices) == 1
    assert devices[0]["vendor_id"] == 0x05AC
    assert devices[0]["product_id"] == 0x12A8
    assert devices[0]["platform"] == "apple"
    assert devices[0]["transport"] == "usb2"
    assert devices[0]["mode"] == "normal"
