# PR41 Completion Implementation Plan

## Overview
This document outlines a detailed implementation plan for completing the PR41 series (A‑E) on the canonical release‑candidate branch **`fix/edition-branding-fallbacks-20260518`**.

> [!WARNING]
> **CRITICAL GATING NOTE:** Automated tests validate the software framework and integration hooks, not physical device success on real silicon. Physical validation on real hardware targets remains a strict prerequisite for release sign-off. The overall release candidate status is currently **RC_PRE_PHYSICAL_VALIDATION**.

---

### 1️⃣ PR41A – Physical USB Boot Validation
- **Goal**: Verify that a physical USB device containing a PhoenixOS recovery image boots reliably on target hardware platforms.
- **Required files/docs**:
  - `desktop/src/core/usb_builder.py` (boot image creation logic)
  - `tests/test_bootforge_physical.py` (new test stub placeholder)
  - Hardware validation checklist (docs/hardware/USB_BOOT_VALIDATION.md)
- **Commands / Tests**:
  ```sh
  # Build USB image
  python3 -m desktop.src.core.usb_builder build --target /dev/sdx

  # Run physical boot test (requires attached hardware)
  pytest tests/test_bootforge_physical.py -vv
  ```
- **Evidence required**:
  - Log files from the boot sequence (`/var/log/phoenix_boot.log`).
  - Photographic proof of successful boot screen.
- **Pass criteria**:
  - Boot completes without kernel panics on **all** listed hardware models.
  - Log contains “BOOT_SUCCESS” marker.
- **Blocker criteria**:
  - Any kernel panic or failure to mount the root filesystem.
- **Hardware required**:
  - At least one reference device per platform (Intel x86‑64, ARM64, ChromeOS dev board).
- **Destructive writes allowed?**: **No** – use a disposable USB stick.
- **Expected commit message**:
  ```
  test(usb-boot): add physical validation for recovery USB
  ```

---

### 2️⃣ PR41B – Safety Enforcement Validation
- **Goal**: Ensure all safety gates (write‑gating, central‑format gating) are enforced for any USB‑related operation.
- **Required files/docs**:
  - `desktop/src/gui/safety_validator.py`
  - `tests/test_safety_gating.py`
  - Policy doc `docs/policy/SAFETY_GATES.md`
- **Commands / Tests**:
  ```sh
  pytest tests/test_safety_gating.py::TestSafetyGating -vv
  ```
- **Evidence required**:
  - JSON report `safety_report.json` with pass/fail per gate.
- **Pass criteria**:
  - All safety gates report `pass: true`.
- **Blocker criteria**:
  - Any gate reports `pass: false` or raises `SafetyGateError`.
- **Hardware required**:
  - None (pure software validation).
- **Destructive writes allowed?**: **No**.
- **Expected commit message**:
  ```
  test(safety): validate all safety gates for USB operations
  ```

---

### 3️⃣ PR41C – Transactional Dry‑Run / Rollback Guarantees
- **Goal**: Provide a transactional dry‑run mode that can roll back partially applied changes without leaving the system in an inconsistent state.
- **Required files/docs**:
  - `desktop/src/core/transaction_manager.py`
  - `tests/test_transactional_dryrun.py`
  - Design spec `docs/design/TRANSACTIONAL_DRYRUN.md`
- **Commands / Tests**:
  ```sh
  pytest tests/test_transactional_dryrun.py -vv
  ```
- **Evidence required**:
  - Log snippet showing `BEGIN_TX`, `ROLLBACK_TX`, and final state verification.
- **Pass criteria**:
  - Dry‑run completes with `ROLLBACK_TX` and the system state matches the pre‑run snapshot.
- **Blocker criteria**:
  - State mismatch after rollback or unhandled exceptions.
- **Hardware required**:
  - None (simulation only).
- **Destructive writes allowed?**: **No**.
- **Expected commit message**:
  ```
  feat(tx): add transactional dry‑run and rollback guarantees for USB ops
  ```

---

### 4️⃣ PR41D – Apple EFI / T2 / Legacy Mac Behavior
- **Goal**: Validate that the USB recovery image works on Apple hardware, including EFI boot paths, T2‑controlled storage, and legacy BIOS fallback.
- **Required files/docs**:
  - `desktop/src/platform/apple_efi.py`
  - `tests/test_apple_efi.py`
  - Test matrix `docs/hardware/APPLE_EFI_MATRIX.md`
- **Commands / Tests**:
  ```sh
  # Run on a Mac (requires physical Mac or VM with EFI support)
  pytest tests/test_apple_efi.py -vv
  ```
- **Evidence required**:
  - EFI boot log (`efi_boot.log`).
  - Confirmation that Secure Boot bypass works on T2 machines.
