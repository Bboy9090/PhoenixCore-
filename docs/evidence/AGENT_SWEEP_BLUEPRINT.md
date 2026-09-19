# Agent Sweep Blueprint

Purpose: preserve the reasoning, evidence, failures, fixes, and exit criteria from Windows Recovery Forge so future agents can start from a proven operating method instead of rediscovering the same process.

This is a living document. Every material pass should append evidence, not overwrite history.

## 0. Standard sweep record

For every sweep/pass, record:

- Sweep ID / name
- Date / branch / starting HEAD
- Objective: what this pass is meant to prove
- Inputs: files, fixtures, hardware, branches, APIs, connected sources
- Scope: exact subsystems touched
- Non-goals: what must remain unchanged
- Tests / commands / CI jobs run
- Findings: defects, unknowns, regressions, missing evidence
- Fixes made
- Safety impact
- User-experience impact
- Evidence: commits, logs, CI checks, receipts, screenshots, manifests
- Exit criteria
- Result: PASS / PARTIAL / FAIL / BLOCKED
- Carry-forward items
- Agent lesson: what the next project should copy or avoid

The most important rule: a pass is not complete because code was written. It is complete only when its claim is backed by repeatable evidence.

---

# WINDOWS RECOVERY FORGE — RECORDED PASSES

## Sweep 1 — Repository / lineage reconnaissance

Objective:
Establish the real repository, current branch family, reusable BootForge/Phoenix Key infrastructure, and historical recovery/USB work before implementation.

Key work:
- identified `Bboy9090/PhoenixCore-` as the target repository
- treated historical branches and commits as coordinates, not automatically trustworthy integration targets
- reviewed BootForge, Phoenix Key, USB writer, recovery, installer, Wave 7/8/9, and safe-device writer lineage
- explicitly separated Phoenix/BootForge/ARCWYRE work from unrelated projects
- selected a convergence strategy instead of restarting architecture

Why this pass matters:
Future agents must never start by coding from a user description alone when a mature repo already exists. First establish canonical lineage and where the strongest implementation already lives.

Reusable agent instruction:
> Before changing code, inventory remotes, branches, heads, relevant historical commits, current tests, safety gates, and overlapping implementations. Build a lineage matrix and choose the integration base from evidence rather than branch names.

Exit criteria:
- correct repository established
- active convergence lane identified
- no blind branch merge/cherry-pick
- existing writer/safety architecture understood

Result: PASS.

---

## Sweep 2 — Safety-boundary baseline

Objective:
Ensure recovery analysis can be developed without opening a new destructive disk-write path.

Key work:
- recovery work began read-only
- existing Phoenix Key writer remained isolated
- added/kept a machine-checkable destructive-boundary scan
- prohibited recovery analysis/probe code from calling physical writer operations, partitioning tools, filesystem creators, low-level Windows device writes, or `dd`

Safety doctrine established:
- inspection and planning are separate from execution
- destructive restore features do not get enabled merely because the planner recognizes a source
- write operations require their own identity, target, rollback, and authorization gates

Reusable agent instruction:
> Draw the destructive boundary before feature work. Separate discovery/planning from mutation. Add a CI check that proves the safe layer cannot invoke the destructive layer.

Exit criteria:
- analysis/probe layer cannot write disks
- safety claim enforced by CI, not prose alone

Result: PASS.

---

## Sweep 3 — Cross-platform recovery-core build baseline

Objective:
Prove that the recovery engine builds/tests consistently on Windows, macOS, and Linux.

Initial finding:
Ubuntu failed while Windows and macOS passed.

Root cause:
The failure was CI environment setup, not recovery logic. Tauri's Linux dependency graph required GTK/GLib/WebKit development packages that the runner lacked.

Fix:
- standardized Linux gate on Ubuntu 22.04
- installed Tauri v1 prerequisites including WebKit2GTK/GTK/SSL/AppIndicator/RSVG/patchelf dependencies

Important lesson:
A failing platform job must be classified before modifying application code. Distinguish infrastructure failure from product logic failure.

Reusable agent instruction:
> When one platform fails, first determine whether the failure is environment, dependency, compile, unit test, runtime, packaging, or behavior. Do not "fix" product code for a missing runner dependency.

Exit criteria:
- unit tests execute on each supported CI OS
- recovery probe builds
- Clippy/static checks run
- Linux environment is reproducible

Result: PASS for the infrastructure correction; subsequent integrated sweeps continue validating product changes.

---

## Sweep 4 — Source intelligence / backup classification

Objective:
Make Phoenix Key understand what the user actually selected instead of treating every file/folder as an opaque path.

