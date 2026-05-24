# Phoenix OS App Tier Model

This document establishes the official application tiers, requirements, and compliance standards governing software inclusion in **Phoenix OS / BWOS** builds.

---

## 🚦 Three-Tier Classification Architecture

To prevent uncontrolled ecosystem sprawl from destabilizing packaging pipelines or complicating UX quality audits, every package is mapped into one of three structural tiers:

```text
  ┌──────────────────────────────────────────────────────────┐
  │                        TIER 1                            │
  │   - Flagship User-Facing Applications                    │
  │   - 100% Functionality Guaranteed                        │
  │   - Visible in Public Menu                               │
  └────────────────────────────┬─────────────────────────────┘
                               │
  ┌────────────────────────────▼─────────────────────────────┐
  │                        TIER 2                            │
  │   - Beta / Experimental Services                         │
  │   - Hidden Behind Configuration Flags                    │
  │   - Excluded from Production Public ISOs                 │
  └────────────────────────────┬─────────────────────────────┘
                               │
  ┌────────────────────────────▼─────────────────────────────┐
  │                        TIER 3                            │
  │   - Internal / Developer-Only Utilities                  │
  │   - Stripped fully from packaging profiles               │
  │   - Highly restricted, unsafe execution helpers          │
  └──────────────────────────────────────────────────────────┘
```

---

## 📋 Tier Requirements & Criteria

### Tier 1: Flagship Applications
* **Requirements:** Must fully perform its core purpose offline or with clear network exception pages. Must possess a valid FreeDesktop desktop entry and a registered upstream or custom package path. Must undergo active pre-flight smoke testing before packaging.
* **Launch Visibility:** **VISIBLE** on default application menus.

### Tier 2: Beta Applications
* **Requirements:** Undergoing active development or integration. Core functionalities are simulated or partially implemented. Must not expose raw destructive commands.
* **Launch Visibility:** **HIDDEN** from default menus; only enabled on explicit `--mode=dev` compilation flags.

### Tier 3: Internal / Dev-Only
* **Requirements:** Structural test suites, raw block-level mutation commands, un-gated heartbeats helpers, or repair shell script templates.
* **Launch Visibility:** **EXCLUDED** entirely from chroot staging targets on public release ISO configurations.
