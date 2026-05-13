# Phoenix Agent Safety Gates

The Phoenix Platform implements a multi-gate safety model to prevent accidental or unauthorized system damage.

## Safety Levels
Operations are classified by their maximum potential impact:

| Level | Description | Example |
| :--- | :--- | :--- |
| `read_only` | No changes to system state. | Hardware discovery, log reading. |
| `preview_only` | Simulation of changes. | Dry-run partition sizing. |
| `privileged` | Changes to non-system files/config. | App settings, log rotation. |
| `destructive` | Irreversible changes to system disks. | Formatting, repartitioning. |
| `firmware_adjacent` | Changes to bootloader or hardware FW. | EFI staging, BIOS updates. |

## Required Validation Gates

### 1. Identity Gate
Verifies that the target device matches the `device_identity` provided in the request.
- **Fail Case**: Device disconnected, serial mismatch, or unauthorized transport (e.g. non-encrypted USB).

### 2. Policy Gate
Evaluates the operation against the `DeploymentPolicy`.
- **Checks**: Time-of-day, actor-role, target-classification (e.g. "Never touch System Disk").

### 3. Confirmation Gate
Requires explicit user interaction.
- **Low Risk**: Simple button click.
- **High Risk**: Explicit typing of "CONFIRM", MFA, or `PHX-TOKEN` entry.