Implemented recognition includes:
- Windows installer media
- WIM / ESD image sources
- VHD / VHDX images
- WinRE/recovery media
- extracted Windows media structures
- WindowsImageBackup hierarchy
- incomplete WindowsImageBackup cases where metadata exists but the actual VHD/VHDX payload is absent

Output was expanded beyond a technical type identifier to include:
- confidence
- plain-language summary
- recommended action
- restore-candidate state
- warnings
- detected evidence/signatures
- discovered system-image files

Key principle:
Never infer that a backup is restorable merely because its folder name looks correct.

Reusable agent instruction:
> Build signature-based source intelligence before implementing execution. Classification must explain what evidence caused the classification and must have an explicit incomplete/ambiguous state.

Exit criteria:
- supported source types are distinguishable
- incomplete backups do not masquerade as valid restore sources
- classification contains explainable evidence

Result: PASS for first source-intelligence layer.

---

## Sweep 5 — Hardware / architecture routing

Objective:
Prevent Phoenix Key from proposing an impossible Windows recovery route on the wrong Mac architecture.

Implemented policy:
- Intel Mac can proceed toward traditional Boot Camp-specific planning, subject to exact hardware/driver/partition checks
- Apple Silicon is explicitly blocked from pretending traditional Boot Camp is supported
- Apple Silicon routes toward supported ARM VM/VHDX/external recovery strategies instead
- Windows-native and generic cross-platform analysis remain distinct routes

Reusable agent instruction:
> Detect hardware/architecture before presenting workflows. Unsupported operations should not merely fail late; they should disappear or be clearly blocked at planning time with the correct alternative route.

Exit criteria:
- Intel and Apple Silicon are not conflated
- user gets an actionable route instead of a generic incompatibility error

Result: PASS for routing baseline; exact Intel model/driver mapping remains future work.

---

## Sweep 6 — Dry-run recovery planning

Objective:
Turn source detection into a structured plan without performing recovery.

Planning gates established around:
- source integrity/completeness
- target enumeration
- source/target separation
- target identity
- capacity
- partition layout
- EFI / boot mode
- Intel Mac/Boot Camp compatibility
- rollback requirements
- explicit destructive authorization
- immediate pre-write identity recheck

Key principle:
A dry run is a product feature, not just a developer flag. The user should be able to understand the intended changes before any destructive step exists.

Reusable agent instruction:
> Every destructive workflow should have a first-class dry-run representation that describes inputs, target, planned mutations, blocking conditions, rollback evidence, and authorization requirements.

Result: PASS for planning architecture; execution intentionally remains disabled.

---

## Sweep 7 — Recovery Center backend boundary

Objective:
Expose recovery intelligence to the desktop app without exposing destructive operations.

Implemented:
- dedicated read-only Recovery Center command boundary
- inspection and plan commands registered with the Tauri application
- writer commands remain separate
- recovery probe was expanded so the CI target compiles the same recovery boundary rather than testing only an isolated helper

Reusable agent instruction:
> Do not let a UI call internal helper code through ad-hoc bridges. Create a narrow explicit application command boundary and include that boundary in CI.

Exit criteria:
- desktop command registration compiles
- recovery commands are read-only
- CI includes the boundary module

Result: PASS for backend integration.

---

## Sweep 8 — Human-readable Recovery Center UX

Objective:
Replace raw engineering output with an interface a non-expert can follow correctly.

Implemented UX principles:
- Recovery Center enabled as a real navigation destination
- read-only state visibly labeled
- plain-language summary shown first
- confidence and warnings visible
- "what we found" separated from "what this computer can do"
- recommended next route shown
- technical JSON/evidence hidden behind an optional disclosure
- keyboard focus and reduced-motion considerations added to styles

Important lesson:
Raw JSON is evidence, not primary UX.

Reusable agent instruction:
> For every technical subsystem, design two views: a human decision view and an expandable evidence view. The evidence must remain available without forcing normal users to interpret implementation-level structures.

Result: PASS for first usability layer; accessibility/first-run language still requires hostile user testing.

---

## Sweep 9 — Native source chooser / path-entry reduction

Objective:
Remove unnecessary technical burden from the user.

Finding:
Requiring people to type paths such as `/Volumes/...` or `C:\\...` contradicted the goal of an easy recovery utility.

Fix:
- native "Choose Backup Folder" flow
- native "Choose Image File" flow
- manual path remains available for advanced users
- Tauri permission expanded narrowly for native open-dialog capability while shell execution remains disabled

Reusable agent instruction:
> Any field that expects users to know filesystem syntax should be challenged. Prefer constrained native selection, discovery, or auto-detection, while retaining a manual advanced path when useful.

Result: PASS.

---

## Sweep 10 — Integrated CI gate expansion

