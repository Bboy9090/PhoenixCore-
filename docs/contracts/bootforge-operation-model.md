# BootForge Operation Model

## 1. Imaging Operation Lifecycle
All imaging operations within the Phoenix ecosystem must follow this canonical lifecycle to ensure safety and auditability.

| Phase | Responsibility | Action |
| :--- | :--- | :--- |
| **Request** | Control Center | User initiates an imaging task with a specific Recipe and Target. |
| **Preview** | BootForge | Calculate data flow, partition changes, and estimated time. |
| **Safety Evaluation** | Phoenix Agent | Run safety gates (Disk Type, Size, Power, Integrity). |
| **Target Confirmation** | Control Center | UI displays the preview and requires explicit "ARM" interaction. |
| **Execution** | Rust Imaging | Physical disk I/O commences. |
| **Progress Stream** | Phoenix Agent | Real-time byte/percent feedback to UI. |
| **Report Bundle** | BootForge | Post-op verification (checksums) and success/failure logs. |
| **Audit Record** | Phoenix Agent | Persist the complete operation history to the secure ledger. |

## 2. Safety Classifications
Disks and targets are classified into risk tiers:

1.  **Removable Media (Low Risk)**: SD cards, USB flash drives. Default target for BootForge.
2.  **Internal Disk (High Risk)**: Secondary fixed storage. Requires elevated admin role.
3.  **System Disk (Extreme Risk)**: The current OS drive. Requires "Override Token" + Physical Presence.
4.  **Firmware-Adjacent (Critical Risk)**: EFI partitions, ESP, Recovery partitions.
5.  **Recovery-Only**: Targets restricted to specific recovery environments (WinPE/macOS Recovery).

## 3. Operational State Machine
*   `IDLE` -> `PROPOSING` (Preview generated)
*   `PROPOSING` -> `ARMED` (Safety checks passed, User confirmed)
*   `ARMED` -> `EXECUTING` (Disk I/O active)
*   `EXECUTING` -> `VERIFYING` (Post-copy checksums)
*   `VERIFYING` -> `COMPLETED` | `FAILED`
*   `FAILED` -> `ROLLBACK` (Attempted if safety policy allows)
