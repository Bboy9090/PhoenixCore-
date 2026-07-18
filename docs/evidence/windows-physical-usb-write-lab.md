# Windows Physical USB Write Lab

This lane enables one CLI-only, byte-for-byte image write to a scanner-proven
external Windows disk. It does not add a Phoenix Key dashboard write button and
does not enable macOS, Linux, fixed-disk, internal-disk, or system-disk writes.

## Required safety chain

The writer opens a raw disk only when all of these conditions are true:

- Windows process is elevated.
- `BOOTFORGE_ENABLE_PHYSICAL_USB_WRITE` has the exact lab unlock value.
- Target is an exact `\\.\PHYSICALDRIVE<n>` path.
- Live scanner says the target is removable/external, not fixed, and not system.
- Fresh scanner identity matches the saved identity lock.
- Identity lock, preflight, and dry-run receipts all name the same target.
- Preflight and dry-run image hashes match the current image SHA-256.
- Dry-run receipt is eligible, unblocked, non-destructive, and wrote zero bytes.
- Image fits on the target.
- Explicit byte cap exactly equals the image size.
- All three risk phrases and the exact raw target are re-entered.
- A pre-write ledger record is flushed to disk before the raw handle opens.
- Windows grants an exclusive raw-disk handle. Mounted or busy targets fail closed.

## Controlled Windows procedure

Run PowerShell **as Administrator** from the repository root. Use only a
sacrificial external disk. The commands below assume the intended target was
independently confirmed as `PHYSICALDRIVE1` in Disk Management.

```powershell
$Target = '\\.\PHYSICALDRIVE1'
$Image = 'C:\Users\Bobby\Downloads\iCloudDrive\home-native.iso'
$Evidence = Join-Path $PWD 'physical-write-evidence'
New-Item -ItemType Directory -Path $Evidence -ErrorAction Stop

$env:BOOTFORGE_ENABLE_PHYSICAL_USB_WRITE = 'I_ACCEPT_SACRIFICIAL_USB_WRITE_RISK'
$ImageBytes = (Get-Item -LiteralPath $Image).Length

python .\usb_creator.py --lock-removable-target `
  --target-drive $Target `
  --export-identity-lock-json (Join-Path $Evidence 'identity-lock.json')

python .\usb_creator.py --hardware-writer-preflight `
  --target-drive $Target --image $Image `
  --export-hardware-preflight-json (Join-Path $Evidence 'preflight.json')

python .\usb_creator.py --plan-write `
  --target-drive $Target --image $Image `
  --export-write-plan-json (Join-Path $Evidence 'write-plan.json')

python .\usb_creator.py --audit-plan `
  --target-drive $Target --image $Image `
  --export-json (Join-Path $Evidence 'audit.json')

python .\usb_creator.py --simulate-write `
  --target-drive $Target --image $Image `
  --export-mock-write-json (Join-Path $Evidence 'simulation.json')
```

Inspect all three JSON files before continuing. The write plan must show
`eligible: true`, `blocked: false`, `actual_write_enabled: false`, and the exact
target and image hash.

Close every Explorer window or program using the external disk. If Windows still
mounts it, take only the confirmed sacrificial target disk offline in Disk
Management. Do not take the internal/system disk offline.

Then run the final command:

```powershell
python .\usb_creator.py --physical-usb-write-lab `
  --target-drive $Target --confirm-physical-target $Target `
  --image $Image --physical-write-max-bytes $ImageBytes `
  --physical-write-chunk-size 1048576 --verify-after-write `
  --require-identity-lock (Join-Path $Evidence 'identity-lock.json') `
  --require-preflight-result (Join-Path $Evidence 'preflight.json') `
  --require-dryrun-result (Join-Path $Evidence 'write-plan.json') `
  --require-audit-result (Join-Path $Evidence 'audit.json') `
  --require-simulation-result (Join-Path $Evidence 'simulation.json') `
  --append-writer-contract-ledger (Join-Path $Evidence 'write-ledger.jsonl') `
  --export-physical-write-json (Join-Path $Evidence 'write-result.json') `
  --typed-confirmation 'I UNDERSTAND THIS WILL OVERWRITE THE SELECTED PHYSICAL USB DRIVE' `
  --destructive-acknowledgement 'I CONFIRM THIS IS A SACRIFICIAL REMOVABLE TEST USB DRIVE' `
  --final-irreversible-acknowledgement 'I ACCEPT FULL RESPONSIBILITY FOR THIS TEST USB WRITE'
```

Success requires the full image byte count and a matching read-back SHA-256.
Any mismatch or Windows raw-handle error returns a blocked result and stops.
