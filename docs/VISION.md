# PhoenixCore Vision

## What it is

PhoenixCore is a bootable recovery and deployment platform designed for when things have already gone wrong.  
It provides a consistent environment that can start up on a broken or misconfigured system, understand its state, and guide the operator through safe recovery, reinstall, or redeploy flows.

PhoenixCore is opinionated: it focuses on reliability, safety, and clear operator UX rather than being a generic toolbox or experiment playground.

## What it does

- **Boot**  
  Start a minimal, reliable environment on bare metal or from USB, even when the host OS is unbootable.

- **Diagnose**  
  Inspect hardware, disks, partitions, and OS installs; surface health, layout, and likely failure modes.

- **Recover**  
  Read from disks in a safety‑first way, copy out important data, and capture evidence and logs.

- **Reinstall**  
  Lay down a fresh OS image on a target device with guardrails (device selection, confirmations, integrity checks).

- **Revive**  
  Combine diagnostics, recovery, and reinstall into guided workflows that bring a machine back into a known‑good state.

## What it is not

- **Not a random template repo**  
  The goal is a focused recovery product, not a place to dump generic app scaffolds.

- **Not a generic dev starter**  
  PhoenixCore is not meant to be the base for arbitrary Python/Rust projects; its structure and tooling are tailored to recovery/deployment.

- **Not every experiment ever made**  
  Experimental code should live in clearly marked areas (e.g. `archive/`) or separate repos, not scattered through the core tree.

## Core promise

When the machine fails, PhoenixCore boots.  
From there, it should reliably help you:

- see what is broken,
- protect what matters,
- and get back to a working system with clear, auditable steps.

