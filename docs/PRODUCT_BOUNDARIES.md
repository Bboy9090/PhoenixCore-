# PhoenixCore Product Boundaries

## Purpose

PhoenixCore is the device-intelligence, compatibility, repair-planning, and evidence-orchestration layer in Bobby’s Workshop. It converts read-only device facts into understandable capabilities, limitations, risks, recommended actions, and versioned repair-session contracts.

It is not the entire ecosystem and must not duplicate the native operating-system source.

## Ownership map

| Product | Owns | Does not own |
|---|---|---|
| Phoenix Prime Kernel | Shared native kernel, boot, memory, scheduling, syscalls, drivers, native security | Cross-platform workshop applications or host-side USB orchestration |
| ARCWYRE Native | Lightweight repair-first native edition | General host-side diagnosis or third-party OS media acquisition |
| ARCWYRE Eternum | Performance, creator, developer, and future gaming native edition | Mobile diagnosis or host-side USB writing |
| ARCWYRE Live | Live native repair, recovery, manifest verification, and deployment execution | Host-side app packaging or silent repair authorization |
| PhoenixCore | Device interpretation, diagnostics, compatibility decisions, plan generation, repair-session contracts, evidence orchestration | Kernel, native drivers, or a second ISO builder |
| BootForge | Reusable low-level USB discovery, immutable target identity, and gated media primitives | Complete technician workflow or diagnostic policy |
| Phoenix Key | User-facing approved media workflow and write receipts | Silent target selection or unsupported writes |
| Bobby’s Workshop | Human approvals, cases, notes, reports, and integrated technician experience | Reimplementation of every lower-level engine in one repository |

## PhoenixCore responsibilities

PhoenixCore may:

- accept normalized read-only observations from supported adapters
- identify device family, connection mode, confidence, and unknown fields
- report missing or conflicting evidence
- calculate supported diagnostic and installation options
- recommend owner-authorized recovery paths
- create versioned repair-session and build-request manifests
- preserve upstream artifact and evidence identities
- coordinate with Phoenix Key and ARCWYRE Live

PhoenixCore must not:

- claim exact identity from insufficient evidence
- authorize work because a fixture or mock succeeded
- treat a missing, malformed, unsigned, mismatched, or untrusted registry as approval
- select a physical target silently
- permit an internal, system, boot, fixed, identity-mismatched, or ambiguous drive
- represent a JSON manifest as a completed ISO
- bypass ownership, activation, FRP, MDM, credentials, anti-theft, carrier, firmware, or platform controls
- claim platform support merely because related code exists

## Contract rules

Every cross-repository contract defines:

- schema name and version
- producer and consumer
- required and optional fields
- source commit and artifact provenance
- identity, confidence, and limitation fields
- error model
- compatibility policy
- test fixtures
- migration and deprecation policy
- signature and checksum policy

Security-sensitive code must not be copied across repositories and allowed to drift. Shared behavior crosses boundaries through reviewed libraries or versioned schemas.

## Evidence ownership

- BootForge records device and transport facts.
- PhoenixCore records diagnostic interpretation, compatibility, and planning facts.
- Phoenix Key records media planning, authorization, write, and read-back facts.
- ARCWYRE records native boot, kernel, userspace, repair, and deployment facts.
- Bobby’s Workshop records human approval, case activity, and technician-facing reports.

Each layer preserves upstream identities instead of rewriting them into one vague `success` event.

## Hardware evidence decision

Real physical-drive evidence is allowed only after:

1. immutable read-only target identity
2. explicit sacrificial-drive designation
3. image identity and size verification
4. elevated process and exclusive-handle proof
5. typed confirmations and exact target re-entry
6. bounded write and full read-back hash
7. retained boot receipt

This is not a prohibition on hardware access. It is the required proof boundary between an authorized test and accidental destruction.