Objective:
Make the convergence branch prove the complete recovery slice rather than individual files.

Current recovery-specific gates include:
1. Rust recovery core — Windows
2. Rust recovery core — macOS
3. Rust recovery core — Ubuntu 22.04
4. Recovery Center TypeScript/Vite build
5. destructive-boundary scan

Related repository-wide gates continue independently.

Required interpretation:
A green feature-specific workflow is necessary but not sufficient for release. It proves the recovery slice is internally coherent, not that destructive recovery is ready.

Reusable agent instruction:
> Maintain a small feature-specific CI workflow with fast, explicit proof gates. Do not rely only on giant repository CI where the signal is difficult to interpret.

Result: ACTIVE / recurring after each integrated change.

---

# PLANNED PASSES

## Sweep 11 — Hostile source fixture pass

Objective:
Break source classification deliberately.

Fixtures required:
- empty directory
- random file renamed `.iso`
- zero-byte WIM/VHDX
- truncated image
- corrupted header/signature
- incomplete split WIM/SWM set
- WindowsImageBackup metadata without image payload
- multiple backup generations
- deeply nested backup
- symlink/path alias cases where supported
- source that changes between analysis and plan

Exit criteria:
- no hostile input becomes a high-confidence restore candidate incorrectly
- errors are understandable
- parser remains bounded and does not scan indefinitely

---

## Sweep 12 — Source integrity and change-detection pass

Objective:
Prove that the source analyzed is the source eventually used.

Required evidence:
- stable source identity record
- file size / modification metadata
- hashes where practical
- manifest for multi-file backups
- changed-source invalidation between analysis, planning, staging, and execution

Exit criteria:
Any material source change forces re-analysis/re-authorization.

---

## Sweep 13 — Target collision / capacity / topology pass

Objective:
Prevent valid source recognition from producing an unsafe restore target.

Tests:
- source and target are same physical device
- target smaller than required image
- target disappears/reappears under a different identifier
- internal/system disk selected accidentally
- ambiguous disk identity
- partition map conflicts
- APFS/macOS partitions present
- insufficient contiguous space for Boot Camp-style allocation

Exit criteria:
Unsafe topology never reaches executable state.

---

## Sweep 14 — Intel Mac exact-model + Boot Camp driver pass

Objective:
Stop treating all Intel Macs as equivalent.

Required work:
- exact Mac model identifier
- firmware/boot characteristics
- supported Windows generation where applicable
- exact or verified-compatible Boot Camp support package
- driver manifest
- no random driver injection

Exit criteria:
Phoenix Key can explain why a specific driver package matches a specific machine.

---

## Sweep 15 — EFI / BCD / WinRE evidence pass

Objective:
Model recovery boot state before mutation.

Evidence to capture:
- EFI System Partition state
- Windows boot files
- BCD configuration
- Windows partition identifiers
- WinRE configuration
- expected post-restore boot layout

Exit criteria:
The plan can distinguish image restoration from boot repair and avoid unnecessary rewrites.

---

## Sweep 16 — Rollback-manifest pass

Objective:
Make rollback a prerequisite, not an afterthought.

Manifest should include where applicable:
- GPT / partition table snapshot
- partition UUIDs / identifiers
- EFI directory inventory
- BCD export
- WinRE state
- hardware identity
- source identity
- target identity
- driver selection
- planned mutations
- logs / checksums / timestamps

Exit criteria:
No destructive restore path can unlock without a persisted rollback package.

---

## Sweep 17 — Interruption / power-loss / unplug pass

Objective:
Define behavior when recovery stops halfway.

Cases:
- source staging interrupted
- target unplugged before mutation
- target unplugged during write
- application crash
- host reboot
- storage-full/ENOSPC
- corrupted temporary cache
- resume after partial transfer

Exit criteria:
Every interruption state has a deterministic receipt and safe recovery/resume rule.

---

## Sweep 18 — Google Drive staging pass

Objective:
Use connected cloud backup safely without pretending metadata-only access is a restorable binary image.

Rules:
- cloud original remains unchanged
- discover source metadata first
- materialize/stage only when binary file access is available
- resumable transfer
- checksum or equivalent integrity proof
- local cache manifest
- no restore until payload completeness is proven

Current known condition:
A WindowsImageBackup hierarchy has been located in connected Drive, but the actual binary VHD/VHDX payload has not yet been exposed through the available connector path. Treat as incomplete until staged and verified.

---

## Sweep 19 — Accessibility / first-run comprehension pass

Objective:
Test whether a user can make the correct choice without already understanding recovery terminology.

