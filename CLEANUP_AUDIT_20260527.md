================================================================================
CLEANUP CANDIDATE AUDIT REPORT
Timestamp: 2026-05-27
Status: READ-ONLY ANALYSIS (NO DELETIONS PERFORMED)
================================================================================

SECTION 1: LARGE ISO/IMG ARTIFACTS WITH METADATA
================================================================================

--- os/phoenix-os/build/ ---
(12 items, ~25GB total)

DUPLICATES (exact SHA256 matches):
  bwos-home.iso [2.1G, May 27 20:05:50] [build]
    SHA: d60e651010bc355dbb9cd404d2666cebcf3a1881a4226721ee5540de1d7c5235
  live-image-amd64.hybrid.iso [2.1G, May 27 20:03:44] [build] **DUPLICATE**
    SHA: d60e651010bc355dbb9cd404d2666cebcf3a1881a4226721ee5540de1d7c5235
  phoenix-os-release-amd64.iso [2.1G, May 27 20:03:48] [build] **DUPLICATE**
    SHA: d60e651010bc355dbb9cd404d2666cebcf3a1881a4226721ee5540de1d7c5235
  → Deduplication savings if kept: 2 x 2.1GB = 4.2GB

Other edition ISOs (all unique, not latest):
  bwos-arcwyre.iso [2.2G, May 18 22:36:50]
  bwos-aurelia.iso [2.2G, May 18 16:09:52]
  bwos-forge.iso [2.2G, May 23 03:44:59]
  bwos-resilient.iso [2.2G, May 23 02:07:44]
  bwos-revival.iso [2.0G, May 23 01:20:01]
  bwos-thunder-god.iso [2.2G, May 18 20:23:25]

Legacy i386 artifacts:
  bwos-home-legacy-i386.img [2.2G, May 23 06:07:18]
    SHA: 70b8efd70b5a3ef0f919cd0f9b6058641c06b56e8cf39aa7290636c6df8207f7
    (checksum file exists and matches)

--- iso/outputs/ (top-level) ---
(8 items, ~19GB total)

bwos-home.iso [2.3G, May 26 13:32:46] [PASS artifact]
  SHA: ceb5cb1657f7b3da68eb5e9b1ef987618cc67ae167afe2f1ade03929987059db
  → Different from build version; this is from successful PR39L run
  → KEEP (latest passing evidence)

bwos-home-legacy-i386.img [2.2G, May 26 00:07:08]
  SHA: 70b8efd70b5a3ef0f919cd0f9b6058641c06b56e8cf39aa7290636c6df8207f7
  → Matches build version; appears to be duplicate

Other editions (archive copies, ~2.0-2.2G each):
  bwos-arcwyre.iso [May 23 04:36:51]
  bwos-aurelia.iso [May 23 02:52:59]
  bwos-forge.iso [May 23 03:45:01]
  bwos-resilient.iso [May 23 02:07:46]
  bwos-revival.iso [May 23 01:20:03]
  bwos-thunder-god.iso [May 18 20:24:36]

--- iso/outputs/archive/ ---
(2 items, ~4.2GB total)

bwos-home-4887e18fa3a6ee6b96637569be1591c13d037612fe5f5e45441c5233b2d0c75d.iso
  [2.1G, May 24 11:11:53]
  SHA: 4887e18fa3a6ee6b96637569be1591c13d037612fe5f5e45441c5233b2d0c75d
  → Filename keyed to SHA256; older archive copy
  → Not duplicate of current builds

legacy-i386-transition/ [2.1G]
  → Directory/folder; investigate contents
  (likely old build artifact)

STALE CHECKSUM FILES:
  /os/phoenix-os/build/bwos-home.iso.sha256
    Records: f113419abc4ad8c343cedb00a667e64fd13076f3c2ed87e658b63dea8059806d
    Actual SHA of current file: d60e6510...
    → STALE (file was updated after checksum was recorded)

================================================================================
SECTION 2: BUILD TELEMETRY & EVIDENCE STATUS
================================================================================

LATEST BUILD (FAILED):
  ID: 20260527T113106Z-home-amd64
  Status: FAILED (debootstrap stage)
  Start: 2026-05-27 11:31:06Z
  End: 2026-05-27 13:21:28Z
  Duration: ~110 min
  Artifact: NONE (failed)
  Telemetry: /os/phoenix-os/build/telemetry/20260527T113106Z-home-amd64/
  → KEEP (failure evidence for forensic review)

RECENT TELEMETRY FOLDERS (sample):
  20260527T061750Z: FAILED
  20260526T181416Z: COMPLETED ✓ (last successful)
  (multiple other folders, need to review mtime for cleanup eligibility)

TOTAL TELEMETRY SIZE: ~6.5M (small; safe to keep)

APP-LAUNCH-EVIDENCE:
  Total folders: 36 (in app-launch-evidence/home/)
  Total size: ~21M
  Latest: 20260527T060558Z
  Range: May 26 20:24:14 - May 27 06:05:58Z (all within PR40 testing window)
  Each folder: 0.5-0.8MB
  → These are PR40 test probes; mostly safe to archive if old ones not needed

