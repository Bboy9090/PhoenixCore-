import unittest

from scripts.hardware.assess_windows_media_boot_compatibility import assess_boot_compatibility


class WindowsBootCompatibilityTests(unittest.TestCase):
    def assess(self, source=None, computer=None):
        media = {"architecture": "x64", "uefi_boot_files": ["EFI/Boot/bootx64.efi"], "required_bytes": 100}
        target = {"firmware_architecture": "x64", "firmware_mode": "uefi", "secure_boot_enabled": False, "media_capacity_bytes": 200}
        media.update(source or {})
        target.update(computer or {})
        return assess_boot_compatibility(media, target)

    def test_compatible_facts_never_prove_boot_or_authorize_write(self):
        result = self.assess({"copy_verified": True, "boot_proven": True})
        self.assertEqual(result["assessment"], "reported_facts_compatible")
        self.assertFalse(result["boot_proven"])
        self.assertFalse(result["write_authorized"])
        self.assertFalse(result["system_mutations_performed"])

    def test_unknowns_stay_unresolved(self):
        result = assess_boot_compatibility({}, {})
        self.assertEqual(result["assessment"], "unresolved")
        self.assertIn("selected_image_architecture_unknown", result["unresolved_reasons"])
        self.assertIn("computer_firmware_mode_unknown", result["unresolved_reasons"])
        self.assertIn("secure_boot_state_unknown", result["unresolved_reasons"])

    def test_architecture_mismatch_is_blocked(self):
        self.assertIn("image_firmware_architecture_mismatch", self.assess(computer={"firmware_architecture": "arm64"})["block_reasons"])

    def test_missing_loader_is_blocked(self):
        self.assertIn("matching_uefi_fallback_loader_missing", self.assess({"uefi_boot_files": []})["block_reasons"])

    def test_secure_boot_cannot_be_certified_by_caller_boolean(self):
        result = self.assess({"signed": True, "secure_boot_accepted": True}, {"secure_boot_enabled": True})
        self.assertEqual(result["assessment"], "unresolved")

    def test_bios_does_not_inherit_uefi_readiness(self):
        self.assertEqual(self.assess(computer={"firmware_mode": "bios"})["assessment"], "blocked")

    def test_capacity_and_boolean_numeric_values(self):
        self.assertIn("media_capacity_insufficient", self.assess(computer={"media_capacity_bytes": 99})["block_reasons"])
        self.assertIn("source_capacity_requirement_invalid", self.assess({"required_bytes": True})["block_reasons"])

    def test_all_supported_loader_architectures(self):
        for arch, loader in (("x64", "bootx64"), ("x86", "bootia32"), ("arm64", "bootaa64")):
            with self.subTest(arch=arch):
                result = self.assess({"architecture": arch, "uefi_boot_files": [f"efi\\boot\\{loader}.efi"]}, {"firmware_architecture": arch})
                self.assertEqual(result["assessment"], "reported_facts_compatible")


if __name__ == "__main__":
    unittest.main()
