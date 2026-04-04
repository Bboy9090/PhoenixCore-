# Phoenix Core — platform integration audit (living document)

This audit supports the goal of a **single authoritative runtime path**, clearer operator workflows, and stronger cross-platform reliability **without** a ground-up rewrite. It reflects the repository as of the branch that introduced this file.

## Executive summary

| Area | Finding | Severity |
|------|---------|----------|
| Module boundaries | README and `docs/LEGACY.md` disagree on whether `src/` is canonical; actual layout is `desktop/src/`, `backend/`, `crates/`, `legacy/` | High |
| Duplicate logic | BootForge engine exists in `desktop/src/`, duplicated under `legacy/bootable_usb/BootForge/`; Flask `server/` expects a different repo layout | High |
| Safety | Backend `validate_safety` previously accepted unknown devices as “demo” — now gated by `PHX_ALLOW_DEMO_DEVICE` | Addressed (Phase 2 partial) |
| Device detection | Linux scan enumerates non-removable disks; risk heuristics can mis-rank internal NVMe; Windows relies on `BusType` for “removable” | Medium |
| Platform drift | Hard-coded `/home/ubuntu/PhoenixCore` paths in backend — replaced with `backend/core/phoenix_paths.py` | Addressed (Phase 1) |
| Operator workflows | FastAPI documents workflows; execution is recipe-mapped with `dry_run` defaults that can surprise operators | Medium |
| Layer confusion | Rust contracts (`docs/core-contracts.md`) vs Python BootForge vs FastAPI backend vs `phoenix-core-mobile` — three parallel “cores” | High |

---

## 1. Canonical vs legacy modules

### Canonical (intended product surface)

| Location | Role |
|----------|------|
| `crates/` + `apps/cli/` | **Authoritative low-level engine**: device graph, safety, host providers, workflows (`phoenix-cli`). |
| `desktop/` | **BootForge host application**: PyQt6 GUI, `desktop/src/` Python engine (USB recipes, safety validator, providers). |
| `backend/` | **FastAPI service**: REST for device scan, recipes, build jobs — orchestration and HTTP front for operators/mobile. |
| `website/` | **Marketing / demo Flask** and static recovery GUI assets. |
| `phoenix-core-mobile/` | **Expo** client; talks to HTTP APIs. |
| `mobile/` | **Alternate React Native** tree (verify which app is shipped before consolidating). |

### Legacy / quarantine

| Location | Role |
|----------|------|
| `legacy/` | Old toolkits, duplicated BootForge, integration experiments. Treat as **read-only reference** unless explicitly ported. |
| `legacy/bootable_usb/BootForge/` | Full duplicate of BootForge `src/` — **do not extend**; merge fixes into `desktop/` only. |
| `server/` | Flask API that assumes `PhoenixCore-` sibling checkout — **fragile**; prefer `backend/` or unify on one API. |

`docs/LEGACY.md` lists `src/` at repo root as legacy; **this repo uses `desktop/src/`** instead. That doc should track the real tree (see `docs/ARCHITECTURE.md` updates).

---

## 2. Duplicate imaging / recovery logic

- **Rust** (`crates/imaging`, `phoenix-core`, workflow engine): imaging providers and workflows per `docs/core-contracts.md`.
- **Python BootForge** (`desktop/src/imaging/cold_fuse.py`, recovery modules): host-side imaging/recovery UX.
- **FastAPI** (`backend/core/usb_builder.py`): build jobs, `dd`, `parted`, recovery USB file staging — **overlaps** Python and Rust responsibilities.

**Direction:** treat `phoenix-cli` + crates as the long-term **single write path**; keep Python/FastAPI as orchestration until Rust parity, and **document** which layer performs destructive I/O for each recipe.

---

## 3. Safety gaps (current + mitigations)

