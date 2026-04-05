# Final cleanup phase report

## F1 — Physical template extraction

**What changed:** Moved **Expo + pnpm + tRPC + `server/` + `drizzle/` + `app/`** and related root files into **`experimental/root-app-template/`**. Added **`experimental/root-app-template/README.md`**, **`experimental/root-app-template/scripts/generate_qr.mjs`**, root **`ROOT_APP_TEMPLATE.redirect.md`**, updated **`CONFIG_ROOT_TEMPLATE.md`**, **`ROOT_NONCORE_NOTICE.md`**, **`experimental/README.md`**, **`README.md`** (table + map), **`docs/REPO_STATUS_MAP.md`**.

**Why:** Repo root now shows **canonical** Python/Rust/mobile paths first; template is physically isolated.

**Migration:** `cd experimental/root-app-template && pnpm install && pnpm dev`. Any automation that used **root** `pnpm` must use this path.

**Risks:** External docs or bookmarks referencing root `package.json` need updating.

**Next:** Archive old blog posts / iOS guides that say “repo root pnpm” (optional doc sweep).

---

## F2 — AST import boundary enforcement

**What changed:** **`scripts/check_import_boundaries.py`** parses **`backend/`**, **`desktop/`**, **`packages/`**, **`tests/`** with `ast`; forbids top-level **`legacy`**, **`experimental`**, **`server`**. **`scripts/ci_truth_enforcement.sh`** invokes it. **`docs/IMPORT_BOUNDARIES.md`**, **`tests/test_import_boundaries_script.py`**.

**Why:** Stronger than grep; catches real imports only.

**Risks:** Relative imports `from server` not used in product; if added, would need a waiver policy.

**Next:** Optional: parse `# import-boundary: allow` comments.

---

## F3 — Startup audit recovery

**What changed:** **`ensure_audit_index()`** after **`rebuild_audit_index_from_jsonl`**; compares JSONL vs DB mtime, removes corrupt DB; **`query_audit`** / **`audit_summary_for_jobs`** call **`ensure_audit_index()`**; FastAPI **`lifespan`** logs startup rebuild. **`docs/AUDIT_LOG.md`**. Tests in **`tests/test_stabilization.py`**.

**Why:** SQLite stays aligned with JSONL without manual steps in common cases.

**Risks:** Clock skew could theoretically trigger extra rebuilds (mtime comparison).

**Next:** Optional WAL mode for SQLite under high write load.

---

## F4 — Operator history visibility

**What changed:** **`phoenix-core-mobile`**: tabs **`usb-create`**, **`devices`**, **`monitor`**; **Monitor** shows **`getAuditJobsSummary`** list + **Rebuild index** + honest rollback text; **`rebuildAuditIndex`** return type fix.

**Why:** Real visibility without a large dashboard.

**Risks:** Large audit lists still need host-side tools.

**Next:** Pull-to-refresh copy for audit section only.

---

## F5 — Deployment / packaging polish

**What changed:** **CI** (Ubuntu): **`build_phoenix_safety_wheel.sh`** + **`upload-artifact`** `phoenix-safety-wheel`. **`docs/BACKEND_DEPLOYMENT.md`** already describes wheel path; version **1.1.0** in **`pyproject.toml`**.

**Why:** Downloadable wheel per CI run for semi-detached deploys.

**Risks:** Artifact retention per GitHub policy.

**Next:** Optional release workflow attaching wheel to GitHub Releases.
