# Phoenix Key Repository Boundary

## Decision

Phoenix Key is a PhoenixCore application. `Bootforge-usb` remains the low-level connected-device detection project and is consumed as a pinned dependency.

## Ownership

| Capability | Owner |
| --- | --- |
| USB peripheral enumeration, VID/PID, phone service-mode classification | `Bootforge-usb` / `libbootforge` |
| Removable block-device discovery, identity locks, image inspection, dry-run planning | PhoenixCore |
| User-facing desktop workflow and installer | `apps/phoenix-key` in PhoenixCore |
| Governed third-party tool selection and provenance | PhoenixCore tool registry |
| Privileged or destructive execution | Future Phoenix Agent safety boundary; unavailable in this phase |

## Integration contract

Phoenix Key has two intentionally different hardware lanes:

1. Device Forge calls the pinned `libbootforge` Rust API for phones and USB peripherals.
2. Media Builder calls the canonical PhoenixCore Python scanner and `--plan-write` dry-run contract for removable storage.

The desktop binary embeds the canonical PhoenixCore Python sources at compile time and stages them only in the host temporary directory for execution. This keeps packaged builds self-contained without copying a second maintained scanner into the application source tree.

## Safety invariants

- Browser mode never creates sample hardware results.
- The Tauri shell allowlist remains closed.
- The UI exposes no physical write, format, partition, mount, or unmount control.
- A target must be removable, non-system, non-fixed, and scanner-eligible before dry-run planning is enabled.
- Python bridge failures return their real cause; there is no fake-success fallback.
- `libbootforge` is pinned to a reviewed commit instead of tracking a moving branch.

## Migration rule

Do not delete the donor Phoenix Key application from `Bootforge-usb` until the PhoenixCore installer passes CI and real Windows hardware validation. After parity, the donor UI may be reduced to a library integration example while `apps/phoenix-key` remains the product source of truth.
