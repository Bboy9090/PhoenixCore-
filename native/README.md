# Blue Phoenix Native Workspace

This directory tracks the sovereign, non-Linux Blue Phoenix Native program.

## Purpose

- Keep Native work running in parallel while desktop/live ISO editions ship.
- Define proof gates so progress is measurable and auditable.
- Prevent Native R&D from destabilizing the active Linux edition pipeline.

## Structure

- `roadmap.yaml`: Native track metadata, maturity state, and milestone proof gates.
- `kernel/`: Kernel source and scheduler/memory work.
- `boot/`: Bootloader and early boot chain work.
- `userland/`: Native shell, runtime, and first-party app runtime components.
- `evidence/`: Captured proof artifacts for milestone promotion.

## Promotion Rule

A milestone can only move to `done` when required proof artifacts are present under `native/evidence/`.
