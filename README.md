
# Phoenix Core

Windows-first core engine that supplies the product capabilities:
- Device graph (disks + volumes)
- Safety gates
- Read-only imaging primitives (chunk plan + SHA-256 hashing)
- Evidence reports

No-wrapper policy: UI never touches OS APIs. Host providers do.

## Phoenix Core Layout (current)
```
.
├── Cargo.toml
├── README.md
├── .gitignore
├── .github/
│   └── workflows/
│       └── ci-windows.yml
├── docs/
│   ├── no-wrapper-policy.md
│   ├── supplier-matrix.md
│   ├── device-graph.md
│   ├── cursor-projects/
│   └── cursor-issues/
├── crates/
│   ├── core/
│   ├── host-windows/
│   ├── imaging/
│   ├── report/
│   ├── safety/
│   └── workflow-engine/
└── apps/
    └── cli/
```


This repository has been renamed to indicate its archived status as part of its role as a donor repo in the Phoenix suite.
