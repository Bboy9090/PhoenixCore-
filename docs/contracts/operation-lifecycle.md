# Phoenix Agent Operation Lifecycle

This document defines the formal lifecycle for all system operations managed by the Phoenix Agent.

## Canonical Flow
Every system-altering operation must progress through these stages:

1.  **Request**: Client submits intent with parameters.
2.  **Preview**: Agent generates an `ImpactReport` (read-only analysis).
3.  **Safety Evaluation**: Platform evaluates the operation against `DeploymentPolicy`.
4.  **Confirmation**: User acknowledges risks and provides `PHX-TOKEN` if required.
5.  **Execution**: Agent commits the change (e.g., via Rust system crates).
6.  **Status Stream**: Real-time logging and progress reporting.
7.  **Report Bundle**: Generation of signed evidence and hashes.
8.  **Audit Record**: Permanent entry in the immutable audit log.

## Operation Metadata
All operations MUST include:
- `operation_id`: Unique UUID.
- `actor_id`: User or service account initiating the action.
- `device_identity`: Verified hardware profile.
- `target_summary`: Plain-language description of what is being touched.
- `risk_level`: (read_only | preview_only | privileged | destructive | firmware_adjacent).
- `rollback_possible`: Boolean indicating if automatic reversal is supported.
