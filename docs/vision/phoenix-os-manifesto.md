# Phoenix OS Manifesto

## Purpose

Phoenix OS exists to make serious computing feel recoverable, personal, and powerful again.

It is an everyday desktop operating system for normal users, streamers, creators, gamers, students, repair techs, and power users. It must boot into a complete daily-driver desktop first, then reveal recovery, deployment, diagnostics, and provisioning superpowers when they are needed.

Phoenix OS is not a recovery toolkit with a wallpaper. It is not an Ubuntu remix with extra apps. It is not a forensic workstation, an enterprise dashboard, or a pile of disconnected experiments. It is a coherent operating system with a strong identity and a disciplined platform underneath it.

## Canonical Naming

- Phoenix OS: the operating system.
- Phoenix Platform: the monorepo ecosystem that builds the OS, apps, services, crates, docs, and tooling.
- Phoenix Control Center: the main desktop control surface for settings, device health, recovery, deployment, updates, and diagnostics.
- Phoenix Agent: the privileged backend bridge/service that exposes safe system operations to Phoenix apps.
- BootForge: the deployment, imaging, installer-media, and USB creation layer.
- Phoenix Key: the rescue, recovery, provisioning, and field-service mode.

Do not invent competing names for these roles. New features must attach to this vocabulary unless a new product boundary is explicitly approved.

## Canonical Stack

- Desktop app shell: Tauri + React + TypeScript + Tailwind + Rust.
- Agent: Rust-first, with FastAPI acceptable only as a transitional bridge while capabilities migrate.
- OS base: Debian/Ubuntu family.
- Desktop environment: KDE Plasma.
- Display stack: Wayland-first, with compatibility paths where needed.
- Mobile: Expo React Native.
- Web: Next.js.

Technology choices should reduce fragmentation. A new framework, language, service, or app stack needs a clear reason, owner, lifecycle, and retirement plan for any duplicated old path.

## What Phoenix OS Is

Phoenix OS is:

- A full daily-driver desktop operating system.
- A creator and streaming-ready workstation.
- A gaming-ready desktop with a practical path for GPU drivers, Steam, Proton/Wine, controllers, and performance tuning.
- A recovery-capable OS that can diagnose, repair, image, reinstall, and export evidence when systems fail.
- A deployment platform for building and managing bootable media through BootForge.
- A rescue/provisioning platform through Phoenix Key.
- A safety-first system for high-risk disk, boot, driver, and firmware-adjacent workflows.

The desktop must be useful before disaster strikes. Recovery is a flagship advantage, not the whole product.

## What Phoenix OS Is Not

Phoenix OS is not:

- Recovery-only.
- A random Linux remix.
- A skin over KDE with no platform strategy.
- A warehouse for every experiment.
- A generic enterprise monitoring suite.
- A forensic-only distribution.
- A gaming-only distribution.
- A cloud dashboard pretending to be an OS.
- A place to ship dangerous disk operations without shared safety gates.

If a feature cannot explain how it strengthens the everyday OS, the creator/gaming/media story, BootForge, Phoenix Key, or the safety platform, it does not belong in active source.

## Daily-Driver Philosophy

Phoenix OS must be comfortable for ordinary daily use:

- Fast install, clean first boot, and predictable updates.
- KDE Plasma as the default desktop, tuned for clarity and performance.
- Browser, office, media, app store, Flatpak, Bluetooth, Wi-Fi, printing, audio, and graphics support treated as core OS requirements.
- Phoenix Welcome for first-run setup, identity, app discovery, hardware readiness, recovery media prompts, and safe defaults.
- Phoenix Control Center as the primary place to understand and operate the machine.

The baseline user should not need to know the recovery story to enjoy the OS.

## Creator-First Philosophy

Creators and streamers are first-class users:

- OBS and media tools must have an obvious readiness path.
- Audio, camera, screen capture, codecs, GPU acceleration, and storage workflows must be tested as product workflows, not left as package trivia.
- The OS should make it easy to prepare a machine for streaming, editing, recording, uploading, and managing large media files.
- Performance controls should be understandable without turning the UI into a lab instrument.

Creator readiness is not a bundle of apps. It is an end-to-end workflow.

## Gaming Philosophy

Phoenix OS should be honest and practical about gaming:

