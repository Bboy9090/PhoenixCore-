# Capability matrix (enforced vs documented)

| Capability | BootForge desktop | FastAPI `backend/` |
|------------|-------------------|---------------------|
| Full wizard + integrations | Yes | N/A (API only) |
| Device scan (all disks) | Yes | `GET /api/devices` |
| Device scan (removable only) | N/A | `GET /api/devices?removable_only=true` |
| SafetyValidator | Yes (native) | Yes if `desktop/src` importable |
| Non-dry-run destructive USB write (`dd`/`parted`) | Platform-dependent (full tools in Python path) | **`destructive_usb_write_native` only** — blocked otherwise |
| macOS / Windows native write in `usb_builder` | Partial in code paths | **Blocked** for non-dry-run until Linux-style tools path exists |
| Rollback after failed write | No | **No** (`rollback_available: false`) |

**Source of truth in API:** `GET /api/health` → `capabilities` and `features.destructive_usb_write_native`.

**Rule:** Do not claim cross-OS parity in marketing; point operators to BootForge when the API refuses a job.
