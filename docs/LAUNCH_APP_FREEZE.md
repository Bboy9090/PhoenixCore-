# Phoenix OS Launch App Freeze

This document freezes the application suite approved for the first public **Phoenix OS / BWOS** release milestone.

---

## ❄️ Shipped Application Freeze Registry

To guarantee engineering stability and prevent the "cool app name" explosion from polluting our launch experience, the launch set is frozen to **exactly eight flagship apps**. Any other utility is kept out:

### 1. Shipped Flagship Apps:
* **Command:** Real, functional Terminal shell (Konsole).
* **Harbor:** Secure dynamic package and manifest manager (Firefox-ESR to Harbor repository dashboard).
* **Relay:** Real secure communication bridge (Firefox-ESR to relay chat panels).
* **Compass:** Full-fidelity technician file system manager (Dolphin).
* **Safe:** Comprehensive system settings console (systemsettings).
* **Workshop:** Read-only audited SMART disk inventory panel.
* **BootForge:** Audited serial heartbeat port transmission helper.
* **Market:** Upstream corporate financial management app (Firefox-ESR mock panel).

### 2. Optional / Future Reserved Registry:
These names are reserved for subsequent milestone sprints, but are **fully excluded and hidden** from the current release menus:
* *Sonic Codex* (Creator digital audio workstation) ➔ **EXCLUDED**
* *Ghost Writer* (Audited tech writer / text workspace) ➔ **EXCLUDED**
* *DeviceScope* (Dynamic live driver analyzer) ➔ **EXCLUDED**
* *PulseCheck* (Continuous real-time system heart telemetry) ➔ **EXCLUDED**
* *TruthLog* (Audit-log forensic viewer dashboard) ➔ **EXCLUDED**

---

## 🚫 Sprawl Lockout Directives

* Crate additions or new packages designed to compile custom applications under any of the reserved names listed above are blocked until a formal architecture review maps their safety parameters.
* Upstream packages that are not explicitly registered as dependencies inside `package-lists/` will be actively stripped by the `validate-launch-experience.sh` scanner.
