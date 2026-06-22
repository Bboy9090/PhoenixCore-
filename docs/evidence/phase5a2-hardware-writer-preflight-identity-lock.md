# Phase 5A-2: Hardware USB Writer Preflight + Removable Target Identity Lock

## Purpose

Phase 5A-2 adds hardware writer preflight and removable target identity locking. This phase prepares the system for a future physical USB writer by proving that a removable target can be identified, locked, re-scanned, compared, and rejected if identity drift occurs.

This phase does not perform physical USB writing.

## Files Changed

- real_writer_interface.py
- usb_creator.py
- dashboard/vite.config.js
- dashboard/src/App.jsx
- tests/test_hardware_writer_preflight.py
- docs/evidence/phase5a2-hardware-writer-preflight-identity-lock.md

## Hardware Preflight Design

The hardware preflight payload uses schema:

```text
bootforge.hardware_writer_preflight.v1
```

It records target identity, removable/external/fixed/system status, image identity when supplied, identity lock status, drift detection, block reasons, warnings, and next required action.

The following remain locked:

```text
physical_writer_allowed: false
physical_write_attempted: false
```

## Removable Target Identity Lock Design

The identity lock payload uses schema:

```text
bootforge.removable_target_identity_lock.v1
```

The identity lock ID is deterministic from stable target identity fields and excludes volatile timestamps.

Identity lock blocks:

* fixed/internal targets
* system drives
* ambiguous targets
* missing stable IDs
* missing identity hashes
* missing size
* raw device paths not tied to scan evidence

## Re-scan Identity Comparison

The re-scan comparison checks the latest target identity against the original lock.

It blocks when:

* latest identity hash is missing
* latest identity hash differs from the locked identity hash
* target identity drift is detected

## CLI Behavior

Added preflight-related CLI behavior:

* --hardware-writer-preflight
* --lock-removable-target
* --rescan-target-identity
* --export-hardware-preflight-json
* --export-hardware-preflight-markdown

All CLI output is JSON-safe.

No physical USB write is performed in this phase.

## Dashboard Behavior

The dashboard exposes read-only hardware preflight status only.

The dashboard cannot start a physical USB write.

Required dashboard safety statement:

```text
Hardware writer preflight only. Physical USB writing is still locked and cannot be started from the dashboard.
```

## Evidence Export Behavior

Hardware preflight evidence can be exported as:

* JSON
* Markdown

Export validation blocks:

* empty paths
* missing parent folders
* directories
* overwrites
* wrong extensions
* raw device paths
* UNC/device namespace paths
* target-drive roots
* suspicious system paths

Unsafe paths are rejected before Path.resolve().

## Ledger Integration

Hardware preflight can integrate with the existing writer safety JSONL ledger.

Ledger writes remain append-only and evidence-only.

## Validation Results

Backend tests:

```text
171/171 OK
```

Dashboard build:

```text
Vite build completed successfully
```

## Danger Scan Summary

Danger scan reviewed.

No executable destructive writer path was introduced.

Allowed hits were limited to tests, docs, evidence files, blocked adapter strings, or safety copy.

Forbidden UI label scan:

```text
No forbidden dashboard write labels found.
```

## Safety Lock Statement

Physical USB writing remains locked.

The dashboard cannot start a write.

The system still does not perform:

* disk formatting
* partition editing
* mount automation
* unmount automation
* diskpart execution
* dd execution
* mkfs execution
* raw physical USB write execution
* bootloader writing
* dashboard-triggered write
