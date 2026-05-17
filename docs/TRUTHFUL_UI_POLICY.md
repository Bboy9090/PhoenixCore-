# Phoenix OS Truthful UI Policy

This policy governs user interface integrity, diagnostic reporting states, and feature completeness labeling inside all graphical applications shipped on **Phoenix OS / BWOS**.

---

## 🚫 The Anti-Faking Mandate

To preserve absolute engineering integrity and secure trust on the workbench, **mocking, simulating, or pretending to run deep operations is strictly prohibited.** Interfaces must never lie to the technician.

1. **No Fake Progress Bars:**
   * Progress loaders must map to active, linear subprocess execution percentages. 
   * "Fake timer loops" designed to hover, stall, or artificially slow down completion are illegal.
2. **No False Success Labels:**
   * An application must never declare "System Repaired" or "Disk Recovered" if the core operations were mocked or skipped.
   * If a recovery cycle completes with non-zero exit codes, a verbose warning block containing the actual system error must be shown.
3. **Explicit Simulation Indicators:**
   * If a safe preview or dynamic mockup mode is active, the screen must display a permanent, high-contrast, glowing yellow **`[PREVIEW-ONLY]`** or **`[SIMULATION MODE]`** tag.
4. **Truthful Incomplete Features Labeling:**
   * Features under active development must not be displayed as active buttons. 
   * If exposed, clicking them must explicitly show: **`[Feature under active development: Not Yet Implemented]`**.

---

## 🧪 Graphical State Audit Guidelines

| UI Element | Prohibited Behavior | Approved Behavior |
|---|---|---|
| **Loader / Spinners** | Static timer loops that spin for exactly 5 seconds. | Real asynchronous event updates mapped to subprocess outputs. |
| **Success Banners** | "Files recovered successfully!" on standard mock loops. | "Diagnostics Complete. Read-only review mode. Zero sectors written." |
| **Diagnostic Errors** | generic "Something went wrong" boxes. | Actual stderr reports from low-level Rust execution blocks. |
| **Repair buttons** | Launching destructive shell commands in background. | Gated, disabled states explaining: "Low-level write mutations disabled in Live environment." |
