# Python import boundaries (enforced)

Canonical trees **`backend/`**, **`desktop/`**, **`packages/`**, and **`tests/`** must not import:

- **`legacy`** — archived code
- **`experimental`** — template / non-core
- **`server`** — deprecated Flask + Node template (use **`backend/`** FastAPI)

Paths under **`legacy/`** or **`experimental/`** are not scanned (they may reference each other).

## Checker

```bash
python3 scripts/check_import_boundaries.py
```

CI runs this after **`scripts/ci_truth_enforcement.sh`** (which also runs **`grep`** heuristics).

## Whitelist

To allow a rare exception, add a documented waiver in this file and a `# import-boundary: allow server.X` comment next to the import (future: parse comments). **Current policy: no waivers.**
