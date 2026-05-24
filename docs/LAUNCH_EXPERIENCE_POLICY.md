# Phoenix OS Launch Experience Policy

This policy governs graphical menus organization, application launch expectations, and user experience standards within public **Phoenix OS / BWOS** ISO releases.

---

## 🧼 Clean Menu Standards

To provide a premium, technician-grade out-of-the-box layout, every synthesized ISO must enforce the following graphical menu guidelines:

1. **Zero Dead Launchers:** Every visible launcher in the application menu must point to a real executable installed inside the staging root path.
2. **No Duplicated Entries:** Applications must register under unique names and icon specifications. Multiple desktop files launching the same binary under differing categories must be resolved at build time.
3. **No Unfinished Apps:** Utilities classified as Tier 2 (Beta) or Tier 3 (Internal) must not expose desktop shortcuts inside standard release builds. 
4. **Truthful offline/online UI states:** If a service requires active network access (e.g. the Harbor package center), the app must gracefully boot to an informative offline notice when no network links are active.
5. **Consistent Iconography:** All launch-suite applications must use the official, unified icon branding files matching the active edition's design tokens (e.g. the dynamic **Phoenix Family Variants**).

---

## 📂 Desktop Entry Categories Mapping

Standard desktop shortcuts must map cleanly to standard FreeDesktop categories to ensure uniform organization in the Citadel Shell:

| Application | Icon Signature | Category | Executable Path |
|---|---|---|---|
| **Command** | Terminal Emblem | `System;TerminalEmulator;` | `/usr/bin/konsole` |
| **Harbor** | Network Harbor | `System;PackageManager;` | `/usr/bin/firefox-esr` (to harbor url) |
| **Relay** | Secure Signal | `Network;InstantMessaging;` | `/usr/bin/firefox-esr` |
| **Compass** | Navigational Ring| `Utility;FileAccess;` | `/usr/bin/dolphin` |
| **Safe** | Gated Crypt | `Utility;Security;` | `/usr/bin/systemsettings` |
| **Workshop** | Heavy Gear | `System;HardwareSettings;` | `/usr/libexec/phoenix/phoenix-smart-helper` |
| **BootForge** | Flame Hammer | `System;Setup;` | `/usr/libexec/phoenix/phoenix-heartbeat-helper` |
| **Market** | Cart Loop | `Office;Finance;` | `/usr/bin/firefox-esr` |
