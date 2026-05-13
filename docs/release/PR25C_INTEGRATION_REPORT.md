# PR25C Phoenix Control Center Integration Report

Date: 2026-05-13

## Summary

PR25C integrates the harvested components from PR25B into a unified architecture. The logic is now split into a clean **Engine Layer** (`phoenix-core`) and a **Bridge Layer** (`phoenix-control-center` Tauri app).

## 1. Engine Integration (`phoenix-core`)
- **Exposed Modules**: `dashboard::system`, `dashboard::build_monitor`, `dashboard::notifications`, and `dashboard::log_export` are now public.
- **Library Decoupling**: Removed all `tauri` specific attributes and dependencies from the `phoenix-core` dashboard modules to ensure it remains a pure Rust engine.
- **Dependencies**: Added `sysinfo`, `lazy_static`, and `hostname` to `crates/core/Cargo.toml`.

## 2. App Integration (`phoenix-control-center`)
- **Tauri Bridge**: Refactored `src-tauri/src/main.rs` to act as a thin bridge, delegating all system and build commands to `phoenix-core`.
- **Cargo Configuration**: Updated `src-tauri/Cargo.toml` to link against the local `phoenix-core` crate.
- **Frontend Wiring**:
    - Fixed relative imports in `SystemInfo.tsx`, `DiskManagement.tsx`, `systemService.ts`, and `systemStore.ts`.
    - Integrated `LoadingSkeleton` and `ErrorBoundary` components for a polished UI experience.
    - Verified that `systemService.ts` correctly calls Tauri's `invoke` for the renamed dashboard commands.

## 3. Truth-First Validation
- [x] **Namespace Sync**: `system::` and `log_export::` prefixes removed in favor of direct crate exports.
- [x] **Type Integrity**: TypeScript interfaces in `system.ts` are synchronized with the Rust `PartitionInfo` and `HardwareInfo` structs.
- [x] **Safety Gates**: Disk management operations in the UI are correctly gated for non-system disks.

## Next Steps
**PR26: Full System Build & Simulation Pass.**
With the dashboard integrated, we can now attempt a full build and use the new **Build Monitor** to track progress in real-time within the UI.
