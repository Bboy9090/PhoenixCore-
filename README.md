
# Phoenix Core

Windows-first core engine that supplies the product capabilities:
- Device graph (disks + volumes)
- Safety gates
- Read-only imaging primitives (chunk plan + SHA-256 hashing)
- Evidence reports

No-wrapper policy: UI never touches OS APIs. Host providers do.

## Workflow Runner
Run JSON workflow definitions:
```
phoenix-cli workflow-run --file workflow.json --report-base .
```

## Schemas & Packs
Schema references:
- docs/schemas/workflow.schema.json
- docs/schemas/pack.schema.json

Export a pack zip bundle:
```
phoenix-cli pack-export --manifest pack.json --out phoenix-pack.zip
```

## Phoenix Forge Brand
Brand assets and usage guide:
- docs/phoenix_brand/phoenix_forge.md
- assets/brand/phoenix-forge/

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
│   ├── host-linux/
│   ├── host-macos/
│   ├── host-windows/
│   ├── imaging/
│   ├── wim/
│   ├── report/
│   ├── safety/
│   └── workflow-engine/
└── apps/
    └── cli/
```


This repository has been renamed to indicate its archived status as part of its role as a donor repo in the Phoenix suite.
