import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.append(str(Path(__file__).parent.parent))
import usb_creator


class TestImageInspection(unittest.TestCase):
    def test_build_image_inspection_payload_success(self):
        """Verify read-only image inspection reports metadata and SHA256."""
        expected_bytes = b"PhoenixCore image fixture"

        with tempfile.NamedTemporaryFile(suffix=".iso", delete=False) as tmp:
            tmp_path = Path(tmp.name)
            tmp.write(expected_bytes)

        try:
            payload = usb_creator.build_image_inspection_payload(str(tmp_path))

            self.assertEqual("bootforge.image_inspection.v1", payload["schema"])
            self.assertTrue(payload["safe_mode"])
            self.assertFalse(payload["destructive"])
            self.assertEqual("read_only_image_inspection", payload["operation"])
            self.assertIsNone(payload["error"])
            self.assertTrue(payload["image"]["exists"])
            self.assertTrue(payload["image"]["supported"])
            self.assertEqual(".iso", payload["image"]["extension"])
            self.assertEqual(len(expected_bytes), payload["image"]["size_bytes"])
            self.assertEqual(usb_creator.calculate_file_sha256(tmp_path), payload["image"]["sha256"])
        finally:
            if tmp_path.exists():
                tmp_path.unlink()

    def test_build_image_inspection_payload_missing_file(self):
        """Verify missing images return a safe JSON error without crashing."""
        missing_path = Path(tempfile.gettempdir()) / "phoenixcore_missing_image.iso"
        if missing_path.exists():
            missing_path.unlink()

        payload = usb_creator.build_image_inspection_payload(str(missing_path))

        self.assertEqual("bootforge.image_inspection.v1", payload["schema"])
        self.assertTrue(payload["safe_mode"])
        self.assertFalse(payload["destructive"])
        self.assertEqual("Image path does not exist.", payload["error"])
        self.assertFalse(payload["image"]["exists"])
        self.assertTrue(payload["image"]["supported"])
        self.assertIsNone(payload["image"]["sha256"])

    def test_build_image_inspection_payload_unsupported_extension(self):
        """Verify unsupported files can be inspected but are flagged as unsupported."""
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as tmp:
            tmp_path = Path(tmp.name)
            tmp.write(b"not a boot image")

        try:
            payload = usb_creator.build_image_inspection_payload(str(tmp_path))

            self.assertFalse(payload["image"]["supported"])
            self.assertEqual(".txt", payload["image"]["extension"])
            self.assertIsNone(payload["error"])
            self.assertIsNotNone(payload["image"]["sha256"])
        finally:
            if tmp_path.exists():
                tmp_path.unlink()

    def test_print_image_inspection_json_outputs_json_only(self):
        """Verify --inspect-image bridge output can be parsed without log pollution."""
        with tempfile.NamedTemporaryFile(suffix=".img", delete=False) as tmp:
            tmp_path = Path(tmp.name)
            tmp.write(b"json output fixture")

        try:
            capture = io.StringIO()
            with patch("sys.stdout", capture):
                usb_creator.print_image_inspection_json(str(tmp_path))

            parsed = json.loads(capture.getvalue())
            self.assertEqual("bootforge.image_inspection.v1", parsed["schema"])
            self.assertEqual("read_only_image_inspection", parsed["operation"])
            self.assertFalse(parsed["destructive"])
            self.assertTrue(parsed["image"]["supported"])
        finally:
            if tmp_path.exists():
                tmp_path.unlink()


if __name__ == "__main__":
    unittest.main()