PACKAGE CACHE:
  Path: /os/phoenix-os/cache/packages.chroot
  Size: 2.8G
  Files: 3334 .deb packages
  → Used for incremental builds to avoid re-downloading
  → KEEP (critical for next build attempt)

================================================================================
SECTION 3: DOCKER STATUS (NO PRUNE YET)
================================================================================

IMAGES: 16 total, 8 active, 16.02GB used
  Reclaimable: 3.062GB (19%) [from unused images]

CONTAINERS: 10 total, 5 active, 3.252MB
  Reclaimable: 1.929MB (59%) [from stopped containers]

VOLUMES: 8 total, 8 active, 514.8MB
  Reclaimable: 0B (0%) [all in use]

BUILD CACHE: 105 layers, 0 active, 10.68GB
  Reclaimable: 5.353GB (50%) [dangling/unused layers]

DOCKER CONTAINER STORAGE:
  Path: ~/Library/Containers/com.docker.docker
  Size: 18GB
  (VM disk image for Docker Desktop)

ESTIMATED DOCKER CLEANUP GAINS:
  Aggressive prune (system prune --volumes): ~8.4GB
  Safe prune (builder prune + image prune -a): ~5-8GB
  → Not critical; reclaim only if needed; do not touch until disk < 30GB

================================================================================
SECTION 4: CATEGORIZED RECOMMENDATIONS
================================================================================

SAFE TO MOVE/ARCHIVE (off-host or external drive):
────────────────────────────────────────────────────────
  1. Older edition ISOs in /os/phoenix-os/build/:
     - bwos-arcwyre.iso [2.2G, May 18]
     - bwos-aurelia.iso [2.2G, May 18]
     - bwos-forge.iso [2.2G, May 23]
     - bwos-resilient.iso [2.2G, May 23]
     - bwos-revival.iso [2.0G, May 23]
     - bwos-thunder-god.iso [2.2G, May 18]
     Subtotal: ~13.1G (if all moved)
     Reason: Older edition builds; not latest; not part of current PR39L

  2. Duplicate/stale ISOs in /iso/outputs/ matching /build/:
     - bwos-arcwyre.iso [2.2G] (May 23 in outputs, May 18 in build)
     - bwos-aurelia.iso [2.2G]
     - bwos-forge.iso [2.2G]
     - bwos-resilient.iso [2.2G]
     - bwos-revival.iso [2.0G]
     - bwos-thunder-god.iso [2.2G]
     Subtotal: ~13.1G (if all moved)
     Reason: Duplicates; older; preserved in /build/

  3. Old app-launch-evidence folders (not latest probe):
     - All folders except 20260527T060558Z (latest)
     - Range: 0.5-0.8MB each × 35 folders = ~21-24MB
     Subtotal: ~20M
     Reason: PR40 test probes; can archive if not active investigation

  4. Archive folder duplicate:
     - /iso/outputs/archive/bwos-home-4887e18fa3a6ee6b96637569be1591c13d037612fe5f5e45441c5233b2d0c75d.iso
     [2.1G, May 24]
     Reason: Old archived copy; SHA indicates older version

ESTIMATED GAIN: 13 + 13 + 0.02 + 2.1 = ~28GB if all moved

SAFE TO DELETE:
────────────────────────────────
  1. Empty or zero-size directories:
     - /os/phoenix-os/build/packages/ (0B)
     Reason: Empty; no packages stored

  2. Stale/mismatched checksum files:
     - /os/phoenix-os/build/bwos-home.iso.sha256
       (file was updated after checksum recorded; safe to regenerate)
     Reason: Can be regenerated

  3. Stale checksum in /iso/outputs/:
     - /iso/outputs/bwos-home-legacy-i386.img.sha256
       (checksum exists; matches current file; safe)
     - /iso/outputs/bwos-home.iso.sha256
       (checksum exists; safe to keep or regenerate)
     Reason: Can be regenerated if needed; tiny files

ESTIMATED GAIN: <1MB

