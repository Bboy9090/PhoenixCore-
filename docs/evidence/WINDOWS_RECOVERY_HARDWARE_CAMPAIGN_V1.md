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
3. a **different physical disk** for rollback artifacts and the campaign evidence folder
4. a second external disk for substitution testing

The campaign preflight resolves the evidence folder back to its physical disk
and rejects the setup if that disk has the same stable identity as the target.

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

## Phase -1 — Discover candidate disks

Before choosing a raw `PHYSICALDRIVE` number, enumerate the current Windows
storage set read-only:

```powershell
python scripts/hardware/run_windows_recovery_hardware_campaign.py discover
```

The discovery report is checksum-bound with `discovery_sha256` and returns:

- `target_candidates`: external, non-boot, non-system GPT disks with stable
  hardware identity that also pass the existing future-write safety verdict
- `evidence_candidates`: external, non-boot, non-system disks with stable
  hardware identity and at least one currently mounted volume
- explicit block reasons for every inspected disk

Choose the intended target and a **different** evidence disk whose
`stable_identity_sha256` differs. The later Phase 0 preflight remains
authoritative and independently rechecks the exact target and the physical disk
behind the selected campaign directory.

Discovery performs no target writes and always reports:

- `read_only: true`
- `restore_executor_authorized: false`
- `system_mutations_performed: false`

---

## Phase 0 — Hardware campaign preflight

Before collecting baseline evidence, prove that the chosen target and campaign
evidence folder are physically safe for the validation campaign.

Run:

```powershell
python scripts/hardware/run_windows_recovery_hardware_campaign.py preflight `
  --target "\\.\PHYSICALDRIVE7" `
  --campaign-dir "D:\PhoenixKeyEvidence\campaign-001"
```

This preflight performs only read-only observation.

It proves:

- live Windows hardware was actually observed
- the target has a stable hardware identity
- the target is on an allowed external bus
- the target is not the Windows boot disk
- the target is not the Windows system disk
- the target uses GPT
- the target clears Phoenix Key's existing future-write safety verdict
- the raw-drive probe performed zero writes
- the campaign evidence folder resolves to a real backing physical disk
- that evidence disk has a stable hardware identity
- the evidence disk stable identity is different from the target stable identity

It writes:

- `preflight-target-drive-evidence.json`
- `hardware-campaign-preflight.json`

Required result:

`ready_for_hardware_campaign = true`

The preflight receipt is checksum-bound with `preflight_sha256`. Phase 1 refuses
to start if this receipt is missing, tampered, blocked, belongs to a different
campaign directory, or no longer matches the freshly observed target snapshot
and stable hardware identity.

The preflight always keeps:

- `restore_executor_authorized: false`
- `target_write_attempted: false`
- `system_mutations_performed: false`

If the evidence folder is physically located on the target disk, the preflight
fails. A different folder on the same physical disk is not sufficient.

---

## Phase 1 — Baseline live target

First identify the intended external target as an exact Windows raw path such as:

`\\.\PHYSICALDRIVE7`

Phase 1 is mechanically bound to the successful Phase 0 preflight. Re-run Phase 0 if the target or campaign directory changes.

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

## Phase 3 — Live target boot metadata

Capture boot metadata while the original baseline snapshot and GPT rollback capture are still current.

Use:

`scripts/hardware/capture_windows_restore_target_boot_metadata.py`

The target-boot receipt schema is:

`phoenix_key.restore_target_boot_metadata.v1`

Current V1 receipts distinguish:

- `evidence_source: live`
- `evidence_source: fixture`

A receipt may be labeled `live` only when both upstream inputs are also live:

- target drive evidence
- GPT rollback-capture receipt

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
- baseline snapshot identity match
- baseline stable identity match
- exact rollback-capture receipt match
- exact rollback-contract match
- zero target writes
- no partition mount / assignment attempt
- no system mutation

The boot metadata receipt may still report individual metadata items as inaccessible. That fact must remain visible; do not mount partitions merely to turn a missing item green.

The campaign harness now rejects boot metadata unless a rollback capture has already been recorded and the boot receipt is bound to that exact rollback receipt, rollback contract, baseline snapshot, and stable hardware identity.

If boot metadata must be recaptured **after** a reconnect that changes the snapshot, first perform fresh target reanalysis and produce a new rollback capture bound to that new snapshot. Never reuse a stale rollback receipt across snapshots.

---

## Phase 4 — Physical unplug / reconnect

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
- the checksum-bound before/after comparator must be trusted
- both comparison inputs must be live hardware evidence
- stale authorization must remain non-reusable

For `reenumeration_observed`:

- the physical reconnect must be operator-confirmed
- evidence must be live
- stable identity must still equal baseline
- **snapshot identity or PHYSICALDRIVE path must have changed**

If Windows reconnects the disk under the exact same path and snapshot, the campaign records the reconnect but does **not** claim re-enumeration was proven. Repeat the physical test later under conditions where Windows actually re-enumerates the target.

---

## Phase 5 — Hardware substitution rejection

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
The campaign also runs the checksum-bound re-enumeration comparator and requires
`hardware-substitution-or-mismatch`, trusted same-revision evidence, live
hardware inputs, and `stale_authorization_reusable = false`. Merely observing
a different disk is not enough to satisfy the gate.

If the candidate resolves to the baseline stable identity, the harness stops instead of manufacturing a substitution pass.

Reconnect the original target after this observation before any additional target-specific evidence collection.

---

## Operator planner — exact next action

At any point after the baseline manifest exists, ask the harness for the one next
required action:

```powershell
python scripts/hardware/run_windows_recovery_hardware_campaign.py next-step `
  --campaign-dir "D:\PhoenixKeyEvidence\campaign-001"
```

The result is checksum-bound with `next_step_sha256` and tied to the current
`manifest_sha256`.

The planner enforces this order:

1. live zero-write rollback capture
2. live boot metadata bound to that rollback chain
3. physical disconnect/reconnect and real re-enumeration proof
4. different-disk substitution proof
5. data-preservation resolution and final non-executable preflight

For physical reconnect and substitution steps, the plan explicitly reports
`operator_confirmation_required = true`.

It never authorizes a restore executor and always reports:

- `restore_executor_authorized: false`
- `system_mutations_performed: false`

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
4. require `phoenix_key.final_recovery_preflight.v1` to report
   `ready_for_restore_executor_architecture_review = true`
5. review the complete evidence package
6. only then design a **separate** restore-executor architecture gate / PR

The final preflight is checksum-bound with `receipt_sha256`. It independently
requires a valid Recovery Evidence Bundle v2 checksum, complete software and
hardware evidence chains, resolved data handling, resolved boot metadata, no
outstanding evidence requirements, valid critical identities, and trusted
critical evidence components.

Even when every final preflight gate passes, it always keeps:

- `restore_executor_authorized = false`
- `executable = false`
- `automatic_destructive_resume = false`
- `system_mutations_performed = false`

A green final preflight means only that the evidence package may proceed to a
separate restore-executor **architecture review**. It is not permission to
format, repartition, apply an image, rewrite EFI/BCD/WinRE, or otherwise mutate
the target.

No destructive restore implementation belongs in this validation lane.
