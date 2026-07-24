from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CHECKPOINT_PATH = ROOT / "scripts" / "continuity" / "checkpoint_store.py"

spec = importlib.util.spec_from_file_location("checkpoint_store", CHECKPOINT_PATH)
checkpoint_module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
sys.modules["checkpoint_store"] = checkpoint_module
spec.loader.exec_module(checkpoint_module)


class CheckpointStoreTests(unittest.TestCase):
    def test_checkpoint_has_unique_nonzero_id_and_restores_bytes(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = root / "source.bin"
            source.write_bytes(b"original-state" * 4096)
            store = checkpoint_module.CheckpointStore(root / "continuity")

            checkpoint = store.create_checkpoint(source, repair_id=17)
            self.assertNotEqual(
                checkpoint.checkpoint_id,
                checkpoint_module.ZERO_UUID,
            )
            self.assertEqual(store.list_pending(), [checkpoint])

            source.write_bytes(b"corrupted")
            restored = store.restore(checkpoint.checkpoint_id, source)
            self.assertEqual(restored.state, checkpoint_module.CheckpointState.RESTORED)
            self.assertEqual(source.read_bytes(), b"original-state" * 4096)

    def test_checkpoint_detects_backup_tampering(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = root / "source.bin"
            source.write_bytes(b"safe-state")
            store = checkpoint_module.CheckpointStore(root / "continuity")
            checkpoint = store.create_checkpoint(source, repair_id=1)

            Path(checkpoint.backup_path).write_bytes(b"tampered")
            with self.assertRaises(checkpoint_module.CheckpointError):
                store.verify(checkpoint.checkpoint_id)
            with self.assertRaises(checkpoint_module.CheckpointError):
                store.restore(checkpoint.checkpoint_id, source)

    def test_completed_checkpoint_leaves_pending_list(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = root / "source.bin"
            source.write_bytes(b"state")
            store = checkpoint_module.CheckpointStore(root / "continuity")
            checkpoint = store.create_checkpoint(source, repair_id=2)
            completed = store.mark_completed(checkpoint.checkpoint_id)
            self.assertEqual(
                completed.state, checkpoint_module.CheckpointState.COMPLETED
            )
            self.assertEqual(store.list_pending(), [])

    def test_rejects_directory_source_and_negative_repair_id(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            store = checkpoint_module.CheckpointStore(root / "continuity")
            with self.assertRaises(checkpoint_module.CheckpointError):
                store.create_checkpoint(root, repair_id=1)
            source = root / "source.bin"
            source.write_bytes(b"state")
            with self.assertRaises(checkpoint_module.CheckpointError):
                store.create_checkpoint(source, repair_id=-1)

    def test_rejects_zero_checkpoint_id(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            store = checkpoint_module.CheckpointStore(Path(temp_dir) / "continuity")
            with self.assertRaises(checkpoint_module.CheckpointError):
                store.load(checkpoint_module.ZERO_UUID)

    def test_restore_rejects_directory_target(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = root / "source.bin"
            source.write_bytes(b"state")
            store = checkpoint_module.CheckpointStore(root / "continuity")
            checkpoint = store.create_checkpoint(source, repair_id=3)
            with self.assertRaises(checkpoint_module.CheckpointError):
                store.restore(checkpoint.checkpoint_id, root)

    def test_cli_create_verify_restore_round_trip(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = root / "source.bin"
            source.write_bytes(b"before")
            continuity_root = root / "continuity"

            create_result = subprocess.run(
                [
                    sys.executable,
                    str(CHECKPOINT_PATH),
                    "create",
                    "--root",
                    str(continuity_root),
                    "--source",
                    str(source),
                    "--repair-id",
                    "9",
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            created = json.loads(create_result.stdout)
            source.write_bytes(b"after")

            subprocess.run(
                [
                    sys.executable,
                    str(CHECKPOINT_PATH),
                    "verify",
                    "--root",
                    str(continuity_root),
                    "--checkpoint-id",
                    created["checkpoint_id"],
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            restore_result = subprocess.run(
                [
                    sys.executable,
                    str(CHECKPOINT_PATH),
                    "restore",
                    "--root",
                    str(continuity_root),
                    "--checkpoint-id",
                    created["checkpoint_id"],
                    "--target",
                    str(source),
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            restored = json.loads(restore_result.stdout)
            self.assertEqual(restored["state"], "restored")
            self.assertEqual(source.read_bytes(), b"before")


if __name__ == "__main__":
    unittest.main()
