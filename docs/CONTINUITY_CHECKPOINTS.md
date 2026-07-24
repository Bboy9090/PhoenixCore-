# PhoenixCore Continuity Checkpoints

## Purpose

Continuity checkpoints provide verified rollback evidence for ordinary host-side files before a repair transaction mutates them.

The checkpoint store uses:

- UUIDv4 checkpoint identifiers
- regular-file-only sources
- streamed backup copy
- `fsync` on backup data
- atomic backup rename
- atomic metadata replacement
- SHA-256 and exact-size backup verification
- restore through a temporary file
- post-restore SHA-256 verification
- pending, completed, failed, and restored states

## Schema

Checkpoint records use:

```text
bws.continuity-checkpoint/v1
```

## CLI

Create a checkpoint:

```bash
python scripts/continuity/checkpoint_store.py create \
  --root evidence/continuity \
  --source path/to/file \
  --repair-id 17
```

Verify a checkpoint:

```bash
python scripts/continuity/checkpoint_store.py verify \
  --root evidence/continuity \
  --checkpoint-id <uuid>
```

Restore a checkpoint:

```bash
python scripts/continuity/checkpoint_store.py restore \
  --root evidence/continuity \
  --checkpoint-id <uuid> \
  --target path/to/file
```

## Detects

- zero checkpoint identifiers
- missing metadata
- missing backup files
- backup size drift
- backup SHA-256 drift
- non-regular source files
- non-regular restore targets
- negative repair identifiers

## Safety boundary

This system does **not** restore:

- partitions
- block devices
- disks
- filesystems
- kernel memory
- firmware
- NVRAM
- cloud state
- remote systems

It does not claim TPM sealing, transparency logging, timestamp authority, or release eligibility.

This is a verified file checkpoint primitive. It is not a mystical undo button for bad ideas, despite the market’s long tradition of selling those.

## Ownership

PhoenixCore owns this host-side checkpoint store because PhoenixCore coordinates repairs, drive evidence, lifecycle receipts, and operator-facing recovery workflows.

bluephoenix-native receives the separate native continuity state contract in its own PR.
