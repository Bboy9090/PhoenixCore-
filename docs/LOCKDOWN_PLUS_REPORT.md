# Lockdown Plus — implementation report

## P1 — Shared safety package

**What changed:** Added **`packages/phoenix_safety/`** (editable setuptools package) containing the former `safety_validator.py`. **`desktop/src/core/safety_validator.py`** is now a re-export. **`backend/core/safety_bridge.py`** imports **`phoenix_safety.safety_validator`** (no `desktop/` on `sys.path`). Root **`requirements.txt`** and **`desktop/requirements.txt`** and **`backend/requirements.txt`** include **`-e packages/phoenix_safety`**.

**Why:** One physical module for desktop + API; no brittle cross-tree import.

**Files:** `packages/phoenix_safety/**`, `desktop/src/core/safety_validator.py`, `backend/core/safety_bridge.py`, `requirements.txt`, `desktop/requirements.txt`, `backend/requirements.txt`, `docs/SAFETY_MODEL.md`, `docs/AUTHORITY_MODEL.md`

**Migration:** `pip install -r requirements.txt` (root) or `pip install -e packages/phoenix_safety`.

**Risks:** CI must install editable package (root requirements updated).

**Next:** Optional: publish `phoenix-safety` to an internal index for non-checkout deploys.

---

## P2 — Durable audit persistence

**What changed:** **`backend/core/audit_store.py`** — JSONL under **`PHOENIX_AUDIT_DIR`** (default `~/.phoenix_core/audit/`), rotation by size. **`usb_builder`** appends **preflight**, **job_complete**, **job_failed**, **job_rejected**. **`GET /api/audit/jobs/recent`**, **`GET /api/audit/export/path`**.

**Why:** Survives process restart; exportable for support.

**Files:** `backend/core/audit_store.py`, `backend/core/usb_builder.py`, `backend/main.py`, `docs/AUDIT_LOG.md`

**Migration:** Set **`PHOENIX_AUDIT_DIR`** in production if needed.

**Risks:** Disk growth — operators rotate/archive JSONL.

**Next:** Optional SQLite for query-by-job_id.

---

## P3 — Physical drift isolation

**What changed:** **`ROOT_NONCORE_NOTICE.md`**, **`experimental/README.md`**, **`ROOT_APP_TEMPLATE.redirect.md`**; **`README.md`** repo map + link; **`docs/REPO_STATUS_MAP.md`** updated. The non-core Expo/pnpm/tRPC template was physically moved under **`experimental/root-app-template/`** (no longer at repo root).

**Why:** Cold-checkout clarity: the repo root now shows canonical Python/Rust/mobile paths first.

**Files:** `ROOT_NONCORE_NOTICE.md`, `experimental/README.md`, `ROOT_APP_TEMPLATE.redirect.md`, `README.md`, `docs/REPO_STATUS_MAP.md`, `experimental/root-app-template/**`

**Risks:** External tooling that assumed root `pnpm dev` must now run from `experimental/root-app-template/`.

**Next:** Optional: sweep/retire old docs that still mention running pnpm from repo root.

---

## P4 — Automated truth enforcement

**What changed:** **`scripts/ci_truth_enforcement.sh`**; **`.github/workflows/ci.yml`** runs it; **`docs/TRUTH_ENFORCEMENT.md`**; **`tests/test_lockdown_plus.py`**.

**Why:** CI guards schema version, capability doc mention, legacy import ban, package presence, behavior tests.

**Files:** `scripts/ci_truth_enforcement.sh`, `.github/workflows/ci.yml`, `docs/TRUTH_ENFORCEMENT.md`, `tests/test_lockdown_plus.py`

**Risks:** Script uses `grep -r` (portable).

**Next:** Extend ban-list (e.g. `server/api` imports) if server is removed.

---

## P5 — Operator safety UX (mobile)

**What changed:** **`phoenix-enterprise-client`**: safety payload fields, build progress **failure_stage** / **rollback**; **`usb-create`**: device path + removable + heuristic risk, elevated confirmation for medium/warning risk, failure alert with recovery text, no rollback messaging.

**Why:** Stronger confirmations and honest failure guidance on the active remote UI.

**Files:** `phoenix-core-mobile/lib/api/phoenix-enterprise-client.ts`, `phoenix-core-mobile/app/(tabs)/usb-create.tsx`

**Risks:** Double Alert chaining UX on iOS — acceptable for safety.

**Next:** Surface **`device_risk.overall_risk`** text inline on the review screen.
