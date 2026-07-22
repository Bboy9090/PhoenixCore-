import unittest
import os
import json
import tempfile
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))


class TestLabWriteMode(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.ledger_path = os.path.join(self.test_dir, "ledger.jsonl")

        # Create a dummy image
        self.image_path = os.path.join(self.test_dir, "test_image.img")
        with open(self.image_path, "wb") as f:
            f.write(b"dummy image data" * 64)

        self.target_path = os.path.join(self.test_dir, "target_drive.img")

    def tearDown(self):
        import shutil

        shutil.rmtree(self.test_dir)
        if "BOOTFORGE_ENABLE_LAB_WRITE" in os.environ:
            del os.environ["BOOTFORGE_ENABLE_LAB_WRITE"]

    def test_01_lab_write_blocks_without_env_var(self):
        """1. Lab write blocks without env var."""
        import subprocess

        cmd = [
            sys.executable,
            "usb_creator.py",
            "--lab-write-usb",
            "--target-drive",
            self.target_path,
            "--image",
            self.image_path,
            "--append-writer-contract-ledger",
            self.ledger_path,
            "--typed-confirmation",
            "I UNDERSTAND THIS WILL OVERWRITE THE SELECTED USB DRIVE",
            "--destructive-acknowledgement",
            "I CONFIRM THIS IS A REMOVABLE TEST USB DRIVE",
        ]
        # Exclude environment variable explicitly
        env = os.environ.copy()
        if "BOOTFORGE_ENABLE_LAB_WRITE" in env:
            del env["BOOTFORGE_ENABLE_LAB_WRITE"]
        res = subprocess.run(cmd, env=env, capture_output=True, text=True)
        self.assertEqual(res.returncode, 1)
        data = json.loads(res.stdout)
        self.assertTrue(data["blocked"])
        self.assertIn(
            "Missing or invalid BOOTFORGE_ENABLE_LAB_WRITE",
            "".join(data["block_reasons"]),
        )

    def test_02_lab_write_blocks_without_typed_confirmation(self):
        """2. Lab write blocks without typed confirmation."""
        os.environ["BOOTFORGE_ENABLE_LAB_WRITE"] = "I_ACCEPT_REAL_USB_WRITE_RISK"
        import subprocess

        cmd = [
            sys.executable,
            "usb_creator.py",
            "--lab-write-usb",
            "--target-drive",
            self.target_path,
            "--image",
            self.image_path,
            "--append-writer-contract-ledger",
            self.ledger_path,
            "--typed-confirmation",
            "wrong",
            "--destructive-acknowledgement",
            "I CONFIRM THIS IS A REMOVABLE TEST USB DRIVE",
        ]
        res = subprocess.run(cmd, capture_output=True, text=True)
        self.assertEqual(res.returncode, 1)
        data = json.loads(res.stdout)
        self.assertTrue(data["blocked"])
        self.assertIn(
            "Typed confirmation phrase mismatch.", "".join(data["block_reasons"])
        )

    def test_03_lab_write_blocks_without_destructive_acknowledgement(self):
        """3. Lab write blocks without destructive acknowledgement."""
        os.environ["BOOTFORGE_ENABLE_LAB_WRITE"] = "I_ACCEPT_REAL_USB_WRITE_RISK"
        import subprocess

        cmd = [
            sys.executable,
            "usb_creator.py",
            "--lab-write-usb",
            "--target-drive",
            self.target_path,
            "--image",
            self.image_path,
            "--append-writer-contract-ledger",
            self.ledger_path,
            "--typed-confirmation",
            "I UNDERSTAND THIS WILL OVERWRITE THE SELECTED USB DRIVE",
            "--destructive-acknowledgement",
            "wrong",
        ]
        res = subprocess.run(cmd, capture_output=True, text=True)
        self.assertEqual(res.returncode, 1)
        data = json.loads(res.stdout)
        self.assertTrue(data["blocked"])
        self.assertIn(
            "Destructive acknowledgement phrase mismatch.",
            "".join(data["block_reasons"]),
        )

    def test_04_lab_write_blocks_without_ledger_path(self):
        """4. Lab write blocks without ledger path."""
        os.environ["BOOTFORGE_ENABLE_LAB_WRITE"] = "I_ACCEPT_REAL_USB_WRITE_RISK"
        import subprocess

        cmd = [
            sys.executable,
            "usb_creator.py",
            "--lab-write-usb",
            "--target-drive",
            self.target_path,
            "--image",
            self.image_path,
            "--typed-confirmation",
            "I UNDERSTAND THIS WILL OVERWRITE THE SELECTED USB DRIVE",
            "--destructive-acknowledgement",
            "I CONFIRM THIS IS A REMOVABLE TEST USB DRIVE",
        ]
        res = subprocess.run(cmd, capture_output=True, text=True)
        self.assertEqual(res.returncode, 1)
        data = json.loads(res.stdout)
        self.assertTrue(data["blocked"])
        self.assertIn("Ledger path is missing", "".join(data["block_reasons"]))

    def test_05_file_backed_lab_writer_writes_exact_bytes(self):
        """5. File-backed lab writer writes exact bytes to target file."""
        os.environ["BOOTFORGE_ENABLE_LAB_WRITE"] = "I_ACCEPT_REAL_USB_WRITE_RISK"
        import subprocess

        cmd = [
            sys.executable,
            "usb_creator.py",
            "--lab-write-usb",
            "--target-drive",
            self.target_path,
            "--image",
            self.image_path,
            "--append-writer-contract-ledger",
            self.ledger_path,
            "--typed-confirmation",
            "I UNDERSTAND THIS WILL OVERWRITE THE SELECTED USB DRIVE",
            "--destructive-acknowledgement",
            "I CONFIRM THIS IS A REMOVABLE TEST USB DRIVE",
        ]
        res = subprocess.run(cmd, capture_output=True, text=True)
        self.assertEqual(res.returncode, 0)
        data = json.loads(res.stdout)
        self.assertFalse(data["blocked"])
        self.assertEqual(data["bytes_written"], os.path.getsize(self.image_path))
        self.assertTrue(os.path.exists(self.target_path))
        self.assertEqual(
            os.path.getsize(self.target_path), os.path.getsize(self.image_path)
        )

    def test_06_file_backed_lab_writer_verifies_sha256(self):
        """6. File-backed lab writer verifies SHA256 matches."""
        os.environ["BOOTFORGE_ENABLE_LAB_WRITE"] = "I_ACCEPT_REAL_USB_WRITE_RISK"
        import subprocess

        cmd = [
            sys.executable,
            "usb_creator.py",
            "--lab-write-usb",
            "--target-drive",
            self.target_path,
            "--image",
            self.image_path,
            "--append-writer-contract-ledger",
            self.ledger_path,
            "--typed-confirmation",
            "I UNDERSTAND THIS WILL OVERWRITE THE SELECTED USB DRIVE",
            "--destructive-acknowledgement",
            "I CONFIRM THIS IS A REMOVABLE TEST USB DRIVE",
            "--verify-after-write",
        ]
        res = subprocess.run(cmd, capture_output=True, text=True)
        self.assertEqual(res.returncode, 0)
        data = json.loads(res.stdout)
        self.assertTrue(data["verification_passed"])


if __name__ == "__main__":
    unittest.main()
