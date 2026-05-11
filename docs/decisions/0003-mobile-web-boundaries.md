# 0003: Mobile And Web Boundaries

Status: Accepted

Date: 2026-05-11

## Decision

Phoenix Mobile uses Expo React Native.

Phoenix Web uses Next.js in the future for public web, docs, downloads, cloud-adjacent surfaces, support, marketing, and demos.

Current Vite or generated web prototypes are references unless manually migrated into canonical Phoenix Web source.

## Mobile Boundary

Phoenix Mobile may:

- monitor Phoenix systems,
- show devices and build status,
- guide users through safe workflows,
- call Phoenix Agent APIs,
- provide companion flows for creators, repair techs, students, streamers, and power users.

Phoenix Mobile must not:

- execute destructive local disk operations directly,
- own bootloader/imaging logic,
- become the desktop Control Center.

## Web Boundary

Phoenix Web may:

- explain Phoenix OS,
- host docs and downloads,
- publish support and product pages,
- expose cloud-adjacent or demo experiences,
- host non-privileged dashboards.

Phoenix Web must not:

- become a privileged local operations surface,
- replace Phoenix Agent,
- imply that Phoenix OS is recovery-only.

## Current Classification

- `website/recovery-gui/` is Web/demo reference only. It also contains BootForge UI visual-reference ideas.
- Its recovery-only copy and Vite starter structure are not canonical Phoenix Web source.
- A future Phoenix Web implementation should start under `apps/web/` with Next.js after product/content ownership is clear.
