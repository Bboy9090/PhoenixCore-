# Phoenix Core Contribution Rules

These rules enforce the no-wrapper doctrine and safety guarantees.

## No-Wrapper Enforcement
- Do not introduce runtime dependencies on external executables.
- If a bridge is unavoidable, it must:
  - live behind a strict adapter interface
  - include a replacement milestone + removal plan
  - be tracked with a dedicated task/issue

## Safety First
- Default deny on destructive disk writes.
- System disks are blocked unless force-mode + confirmation token are supplied.
- New workflows must emit evidence reports.
- Evidence reports should include a signed manifest when a signing key is available.

## Windows-First (M0)
- Use Windows APIs via the `windows` crate for core capabilities.
- Do not shell out to cmd/powershell for disk/image operations.

## Review Checklist
- Does this change add any external runtime tools? If yes, reject or add a bridge plan.
- Are safety gates enforced for write operations?
- Are reports emitted with device_graph.json + run.json + logs.txt?
