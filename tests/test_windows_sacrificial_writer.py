import io
import json
import os
import tempfile
import unittest
from pathlib import Path

from scripts.hardware import capture_windows_drive_evidence as drive_evidence
from scripts.hardware import write_windows_sacrificial_drive as writer


class CorruptingReadback(io.BytesIO):
    def __init__(self, initial_bytes: bytes):
        super().__init__(initial_bytes)
        self._readback_started = False

    def seek(self, offset, whence=0):
        result = super().seek(offset, whence)
        if offset == 0 and self.tell() == 0 and len(self.getvalue()) > 0:
            self._readback_started = True
        return result

    def read(self, size=-1):
        data = super().read(size)
        if self._readback_started and data:
            return bytes([data[0] ^ 0xFF]) + data[1:]
        return data


class ShortWriteBuffer(io.BytesIO):
    def write(self, data):
        if len(data) <= 1:
            return super().write(data)
        return super().write(data[:-1])


class UnplugAfterFirstWrite(io.BytesIO):
    def __init__(self, initial_bytes: bytes):
        super().__init__(initial_bytes)
        self._writes = 0

    def write(self, data):
        if self._writes > 0:
            raise OSError("simulated device removal")
        self._writes += 1
        return super().write(data)


class EnospcAfterFirstWrite(io.BytesIO):
    def __init__(self, initial_bytes: bytes):
        super().__init__(initial_bytes)
        self._writes = 0

    def write(self, data):
        if self._writes > 0:
            raise OSError(28, "No space left on device")
        self._writes += 1
        return super().write(data)


