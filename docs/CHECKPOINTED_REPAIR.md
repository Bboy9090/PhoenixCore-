# PhoenixCore Checkpointed Repair

## Purpose

The checkpointed repair coordinator applies regular-file repairs only after proving a replacement payload and preserving a verified Continuity checkpoint.

## Sequence

1. Validate the replacement payload size and SHA-256.
2. Create a verified Continuity checkpoint of the target.
3. Append checkpoint evidence to the hash-chained ledger.
4. Copy the replacement into a temporary file and `fsync` it.
5. Reverify the temporary file against the payload manifest.
6. Atomically replace the target.
7. Verify the final target SHA-256.
8. Append successful repair evidence.
9. Mark the checkpoint completed.
10. If repair verification fails, restore from the checkpoint and append rollback evidence.

## Implemented evidence

- successful checkpointed repair
- injected post-replacement corruption test
- automatic rollback to original bytes
- invalid payload rejected before checkpoint or mutation
- hash-chained evidence verification

## CLI

```bash
python scripts/recovery/checkpointed_repair.py \
  --checkpoint-root evidence/continuity \
  --ledger evidence/session.jsonl \
  --target path/to/file \
  --replacement path/to/replacement \
  --repair-id 42
```

## Safety boundary

This coordinator is limited to non-symlink regular files.

It does **not** repair or mutate:

- block devices
- partitions
- filesystems
- firmware
- NVRAM
- kernel memory
- live process memory
- remote systems
- physical hardware

It does not claim package-manager integration, automatic hardware repair, release eligibility, or production readiness.

This is a repair transaction primitive, not a universal resurrection spell. Software has tried that branding before. The results were expensive.
