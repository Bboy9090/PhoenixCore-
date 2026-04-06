# Lockdown phase implementation report

## L1 — Authority lock

**Changes:** Added `docs/AUTHORITY_MODEL.md` (hierarchy: BootForge > FastAPI > Rust primitives). Linked from `README.md`, `AGENTS.md`, `docs/CANONICAL_RUNTIME.md`.

**Why:** Documentation-only truth is insufficient; normative doc anchors enforcement below.

**Files:** `docs/AUTHORITY_MODEL.md`, `README.md`, `AGENTS.md`, `docs/CANONICAL_RUNTIME.md`

**Unresolved:** Rust still not auto-invoked by API; hierarchy is operational policy, not a single binary.

---

## L2 — Safety unification

**Changes:** `backend/core/safety_bridge.py` imports BootForge `SafetyValidator`; `backend/core/safety_schema.py` defines versioned payload; `validate_safety` in `usb_builder.py` merges scanner + recipe + validator + capability gates. DANGEROUS/BLOCKED → no token.

**Why:** Single validation path for API; same class as desktop when import succeeds.

**Files:** `backend/core/safety_bridge.py`, `backend/core/safety_schema.py`, `backend/core/usb_builder.py`, `docs/SAFETY_MODEL.md`

**Unresolved:** Full `desktop/src` import may still require PyQt6 etc.; if import fails, API refuses tokens (fail-closed).

---

## L3 — Capability enforcement

**Changes:** `backend/core/platform_guard.py`; `start_build` and non-dry `validate_safety` call `require_destructive_usb_native`; `POST /api/workflows/run` returns **503** if not dry-run and native false. Health already exposed flags; now duplicated in `features.destructive_usb_write_native`.

**Why:** Stops simulated/non-native destructive jobs from starting with a real token path.

**Files:** `backend/core/platform_guard.py`, `backend/core/usb_builder.py`, `backend/main.py`, `docs/CAPABILITY_MATRIX.md`

**Unresolved:** Linux without `parted` in PATH but present in `/usr/sbin` may still false-negative unless `platform_caps` finds it (existing helper).

---

## L4 — Ghost path purge

**Changes:** `docs/REPO_STATUS_MAP.md`; `mobile/README.md` deprecation; README marks `mobile/` deprecated; `server/` already deprecated in prior work.

**Why:** Hard labels reduce wrong-app onboarding.

**Files:** `docs/REPO_STATUS_MAP.md`, `mobile/README.md`, `README.md`

**Unresolved:** Non-core template not deleted (it was later moved under `experimental/root-app-template/` in Final Cleanup); documented as experimental.

---

## L5 — Device risk hardening

**Changes:** `scan_usb_devices(removable_only=, include_all=)`; `GET/POST` devices accept query params; default remains all disks for compatibility; **API requires `removable` for USB safety** (`require_removable=True`). `phoenix-enterprise-client` uses `removable_only=true` for USB list; `device_risk` in safety payload.

**Why:** Fewer internal disks in mobile picker; explicit risk metadata for clients.

**Files:** `backend/core/device_scanner.py`, `backend/main.py`, `phoenix-core-mobile/lib/api/phoenix-enterprise-client.ts`, `phoenix-core-mobile/app/(tabs)/usb-create.tsx`

**Unresolved:** OS mis-reports removable; operator must still verify physical device.

---

## L6 — Failure integrity

**Changes:** `BuildJob.preflight`, `failure_stage`, `rollback_available=False`; progress dict includes `preflight`, `failure_stage`, `rollback_available`; failed jobs log **no rollback** message.

**Why:** Honest operator expectations after partial writes.

**Files:** `backend/core/usb_builder.py`, `docs/SAFETY_MODEL.md`

**Unresolved:** No new telemetry pipeline; preflight is in-memory on job object.

---

## L7 — Docs/runtime sync

**Changes:** `docs/SAFETY_MODEL.md`, `docs/CAPABILITY_MATRIX.md`, `docs/REPO_STATUS_MAP.md`, `docs/LOCKDOWN_PHASE_REPORT.md`; README index; second-pass audit can reference lockdown.

**Why:** Single place for safety, capabilities, path status.

**Files:** (above)

**Unresolved:** Sweep every legacy markdown in `legacy/` — out of scope; canonical docs updated.
