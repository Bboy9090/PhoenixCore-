# Stabilization phase report

## S1 — Package hardening

**What changed:** `phoenix-safety` **1.1.0** in `pyproject.toml` (metadata, classifiers, URLs). **`backend/requirements.txt`** uses **`../packages/phoenix_safety`** (non-editable path install). **`scripts/build_phoenix_safety_wheel.sh`**, **`docs/BACKEND_DEPLOYMENT.md`**, expanded **`packages/phoenix_safety/README.md`**.

**Why:** Backend-only hosts can `pip install -r backend/requirements.txt` without `-e`; wheels support air-gapped/internal mirrors.

**Files:** `packages/phoenix_safety/pyproject.toml`, `packages/phoenix_safety/README.md`, `backend/requirements.txt`, `scripts/build_phoenix_safety_wheel.sh`, `docs/BACKEND_DEPLOYMENT.md`

**Migration:** Re-run `pip install -r backend/requirements.txt` from repo root context.

**Risks:** Version drift vs lock files — pin wheel version in deploy docs.

**Next:** CI job to build wheel artifact.

---

## S2 — Audit indexing

**What changed:** **`audit_index.sqlite3`** beside JSONL; **`append_record`** writes both; **`query_audit`**, **`audit_summary_for_jobs`**, **`rebuild_audit_index_from_jsonl`**. API: **`GET /api/audit/query`**, **`GET /api/audit/jobs/summary`**, **`POST /api/audit/rebuild-index`**. **`AUDIT_SCHEMA_VERSION` → 1.1.0** (additive: index + same line schema).

**Why:** Operators query by `job_id`, device, time, event without scanning JSONL.

**Files:** `backend/core/audit_store.py`, `backend/main.py`, `docs/AUDIT_LOG.md`

**Migration:** Existing JSONL only → call **`POST /api/audit/rebuild-index`** once.

**Risks:** SQLite write fails silently (JSONL still written); rebuild repairs index.

**Next:** Periodic rebuild cron or startup hook if index missing.

---

## S3 — Physical repo cleanup

**What changed:** **`CONFIG_ROOT_TEMPLATE.md`** tombstone; **`experimental/README.md`** points at root template; **`ROOT_NONCORE_NOTICE`** links barrier. **`README`** / **`REPO_STATUS_MAP`** reference stabilization doc.

**Why:** Stronger cold-checkout guardrails prior to physically moving the non-core template.

**Files:** `CONFIG_ROOT_TEMPLATE.md`, `experimental/README.md`, `ROOT_NONCORE_NOTICE.md`, `README.md`, `docs/REPO_STATUS_MAP.md`

**Migration:** None.

**Risks:** None beyond doc drift (template was later moved in Final Cleanup).

**Next:** Optional doc sweep to remove any remaining “root pnpm” guidance.

---

## S4 — Truth enforcement

**What changed:** **`scripts/ci_truth_enforcement.sh`**: `python3 -c "import phoenix_safety"`; ban **`backend/`** importing **`server.`**; ban **`from legacy`** / **`import legacy.`** in canonical `*.py`. **`docs/TRUTH_ENFORCEMENT.md`** updated.

**Why:** Stricter import boundaries.

**Files:** `scripts/ci_truth_enforcement.sh`, `docs/TRUTH_ENFORCEMENT.md`, `tests/test_stabilization.py` (new)

**Migration:** None.

**Risks:** False positives on string literals containing `legacy.` — pattern is conservative.

**Next:** AST-based checker for imports only.

---

## S5 — Operator history / recovery UX

**What changed:** **`phoenix-enterprise-client`**: **`getAuditJobsSummary`**, **`queryAudit`**, **`rebuildAuditIndex`**. **`usb-create`**: link-style note to audit APIs after failure; **`BuildScreen`**-style improvement via README **Operator audit** section in **`docs/AUDIT_LOG.md`**.

**Why:** Traceability without heavy UI.

**Files:** `phoenix-core-mobile/lib/api/phoenix-enterprise-client.ts`, `phoenix-core-mobile/app/(tabs)/usb-create.tsx`, `phoenix-core-mobile/README.md`, `docs/AUDIT_LOG.md`

**Migration:** None.

**Risks:** Mobile does not ship a full audit browser yet.

**Next:** Optional `monitor` tab listing summary from API.
