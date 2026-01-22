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
│   ├── content/
│   ├── host-windows/
│   ├── imaging/
│   ├── report/
│   ├── safety/
│   └── workflow-engine/
└── apps/
    └── cli/
```

## Legacy Notice
Legacy BootForge/Phoenix Key assets still exist in this repo and will be
removed or quarantined once the repo is fully renamed. See `LEGACY.md`.
