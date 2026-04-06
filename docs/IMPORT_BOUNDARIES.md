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

To allow a rare exception, add an inline waiver **on the same line** as the import:

- `# import-boundary: allow server` (allow any `server.*` import on that line)
- `# import-boundary: allow server.api` (allow that subtree on that line)
- `# import-boundary: allow *` (allow anything on that line; avoid unless unavoidable)

Policy: keep waivers **rare**, **line-scoped**, and **reviewed**.