- **Unknown device “demo” fallback** in `validate_safety`: could proceed without a real disk. **Mitigation:** require `PHX_ALLOW_DEMO_DEVICE=1` for demo device injection; default is block.
- **Confirmation tokens:** workflow runner used a hard-coded demo token in some paths — review clients to always pass tokens from `/api/safety-check`.
- **Desktop `SafetyValidator`:** richer than FastAPI checks — **risk of inconsistent policy** between GUI and API.

---

## 4. Device detection weaknesses

- Linux: includes fixed disks unless filtered; `is_system_disk` heuristic may miss exotic root layouts.
- macOS: `diskutil` list can include internal disks — operators need strong UI labeling.
- Windows: removable inferred from `BusType` only; SD/USB edge cases may be wrong.

**Recommendation:** converge on **one serialized “device graph” shape** (aligned with Rust `DeviceGraph`) and produce it from a single implementation per OS (Rust preferred).

---

## 5. Platform-specific drift

- Build jobs: Linux has real `dd`/`parted`; macOS/Windows branches often **simulate** or log only — document honestly in API responses.
- OCLP paths: must resolve via repo root (`PHOENIX_REPO_ROOT` / `backend/core/phoenix_paths.py`), not developer machine paths.

---

## 6. Incomplete operator workflows

- FastAPI `/api/workflows/run` maps workflow → recipe but **does not** enforce the same step UX as the PyQt6 wizard (confirmations, education).
- Mobile apps are **planners/remotes**; destructive work still targets the **host** running the backend — UX should state this everywhere.

---

## 7. Architectural confusion (Python / Rust / mobile / web)

| Layer | Today | Target |
|-------|-------|--------|
| Rust | Core contracts, CLI | **Source of truth** for disk graph + destructive ops |
| BootForge Python | Rich GUI, legacy integrations | **Host UX**; thin wrappers over Rust |
| FastAPI | HTTP for mobile/cloud | **Orchestration**, same safety policy as desktop |
| Web | Flask demo, recovery GUI static | **Non-authoritative** unless explicitly connected to backend |

---

## Prioritized task list

### P0 — Safety and honesty

1. Align FastAPI safety rules with `SafetyValidator` policy or call shared validation code.
2. Ensure no build path uses demo device without `PHX_ALLOW_DEMO_DEVICE`.
3. Return explicit `platform_support` in build progress when `dd`/format is simulated.

### P1 — Structure

4. Deprecate `server/` or repoint it at `desktop/src` with one `PHOENIX_CORE_PATH` strategy.
5. Mark `legacy/bootable_usb/BootForge` archived in README (pointer only).
6. Resolve `mobile/` vs `phoenix-core-mobile/` product ownership.

### P2 — Convergence

7. Expose `phoenix-cli device-graph` (or similar) and optionally have `backend` shell out or link FFI for scanning.
8. Integration tests: safety validation matrix (missing device, system disk, too small).

### P3 — Visibility

9. Standard job/event schema for mobile polling (build state, logs, cancellation).
10. Document `PHOENIX_REPO_ROOT` for packaged installs.

---

## Implementation plan (phased)

| Phase | Focus | Outcome |
|-------|--------|---------|
| **1** | Docs + path resolution + README accuracy | Operators know what is canonical; no hard-coded paths |
| **2** | Safety + device listing | Shared policy; demo mode explicit; fewer foot-guns |
| **3** | UX | Wizard/API parity for confirmations |
| **4** | Tests + CI | pytest finds `desktop/src`; API tests for safety |
| **5** | Mobile/cloud | One OpenAPI contract; event stream or poll contract |

---

## Code changes in this branch (reviewable)

- `backend/core/phoenix_paths.py` — repo root and OCLP/GUI path resolution.
- `backend/core/usb_builder.py` — demo device gated; paths use `phoenix_paths`.
- `backend/main.py` — diagnostics use repo root, not `/home/ubuntu/...`.
- `main.py` (root) — delegates to `desktop/main.py`.
- `tests/conftest.py` — adds `desktop/` to `sys.path` for `src.*` imports.

Further PRs should keep **mechanical doc + safety changes** separate from **large refactors** for easier review.
