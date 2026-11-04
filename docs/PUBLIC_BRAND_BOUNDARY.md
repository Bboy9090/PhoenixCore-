# PhoenixCore Public Brand Boundary

## Architecture

**PhoenixCore** remains the internal orchestration and device-intelligence layer.

Public computer-repair surfaces should use:

- **Boot It Back** — computer diagnosis, recovery planning, OS install/recovery, disk/partition workflows, boot troubleshooting, and repair-session UX.
- **Phoenix Key** — guarded boot/recovery-media creation and signed-media workflow.
- **BootForge** — internal low-level discovery/media engine only.

Phone/tablet repair belongs to **BobFWTools**, not Boot It Back.

## Why

The public name **BootForge** now collides directly with an unrelated bootable-USB product already shipping in the same category. It must not be used as the customer-facing app/store identity.

## Boot It Back icon

- Computer/display silhouette.
- Power glyph merged with a clockwise return/boot arrow.
- Small drive/partition notch at the base.
- No phone/tablet imagery.
- No generic wrench as the primary mark.

## Boot It Back splash

- Initial state: dark/offline machine silhouette.
- Boot path illuminates through firmware -> disk -> OS.
- Final state: healthy desktop frame.
- Wordmark: **Boot It Back**.
- Secondary line: **Recover. Repair. Reinstall. Boot.**

## Phoenix Key icon

- Physical-key silhouette merged with a USB/media blade.
- One verified/check node.
- Must read as recovery media, not password management.

## Compatibility rule

Do not rename internal PhoenixCore package names, environment variables, evidence schemas, Tauri identifiers, repo paths, persisted case/session data, or receipt formats during public display-brand work.
