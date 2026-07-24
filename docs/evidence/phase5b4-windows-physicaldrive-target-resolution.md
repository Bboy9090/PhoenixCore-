# Phase 5B-4: Windows PHYSICALDRIVE Target Resolution Fix

## Status

Implementation started on branch `fix/windows-physicaldrive-target-resolution`.

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

Phoenix Key now canonicalizes Windows physical-drive target arguments at the desktop bridge boundary before invoking the embedded PhoenixCore dry-run planner.

The bridge normalizes these equivalent target spellings:

```text
\\.\PHYSICALDRIVE1
PHYSICALDRIVE1
physicaldrive1
\\\\.\\PHYSICALDRIVE1
```

into the canonical planner argument:

```text
\\.\PHYSICALDRIVE1
```

This prevents an over-escaped scanner value from bypassing the existing Python scanner-evidence path and falling into ordinary filesystem path validation.

## Files changed

```text
apps/phoenix-key/src-tauri/src/main.rs
docs/evidence/phase5b4-windows-physicaldrive-target-resolution.md
```

## Safety boundary

This fix only normalizes a target identifier before dry-run planning.

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

## Added validation

Rust unit coverage was added for Phoenix Key bridge normalization:

```text
canonicalizes_standard_windows_physical_drive
canonicalizes_plain_physical_drive
canonicalizes_lowercase_physical_drive
canonicalizes_over_escaped_physical_drive
leaves_non_physical_drive_target_unchanged
```

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

After CI passes, run a replacement Windows hardware receipt using the unsigned Phoenix Key preview installer built from this fix branch.

The replacement receipt must prove:

```text
scanner target: \\.\PHYSICALDRIVE1
planner target: \\.\PHYSICALDRIVE1
dry-run plan no longer reports: Drive path does not exist
physical_write_attempted: false
bytes_written: 0
actual_write_enabled: false
```

Only after a clean replacement receipt can PR #123 be considered for a separate ready-for-review approval.