- Provide a clear path for Steam, Proton/Wine, gamepads, launchers, GPU drivers, overlays, performance modes, and storage.
- Avoid pretending every game or anti-cheat stack will work.
- Surface compatibility, driver status, and performance tips in Phoenix Control Center.
- Keep gaming support compatible with everyday desktop stability.

Gaming readiness is a promise to guide the user, not a promise to magically solve every proprietary edge case.

## Recovery Philosophy

Recovery is a superpower, not the whole identity:

- BootForge creates and manages deployment and imaging media.
- Phoenix Key provides rescue, provisioning, diagnostics, and field-service mode.
- Phoenix OS itself should include guided repair, backup, logs, and restore paths where safe.
- Recovery workflows must be auditable and reversible where possible.
- The user must always understand which disk, partition, image, driver, or boot component is being touched.

Phoenix should help users recover confidence, not just recover files.

## Safety Model

All high-risk operations must pass through shared safety gates:

- Disk writes, formatting, repartitioning, bootloader changes, driver injection, firmware-adjacent actions, OCLP workflows, BootCamp provisioning, and destructive repair actions require explicit policy.
- Dry-run and preview modes are preferred before destructive execution.
- Device identity must be shown clearly before write operations.
- System disks must be protected by default.
- Reports, logs, hashes, and manifests must be generated for operations that change system state.
- The privileged boundary belongs in Phoenix Agent and Rust system crates, not scattered across UI code.

The UI may request dangerous work. The platform decides whether it is allowed.

## UI Philosophy

Phoenix UI should feel calm, capable, and direct:

- Build real tools, not marketing screens.
- Prefer clear dashboards, progressive disclosure, and guided workflows.
- Use plain language for normal users, with expert detail available when needed.
- Keep recovery and deployment flows deliberate, visible, and hard to trigger accidentally.
- Avoid novelty UI that hides system truth.
- Avoid clutter, giant decorative surfaces, and feature sprawl.

Phoenix Control Center is the main trust surface. It should make the machine feel understandable.

## Update Philosophy

Updates must protect the user:

- OS updates should be predictable, recoverable, and explain what changed.
- Phoenix-owned packages should have versioned release notes.
- BootForge and Phoenix Key content should be checksum-verified.
- Risky platform updates should provide rollback or recovery instructions.
- Update flows should never silently invalidate rescue media, driver caches, or user recovery assumptions.

The update system is part of the safety story.

## Anti-Bloat Rules

Active source must stay disciplined:

- No checked-in dependency directories.
- No build outputs, release outputs, caches, generated archives, PyInstaller artifacts, or duplicate generated app projects in active source.
- No new app stack without retiring or archiving the old one.
- No duplicate backend for the same role.
- No feature without a product owner, platform boundary, and test path.
- No docs that describe a different product without being marked historical or archived.

The repository should feel like an operating-system company, not an upload folder.

## App Ecosystem Rules

Apps must fit the platform:

- Phoenix Control Center owns system understanding and safe operations.
- Phoenix Welcome owns first-run onboarding.
- BootForge owns deployment and imaging media creation.
- Phoenix Key owns rescue and provisioning mode.
- Mobile apps support remote planning, monitoring, companion flows, and field workflows.
- Web apps support documentation, account/cloud-adjacent experiences, downloads, and public product surfaces.

Apps should share contracts through Phoenix Agent and Rust crates instead of duplicating system logic.

## Hardware Philosophy

Phoenix OS should respect real machines:

- Hardware detection must be accurate, explainable, and reportable.
- Wi-Fi, Bluetooth, printers, cameras, audio, graphics, storage, thermal state, and battery status are daily-driver concerns.
- Unsupported or partially supported hardware should be surfaced honestly.
- Repair-tech workflows should show enough detail for diagnosis without overwhelming normal users.
- Apple hardware, BootCamp, OCLP, and cross-platform provisioning are flagship advantages, but must remain compliant and safety-gated.

Hardware support is product experience, not only kernel compatibility.

## Decision Rule

When a future change is unclear, ask:

1. Does this strengthen Phoenix OS as an everyday desktop?
2. Does it improve creators, streamers, gamers, students, repair techs, or power users?
3. Does it preserve or improve recovery, deployment, diagnostics, BootForge, or Phoenix Key?
4. Does it reduce fragmentation instead of creating another competing system?
5. Does it respect the safety model?

If the answer is not clear, keep it out of active source until the product boundary is clear.
