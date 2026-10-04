# ARCWYRE Drive capability convergence

ARCWYRE Drive is the public desktop product that converges the preserved BootForge Studio workflows with the guarded Phoenix Key/PhoenixCore recovery interface. The product must not claim full parity until each row below is wired into the ARCWYRE Drive UI and passes its stated gate.

## Source authorities

- Current guarded desktop and recovery implementation: PhoenixCore `main` at `2b16b6718fce98567038ec0d26f8ba0f3350c4f4`, under `apps/phoenix-key`.
- Preserved full BootForge Studio source: PhoenixCore commit `92ae215c`, under `bootable_usb/BootForge`, `build_system`, `create_recovery_usb.py`, and `usb_toolkit`.
- Connected-device engine: pinned `libbootforge` revision in `apps/phoenix-key/src-tauri/Cargo.toml`.

The historical BootForge implementation is evidence of intended capability, not automatic release proof. It contains incomplete and placeholder paths, so code is migrated behind PhoenixCore's current fail-closed safety contracts rather than copied wholesale into a release.

## Required product surface

| Capability family | Required ARCWYRE Drive behavior | Current authority | Convergence state |
|---|---|---|---|
| Connected devices | Detect actionable USB peripherals, iPhone Recovery/DFU, and Android ADB/Fastboot while hiding ordinary endpoints | `libbootforge` + current desktop | Wired |
| Removable media | Discover and identity-lock removable/external targets; block system, boot, fixed, read-only, unstable, or ambiguous disks | PhoenixCore current safety core | Wired |
| Raw image creation | Create media from a verified image with dry-run, explicit destructive consent, exact byte cap, cancellation, and full SHA-256 readback | PhoenixCore current Windows writer | Windows wired; macOS/Linux pending guarded adapters |
| Cross-platform host support | Run on Windows, macOS, and Linux and create supported Windows, macOS, Linux, and ARCWYRE media where licensing and host tooling permit | historical platform providers + current scanners | Migration required |
| Windows installation media | Inspect ISO/WIM/ESD/SWM and extracted media, handle FAT32 limits and split-WIM layouts, and build UEFI-compatible media | current Recovery Forge + historical builder | Inspection wired; creation migration required |
| Windows To Go | Create a portable Windows workspace only from a verified eligible Windows image, supported edition, external target, and validated boot layout | user-required product contract | Implementation and hardware proof required |
| Backup-to-drive recovery | Inspect WindowsImageBackup, VHD/VHDX, FFU, WinRE, local/external/cloud sources; bind source and target identities; preserve rollback evidence | current Recovery Forge | Read-only/evidence wired; restore executor intentionally locked |
| Clone and image | Capture a permitted source disk or partition to an image, verify it, resume safely, and restore only through a separately authorized plan | historical intent + current evidence primitives | Implementation required |
| Multiboot | Build GPT/UEFI multiboot media for eligible Windows, Linux, macOS/OpenCore, and ARCWYRE sources with deterministic manifests | historical GRUB manager/builder | Migration and boot-matrix proof required |
| macOS installers | Build supported macOS installer/recovery media; distinguish Intel and Apple Silicon routes | historical macOS provider/OCLP pipeline + current platform gates | Migration required |
| OpenCore/OCLP | Detect exact Mac model, assess compatibility, obtain user-supplied or licensed assets, create EFI, retain consent and evidence, and never invent support | historical OCLP pipeline + current Intel/Apple Silicon gate | Migration and current OCLP validation required |
| Boot Camp | Inspect and verify Boot Camp support software, plan Intel Mac Windows recovery, preserve APFS/macOS, and reject traditional Boot Camp on Apple Silicon | current Recovery Forge | Planning wired; mutating execution locked |
| Linux media | Verify Linux images and build supported UEFI/BIOS media with optional persistence when explicitly configured | historical Linux provider/GRUB manager | Migration required |
| Boot repair | Inspect and plan EFI/BCD/WinRE and Linux bootloader repairs, require backups, and retain rollback evidence before mutation | current Recovery Forge | Windows planning/evidence wired; executors locked |
| Drivers and patches | Inventory, verify, and inject approved Windows/Boot Camp drivers or apply supported patch recipes without bundled unlicensed payloads | historical plugins/patch planner + current manifests | Migration and trust hardening required |
| Image library | Add, classify, hash, cache, download, and verify OS/recovery images with provenance and resumable transfer | historical image manager + current cloud stage | Migration required |
| Diagnostics | Hardware/profile detection, logs, reports, SMART/health where supported, and exportable evidence bundles | historical diagnostics + current evidence bundle | Partial; unified UI required |
| Recipes and plugins | Signed/versioned recipes and governed plugins with explicit capabilities; fail closed for unknown or unsigned actions | historical managers + PhoenixCore governance | Migration required |
| Packaging | Produce signed/notarized Windows, macOS, and Linux installers from one release train with exact-SHA receipts | current workflows + historical packager | Windows/macOS workflows exist; Linux product packaging required |

## Non-negotiable safety and truth rules

1. Browser and store-safe editions never expose raw disk mutation or external helper execution.
2. No target is selected automatically and no stale disk identity authorizes a write.
3. Every destructive action requires a fresh scan, exact target identity, preview, typed authorization, explicit data-loss acknowledgement, and retained result receipt.
4. Backup inspection never implies that a backup is restorable. A restore path stays locked until source integrity, destination safety, rollback evidence, and platform compatibility are proven.
5. Third-party bootloaders, patchers, operating-system images, drivers, and firmware are user-supplied or obtained from authorized upstream sources with license/provenance records.
6. Placeholder, template, simulated, or TODO implementations are never presented as completed features.

## Release gate

ARCWYRE Drive cannot be called feature-complete until every required row is either `Wired` with retained tests/evidence or explicitly excluded from the product contract by an approved decision. Store submission must use a capability-accurate description for the exact signed artifact; it must not advertise the still-locked writers, restore executors, or repair executors.
