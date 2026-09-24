# Windows Recovery Forge — Physical Hardware Campaign V1

## Purpose

This campaign collects the remaining **real Windows hardware evidence** required after Recovery Forge software convergence.

It is deliberately read-only with respect to the recovery target.

The campaign does **not**:

- format a disk
- repartition a disk
- mount or assign an inaccessible partition
- write EFI / BCD / WinRE
- apply a Windows image
- call the sacrificial writer
- unlock a restore executor
- persist destructive authorization

The harness is:

`scripts/hardware/run_windows_recovery_hardware_campaign.py`

Its manifest schema is:

`phoenix_key.windows_recovery_hardware_campaign.v1`

Even when every physical-evidence gate passes:

- `restore_executor_authorized: false`
- `system_mutations_performed: false`

The next action remains data-preservation resolution and a final **non-executable** preflight.

---

## Required hardware

Use hardware you are willing to treat as sacrificial for validation.

You need:

1. a Windows machine running the direct Phoenix Key / Recovery Forge tooling
2. one external GPT target disk with stable serial or unique-ID evidence
3. a **different physical disk** for rollback artifacts
4. a second external disk for substitution testing

Do not use:

- the current Windows boot disk
- the current Windows system disk
- a disk containing irreplaceable data
- the same physical disk for both target and rollback evidence

---

## Campaign directory

Choose one normal filesystem folder on the rollback/evidence disk, for example:

`D:\PhoenixKeyEvidence\campaign-001`

The campaign folder stores receipts and copied rollback metadata only.

It never stores writes on the target itself.

---

## Phase 1 — Baseline live target

First identify the intended external target as an exact Windows raw path such as:

`\\.\PHYSICALDRIVE7`

Then run:

```powershell
python scripts/hardware/run_windows_recovery_hardware_campaign.py baseline `
  --target "\\.\PHYSICALDRIVE7" `
  --campaign-dir "D:\PhoenixKeyEvidence\campaign-001"
```

This performs:

- live `Get-Disk` / `Get-Partition` observation
- stable hardware identity calculation
- snapshot identity calculation
- zero-byte exclusive read-handle probe
- zero target writes
- initial checksum-bound campaign manifest

Required gate:

`baseline_live_hardware = true`

If the drive has no stable serial / unique ID, stop. Do not substitute path or disk number as a stable identity.

---

## Phase 2 — Read-only GPT rollback capture

Use the existing Recovery Center flow to create:

- fresh target verification
- restore rollback contract
- separate rollback destination verification

Then run the existing read-only GPT capture against the exact baseline target.

The resulting receipt must be:

`phoenix_key.restore_target_rollback_capture.v1`

Current V1 receipts now distinguish:

- `evidence_source: live`
- `evidence_source: fixture`

Only `live` may satisfy the physical campaign.

The receipt must prove:

- baseline snapshot identity still matches
- baseline stable identity still matches
- rollback destination stable identity differs from target
- `target_bytes_written = 0`
- `target_write_attempted = false`
- `system_mutations_performed = false`
- `restore_unlock_ready = false`

Record it:

```powershell
python scripts/hardware/run_windows_recovery_hardware_campaign.py record-rollback `
  --campaign-dir "D:\PhoenixKeyEvidence\campaign-001" `
  --receipt "D:\PhoenixKeyEvidence\rollback\restore-rollback-capture.json"
```

Required gate:

`rollback_live_zero_write = true`

A fixture-generated GPT receipt remains useful for software QA but cannot satisfy this gate.

---

## Phase 3 — Physical unplug / reconnect

Physically unplug the baseline target.

Wait until Windows no longer enumerates it.

Reconnect the **same physical device**.

Determine its current exact raw path. It may have changed, for example from:

`\\.\PHYSICALDRIVE7`

to:

`\\.\PHYSICALDRIVE9`

Run:

```powershell
python scripts/hardware/run_windows_recovery_hardware_campaign.py reconnect `
  --campaign-dir "D:\PhoenixKeyEvidence\campaign-001" `
  --current-target "\\.\PHYSICALDRIVE9" `
  --operator-confirmed-physical-reconnect
