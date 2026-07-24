# Windows Physical-Drive Evidence

## Purpose

Capture real, reviewable identity evidence for one exact Windows physical drive before any destructive operation is considered.

This evidence tool performs no writes, formatting, partition changes, volume dismounts, bootloader installation, or firmware operations.

## Command

Run from an elevated PowerShell session for live hardware collection:

```powershell
python scripts/hardware/capture_windows_drive_evidence.py `
  --target '\\.\PHYSICALDRIVE1' `
  --output '.\evidence\hardware\physicaldrive1.json' `
  --source-commit '<CURRENT_COMMIT>' `
  --probe-exclusive-read
```

The optional exclusive probe requests a raw **read-only** handle with no sharing, performs zero reads and zero writes, and closes the handle immediately. Failure may indicate a busy, mounted, protected, or inaccessible target. It does not force a dismount.

## Captured fields

- exact physical-drive path and number
- friendly name
- serial number
- Windows unique ID
- bus type
- capacity in bytes
- partition style and partition inventory
- boot, system, offline, and read-only flags
- health and operational status
- canonical identity SHA-256
- exclusive read-handle result
- source commit and timestamp
- receipt SHA-256

## Candidate decision

A disk is only marked `write_candidate: true` when:

- it is not the boot disk
- it is not the system disk
- Windows reports an external/removable bus type from the allowed set
- a stable serial number or unique ID exists

This status does not authorize a write. It only means the disk may advance to explicit sacrificial-drive authorization under issue #135.

## Evidence classifications

- `fixture-validated`: deterministic fixture only, no hardware claim
- `hardware-evidence-captured`: live Windows observation was collected
- `hardware-attempted`: a real write or boot was attempted but validation did not complete
- `hardware-validated`: reserved for the complete write, read-back, and boot receipt gates

## Required invariants

Every receipt emitted by this tool contains:

```text
operation: read-only-physical-drive-evidence
bytes_written: 0
physical_write_attempted: false
hardware_validated: false
```

The implementation rejects any supplied probe observation reporting nonzero writes.

## Verify a retained receipt

The receipt digest binds the canonical JSON object before the `receipt_sha256` field is added:

```powershell
python -c "import hashlib,json,pathlib; p=pathlib.Path(r'.\evidence\hardware\physicaldrive1.json'); r=json.loads(p.read_text()); expected=r.pop('receipt_sha256'); encoded=json.dumps(r,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode(); actual=hashlib.sha256(encoded).hexdigest(); print('PASS' if actual==expected else 'FAIL', actual)"
```

A matching digest proves the saved receipt has not changed since collection. It does not independently prove the operating system reported truthful hardware metadata, which is why the next gate repeats identity immediately before any write.

## Fixture validation

```bash
python scripts/hardware/capture_windows_drive_evidence.py \
  --target '\\.\PHYSICALDRIVE1' \
  --fixture-json tests/fixtures/windows_disk_usb.json \
  --output /tmp/windows-drive-evidence.json \
  --source-commit fixture
```

Fixture success is not hardware evidence.

## Next gate

After a live receipt identifies the intended sacrificial disk, issue #135 requires explicit destruction authorization, immediate identity re-scan, bounded write, full read-back SHA-256, and a named-machine boot receipt.
