## Goal
Make BootForge/Phoenix Key the supplier of core capabilities (no runtime dependency on external imaging/USB tools).

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
- [ ] [TASK] Create Supplier Matrix (inventory all dependencies)
- [ ] [TASK] Define Core Capability Contracts (provider interfaces)
- [ ] [TASK] Windows Disk + Partition Enumeration (real)
- [ ] [TASK] Safety Engine (policy + confirmation tokens)
- [ ] [TASK] Imaging Read Probe + Chunk Hashing
- [ ] [TASK] Evidence Reports (run bundles)
- [ ] [TASK] Windows Installer USB Workflow (MVP)
- [ ] [TASK] CI: Windows build + tests
- [ ] [TASK] Docs: “No Wrapper” policy + contribution rules