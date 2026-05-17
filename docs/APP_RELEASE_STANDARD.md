# Phoenix OS Application Release Standard

This standard defines the mandatory rules and quality bars that every application must pass to be approved for inclusion in public **Phoenix OS** launch images.

---

## 🛡️ The Golden Rules of Launch Apps

Every shipped launch application must adhere to the following principles:

1. **Strictly Truth-First (No Placeholders):**
   * An application must perform the core utility advertised.
   * Placeholder UI layouts, mock screens, "TODO" windows, or disabled features masquerading as finished utilities are **strictly prohibited**.
2. **Launch & Crash Protection:**
   * The app must launch reliably from standard graphical menus (SDDM / KDE Plasma Launcher).
   * It must open without crashing and close gracefully without leaving orphan background processes.
3. **Valid Desktop Entry:**
   * The app must possess a fully valid `.desktop` launcher stored under `/usr/share/applications/`.
   * The launcher must point to a real executable (`Exec=`) and carry a correct icon (`Icon=`).
4. **Verified Package Path:**
   * The app must be installed via a standard, reproducible package pathway (APT package profile or registered custom `.deb` cache).
5. **No Safety Gate Bypasses:**
   * The app must strictly respect the **Phoenix Agent Capability Matrix** and the core security hooks of **PR27**.
   * It must not attempt or request root permissions directly without active system agent authorization.

---

## 🧪 Smoke Testing & Manual Validation Steps

Before any custom utility is upgraded to **SHIP** status, it must undergo these basic smoke test verifications:

| Step | Action | Expected Behavior | Pass/Fail Criteria |
|---|---|---|---|
| **1. Graphical Launch** | Click app in Application Menu | App window draws and gains active focus | **PASS:** Draws instantly <br>**FAIL:** App hangs, throws segfault, or fails to render |
| **2. Interface Audit** | Click primary utility controls | Operations complete natively; no fake success screens | **PASS:** Interactive controls function <br>**FAIL:** Shows "TODO/Mock" overlays |
| **3. Offline Immunity** | Disconnect network link | App remains responsive with appropriate offline error state | **PASS:** Handles offline gracefully <br>**FAIL:** Network timeout hangs app |
| **4. Process Cleanup** | Close app window | App terminates cleanly; process disappears from `htop` | **PASS:** Zero orphan processes <br>**FAIL:** Process leaks in background |
