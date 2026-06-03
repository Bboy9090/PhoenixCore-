# Phoenix Apps

`apps/` is the future home for user-facing Phoenix Platform applications.

PR 3 establishes the city map only. Existing working source remains in its current locations until migration PRs can move one subsystem at a time with tests and ownership notes.

Canonical app targets:

- `phoenix-control-center/` - the main Phoenix OS desktop shell and system UI.
- `phoenix-welcome/` - first-run onboarding for a new Phoenix OS install.
- `bootforge/` - deployment, imaging, USB creation, and repair workflows.
- `phoenix-key/` - rescue and provisioning mode.
- `mobile/` - Expo React Native companion app.
- `web/` - public web, docs, download, and support surfaces.

Existing `apps/cli/` remains in place as the current Rust CLI entrypoint. It is not migrated or rewritten in PR 3.
