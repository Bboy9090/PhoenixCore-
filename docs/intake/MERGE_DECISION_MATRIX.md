# Phoenix Ecosystem Merge Decision Matrix (PR25A)

This matrix defines the handling of artifacts from Claude and Manus during the intake audit.

## 1. Top 20 Harvest Candidates

| Rank | Source | Candidate | Target Path | Decision |
|------|--------|-----------|-------------|----------|
| 1 | Manus | `system.rs` / `build_monitor.rs` | `crates/core/src/` | HARVEST |
| 2 | Claude | `packages/phoenix-theme/` | `os/phoenix-os/branding/` | HARVEST |
| 3 | Manus | `DiskManagement.tsx` | `apps/desktop/src/` | HARVEST |
| 4 | Claude | `50-phoenix-disk-ops.rules` | `os/phoenix-os/config/polkit/` | HARVEST |
| 5 | Manus | `SystemInfo.tsx` | `apps/desktop/src/` | HARVEST |
| 6 | Claude | `90-phoenix-disk-policy.rules`| `os/phoenix-os/config/udev/` | HARVEST |
| 7 | Manus | `themeStore.ts` | `apps/desktop/src/store/` | HARVEST |
| 8 | Claude | `validate-iso.sh` | `os/phoenix-os/scripts/` | HARVEST |
| 9 | Manus | `LogExporter.rs` | `crates/core/src/` | HARVEST |
| 10| Claude | `package-debs.sh` | `os/phoenix-os/scripts/` | HARVEST |
| 11| Manus | `notifications.rs` | `crates/core/src/` | HARVEST |
| 12| Claude | `phoenix-welcome` app | `os/phoenix-os/apps/` | HARVEST |
| 13| Manus | `systemStore.ts` | `apps/desktop/src/store/` | HARVEST |
| 14| Manus | `ARCHITECTURE.md` (Manus) | `docs/architecture/` | KEEP |
| 15| Manus | `BOOTCAMP_DRIVER_SYSTEM.md` | `docs/research/` | KEEP |
| 16| Claude | SDDM/Plymouth Themes | `os/phoenix-os/branding/` | HARVEST |
| 17| Manus | `Cargo.toml` (for deps only) | `crates/core/Cargo.toml` | REWRITE |
| 18| Claude | `auto/config` (for flags) | `os/phoenix-os/live-build/` | REWRITE |
| 19| Manus | `pasted_content.txt` (Audit) | `docs/audits/` | ARCHIVE |
| 20| Manus | `INTEGRATION_PLAN.md` | `docs/strategy/` | KEEP |

## 2. Rejected Files & Reasons

- **Claude: `scripts/setup-dev.sh`**: Reason: Unsafe host-level `apt-get` mutation.
- **Manus: `deploy-heroku.sh`**: Reason: Out of scope; non-industrial deployment target.
- **Manus: `vercel.json`**: Reason: Out of scope.
- **Manus: `driver_database.json`**: Reason: Requires manual verification against trusted hardware vendor lists.
- **Claude: `scripts/build-iso.sh`**: Reason: Redundant; our OCI-hardened version is superior for industrial use.

## 3. Recommended PR25B Harvest Scope

**PR25B Focus**: Visual & Logic Ingestion.
1.  **Themes**: Ingest Claude's Plymouth and SDDM themes into `os/phoenix-os/branding/`.
2.  **Dashboard Backend**: Ingest Manus's `system` and `monitor` Rust modules into `crates/core/` (gated by `CapabilityMatrix`).
3.  **Dashboard Frontend**: Ingest Manus's React components into a new `apps/desktop/` or `apps/agent-gui/` directory.
4.  **Safety Rules**: Ingest Claude's Polkit and Udev rules into the `live-build` config to ensure a safe live session.

## 4. Integration Guardrails
- All harvested code must be audited for **destructive patterns**.
- All Rust logic must be wrapped in **`CapabilityMatrix`** checks.
- No merged code should bypass the **Truth-First** audit pipeline.
