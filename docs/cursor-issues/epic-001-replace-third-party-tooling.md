# [EPIC-001] Replace 3rd-party tooling with BootForge Core (Windows First)

Cursor tags: type:epic, area:core, P0-blocker, M0-spine  
Status: In Progress

## Goal
Make BootForge/Phoenix Key the supplier of core capabilities (no runtime dependency on external imaging/usb tools).

## Non-goals
- No macOS/Linux providers in this epic (Windows-first)
- No UI polish beyond basic usability
- No destructive writes without force-mode + confirmation token

## Deliverables
1) Supplier Matrix + dependency inventory
2) Host-Windows provider: disks/partitions/mounts + safety classification
3) Imaging engine: read-only probe + chunk hashing + evidence reports
4) USB build pipeline: partition/format/stage Windows installer media
5) Workflow engine: declarative workflows + audit logs
6) CI: Windows build + tests

## Acceptance Criteria
- No external executables required at runtime for Windows USB creation (by end of M1)
- Every workflow emits a signed evidence report bundle
- System disk writes are blocked by default, always

## Breakdown
- [ ] [TASK-001] Create Supplier Matrix (inventory all dependencies)
- [ ] [TASK-002] Define Core Capability Contracts (provider interfaces)
- [ ] [TASK-003] Windows Disk + Partition Enumeration (real)
- [ ] [TASK-004] Safety Engine (policy + confirmation tokens)
- [ ] [TASK-005] Imaging Read Probe + Chunk Hashing
- [ ] [TASK-006] Evidence Reports (run bundles)
- [ ] [TASK-007] Windows Installer USB Workflow (MVP)
- [ ] [TASK-008] CI: Windows build + tests
- [ ] [TASK-009] Docs: “No Wrapper” policy + contribution rules

## References
- docs/no-wrapper-policy.md
- docs/supplier-matrix.md
- docs/device-graph.md
