# Windows Sacrificial-Drive Write Gate

## Purpose

Write one verified image to one explicitly named disposable Windows physical drive, then read every written byte back and require an exact SHA-256 match.

This tool is intentionally CLI-only. It does not format, partition, initialize, silently dismount, select a target automatically, or write firmware.

## Required input

A live receipt produced by:

```powershell
python scripts\hardware\capture_windows_drive_evidence.py `
  --target '\\.\PHYSICALDRIVE1' `
  --output '.\evidence\hardware\physicaldrive1.json' `
  --source-commit (git rev-parse HEAD) `
  --probe-exclusive-read
```

Fixture receipts cannot authorize physical writes.

## Evidence storage rule

The input receipt and final write receipt must be stored on a different physical disk from the sacrificial target. Create the output directory before execution and confirm its volume is not backed by the selected `PHYSICALDRIVE`.

Do not save the only copy of the evidence onto the disk that is about to be overwritten. The writer cannot preserve a receipt stored on its own destruction target, a fact disks understand more readily than people.

## Authorization phrase

The writer calculates an exact phrase from the receipt:

```text
I AUTHORIZE COMPLETE DESTRUCTION OF \\.\PHYSICALDRIVE1 IDENTITY <64_HEX_IDENTITY> SIZE <EXACT_BYTES>
```

The target, identity hash, and byte capacity must match exactly. Generic confirmation text is rejected.

## Environment unlock

Set this only in the elevated PowerShell session used for the authorized test:

```powershell
$env:BWS_ENABLE_SACRIFICIAL_DRIVE_WRITE = 'I_ACCEPT_COMPLETE_DESTRUCTION_OF_NAMED_TEST_DRIVE'
```

Closing that shell removes the temporary process-level unlock.

## Execute

```powershell
python scripts\hardware\write_windows_sacrificial_drive.py `
  --drive-receipt '.\evidence\hardware\physicaldrive1.json' `
  --image 'C:\path\to\arcwyre-live.iso' `
  --target '\\.\PHYSICALDRIVE1' `
  --authorization 'I AUTHORIZE COMPLETE DESTRUCTION OF \\.\PHYSICALDRIVE1 IDENTITY <IDENTITY_SHA256> SIZE <SIZE_BYTES>' `
  --source-commit (git rev-parse HEAD) `
  --output '.\evidence\hardware\physicaldrive1-write.json' `
  --execute
```

## Mandatory gates

Before opening a writable raw handle, the tool requires:

- valid digest-bound live drive receipt
- zero prior bytes written in the evidence receipt
- target previously classified as a candidate
- target is not boot or system disk
- exact target re-entry
- environment unlock
- 40-character source commit
- positive image size that fits the target
- exact dynamic destruction phrase
- explicit `--execute`
- elevated Windows process
- immediate fresh `Get-Disk` identity match

The raw disk is opened with read and write access and **no sharing**. A mounted, busy, protected, or otherwise unavailable disk fails closed. The tool never forces a dismount.

## Write and verification

- byte cap equals the source image size
- writer stops exactly at the byte cap
- source SHA-256 is calculated while writing
- data is flushed before verification
- the raw target is read from byte zero for exactly the written count
- read-back SHA-256 must equal the source SHA-256
- short writes, short reads, changed source, or mismatches fail

## Result classification

A successful write and read-back receipt records:

```text
classification: hardware-write-readback-verified
physical_write_attempted: true
physical_write_completed: true
readback_completed: true
verification_passed: true
hardware_validated: false
next_required_action: named-machine-boot-test
```

Read-back success does not prove the media boots. Hardware validation still requires the named-machine boot and serial-marker gate in issue #135.

## Current black-screen evidence

The previously reported external SSD boot reached a black screen and remains `hardware-attempted`. Once a new write receipt passes, the next test must capture machine, UEFI mode, Secure Boot state, display path, artifact checksum, and the last Phoenix Prime serial marker.
