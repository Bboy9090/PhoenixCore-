# PR41A Physical USB Boot Matrix

## Artifact Under Test

- ISO: `iso/outputs/bwos-home.iso`
- SHA256: `463e8273b24ef851b64c5b7388ebaafe639f6632b62ddea64e81aff7f43f5686`
- Size bytes: `2276368384`

## Rules

- Read-only boot validation only.
- No installer execution.
- No internal disk formatting.
- No partitioning.
- No repair tools.
- No PASS without desktop evidence.

## Target Order

| Order | Slot | Target | Status | Evidence |
| ---: | --- | --- | --- | --- |
| 1 | `HW-01` | Standard UEFI PC | `PHYSICAL_BOOT_UNTESTED` | `docs/release/PR41A_HW01_EXECUTION_RECORD.md` |
| 2 | `HW-06` | Ryzen Desktop | `PHYSICAL_BOOT_UNTESTED` | pending |
| 3 | `HW-03` | Intel Mac | `PHYSICAL_BOOT_UNTESTED` | pending |
| 4 | `HW-04` | T2 Mac | `PHYSICAL_BOOT_UNTESTED` | pending |
| 5 | `HW-05` | Apple Silicon Observation | `PHYSICAL_BOOT_UNTESTED` | pending |

`HW-02` Legacy BIOS is deferred and not in the current execution order.

## Classification Values

- `PHYSICAL_BOOT_PASS`
- `PHYSICAL_BOOT_PARTIAL`
- `PHYSICAL_BOOT_FAIL_NO_PICKER`
- `PHYSICAL_BOOT_FAIL_BOOTLOADER`
- `PHYSICAL_BOOT_FAIL_KERNEL`
- `PHYSICAL_BOOT_FAIL_DESKTOP`
- `PHYSICAL_BOOT_UNTESTED`

## Current Result

No physical hardware slot has completed validation for the current artifact. Release candidate status remains blocked.