KEEP / PROTECT:
────────────────────────────────
  1. Latest passing ISO:
     - /iso/outputs/bwos-home.iso [2.3G, May 26 13:32:46] [PASS]
     Reason: Latest successful PR39L evidence

  2. Failed build evidence:
     - /os/phoenix-os/build/telemetry/20260527T113106Z-home-amd64/
     - All files in this directory (build.log, build-events.jsonl, etc.)
     Reason: Failure forensics for root-cause analysis

  3. Build artifacts with potential future need:
     - /os/phoenix-os/build/bwos-home.iso [2.1G, May 27] (failed attempt)
       - Only if useful for debugging the failed build
       - Can be deleted if disk pressure > 25GB free

  4. Package cache:
     - /os/phoenix-os/cache/packages.chroot [2.8G]
     Reason: Critical for incremental builds; massive speedup

  5. Live-build config and source files:
     - All /os/phoenix-os/live-build/* (configs, hooks, lists)
     Reason: Source of truth; Git-tracked

  6. Latest PR40 app-launch-evidence:
     - /iso/outputs/app-launch-evidence/home/20260527T060558Z/
     Reason: Latest test probe run

  7. Git-tracked files:
     - All files under .git, all edition configs, all source
     Reason: Source repository

DO NOT TOUCH:
────────────────────────────────
  - .git folder and all version control
  - /editions/* (edition configs)
  - /os/phoenix-os/live-build/* (source)
  - /os/phoenix-os/branding/* (source)
  - Any hook or script files

================================================================================
SECTION 5: FREE-SPACE CALCULATION
================================================================================

CURRENT STATE:
  Filesystem total: 926 GB
  Used: 865 GB
  Free: 15 GB (1.6%)
  Capacity: 99% ⚠️ CRITICAL

TARGET DISK STATE (before rebuild):
  Recommended minimum: 40 GB free (4-5% capacity)
  Safer target: 50 GB free (5-6% capacity)

CLEANUP TO REACH 40GB FREE:
  Current free: 15 GB
  Needed: 40 - 15 = 25 GB additional
  
  Option A (Move older ISOs):
    Move 13G (editions) + 13G (archive editions) = 26G ✓ Achieves 40GB target
    
  Option B (Move + Docker prune):
    Move 13G (editions) = 28G total
    Docker prune: ~5-8GB
    Total gain: ~33-36GB
    New free: 48-51GB ✓ Exceeds 50GB safer target

RECOMMENDED SEQUENCE:
  1. Move /os/phoenix-os/build/bwos-*.iso [except home] to external → ~11G freed
  2. Move /iso/outputs/bwos-*.iso [except home] to external → ~11G freed
  3. Delete /os/phoenix-os/build/packages/ (empty dir)
  4. If still < 40GB free, run: docker builder prune --all → ~5GB freed
  5. If still < 40GB free, run: docker system prune → ~8GB freed
  6. Confirm df -h shows >= 40GB free before rebuilding

================================================================================
SECTION 6: DOCKER CLEANUP DETAILS (NO EXECUTION YET)
================================================================================

RECOMMENDATION: Safe Docker cleanup sequence (when needed)

Safe tier 1 (low risk):
  docker builder prune --all
  → Removes unused build cache layers
  → Reclaims: ~5.35GB
  → Does not affect running containers

Safe tier 2 (medium risk):
  docker image prune --all
  → Removes all unused images (must confirm which images are safe to remove)
  → Reclaims: ~3GB
  → Does not affect running containers or volumes

AGGRESSIVE (tier 3, only if disk < 30GB):
  docker system prune --volumes
  → Removes stopped containers, unused images, dangling volumes
  → Reclaims: ~8-10GB
  → WARNING: Volumes are deleted; confirm no persistent data needed

DO NOT RUN YET (these deletions are optional, use only if critical):

================================================================================
SECTION 7: SUMMARY TABLE
================================================================================

Category                  | Size    | Priority | Action
──────────────────────────┼─────────┼──────────┼────────────────────────────
Old edition ISOs (build)  | 13.1G   | MEDIUM   | Move to external
Old edition ISOs (outputs)| 13.1G   | MEDIUM   | Move to external
Archive ISO (May 24)      | 2.1G    | LOW      | Move to external
Old app-launch evidence   | 0.02G   | LOW      | Archive if not needed
Package cache             | 2.8G    | KEEP     | Do not delete
Latest pass evidence      | 2.3G    | KEEP     | Do not delete
Failed build telemetry    | 0.01G   | KEEP     | Keep for forensics
Docker images (unused)    | 3.06G   | DEFER    | Prune only if disk < 30GB
Docker build cache        | 5.35G   | DEFER    | Prune only if disk < 30GB
──────────────────────────┴─────────┴──────────┴────────────────────────────

TOTAL SAFE MOVE/DELETE: ~28-30GB
EXPECTED FREE SPACE AFTER: ~43-45GB (meets 40GB target)

================================================================================
SECTION 8: VERIFICATION COMMANDS (read-only, run to inspect before action)
================================================================================

# Confirm current free space:
df -h /Users/bj90-m1/PhoenixCore-

# List files to move (verify before deletion):
ls -lh /Users/bj90-m1/PhoenixCore-/os/phoenix-os/build/bwos-*.iso
ls -lh /Users/bj90-m1/PhoenixCore-/iso/outputs/bwos-*.iso
ls -lh /Users/bj90-m1/PhoenixCore-/iso/outputs/archive/

# Show what Docker would reclaim (no action):
docker system df

# Show space gain estimate:
du -sh /Users/bj90-m1/PhoenixCore-/os/phoenix-os/build
du -sh /Users/bj90-m1/PhoenixCore-/iso/outputs/

# Re-check free space after moves:
df -h /Users/bj90-m1/PhoenixCore-

================================================================================