```

The operator-confirmation flag records a human-observed physical event. The software never invents that fact.

Two separate gates exist:

- `reconnect_same_hardware`
- `reenumeration_observed`

For `reconnect_same_hardware`:

- stable hardware identity must equal baseline

For `reenumeration_observed`:

- the physical reconnect must be operator-confirmed
- evidence must be live
- stable identity must still equal baseline
- **snapshot identity or PHYSICALDRIVE path must have changed**

If Windows reconnects the disk under the exact same path and snapshot, the campaign records the reconnect but does **not** claim re-enumeration was proven. Repeat the physical test later under conditions where Windows actually re-enumerates the target.

---

## Phase 4 — Hardware substitution rejection

Disconnect the baseline target.

Connect a **different physical external disk**.

Identify its exact raw path.

Run:

```powershell
python scripts/hardware/run_windows_recovery_hardware_campaign.py substitution `
  --campaign-dir "D:\PhoenixKeyEvidence\campaign-001" `
  --candidate-target "\\.\PHYSICALDRIVE12" `
  --operator-confirmed-physical-substitution
```

Required gate:

`substitution_rejection_proven = true`

The candidate must have a stable identity different from the baseline target.

If the candidate resolves to the baseline stable identity, the harness stops instead of manufacturing a substitution pass.

Reconnect the original target after this observation before collecting target-specific boot metadata.

---

## Phase 5 — Live target boot metadata

Use:

`scripts/hardware/capture_windows_restore_target_boot_metadata.py`

against the original target after fresh target revalidation.

The target-boot receipt schema is:

`phoenix_key.restore_target_boot_metadata.v1`

Current V1 receipts distinguish:

- `evidence_source: live`
- `evidence_source: fixture`

The script only copies metadata from partitions Windows already exposes.

It does not:

- assign a drive letter
- mount an inaccessible EFI partition
- mount an inaccessible Recovery partition
- write to the target

Record the receipt:

```powershell
python scripts/hardware/run_windows_recovery_hardware_campaign.py record-boot-metadata `
  --campaign-dir "D:\PhoenixKeyEvidence\campaign-001" `
  --receipt "D:\PhoenixKeyEvidence\rollback\boot\restore-target-boot-metadata.json"
```

Required gate:

`boot_metadata_live_read_only = true`

The receipt must prove:

- live hardware observation
- baseline stable identity match
- zero target writes
- no partition mount / assignment attempt
- no system mutation

The boot metadata receipt may still report individual metadata items as inaccessible. That fact must remain visible; do not mount partitions merely to turn a missing item green.

---

## Phase 6 — Status

At any point:

```powershell
python scripts/hardware/run_windows_recovery_hardware_campaign.py status `
  --campaign-dir "D:\PhoenixKeyEvidence\campaign-001"
```

The physical campaign is complete only when all are true:

- `baseline_live_hardware`
- `rollback_live_zero_write`
- `reconnect_same_hardware`
- `reenumeration_observed`
- `substitution_rejection_proven`
- `boot_metadata_live_read_only`

The campaign manifest is checksum-bound with:

`manifest_sha256`

If the manifest is manually edited, the harness rejects it on reload.

---

## Fixture boundary

Automated CI intentionally exercises fixture receipts.

Fixture receipts must remain unable to satisfy live hardware gates.

CI specifically tests that:

- fixture baseline does not count as hardware
- fixture GPT capture does not count as hardware
- fixture boot metadata does not count as hardware
- reconnect without snapshot/path change does not prove re-enumeration
- reconnect requires explicit operator confirmation
- same-device substitution is rejected
- tampered campaign manifest is rejected

---

## After the hardware campaign

A completed hardware campaign is **not** permission to restore Windows.

The next safe sequence is:

1. resolve target-data preservation
   - real backup receipt for preserve mode, or
   - explicit discard acknowledgement
2. build a fresh Recovery Evidence Bundle v2
3. run the final non-executable hardware preflight
4. review the complete evidence package
5. only then design a **separate** restore-executor architecture gate / PR

No destructive restore implementation belongs in this validation lane.
