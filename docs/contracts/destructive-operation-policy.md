# Destructive Operation Policy

No destructive operation may execute without satisfying these five requirements:

1.  **Preview**: The user must be shown exactly what will change.
2.  **Explicit Device Identity**: The target must be uniquely identified and verified as the intended recipient.
3.  **Safety Evaluation**: The action must be allowed by the active security policy.
4.  **Confirmation**: The user must perform a deliberate, high-friction action to proceed.
5.  **Audit Generation**: A record must be committed to the log BEFORE the final execution step.

## Definition of Destructive
Any operation that:
- Deletes or modifies user data.
- Changes partition tables.
- Formats filesystems.
- Overwrites bootloaders.
- Modifies hardware firmware.
