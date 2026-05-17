# Phoenix OS Launch App Inventory

This inventory classifies all applications considered for the **Phoenix OS / BWOS** launch image. 

---

## 📋 Application Classification Matrix

Every application is audited and classified into one of five states:

1. **`SHIP`:** 100% functional, real, and approved for default public menus.
2. **`BETA`:** Functional but under active hardening; hidden from default menus.
3. **`DEV-ONLY`:** Strictly for internal debugging; stripped from standard builds.
4. **`PLACEHOLDER`:** Mocked or unimplemented; blocked from all package profiles.
5. **`EXCLUDED`:** Intentionally kept out to reduce image payload footprint.

---

## 🔍 The Shipped & Excluded App Registry

| Application | Category | Classification | Upstream Binary | Launch Menu State | Notes / Status |
|---|---|---|---|---|---|
| **Web Browser** | Internet | **`SHIP`** | `firefox-esr` | **VISIBLE** | Standard, highly secure offline/online browser |
| **Calculator** | Utility | **`SHIP`** | `kcalc` | **VISIBLE** | Upstream kcalc; handles full floating decimals |
| **File Manager** | System | **`SHIP`** | `dolphin` | **VISIBLE** | Upstream Dolphin; robust file system explorer |
| **Terminal** | System | **`SHIP`** | `konsole` | **VISIBLE** | Upstream Konsole; inherits standard shell |
| **Settings Panel** | System | **`SHIP`** | `systemsettings` | **VISIBLE** | Default KDE Control Center |
| **Text Editor** | Utility | **`SHIP`** | `kwrite` | **VISIBLE** | Upstream KWrite; lightweight and reliable |
| **Image Viewer** | Utility | **`SHIP`** | `gwenview` | **VISIBLE** | Upstream Gwenview |
| **Clock Widget** | Desktop | **`SHIP`** | `plasma-widgets` | **VISIBLE** | Digital clock embedded natively in Plasma Panel |
| **Phoenix Control Center**| System | **`BETA`** | `phoenix-control-center`| **HIDDEN** | Real dashboard; write operations safely gated |
| **BootForge** | Recovery | **`DEV-ONLY`** | *None* | **EXCLUDED** | Dynamic bootloader builder; excluded until safe |
| **Workshop/Revival** | Recovery | **`DEV-ONLY`** | *None* | **EXCLUDED** | Deep filesystem recovery utility; development only |
| **Calendar App** | Productivity| **`EXCLUDED`** | *None* | **EXCLUDED** | Intentionally omitted to minimize ISO size |

---

## 📈 Hardening Rules for Beta / Dev-Only Apps

* **BootForge:** Must remain locked as **`DEV-ONLY`** and cannot be compiled into production ISO launch menus until standard GPT/fat32 dry-run simulation constraints are completely locked and proven safe on bare metal.
* **Phoenix Control Center:** Staged as **`BETA`**. All write, partition, or active sector modification actions must remain disabled or gated behind an active terminal prompt requesting administrator privilege escalation.
