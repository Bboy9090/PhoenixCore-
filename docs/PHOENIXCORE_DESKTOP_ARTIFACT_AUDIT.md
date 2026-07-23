# PhoenixCore Desktop Artifact Audit

Status date: 2026-07-23

## Current classification

```text
browser dashboard source: implemented
Vite development bridge: implemented
static frontend build: implemented
standalone desktop runtime: not implemented
installable desktop artifact: not verified
ARCWYRE package: not proven
```

## Source findings

The current dashboard is located under `dashboard/`.

`dashboard/package.json` declares:

- package name: `dashboard`
- version: `0.0.0`
- runtime: React + Vite
- build command: `vite build`
- no Electron dependency
- no Tauri dependency
- no desktop installer command
- no application signing command

`dashboard/vite.config.js` contains the Python bridge for USB scanning, image inspection, drive safety, and dry-run planning. That bridge is registered through Vite's `configureServer` development hook and invokes repository-root Python files directly.

The production `vite build` output is static frontend content. It does not contain a durable desktop host, Python sidecar, Tauri command layer, service manager, installer, update path, rollback path, or uninstall receipt.

## Consequence

The existing dashboard may be used as a development and browser interface, but it must not be classified as the PhoenixCore Desktop installable application merely because the frontend compiles.

This audit does not change the dashboard safety boundary. Physical media writing remains disabled from the normal dashboard flow.

## Required product decision

PhoenixCore Desktop needs one canonical host architecture. The recommended lane is a dedicated desktop shell that reuses the reviewed dashboard UI while moving the Python bridge out of Vite development middleware and into an explicit, versioned native command boundary.

The host architecture must define:

1. application identity and semantic version
2. Windows x86_64 initial target
3. native host technology and update policy
4. Python runtime strategy: embedded, sidecar, or replaced native service
5. versioned command schemas for scan, inspect, safety, and plan operations
6. allowlisted command execution
7. path validation and timeout policy
8. no fabricated browser hardware
9. no dashboard physical-write capability
10. install, launch, update, rollback, and uninstall receipts
11. code signing and signature verification
12. source artifact receipt generation
13. ARCWYRE compatibility and packaging proof

## Release law

Until a real desktop host and installer exist, the source registry must retain:

```text
phoenixcore-desktop.artifact_status = not-verified
```

A Vite `dist/` directory is a web build, not a desktop application artifact.
