# Phoenix Core

Windows-first core engine that supplies the product capabilities:
- Device graph (disks + volumes)
- Safety gates
- Read-only imaging primitives (chunk plan + SHA-256 hashing)
- Evidence reports

No-wrapper policy: UI never touches OS APIs. Host providers do.
