# Safety Gates

Phoenix Agent is the policy boundary. Rust crates are the low-level safety boundary.

## Ownership

- UI apps request operations and show confirmations.
- Phoenix Agent validates policy, user intent, preview state, and audit requirements.
- Rust safety crates validate low-level host, device, and operation risks.
- Host crates perform platform-specific inspection and execution only after safety gates pass.

## Required Gates

Every dangerous operation must pass:

1. Device identity gate.
2. System disk protection gate.
3. Removable media policy gate.
4. Operation capability gate.
5. Preview freshness gate.
6. User confirmation gate.
7. Dry-run or simulation gate when available.
8. Audit/report gate.

## Protected By Default

- System disks are protected by default.
- Unknown devices are protected by default.
- Devices without stable identity are protected by default.
- Operations without previews are rejected.
- Expired previews are rejected.
- UI-provided risk overrides are ignored unless Phoenix Agent policy allows them.

## Preview Requirement

Destructive operations must require preview first.

Preview responses must include:

- `preview_id`
- `operation_type`
- `target_device`
- `risk_level`
- `required_gates`
- `warnings`
- `expires_at`
- `safety_token`

Execution placeholders must require both `preview_id` and `safety_token`.

## Not Implemented Yet

PR6 does not implement safety gate evaluation in Rust or Python. It defines the contract that later PRs must satisfy.
