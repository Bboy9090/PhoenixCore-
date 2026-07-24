from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPAIR_PATH = ROOT / "scripts" / "recovery" / "checkpointed_repair.py"

spec = importlib.util.spec_from_file_location("checkpointed_repair", REPAIR_PATH)
repair_module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
sys.modules["checkpointed_repair"] = repair_module
spec.loader.exec_module(repair_module)


class CheckpointedRepairTests(unittest.TestCase):
    def test_successful_checkpointed_repair(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            target = root / "target.txt"
            replacement = root / "replacement.txt"
            target.write_text("old", encoding="utf-8")
            replacement.write_text("new", encoding="utf-8")
            coordinator = repair_module.RecoveryCoordinator(
                repair_module.checkpoint_module.CheckpointStore(root / "checkpoints"),
                repair_module.ledger_module.EvidenceLedger(root / "evidence.jsonl"),
            )
            manifest = repair_module.PayloadManifest.from_file(replacement)

            result = coordinator.repair_file(
                target,
                replacement,
                manifest,
                repair_id=4,
            )

            self.assertEqual(result.status, repair_module.RecoveryStatus.COMPLETED)
            self.assertEqual(target.read_text(encoding="utf-8"), "new")
            records = coordinator.evidence_ledger.verify()
            self.assertEqual(
                [record.event_type for record in records],
                ["RECOVERY.CHECKPOINT_CREATED", "RECOVERY.REPAIR_VERIFIED"],
            )

    def test_post_replace_corruption_rolls_back_to_original_bytes(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            target = root / "target.txt"
            replacement = root / "replacement.txt"
            target.write_text("old", encoding="utf-8")
            replacement.write_text("new", encoding="utf-8")
            coordinator = repair_module.RecoveryCoordinator(
                repair_module.checkpoint_module.CheckpointStore(root / "checkpoints"),
                repair_module.ledger_module.EvidenceLedger(root / "evidence.jsonl"),
            )
            manifest = repair_module.PayloadManifest.from_file(replacement)

            def corrupt(path: Path) -> None:
                path.write_text("corrupt", encoding="utf-8")

            result = coordinator.repair_file(
                target,
                replacement,
                manifest,
                repair_id=5,
                after_replace=corrupt,
            )

            self.assertEqual(result.status, repair_module.RecoveryStatus.ROLLED_BACK)
            self.assertEqual(target.read_text(encoding="utf-8"), "old")
            records = coordinator.evidence_ledger.verify()
            self.assertEqual(records[-1].event_type, "RECOVERY.ROLLBACK_VERIFIED")

    def test_invalid_payload_rejected_before_checkpoint_or_mutation(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            target = root / "target.txt"
            replacement = root / "replacement.txt"
            target.write_text("old", encoding="utf-8")
            replacement.write_text("new", encoding="utf-8")
            coordinator = repair_module.RecoveryCoordinator(
                repair_module.checkpoint_module.CheckpointStore(root / "checkpoints"),
                repair_module.ledger_module.EvidenceLedger(root / "evidence.jsonl"),
            )
            manifest = repair_module.PayloadManifest(
                path=str(replacement),
                size_bytes=999,
                sha256="a" * 64,
            )

            with self.assertRaises(repair_module.RecoveryError):
                coordinator.repair_file(target, replacement, manifest, repair_id=6)

            self.assertEqual(target.read_text(encoding="utf-8"), "old")
            self.assertFalse((root / "checkpoints").exists())
            self.assertEqual(coordinator.evidence_ledger.verify(), [])

    def test_rejects_directory_target_and_symlink_payload(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            target = root / "target.txt"
            replacement = root / "replacement.txt"
            link = root / "replacement-link.txt"
            target.write_text("old", encoding="utf-8")
            replacement.write_text("new", encoding="utf-8")
            link.symlink_to(replacement)
            coordinator = repair_module.RecoveryCoordinator(
                repair_module.checkpoint_module.CheckpointStore(root / "checkpoints"),
                repair_module.ledger_module.EvidenceLedger(root / "evidence.jsonl"),
            )
            manifest = repair_module.PayloadManifest.from_file(replacement)

            with self.assertRaises(repair_module.RecoveryError):
                coordinator.repair_file(root, replacement, manifest, repair_id=7)
            with self.assertRaises(repair_module.RecoveryError):
                coordinator.repair_file(target, link, manifest, repair_id=7)

    def test_cli_repair_round_trip(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            target = root / "target.txt"
            replacement = root / "replacement.txt"
            target.write_text("old", encoding="utf-8")
            replacement.write_text("new", encoding="utf-8")

            completed = subprocess.run(
                [
                    sys.executable,
                    str(REPAIR_PATH),
                    "--checkpoint-root",
                    str(root / "checkpoints"),
                    "--ledger",
                    str(root / "evidence.jsonl"),
                    "--target",
                    str(target),
                    "--replacement",
                    str(replacement),
                    "--repair-id",
                    "8",
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            result = json.loads(completed.stdout)
            self.assertEqual(result["status"], "completed")
            self.assertEqual(target.read_text(encoding="utf-8"), "new")


if __name__ == "__main__":
    unittest.main()
