# Second-pass structural audit — production coherence

**Repository:** Bboy9090/PhoenixCore-  
**Scope:** Verify structural correctness after compilation, Metro, Rust, and pathing fixes — not feature polish.

**Lockdown enforcement (authority, safety, capabilities):** [`LOCKDOWN_PHASE_REPORT.md`](LOCKDOWN_PHASE_REPORT.md), [`AUTHORITY_MODEL.md`](AUTHORITY_MODEL.md).

---

## 1. Current canonical architecture

### Single authoritative deployment/imaging pipeline (today)

There is **no single fused pipeline** yet; the repo has **three real execution layers** with different completeness:

| Layer | Entry / location | What actually runs |
|-------|------------------|-------------------|
| **A. BootForge (primary operator UI)** | `python3 main.py` → `desktop/main.py` | PyQt6 + `desktop/src/` — disk logic, `SafetyValidator`, USB/recovery flows, Cold Fuse imaging in Python. **Most complete** for interactive host-side work. |
| **B. Phoenix Core API (HTTP orchestration)** | `uvicorn main:app` in `backend/` | FastAPI + `backend/core/*` — real device scan, recipes, `validate_safety`, build jobs (`dd`/`parted` on **Linux** only for full writes). **Authoritative for mobile/remotes** talking HTTP. |
| **C. Rust engine (contracts + CLI)** | `cargo build` / `phoenix-cli` from `apps/cli/` + `crates/` | Device graph, safety crate, workflow engine **per `docs/core-contracts.md`**. **Partially integrated** with Python/FastAPI (not the default path for USB GUI today). |

**Practical “one true path” for operators:**

- **Desktop-first:** **BootForge** (`desktop/`) is the coherent end-to-end path for wizard + imaging **on the machine with the USB**.
- **API / mobile-first:** **`backend/` FastAPI** is the coherent path; it must be running on that same host. The phone does not write USB storage.

**Rust** is the long-term authoritative **primitive** layer; it is **not** yet the only runtime for imaging.

### Overlapping / legacy paths (clearly marked)

| Path | Status |
|------|--------|
| `legacy/bootable_usb/BootForge/` | **Quarantine** — duplicate of old `src/` layout; do not patch. |
| `legacy/` (rest) | **Reference / donor** only. |
| `server/api.py` | **Deprecated** Flask API; wrong historical `PhoenixCore-` path (corrected to repo-relative in-tree). Prefer **`backend/`**. |
| Root `package.json` + `server/_core` | **Separate Expo/pnpm template** — not the same app as `phoenix-core-mobile/`. |
| `mobile/` | **Parallel** React Native tree; product ownership unclear vs `phoenix-core-mobile/`. |
| `website/web_server.py` | **Marketing / toolkit demo** (Flask); not the Phoenix Core API. |
| `crates/imaging`, `phoenix-report`, `phoenix-content`, etc. | **Rust workspace members**; several **do not build** on all platforms (see AGENTS.md). |

---

## 2. Module drift (duplicate responsibilities)

| Responsibility | Implementations | Risk |
|----------------|-----------------|------|
| Device enumeration | `backend/core/device_scanner.py`, `desktop/src/core/*` providers, Rust host providers | Divergent shapes and heuristics |
| Safety before destructive write | `backend/core/usb_builder.validate_safety`, `desktop/src/core/safety_validator.py` | Policy mismatch API vs GUI |
| USB / imaging | `backend/core/usb_builder.py`, `desktop/src/core/usb_builder.py` + imaging | Triple overlap with Rust workflows |
| HTTP API | `backend/` (FastAPI), `server/` (Flask), root template (Express/tRPC) | Operator confusion |
| Mobile | `phoenix-core-mobile/` (Expo, wired to FastAPI), root Expo app, `mobile/` | Three stacks |

**Deprecate / quarantine:** `server/` (except historical reference), `legacy/bootable_usb/BootForge/`, duplicate mobile roots until one is chosen.

---

## 3. Build truth (clean checkout)

| Target | Works? | Notes |
|--------|--------|------|
| `pip install -r requirements.txt` | **Partial** | Root `requirements.txt` had invalid `flaskFlask` entry (corrected). Prefer also `desktop/requirements.txt` / `backend/requirements.txt` where applicable. |
| `python3 -m pytest tests/` | **Yes** (with PyQt6, psutil, etc.) | `tests/conftest.py` adds `desktop/` for `src.*`. |
| `python3 main.py --help` | **Yes** (with deps) | Delegates to `desktop/main.py`. |
| `cd backend && uvicorn main:app` | **Requires** `backend/requirements.txt` (FastAPI, uvicorn) — now documented and file added. |
| `python3 website/web_server.py` | **Yes** (Flask from root requirements or separate install) | Demo only. |
| Rust subset in AGENTS.md | **Yes** on Linux/macOS CI matrix | Windows host crate not in default CI build line; workspace build **fails** on Linux by design (known). |
| Root `pnpm install` / `pnpm dev` | **Separate product** | Succeeds if Node/pnpm OK; **not** Phoenix Core backend. |
| `phoenix-core-mobile` `npm install` | **Yes** | Uses own `package.json`. |

