# PhoenixCore Product Boundaries

## Purpose

PhoenixCore is the device-intelligence and recovery-planning layer in the Bobby’s Workshop ecosystem. Its job is to convert read-only device facts into understandable capabilities, limitations, risks, recommended next steps, and retained evidence.

It is deliberately not the entire ecosystem.

## Ownership map

| Product | Owns | Does not own |
|---|---|---|
| ARCWYRE Native | From-scratch kernel, userspace, native services, operating-system security and recovery | General cross-platform workshop UI or third-party OS imaging |
| PhoenixCore | Device intelligence, diagnostics, plan generation, evidence orchestration, coordination contracts | Kernel, low-level USB library, complete repair desktop, or boot-media UI |
| BootForge | Reusable low-level USB discovery, enumeration, target identity, and carefully gated boot primitives | Complete technician workflow or diagnostic policy |
| Phoenix Key | End-user boot and recovery media experience powered by approved lower-level contracts | Silent target selection, hidden bypass, or unsupported writes |
| Bobby’s Workshop | Technician-facing cases, notes, guided workflows, approvals, reports, and integrated user experience | Reimplementation of every lower-level engine inside one repository |

## PhoenixCore responsibilities

PhoenixCore may:

- accept normalized read-only observations from supported adapters
- identify device family, connection mode, and confidence
- report missing or conflicting evidence
- calculate supported diagnostic capabilities
- recommend owner-authorized recovery paths
- produce machine-readable plans and evidence receipts
- coordinate with Phoenix Key and Bobby’s Workshop through versioned contracts

PhoenixCore must not:

- claim exact hardware identity from insufficient evidence
- authorize an operation because a fixture or mock succeeded
- treat a missing trust registry as approval
- select a physical write target silently
- bypass ownership, activation, account, firmware, bootloader, carrier, or platform security controls
- claim support for a platform merely because related code or documentation exists

## Contract rules

Every cross-repository contract must define:

- schema name and version
- producer and consumer
- required and optional fields
- identity and provenance fields
- confidence and limitation fields
- error model
- compatibility policy
- test fixtures
- migration and deprecation policy

Repositories may share versioned low-level libraries. They must not silently copy security-sensitive source and allow it to drift.

## Evidence ownership

- BootForge records low-level device and transport facts.
- PhoenixCore records diagnostic interpretation and planning facts.
- Phoenix Key records media-planning and approved write facts.
- Bobby’s Workshop records human approval, case activity, and technician-facing reports.
- ARCWYRE records native boot, kernel, userspace, and operating-system evidence.

Each layer preserves upstream identities rather than rewriting them into a single vague “success” event.

## Current boundary decision

The current repository is treated as a prototype collection while the canonical vertical slice is isolated. Existing modules, dashboards, plans, and recovered assets are not automatically part of the supported PhoenixCore surface.

Issue [#125](https://github.com/Bboy9090/PhoenixCore-/issues/125) owns the initial supported-surface decision.