Scenarios:
- user selects wrong folder level
- user selects an installer ISO when they intend to restore an old system
- user has Apple Silicon but asks for Boot Camp
- user has incomplete cloud backup
- user has multiple removable disks
- user cannot distinguish source vs target

Required UX checks:
- keyboard-only
- focus order
- screen-reader labels
- high zoom/small window
- reduced motion
- actionable error language
- no irreversible button presented prematurely

Exit criteria:
The user can tell what Phoenix Key found, what it cannot do yet, what it needs next, and whether anything will modify their disks.

---

## Sweep 20 — Release evidence pass

Objective:
Prove the application that passed tests is the application being distributed.

Evidence:
- exact source commit
- clean build provenance
- signed/notarized desktop artifacts as applicable
- artifact hashes
- installed-app smoke test
- recovery feature smoke test
- permissions/capability audit
- release manifest

Exit criteria:
Release artifact can be traced to an exact tested commit.

---

# END-OF-PROJECT AGENT BLUEPRINT

When handing the next project to agents, use this sequence.

## Phase A — Reconnaissance

Agent must:
1. identify canonical repo/branch/head
2. inventory historical branches/PRs/commits
3. identify duplicate/superseded implementations
4. map architecture and safety boundaries
5. build a lineage matrix
6. choose integration base from evidence

Deliverable:
`RECON_REPORT.md`

## Phase B — Baseline verification

Agent must:
1. run existing tests without modifications
2. classify failures by infrastructure vs product
3. establish platform matrix
4. preserve known-good evidence

Deliverable:
`BASELINE_EVIDENCE.md`

## Phase C — Feature slice

Agent must:
1. implement smallest coherent vertical slice
2. preserve existing safety boundaries
3. expose human-readable output
4. expose technical evidence separately
5. add tests with the feature

Deliverable:
code + feature-specific CI.

## Phase D — Hostile testing

Agent must deliberately test malformed inputs, stale state, missing dependencies, contradictory state, interruptions, invalid targets, and user mistakes.

Deliverable:
`HOSTILE_TEST_MATRIX.md`

## Phase E — Safety / rollback

Any feature capable of mutation must establish target identity, source identity, dry-run, rollback evidence, explicit authorization, pre-action revalidation, and post-action verification.

Deliverable:
`SAFETY_CONTRACT.md`

## Phase F — UX simplification

Agent must remove avoidable expert-only steps, add native selection/discovery where possible, make errors actionable, and verify accessibility/focus/first-run behavior.

Deliverable:
`UX_ACCEPTANCE_MATRIX.md`

## Phase G — Release proof

Agent must prove exact source → CI → artifact → installed behavior lineage.

Deliverable:
`RELEASE_EVIDENCE.md`

---

# STANDARD AGENT PROMPT SKELETON

Use this as the base prompt for future projects:

> You are joining an existing production project. Do not restart it, redesign it from scratch, or assume `main` is the best implementation.
>
> First perform repository reconnaissance and establish the canonical repo, branch, HEAD, architecture, safety boundaries, existing test coverage, active PRs, relevant historical branches, and superseded implementations. Produce a lineage matrix before integration decisions.
>
> Work in evidence-backed sweeps. For every sweep record: objective, starting state, inputs, scope, non-goals, tests, findings, fixes, safety impact, UX impact, evidence, exit criteria, result, and carry-forward items.
>
> Separate read-only discovery/planning from mutation. Any destructive feature requires a dry run, stable source identity, stable target identity, source/target separation, rollback evidence, explicit authorization, immediate pre-action revalidation, and post-action verification.
>
> When a test fails, classify the failure before editing code: infrastructure, dependency, compile, unit test, integration, runtime, packaging, environment, hardware, or product logic.
>
> Build one coherent vertical slice at a time. Add its tests and feature-specific CI in the same pass. Do not call a pass complete because code exists; require repeatable evidence.
>
> Design two output layers: plain-language decision UX for normal users and expandable technical evidence for advanced/debug use.
>
> Run hostile-input and interruption testing before enabling destructive execution. Treat unsupported, ambiguous, incomplete, or changed state as blocked—not as best-effort success.
>
> Maintain a living sweep blueprint so another agent can resume from exact evidence without rediscovering previous reasoning.
>
> Do not stop at an architecture document. Implement, test, repair, document the evidence, and leave the branch in a verifiable state.

---

# DAILY CLOSING CHECKLIST

Before ending a work day, update this file with:
- new sweeps completed
- new failures discovered
- fixes and commit SHAs
- CI result for the exact current HEAD
- current blockers
- unverified assumptions
- next three highest-value sweeps
- safety boundary changes, if any
- UX findings
- release-readiness delta

This makes the day's work directly reusable as training material for the next agent/team/project.