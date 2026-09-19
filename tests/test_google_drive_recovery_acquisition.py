import hashlib
import importlib.util
import io
import json
import tempfile
import unittest
from pathlib import Path

MODULE_PATH = (
    Path(__file__).resolve().parent.parent
    / "scripts"
    / "hardware"
    / "acquire_google_drive_recovery.py"
)
SPEC = importlib.util.spec_from_file_location("drive_acquisition", MODULE_PATH)
assert SPEC and SPEC.loader
drive = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(drive)


class FakeResponse:
    def __init__(self, body, status=200, headers=None):
        self._stream = io.BytesIO(body)
        self.status = status
        self.headers = headers or {}

    def read(self, size=-1):
        return self._stream.read(size)

    def getcode(self):
        return self.status

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


class GoogleDriveAcquisitionTests(unittest.TestCase):
    def test_token_is_required_from_environment(self):
        with self.assertRaises(drive.DriveAcquisitionError):
            drive.require_token({})

    def test_folder_listing_is_read_only_and_paginates(self):
        requests = []

        def opener(request):
            requests.append(request)
            query = request.full_url
            if "pageToken=next" in query:
                payload = {"files": [{"id": "b", "name": "backup.vhd"}]}
            else:
                payload = {
                    "files": [{"id": "a", "name": "Catalog"}],
                    "nextPageToken": "next",
                }
            return FakeResponse(json.dumps(payload).encode())

        result = drive.list_folder("folder_123", token="secret", opener=opener)
        self.assertEqual(2, result["file_count"])
        self.assertTrue(result["read_only"])
        self.assertFalse(result["cloud_original_modified"])
        self.assertEqual(["GET", "GET"], [request.method for request in requests])
        self.assertTrue(
            all(request.get_header("Authorization") == "Bearer secret" for request in requests)
        )

    def test_complete_download_verifies_provider_md5_and_hashes_sha256(self):
        content = b"conectix" + (b"x" * 8192)
        md5 = hashlib.md5(content).hexdigest()
        calls = []

        def opener(request):
            calls.append(request)
            if "alt=media" in request.full_url:
                return FakeResponse(content, status=200)
            metadata = {
                "id": "file_123",
                "name": "backup.vhd",
                "mimeType": "application/octet-stream",
                "size": str(len(content)),
                "md5Checksum": md5,
                "capabilities": {"canDownload": True},
            }
            return FakeResponse(json.dumps(metadata).encode())

        with tempfile.TemporaryDirectory() as tmpdir:
            destination = Path(tmpdir) / "backup.vhd"
            result = drive.download_file(
                "file_123", destination, token="secret", opener=opener
            )
            self.assertTrue(result["complete"])
            self.assertTrue(result["provider_md5_verified"])
            self.assertTrue(result["identity_lock_ready"])
            self.assertFalse(result["recovery_eligible"])
            self.assertEqual(\n                hashlib.sha256(content).hexdigest(), result["observed_sha256"]\n            )
            self.assertEqual(content, destination.read_bytes())
            self.assertFalse(destination.with_name("backup.vhd.partial").exists())
            self.assertEqual(["GET", "GET"], [request.method for request in calls])

    def test_resume_requires_server_to_honor_range(self):
        content = b"0123456789"
        md5 = hashlib.md5(content).hexdigest()

        def opener(request):
            if "alt=media" not in request.full_url:
                metadata = {
                    "id": "file_123",
                    "name": "backup.vhd",
                    "mimeType": "application/octet-stream",
                    "size": str(len(content)),
                    "md5Checksum": md5,
                    "capabilities": {"canDownload": True},
                }
                return FakeResponse(json.dumps(metadata).encode())
            self.assertEqual("bytes=4-", request.get_header("Range"))
            return FakeResponse(
                content[4:],
                status=206,
                headers={"Content-Range": "bytes 4-9/10"},
            )

        with tempfile.TemporaryDirectory() as tmpdir:
            destination = Path(tmpdir) / "backup.vhd"
            destination.with_name("backup.vhd.partial").write_bytes(content[:4])
            result = drive.download_file(
                "file_123", destination, token="secret", opener=opener
            )
            self.assertEqual(4, result["resume_offset_bytes"])
            self.assertEqual(content, destination.read_bytes())

    def test_resume_fails_closed_if_range_is_ignored(self):
        content = b"0123456789"

        def opener(request):
            if "alt=media" not in request.full_url:
                metadata = {
                    "id": "file_123",
                    "name": "backup.vhd",
                    "mimeType": "application/octet-stream",
                    "size": str(len(content)),
                    "capabilities": {"canDownload": True},
                }
                return FakeResponse(json.dumps(metadata).encode())
            return FakeResponse(content, status=200)

        with tempfile.TemporaryDirectory() as tmpdir:
            destination = Path(tmpdir) / "backup.vhd"
            partial = destination.with_name("backup.vhd.partial")
            partial.write_bytes(content[:4])
            with self.assertRaisesRegex(
                drive.DriveAcquisitionError, "resume byte range"
            ):
                drive.download_file(
                    "file_123", destination, token="secret", opener=opener
                )
            self.assertEqual(content[:4], partial.read_bytes())

    def test_download_permission_and_workspace_files_are_blocked(self):
        with self.assertRaises(drive.DriveAcquisitionError):
            drive.validate_download_metadata(
                {
                    "name": "native",
                    "mimeType": "application/vnd.google-apps.document",
                    "size": "10",
                    "capabilities": {"canDownload": True},
                }
            )
        with self.assertRaises(drive.DriveAcquisitionError):
            drive.validate_download_metadata(
                {
                    "name": "backup.vhd",
                    "mimeType": "application/octet-stream",
                    "size": "10",
                    "capabilities": {"canDownload": False},
                }
            )

    def test_malformed_file_id_is_rejected_before_network(self):
        with self.assertRaises(drive.DriveAcquisitionError):
            drive.require_file_id("../../secret")


if __name__ == "__main__":
    unittest.main()