class WindowsSacrificialWriterTests(unittest.TestCase):
    def setUp(self):
        fixture_path = Path(__file__).parent / "fixtures" / "windows_disk_usb.json"
        self.raw_disk = json.loads(fixture_path.read_text(encoding="utf-8"))
        self.target = r"\\.\PHYSICALDRIVE1"
        self.evidence = drive_evidence.build_receipt(
            target=self.target,
            raw_disk=self.raw_disk,
            evidence_source="live",
            source_commit="a" * 40,
            captured_at="2026-07-24T02:00:00Z",
        )
    def _authorization_for(self, image):
        return writer.expected_authorization(
            self.target,
            self.evidence["disk"]["identity_sha256"],
            self.evidence["disk"]["size_bytes"],
            writer.file_sha256(image),
        )

    def _write_receipt(self, directory: str, receipt=None) -> Path:
        path = Path(directory) / "drive-evidence.json"
        path.write_text(
            json.dumps(receipt or self.evidence, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        return path

    def _query_disk(self, number):
        self.assertEqual(1, number)
        return dict(self.raw_disk)

    def _resolve_source_disk(self, source_path):
        self.assertTrue(source_path)
        return {
            "schema": "phoenix_key.windows_source_disk.v1",
            "source_path": source_path,
            "drive_letter": "E",
            "disk_number": 2,
            "partition_number": 1,
            "physical_target": r"\\.\PHYSICALDRIVE2",
            "resolved": True,
            "read_only": True,
        }

    def test_live_receipt_loads_and_fixture_receipt_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            live_path = self._write_receipt(tmpdir)
            loaded = writer.load_drive_evidence(live_path)
            self.assertEqual(
                self.evidence["disk"]["identity_sha256"],
                loaded["disk"]["identity_sha256"],
            )

            fixture = drive_evidence.build_receipt(
                target=self.target,
                raw_disk=self.raw_disk,
                evidence_source="fixture",
                source_commit="b" * 40,
                captured_at="2026-07-24T02:00:00Z",
            )
            fixture_path = self._write_receipt(tmpdir, fixture)
            with self.assertRaises(writer.WriteGateError):
                writer.load_drive_evidence(fixture_path)

    def test_tampered_drive_receipt_is_rejected(self):
        tampered = json.loads(json.dumps(self.evidence))
        tampered["disk"]["size_bytes"] += 1
        with tempfile.TemporaryDirectory() as tmpdir:
            path = self._write_receipt(tmpdir, tampered)
            with self.assertRaises(writer.WriteGateError):
                writer.load_drive_evidence(path)

    def test_valid_request_binds_image_target_identity_and_byte_cap(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            image = Path(tmpdir) / "image.bin"
            image.write_bytes(b"ARCWYRE" * 1024)
            plan = writer.validate_write_request(
                evidence=self.evidence,
                image_path=image,
                target=self.target,
                authorization=self._authorization_for(image),
                source_commit="c" * 40,
                execute=True,
                environment={writer.UNLOCK_ENV: writer.UNLOCK_VALUE},
                admin=True,
                query_disk=self._query_disk,
                resolve_source_disk=self._resolve_source_disk,
            )

            self.assertEqual(image.stat().st_size, plan["byte_cap"])
            self.assertEqual(image.stat().st_size, plan["image_size_bytes"])
            self.assertEqual(writer.file_sha256(image), plan["image_sha256"])
            self.assertEqual(
                self.evidence["disk"]["identity_sha256"],
                plan["identity_sha256"],
            )

    def test_request_rejects_missing_unlock(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            image = Path(tmpdir) / "image.bin"
            image.write_bytes(b"x")
            with self.assertRaisesRegex(writer.WriteGateError, "environment unlock"):
                writer.validate_write_request(
                    evidence=self.evidence,
                    image_path=image,
                    target=self.target,
                    authorization=self._authorization_for(image),
                    source_commit="d" * 40,
                    execute=True,
                    environment={},
                    admin=True,
                    query_disk=self._query_disk,
                    resolve_source_disk=self._resolve_source_disk,
                )

    def test_request_rejects_wrong_authorization_and_missing_execute(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            image = Path(tmpdir) / "image.bin"
            image.write_bytes(b"x")
            common = {
                "evidence": self.evidence,
                "image_path": image,
                "target": self.target,
                "source_commit": "e" * 40,
                "environment": {writer.UNLOCK_ENV: writer.UNLOCK_VALUE},
                "admin": True,
                "query_disk": self._query_disk,
                "resolve_source_disk": self._resolve_source_disk,
            }
            with self.assertRaisesRegex(writer.WriteGateError, "authorization"):
                writer.validate_write_request(
                    authorization="I AUTHORIZE SOMETHING VAGUE",
                    execute=True,
                    **common,
                )
            with self.assertRaisesRegex(writer.WriteGateError, "--execute"):
                writer.validate_write_request(
                    authorization=self._authorization_for(image),
                    execute=False,
                    **common,
                )

    def test_request_rejects_source_target_collision(self):
        def same_disk(source_path):
            record = self._resolve_source_disk(source_path)
            record["disk_number"] = 1
            record["physical_target"] = self.target
            return record

        with tempfile.TemporaryDirectory() as tmpdir:
            image = Path(tmpdir) / "image.bin"
            image.write_bytes(b"x")
            with self.assertRaisesRegex(writer.WriteGateError, "same physical device"):
                writer.validate_write_request(
                    evidence=self.evidence,
                    image_path=image,
                    target=self.target,
                    authorization=self._authorization_for(image),
                    source_commit="9" * 40,
                    execute=True,
                    environment={writer.UNLOCK_ENV: writer.UNLOCK_VALUE},
                    admin=True,
                    query_disk=self._query_disk,
                    resolve_source_disk=same_disk,
                )

    def test_request_rejects_identity_drift(self):
        def drifted_query(number):
            drifted = dict(self.raw_disk)
            drifted["SerialNumber"] = "DIFFERENT-DEVICE"
            return drifted

        with tempfile.TemporaryDirectory() as tmpdir:
            image = Path(tmpdir) / "image.bin"
            image.write_bytes(b"x")
            with self.assertRaisesRegex(writer.WriteGateError, "identity"):
                writer.validate_write_request(
                    evidence=self.evidence,
                    image_path=image,
                    target=self.target,
                    authorization=self._authorization_for(image),
                    source_commit="f" * 40,
                    execute=True,
                    environment={writer.UNLOCK_ENV: writer.UNLOCK_VALUE},
                    admin=True,
                    query_disk=drifted_query,
                    resolve_source_disk=self._resolve_source_disk,
                )

    def test_prewrite_recheck_rejects_source_byte_mutation(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            image = Path(tmpdir) / "image.bin"
            image.write_bytes(b"original-source")
            plan = writer.validate_write_request(
                evidence=self.evidence,
                image_path=image,
                target=self.target,
                authorization=self._authorization_for(image),
                source_commit="7" * 40,
                execute=True,
                environment={writer.UNLOCK_ENV: writer.UNLOCK_VALUE},
                admin=True,
                query_disk=self._query_disk,
                resolve_source_disk=self._resolve_source_disk,
            )
            image.write_bytes(b"mutated-source!")
            with self.assertRaisesRegex(writer.WriteGateError, "SHA-256 changed"):
                writer.revalidate_source_before_raw_open(
                    plan=plan,
                    image_path=image,
                    resolve_source_disk=self._resolve_source_disk,
                )

    def test_prewrite_recheck_rejects_source_device_change(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            image = Path(tmpdir) / "image.bin"
            image.write_bytes(b"stable-source")
            plan = writer.validate_write_request(
                evidence=self.evidence,
                image_path=image,
                target=self.target,
                authorization=self._authorization_for(image),
                source_commit="8" * 40,
                execute=True,
                environment={writer.UNLOCK_ENV: writer.UNLOCK_VALUE},
                admin=True,
                query_disk=self._query_disk,
                resolve_source_disk=self._resolve_source_disk,
            )

            def moved_source(source_path):
                record = self._resolve_source_disk(source_path)
                record["disk_number"] = 3
                record["physical_target"] = r"\\.\PHYSICALDRIVE3"
                return record

            with self.assertRaisesRegex(writer.WriteGateError, "physical device changed"):
                writer.revalidate_source_before_raw_open(
                    plan=plan,
                    image_path=image,
                    resolve_source_disk=moved_source,
                )

    def test_file_backed_write_and_full_readback_pass(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            image = Path(tmpdir) / "image.bin"
            target = Path(tmpdir) / "target.bin"
            content = os.urandom((2 * 1024 * 1024) + 137)
            image.write_bytes(content)
            target.write_bytes(b"\x00" * (len(content) + 4096))

            with target.open("r+b", buffering=0) as stream:
                result = writer.write_and_verify(
                    image_path=image,
                    target_stream=stream,
                    byte_cap=len(content),
                    chunk_size=65536,
                )

            self.assertEqual(len(content), result["bytes_written"])
            self.assertEqual(len(content), result["bytes_read_back"])
            self.assertEqual(result["source_sha256"], result["readback_sha256"])
            self.assertTrue(result["verification_passed"])
            self.assertEqual(content, target.read_bytes()[: len(content)])

    def test_short_write_and_corrupt_readback_fail(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            image = Path(tmpdir) / "image.bin"
            image.write_bytes(b"0123456789")

            with self.assertRaisesRegex(writer.WriteGateError, "Short write"):
                writer.write_and_verify(
                    image_path=image,
                    target_stream=ShortWriteBuffer(b"\x00" * 32),
                    byte_cap=10,
                    chunk_size=10,
                )

            with self.assertRaisesRegex(writer.WriteGateError, "SHA-256"):
                writer.write_and_verify(
                    image_path=image,
                    target_stream=CorruptingReadback(b"\x00" * 32),
                    byte_cap=10,
                    chunk_size=10,
                )

    def test_unplug_failure_is_nonresumable_and_receipted(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            image = Path(tmpdir) / "image.bin"
            image.write_bytes(b"0123456789")
            with self.assertRaises(writer.WriteInterruptedError) as caught:
                writer.write_and_verify(
                    image_path=image,
                    target_stream=UnplugAfterFirstWrite(b"\x00" * 32),
                    byte_cap=10,
                    chunk_size=4,
                )

            self.assertEqual("target-write", caught.exception.stage)
            self.assertEqual(4, caught.exception.bytes_written)

            plan = {
                "source_commit": "8" * 40,
                "target": self.target,
                "identity_sha256": self.evidence["disk"]["identity_sha256"],
                "target_size_bytes": self.evidence["disk"]["size_bytes"],
                "source_physical_target": r"\\.\PHYSICALDRIVE2",
                "source_target_distinct": True,
                "image_path": str(image),
                "image_size_bytes": 10,
                "image_sha256": writer.file_sha256(image),
                "byte_cap": 10,
            }
            receipt = writer.build_failure_result(
                plan=plan,
                error=caught.exception,
                started_at="2026-09-17T22:10:00Z",
                failed_at="2026-09-17T22:10:01Z",
            )
            self.assertEqual("hardware-write-interrupted", receipt["classification"])
            self.assertEqual("target-write", receipt["failure_stage"])
            self.assertEqual(4, receipt["bytes_written"])
            self.assertFalse(receipt["resume_allowed"])
            self.assertTrue(receipt["restart_requires_fresh_source_identity"])
            self.assertTrue(receipt["restart_requires_fresh_target_identity"])
            self.assertFalse(receipt["verification_passed"])
            self.assertEqual(64, len(receipt["receipt_sha256"]))

    def test_enospc_failure_is_nonresumable_and_receipted(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            image = Path(tmpdir) / "image.bin"
            image.write_bytes(b"0123456789")
            with self.assertRaises(writer.WriteInterruptedError) as caught:
                writer.write_and_verify(
                    image_path=image,
                    target_stream=EnospcAfterFirstWrite(b"\x00" * 32),
                    byte_cap=10,
                    chunk_size=4,
                )

            self.assertEqual("target-write", caught.exception.stage)
            self.assertIn("No space left", str(caught.exception))
            plan = {
                "source_commit": "9" * 40,
                "target": self.target,
                "identity_sha256": self.evidence["disk"]["identity_sha256"],
                "target_size_bytes": self.evidence["disk"]["size_bytes"],
                "source_physical_target": r"\\.\PHYSICALDRIVE2",
                "source_target_distinct": True,
                "prewrite_source_recheck": {"source_sha256": writer.file_sha256(image)},
                "prewrite_target_recheck": {"identity_sha256": self.evidence["disk"]["identity_sha256"]},
                "image_path": str(image),
                "image_size_bytes": 10,
                "image_sha256": writer.file_sha256(image),
                "byte_cap": 10,
            }
            receipt = writer.build_failure_result(
                plan=plan,
                error=caught.exception,
                started_at="2026-09-19T14:00:00Z",
                failed_at="2026-09-19T14:00:01Z",
            )
            self.assertEqual("hardware-write-interrupted", receipt["classification"])
            self.assertFalse(receipt["resume_allowed"])
            self.assertEqual("target-write", receipt["failure_stage"])
            self.assertIn("No space left", receipt["error"])
            self.assertIsNotNone(receipt["prewrite_source_recheck"])
            self.assertIsNotNone(receipt["prewrite_target_recheck"])

    def test_success_receipt_requires_boot_test_next(self):
        plan = {
            "source_commit": "1" * 40,
            "target": self.target,
            "identity_sha256": self.evidence["disk"]["identity_sha256"],
            "target_size_bytes": self.evidence["disk"]["size_bytes"],
            "image_path": "C:\\lab\\arcwyre.iso",
            "image_size_bytes": 1024,
            "image_sha256": "2" * 64,
            "byte_cap": 1024,
        }
        result = {
            "bytes_expected": 1024,
            "bytes_written": 1024,
            "bytes_read_back": 1024,
            "source_sha256": "2" * 64,
            "readback_sha256": "2" * 64,
            "verification_passed": True,
        }
        receipt = writer.build_result(
            plan=plan,
            write_result=result,
            started_at="2026-07-24T02:00:00Z",
            completed_at="2026-07-24T02:01:00Z",
        )
        self.assertEqual("hardware-write-readback-verified", receipt["classification"])
        self.assertFalse(receipt["hardware_validated"])
        self.assertEqual("named-machine-boot-test", receipt["next_required_action"])
        self.assertEqual(64, len(receipt["receipt_sha256"]))

    def test_read_only_target_is_never_a_write_candidate(self):
        raw_disk = dict(self.raw_disk)
        raw_disk["IsReadOnly"] = True
        receipt = drive_evidence.build_receipt(
            target=self.target,
            raw_disk=raw_disk,
            evidence_source="live",
            source_commit="3" * 40,
        )
        self.assertFalse(receipt["disk"]["write_candidate"])
        self.assertIn("target-is-read-only", receipt["disk"]["write_block_reasons"])

    def test_non_external_bus_is_never_a_write_candidate(self):
        raw_disk = dict(self.raw_disk)
        raw_disk["BusType"] = "NVMe"
        receipt = drive_evidence.build_receipt(
            target=self.target,
            raw_disk=raw_disk,
            evidence_source="live",
            source_commit="4" * 40,
        )
        self.assertFalse(receipt["disk"]["write_candidate"])
        self.assertIn(
            "target-not-proven-external-removable",
            receipt["disk"]["write_block_reasons"],
        )


if __name__ == "__main__":
    unittest.main()
