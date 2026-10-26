"""Portable contracts for the native Windows volume-lock primitive."""

import importlib.util
from pathlib import Path
import unittest
from unittest.mock import call, patch


SPEC = importlib.util.spec_from_file_location(
    "windows_volume_lock",
    Path(__file__).resolve().parents[1]
    / "scripts/hardware/windows_volume_lock.py",
)
module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(module)


class WindowsVolumeLockTests(unittest.TestCase):
    def test_exact_drive_designator_required(self):
        self.assertEqual("G:", module.canonical_volume("g:"))
        for invalid in (None, "", "G:\\", r"\\.\G:", r"\\.\PHYSICALDRIVE2"):
            with self.subTest(invalid=invalid):
                with self.assertRaises(module.VolumeLockError):
                    module.canonical_volume(invalid)

    def test_context_locks_then_unlocks_and_closes(self):
        with patch.object(module, "_open_volume_handle", return_value=42), patch.object(
            module, "_device_control"
        ) as control, patch.object(module, "_close_handle") as close:
            with module.LockedWindowsVolume("G:") as lease:
                self.assertTrue(lease.locked)
                self.assertEqual(42, lease.handle)
            self.assertEqual(
                [
                    call(42, module.FSCTL_LOCK_VOLUME),
                    call(42, module.FSCTL_UNLOCK_VOLUME),
                ],
                control.call_args_list,
            )
            close.assert_called_once_with(42)

    def test_dismount_requires_and_preserves_lock(self):
        with self.assertRaises(module.VolumeLockError):
            module.LockedWindowsVolume("G:").dismount()
        with patch.object(module, "_open_volume_handle", return_value=7), patch.object(
            module, "_device_control"
        ) as control, patch.object(module, "_close_handle"):
            with module.LockedWindowsVolume("G:") as lease:
                lease.dismount()
                self.assertTrue(lease.locked)
                self.assertTrue(lease.dismounted)
            self.assertEqual(
                module.FSCTL_DISMOUNT_VOLUME, control.call_args_list[1].args[1]
            )

    def test_cancellation_before_open_or_after_lock_cleans_up(self):
        with patch.object(module, "_open_volume_handle") as open_handle:
            with self.assertRaisesRegex(module.VolumeLockError, "before opening"):
                module.LockedWindowsVolume("G:", lambda: True).__enter__()
            open_handle.assert_not_called()

        checks = 0

        def cancelled():
            nonlocal checks
            checks += 1
            return checks > 1

        with patch.object(module, "_open_volume_handle", return_value=9), patch.object(
            module, "_device_control"
        ) as control, patch.object(module, "_close_handle") as close:
            with self.assertRaisesRegex(module.VolumeLockError, "after locking"):
                module.LockedWindowsVolume("G:", cancelled).__enter__()
            self.assertEqual(
                module.FSCTL_UNLOCK_VOLUME, control.call_args_list[-1].args[1]
            )
            close.assert_called_once_with(9)

    def test_lock_failure_closes_handle_without_unlock(self):
        with patch.object(module, "_open_volume_handle", return_value=11), patch.object(
            module,
            "_device_control",
            side_effect=module.VolumeLockError("busy"),
        ) as control, patch.object(module, "_close_handle") as close:
            with self.assertRaisesRegex(module.VolumeLockError, "busy"):
                module.LockedWindowsVolume("G:").__enter__()
            control.assert_called_once_with(11, module.FSCTL_LOCK_VOLUME)
            close.assert_called_once_with(11)

    def test_close_failure_does_not_mask_active_operation_failure(self):
        with patch.object(module, "_open_volume_handle", return_value=13), patch.object(
            module, "_device_control"
        ) as control, patch.object(
            module, "_close_handle", side_effect=module.VolumeLockError("close failed")
        ):
            with self.assertRaisesRegex(RuntimeError, "operation failed"):
                with module.LockedWindowsVolume("G:"):
                    raise RuntimeError("operation failed")
            self.assertEqual(
                module.FSCTL_UNLOCK_VOLUME, control.call_args_list[-1].args[1]
            )


if __name__ == "__main__":
    unittest.main()