**Hidden assumptions:** `PHOENIX_REPO_ROOT` optional for packaged layouts; OCLP under `third_party/`; physical USB operations only on **host** running API or BootForge.

---

## 4. Product truth (operator workflow)

| Workflow | Usable E2E? |
|----------|-------------|
| BootForge GUI on desktop | **Yes** (primary). |
| FastAPI + real USB on **Linux host** | **Largely yes** for recipes that use `dd`/`parted`. |
| FastAPI on **macOS / Windows** | **Partial** — many branches log or simulate; not equivalent to Linux. |
| Mobile + `EXPO_PUBLIC_API_URL` → FastAPI | **Yes** for control/status **if** host API reachable; no on-device USB write. |
| Rust `phoenix-cli` for all imaging | **Not** documented as sole production path today. |

**Docs vs reality:** README and AGENTS describe `desktop/` + `backend/` + Rust subset; root Node app and `server/` Flask must be called out as **non-canonical** (done in README + this audit).

---

## 5. Safety and reliability

| Area | State |
|------|--------|
| Unknown device | FastAPI **fails closed** (no synthetic device). |
| Confirmation token | Required for real builds; workflow route does not use fake tokens. |
| Device list | Linux lists **all** block devices — internal disks appear; relies on `removable` + `is_system_disk` + operator care. |
| Rollback | Build jobs: cancel flag; **no** automatic disk rollback after partial `dd`. |
| Error handling | Mixed by layer (GUI vs API vs Rust). |

---

## Fake or drifting paths (remove or isolate)

1. **Root `package.json` “app-template”** — isolate mentally: not Phoenix Core mobile; document in README.
2. **`server/api.py` sibling `PhoenixCore-` path** — **fixed** to `desktop/` on `sys.path` when present.
3. **`legacy/bootable_usb/BootForge`** — do not use for fixes.
4. **Invalid pip name `flaskFlask`** in root `requirements.txt` — **fixed**.

---

## Production-ready vs partial

| Production-ready | Partial / not production-complete |
|------------------|-----------------------------------|
| BootForge desktop path with validated deps | Full workspace `cargo build --workspace` on Linux |
| FastAPI backend on Linux for USB jobs | macOS/Windows **native** write parity in `usb_builder` |
| Rust crates listed in AGENTS.md | `phoenix-imaging`, report/content crates in CI |
| Mobile ↔ FastAPI contract in `phoenix-enterprise-client.ts` | Root Expo app integration with Phoenix |
| Safety fail-closed for missing devices | Unified safety policy file shared by API + GUI |

---

## Highest-risk technical debt

1. **Three safety / imaging implementations** without a shared policy module.
2. **Device graph** not serialized from one implementation (Rust vs Python vs FastAPI).
3. **macOS/Windows** API builds implying parity with Linux without surfacing **capability flags** to the client.
4. **Multiple mobile / Node roots** — onboarding and CI confusion.

---

## Correction plan (implementation order)

### PHASE 1 — Architecture truth and de-duplication *(this commit)*

- [x] Add this audit document.
- [x] Add `docs/CANONICAL_RUNTIME.md` (short pointer).
- [x] README: monorepo warning (root `package.json` vs `phoenix-core-mobile/`).
- [x] `server/README.md`: deprecated; use `backend/`.
- [x] Fix `server/api.py` `sys.path` to repo `desktop/` (stop `PhoenixCore-` fiction).

### PHASE 2 — Build truth *(this commit)*

- [x] Fix `requirements.txt` `flaskFlask` → `Flask==2.3.3`.
- [x] Add `backend/requirements.txt` (FastAPI, uvicorn, pydantic, psutil).
- [x] Document backend install in README + `.github/copilot-instructions.md` + AGENTS.md.
- [x] CI: install `backend/requirements.txt` so backend modules stay importable if tests expand.

### PHASE 3 — Imaging / device workflow hardening *(this commit)*

- [x] Add `backend/core/platform_caps.py` and expose `features.destructive_usb_write_native` in `/api/health` from host OS reality.

### PHASE 4 — Operator UX / documentation alignment *(this commit)*

- [x] Cross-link audits in `docs/ARCHITECTURE.md`.
- [x] Update `docs/AUDIT_PLATFORM_INTEGRATION.md` executive summary to reference second-pass doc.

---

## Next steps (out of scope for this patch)

- Unify safety: shared module or subprocess contract from desktop → API.
- Optional `GET /api/devices?removable_only=true` default for safer mobile UX.
- Deprecate `mobile/` or merge into `phoenix-core-mobile/` explicitly.
- CI: optional Windows `phoenix-host-windows` build job.
