# PhoenixCore Roadmap

This roadmap locks what belongs in **PhoenixCore V1** and pushes everything else to **V2+**.  
V1 is about a reliable, boring‑in‑a‑good‑way rescue product, not every possible feature.

---

## PhoenixCore V1 (scope is locked)

V1 should deliver a complete, end‑to‑end rescue loop:

1. **Build bootable USB**
   - Build a PhoenixCore‑based image from source.
   - Write that image safely to USB (with dry‑run and confirmations).
   - Verify the write (hash checks, basic sanity checks on the target device).

2. **Boot rescue environment**
   - Boot reliably on supported hardware from the created USB.
   - Start the PhoenixCore runtime with access to disks and basic networking (where available).

3. **Detect drives / OS / hardware state**
   - Enumerate physical disks, partitions, and volumes.
   - Detect installed operating systems and basic hardware metadata.
   - Present this information in a human‑readable form (CLI and/or UI).

4. **Recover files**
   - Mount or otherwise read user data partitions in a read‑safe way.
   - Copy files out to another disk or network target.
   - Handle common failure modes gracefully (I/O errors, partial reads).

5. **Reinstall OS**
   - Select a target device and OS image.
   - Apply safety gates (multi‑step confirmation, device identity checks).
   - Lay down a fresh OS in a predictable, documented way.

6. **Export logs**
   - Capture logs from discovery, recovery, and reinstall workflows.
   - Export logs and an optional support bundle to external storage.
   - Make export paths obvious and easy to reference in support tickets.

All of the above should be:

- **Documented** in `README.md`, `WINDOWS-README.txt`, `QUICK_START.txt`, and `docs/*`.
- **Tested** via automated tests where possible (Rust + Python CI) and manual test plans where not.

---

## Out-of-scope for V1 (V2+)

Anything beyond the loop above should be considered **V2 or later**, for example:

- advanced partitioning UIs
- complex multi‑OS boot managers
- deep hardware diagnostics beyond what is needed for recovery decisions
- cloud‑integrated workflows (remote backup/restore, fleet‑wide orchestration)
- heavy customization frameworks or plugin ecosystems

These ideas are not rejected; they are explicitly **deferred** so V1 can ship as a dependable recovery tool.

---

## Principles for Future Versions

When planning V2+:

- do not break V1 workflows without a strong reason and migration path
- keep the bootable runtime small and reliable
- require clear user stories and maintenance ownership for new modules
- keep legacy or experimental work clearly marked (see `docs/REPO_MAP.md` and `archive/`)

