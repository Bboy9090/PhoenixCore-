# PR41A Device Inventory

This ledger tracks real physical machines used for PR41A. It must not be filled with assumed or example hardware.

## Target Order

| Order | Slot | Target | Inventory status |
| ---: | --- | --- | --- |
| 1 | `HW-01` | Standard UEFI PC | `PENDING_REAL_HARDWARE_ENTRY` |
| 2 | `HW-06` | Ryzen Desktop | `PENDING_REAL_HARDWARE_ENTRY` |
| 3 | `HW-03` | Intel Mac | `PENDING_REAL_HARDWARE_ENTRY` |
| 4 | `HW-04` | T2 Mac | `PENDING_REAL_HARDWARE_ENTRY` |
| 5 | `HW-05` | Apple Silicon Observation | `PENDING_REAL_HARDWARE_ENTRY` |

`HW-02` Legacy BIOS is deferred for this execution order.

## Required Fields Per Machine

- Manufacturer
- Model
- CPU
- RAM
- Firmware type
- Secure Boot status
- Boot picker key or external boot process
- USB controller/port used if known

## HW-01 Standard UEFI PC

| Field | Value |
| --- | --- |
| Manufacturer | `PENDING_REAL_HARDWARE_ENTRY` |
| Model | `PENDING_REAL_HARDWARE_ENTRY` |
| CPU | `PENDING_REAL_HARDWARE_ENTRY` |
| RAM | `PENDING_REAL_HARDWARE_ENTRY` |
| Firmware type | `PENDING_REAL_HARDWARE_ENTRY` |
| Secure Boot status | `PENDING_REAL_HARDWARE_ENTRY` |
| Evidence record | `docs/release/PR41A_HW01_EXECUTION_RECORD.md` |
| Current status | `PHYSICAL_BOOT_UNTESTED` |

## Notes

Example machines may be listed separately in planning docs, but they are not execution evidence. PR41A status changes require the actual target machine fields plus photos/log outputs.
