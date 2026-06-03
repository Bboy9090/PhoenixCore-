# Phoenix Control Center Migration Notes

Current source candidates:

- Root Expo app: `app/`, `App.tsx`, `index.tsx`, `package.json`, and related Expo config.
- Existing Tauri traces: `desktop/tauri-app/`.
- Rust system layer: `crates/core/`, `crates/safety/`, `crates/report/`, `crates/workflow-engine/`, and host crates.
- Transitional API candidates: `backend/`, `server/`, and `services/api.ts`.

Migration rule:

Do not copy everything into this app at once. First define the Control Center shell contract, then migrate one user workflow at a time while keeping the current root app operational.

Not migrated in PR 3:

- Root Expo routes.
- Existing Tauri code.
- Backend or Rust command bindings.
- UI components or styling.
