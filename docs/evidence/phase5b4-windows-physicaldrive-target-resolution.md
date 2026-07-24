# Phase 5B-4: Windows PHYSICALDRIVE Target Resolution Fix

## Status

Implementation is active on branch `fix/windows-physicaldrive-target-resolution` in draft PR #143.

This lane is a focused blocker fix for PR #123 hardware-test evidence. It does not authorize marking PR #123 ready, merging `main`, adding physical-write controls, or changing the BootForge USB repository.

## Blocking receipt being addressed

The accepted Windows hardware receipt attached to PR #123 reported:

```text
Scanner: \\.\PHYSICALDRIVE1 eligible / high confidence
Dry-run planner: same drive rejected as nonexistent
Result: FAIL — SAFELY BLOCKED
```

Safety boundary held during the failed receipt:

```text
physical_write_attempted: false
bytes_written: 0
actual_write_enabled: false
```

## Fix summary

Phoenix Key now resolves Windows physical-drive target arguments through a dedicated typed resolver before invoking the embedded PhoenixCore dry-run planner.

The resolver accepts these equivalent target spellings:

```text
\\.\PHYSICALDRIVE1
PHYSICALDRIVE1
physicaldrive1
\\\\.\\PHYSICALDRIVE1
//./physicaldrive1
```

and emits the canonical planner argument:

```text
\\.\PHYSICALDRIVE1
```

The resolver also:

- removes leading zeroes from a disk number, such as `PHYSICALDRIVE001` to `\\.\PHYSICALDRIVE1`
- rejects embedded markers such as `C:\temp\PHYSICALDRIVE1`
- rejects trailing junk such as `PHYSICALDRIVE1.tmp`
- rejects an empty target
- passes ordinary drive-letter or filesystem targets through unchanged

This prevents over-escaped or non-canonical scanner values from bypassing the existing Python scanner-evidence path and falling into ordinary filesystem path validation.

## Integration behavior

`plan_media_build` now:

1. resolves the selected target through `windows_target::resolve_target`
2. passes the canonical target to the embedded PhoenixCore `--plan-write` command
3. records target-resolution evidence in the returned JSON plan

The added `target_resolution` object contains:

```text
requested_path
canonical_path
resolution_source
target_kind
canonicalized
planner_root
scanner_planner_consistent
```

For the receipt scenario, expected evidence is:

```json
{
  "requested_path": "PHYSICALDRIVE1",
  "canonical_path": "\\\\.\\PHYSICALDRIVE1",
  "resolution_source": "phoenix_key_bridge",
  "target_kind": "windows_physical_drive",
  "canonicalized": true,
  "planner_root": "\\\\.\\PHYSICALDRIVE1",
  "scanner_planner_consistent": true
}
```

If PhoenixCore does not return a matching planner root, the plan remains visible but `scanner_planner_consistent` is recorded as `false`. The bridge does not guess, substitute a different disk, or enable writing.

## Files changed

```text
.github/workflows/phoenix-key-desktop.yml
apps/phoenix-key/src-tauri/src/main.rs
apps/phoenix-key/src-tauri/src/windows_target.rs
docs/evidence/phase5b4-windows-physicaldrive-target-resolution.md
```

## Safety boundary

This fix only resolves and records a target identifier before dry-run planning.

It does not add:

```text
physical writing
raw device writing
formatting
partition editing
mount automation
unmount automation
dashboard write controls
consumer write mode
```

Existing safety claims remain:

```text
actual_write_enabled: false
physical_write_attempted: false
bytes_written: 0
dashboard write path: absent
```

## Added validation

Rust unit coverage now includes:

```text
canonicalizes_standard_windows_physical_drive
canonicalizes_plain_physical_drive
canonicalizes_lowercase_physical_drive
canonicalizes_over_escaped_physical_drive
canonicalizes_forward_slash_physical_drive
removes_leading_zeroes_from_disk_number
leaves_non_physical_drive_target_unchanged
rejects_embedded_physical_drive_marker
rejects_trailing_physical_drive_junk
rejects_empty_target
records_consistent_scanner_planner_resolution
records_missing_planner_root_as_inconsistent
rejects_non_object_plan_payload
```

The Phoenix Key Windows workflow now runs:

```text
cargo test --manifest-path src-tauri/Cargo.toml
```

before building MSI and NSIS preview installers. A failed Rust unit test blocks installer packaging and artifact upload.

## Required verification before merge

Run from the Phoenix Key app directory:

```text
cd apps/phoenix-key
cargo test --manifest-path src-tauri/Cargo.toml
npm run check:boundaries
npm run build
```

Run repository checks:

```text
black --check --diff . --exclude "node_modules|dist"
flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics --exclude=node_modules,dist
cd dashboard && npm run lint && npm run build
```

Run danger scans:

```text
git grep -n -i -e "diskpart" -e " dd " -e "CreateFile" -e "WriteFile" -e "DeviceIoControl" -e "mkfs" -e "mount" -e "umount" -e "format" -- "*.py" "dashboard/src/App.jsx" "dashboard/vite.config.js"

git grep -n -i -e "Write USB" -e "Burn USB" -e "Flash USB" -e "Start Write" -e "Format USB" -e "Erase Drive" -e "Arm Writer" -e "Execute Write" -e "Destructive Write" -e "Write Now" -- dashboard/src/App.jsx
```

Expected result:

```text
no physical writing added
no dashboard write trigger added
main untouched
PR #123 remains draft
```

## Required hardware retest

After CI passes, run a replacement Windows hardware receipt using the unsigned Phoenix Key preview installer built from PR #143.

The replacement receipt must prove:

```text
scanner target: \\.\PHYSICALDRIVE1
planner target: \\.\PHYSICALDRIVE1
target_resolution.scanner_planner_consistent: true
dry-run plan no longer reports: Drive path does not exist
physical_write_attempted: false
bytes_written: 0
actual_write_enabled: false
```

Only after a clean replacement receipt can PR #143 be merged into `usb-creator-foundation-lock`. PR #123 still requires separate future approval to be marked ready, and merging PR #123 into `main` remains a separate final gate.