- **Pass criteria**:
  - EFI boot succeeds on **all** listed Apple models.
- **Blocker criteria**:
  - Failure to boot on any Apple device, or inability to disable T2‑controlled Secure Boot.
- **Hardware required**:
  - Minimum: one modern MacBook with T2 chip, one older Intel‑based Mac.
- **Destructive writes allowed?**: **No** – use a disposable USB.
- **Expected commit message**:
  ```
  test(apple-efi): verify USB recovery boot on Apple hardware
  ```

---

### 5️⃣ PR41E – Final Evidence Gate & RC Approval
- **Goal**: Produce a comprehensive evidence package for release‑candidate (RC) approval, combining results from A‑D.
- **Required files/docs**:
  - `docs/release/PR41_EVIDENCE_PACKAGE.md`
  - `scripts/generate_evidence_report.sh`
  - Sign‑off checklist `docs/release/RC_SIGNOFF_CHECKLIST.md`
- **Commands / Tests**:
  ```sh
  ./scripts/generate_evidence_report.sh > evidence_report.txt
  ```
- **Evidence required**:
  - Consolidated `evidence_report.txt` containing all logs, test results, and hardware photos.
  - Signed sign‑off sheet from QA lead.
- **Pass criteria**:
  - All prior PR41 sections report “PASS”.
  - Evidence package reviewed and signed by QA and Security leads.
- **Blocker criteria**:
  - Missing logs, failed tests, or unsigned sign‑off.
- **Hardware required**:
  - None (aggregated from previous steps).
- **Destructive writes allowed?**: **No**.
- **Expected commit message**:
  ```
  doc(evidence): add final PR41 evidence package and RC sign‑off checklist
  ```

---

## Owner / Timeline Matrix
| Milestone | Owner | Target Completion | Dependencies |
|----------|-------|-------------------|--------------|
| PR41A – Physical USB Boot Validation | **Hardware Lab Lead** (Alex) | 2026‑06‑05 | USB image builder ready (already merged) |
| PR41B – Safety Enforcement Validation | **Security Engineer** (Mira) | 2026‑06‑07 | Safety validator implementation present |
| PR41C – Transactional Dry‑Run | **Backend Lead** (Ravi) | 2026‑06‑10 | Transaction manager module baseline |
| PR41D – Apple EFI Validation | **Mac Platform Owner** (Lin) | 2026‑06‑12 | Apple hardware allocated |
| PR41E – Evidence Gate & RC Approval | **Release Manager** (Sofia) | 2026‑06‑14 | All prior milestones completed |

## Risk & Mitigation Table
| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| Hardware unavailability (Apple T2 machines) | Delays PR41D & PR41E | Medium | Reserve loaner Macs from partner labs; use virtualization with EFI support as fallback |
| Flaky physical USB boot tests | False‑negative failures | High | Repeat tests 3×, capture logs automatically, use multiple USB sticks |
| Safety gate regression after future merges | Release safety breach | Medium | Pin safety validator version in CI, add regression test suite |
| Transactional dry‑run state drift | Inconsistent rollback | Low | Snapshot pre‑run state, compare checksum after rollback |
| Evidence package incomplete | RC sign‑off blocked | Low | Automate report generation, checklist enforcement in CI |

## Integration Checklist (to be run after all PR41 milestones are GREEN)
1. **Run full test suite** on `fix/edition-branding-fallbacks-20260518`:
   ```sh
   python3 -m pytest -vv
   ```
2. **Verify `git diff --check`** reports no whitespace errors.
3. **Confirm CI badge** for `safety-gates` and `usb-boot` are **green**.
4. **Generate evidence report** (`scripts/generate_evidence_report.sh`).
5. **Update release notes** (`docs/release/RELEASE_NOTES.md`) with PR41 outcomes.
6. **Create a signed RC tag**:
   ```sh
   git tag -a rc-20260615 -m "Release Candidate 2026‑06‑15 – PR41 complete"
   git push origin rc-20260615
   ```
7. **Notify stakeholders** (QA, Security, Product) with link to `evidence_report.txt`.

## Final RC Go/No‑Go Checklist
| Item | ✅ | ❌ |
|------|----|----|
| All PR41A‑D tests pass in CI |  |  |
| No `git diff --check` warnings |  |  |
| Evidence package generated and signed |  |  |
| Release notes updated |  |  |
| RC tag created and pushed |  |  |
| Stakeholder sign‑off recorded |  |  |

*If any red cell remains, the RC is a **No‑Go** and the corresponding PR41 milestone must be revisited.*

---

*Document created per user request. No code changes have been made.*
