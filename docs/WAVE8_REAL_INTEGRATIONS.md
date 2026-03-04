# Wave 8: Real Integrations (No False/Placeholder)

False or placeholder integrations converted to real implementations.

## Completed

| Area | Change |
|------|--------|
| **Windows payload staging** | Extract ISO via 7z/bsdtar, copy EFI/BOOT and sources to EFI/Windows partitions |
| **Linux payload staging** | Extract ISO, copy vmlinuz and initrd to EFI/BOOT |
| **macOS payload staging** | Copy installer .dmg/.app to macOS partition when mounted |
| **Recipe compatibility** | Uses `get_compatible_profiles()` and hardware profile matching |
| **Patch config loading** | Load from `configs/patches/` and `~/.bootforge/configs/patches/` YAML files |
| **StorageBuilderEngine** | `create_patch_plan` accepts optional `detected_hardware` from HardwareDetector |
| **Driver matching** | PCI vendor hints (VEN_8086=Intel, VEN_10EC=Realtek) in `_driver_matches_hardware` |
| **Consent comments** | Clarified BYPASS vs interactive prompt flow |

## ISO Extraction

- Uses `7z x` or `bsdtar -xf` (whichever is available)
- Extracts full ISO to temp dir, then copies required paths
- Windows: EFI/BOOT/*, sources/*
- Linux: casper/vmlinuz, casper/initrd, install/vmlinuz, etc.

## Patch Config Paths

- `configs/patches/*.yaml` (project root)
- `~/.bootforge/configs/patches/*.yaml`
