import importlib.util
import io
import json
import sys
import unittest
import urllib.parse
from pathlib import Path

MODULE_DIR = (
    Path(__file__).resolve().parent.parent / "scripts" / "hardware"
)
if str(MODULE_DIR) not in sys.path:
    sys.path.insert(0, str(MODULE_DIR))

MODULE_PATH = MODULE_DIR / "google_drive_picker_recovery.py"
SPEC = importlib.util.spec_from_file_location("drive_picker", MODULE_PATH)
assert SPEC and SPEC.loader
picker = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(picker)


class FakeResponse:
    def __init__(self, payload):
        self._stream = io.BytesIO(json.dumps(payload).encode("utf-8"))

    def read(self, size=-1):
        return self._stream.read(size)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


class GoogleDrivePickerTests(unittest.TestCase):
    def test_client_id_is_required_and_must_be_desktop_google_id(self):
        with self.assertRaises(picker.PickerError):
            picker.require_client_id({})
        with self.assertRaises(picker.PickerError):
            picker.require_client_id({picker.CLIENT_ID_ENV: "not-a-client"})
        value = "123.apps.googleusercontent.com"
        self.assertEqual(
            value,
            picker.require_client_id({picker.CLIENT_ID_ENV: value}),
        )

    def test_authorization_url_is_single_scope_picker_with_pkce(self):
        verifier = "a" * 64
        url = picker.build_picker_url(
            client_id="123.apps.googleusercontent.com",
            redirect_uri="http://127.0.0.1:49152/oauth2callback",
            state="state-token",
            challenge=picker.code_challenge(verifier),
        )
        query = urllib.parse.parse_qs(urllib.parse.urlsplit(url).query)
        self.assertEqual([picker.DRIVE_FILE_SCOPE], query["scope"])
        self.assertEqual(["S256"], query["code_challenge_method"])
        self.assertEqual(["state-token"], query["state"])
        self.assertEqual(["consent"], query["prompt"])
        self.assertEqual(["true"], query["trigger_onepick"])
        self.assertEqual(["false"], query["allow_multiple"])
        self.assertNotIn("client_secret", query)

    def test_non_loopback_redirect_is_rejected(self):
        with self.assertRaisesRegex(picker.PickerError, "loopback"):
            picker.build_picker_url(
                client_id="123.apps.googleusercontent.com",
                redirect_uri="https://example.com/callback",
                state="state-token",
                challenge="challenge",
            )

    def test_callback_requires_state_single_file_and_drive_file_scope(self):
        query = urllib.parse.urlencode(
            {
                "state": "expected",
                "code": "authorization-code",
                "picked_file_ids": "file_123",
                "scope": picker.DRIVE_FILE_SCOPE,
            }
        )
        result = picker.parse_picker_callback(query, "expected")
        self.assertEqual("file_123", result["file_id"])
        with self.assertRaisesRegex(picker.PickerError, "state"):
            picker.parse_picker_callback(query, "wrong")

        multiple = query.replace("file_123", "file_123%2Cfile_456")
        with self.assertRaisesRegex(picker.PickerError, "exactly one"):
            picker.parse_picker_callback(multiple, "expected")

        broad = query.replace(
            urllib.parse.quote_plus(picker.DRIVE_FILE_SCOPE),
            urllib.parse.quote_plus(
                "https://www.googleapis.com/auth/drive.readonly"
            ),
        )
        with self.assertRaisesRegex(picker.PickerError, "scope"):
            picker.parse_picker_callback(broad, "expected")

    def test_token_exchange_uses_pkce_without_client_secret(self):
        requests = []

        def opener(request):
            requests.append(request)
            return FakeResponse(
                {
                    "access_token": "short-lived-token",
                    "token_type": "Bearer",
                    "scope": picker.DRIVE_FILE_SCOPE,
                }
            )

        token = picker.exchange_code(
            client_id="123.apps.googleusercontent.com",
            code="authorization-code",
            verifier="a" * 64,
            redirect_uri="http://127.0.0.1:49152/oauth2callback",
            opener=opener,
        )
        self.assertEqual("short-lived-token", token)
        self.assertEqual(1, len(requests))
        request = requests[0]
        self.assertEqual("POST", request.method)
        form = urllib.parse.parse_qs(request.data.decode("ascii"))
        self.assertEqual(["authorization_code"], form["grant_type"])
        self.assertEqual(["a" * 64], form["code_verifier"])
        self.assertNotIn("client_secret", form)

    def test_token_exchange_rejects_broader_scope(self):
        def opener(_request):
            return FakeResponse(
                {
                    "access_token": "token",
                    "token_type": "Bearer",
                    "scope": "https://www.googleapis.com/auth/drive.readonly",
                }
            )

        with self.assertRaisesRegex(picker.PickerError, "scope"):
            picker.exchange_code(
                client_id="123.apps.googleusercontent.com",
                code="authorization-code",
                verifier="a" * 64,
                redirect_uri="http://127.0.0.1:49152/oauth2callback",
                opener=opener,
            )

    def test_picker_forwards_progress_and_cancel_paths(self):
        source = Path(picker.__file__).read_text(encoding="utf-8")
        self.assertIn("progress_file=progress_file", source)
        self.assertIn("cancel_file=cancel_file", source)
        self.assertIn('"--progress-file"', source)
        self.assertIn('"--cancel-file"', source)

    def test_local_name_neutralizes_path_separators(self):
        name = picker.safe_local_name(
            '../Windows\\system:bad*name?.vhd', "file_1234567890"
        )
        for character in '<>:"/\\|?*':
            self.assertNotIn(character, name)
        self.assertTrue(name.endswith("system_bad_name_.vhd"))


if __name__ == "__main__":
    unittest.main()
