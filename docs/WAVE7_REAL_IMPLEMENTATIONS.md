# Wave 7: Real Implementations (No Placeholders)

Items converted from TODO/placeholder to real implementations.

## Completed

| Item | Location | Change |
|------|----------|--------|
| Timestamp | hardware_profiles, patch_config_loader | `time.time()` instead of `1234567890.0` |
| Consent checking | patch_pipeline._has_sufficient_consent | Reads safety_validator._consent_records, BOOTFORGE_PATCH_CONSENT_LEVEL env |
| Device state capture | error_prevention_recovery._capture_device_state | Runs sfdisk --dump (Linux) or diskutil list (macOS) |
| Device state restore | error_prevention_recovery._restore_device_state | Runs sfdisk restore from saved dump |
| Windows/Linux tabs | stepper_wizard_widget | Removed NotImplementedError; all 3 platforms load profiles |
| macOS log message | macos_provider | "dry-run completed" instead of "simulated" |
| Registry bypass comment | win_patch_engine | Clarified DISM limitation and offline approach |
| Main window icon | main_window | Removed outdated "placeholder" comment (uses icon_manager) |
| Wizard step comment | stepper_wizard | Removed placeholder/TODO; HardwareDetectionStep is real |
| Summary labels | stepper_wizard_widget | Comment: "populated from wizard state in load_step_data" |

## Environment Variables

- `BOOTFORGE_PATCH_CONSENT_LEVEL=expert` – Pre-approve dangerous patch consent (CI/automation)
- `BOOTFORGE_PATCH_CONSENT_LEVEL=informed` – Pre-approve DANGEROUS-level only

## Restore Behavior

- **Linux**: `sfdisk --dump` → file; restore via `sfdisk <device` with dump stdin
- **macOS**: `diskutil list -plist` captured; full restore not automated (manual diskutil)
- **Windows**: Metadata only; manual diskpart required
