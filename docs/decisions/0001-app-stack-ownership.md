# 0001: App Stack Ownership

Status: Accepted

Date: 2026-05-11

## Context

PhoenixCore currently has multiple overlapping app stacks:

- root Expo app in `app/`, `App.tsx`, and `index.tsx`,
- secondary Expo/React Native app in `mobile/`,
- duplicate Expo app in `phoenix-core-mobile/`,
- Vite recovery GUI in `website/recovery-gui/`,
- shared typed client candidate in `services/api.ts`,
- Manus-generated runtime/template references in the root app and server template code.

PR5 resolves ownership labels before any source movement.

## Decision

| Current system | PR5 label | Future owner |
| --- | --- | --- |
| Root Expo app | Canonical Mobile | Mobile |
| `mobile/` | Feature harvest candidate | Mobile |
| `phoenix-core-mobile/` | Feature harvest candidate | Mobile, then possible Archive |
| `website/recovery-gui/` | Web/demo reference only | Web, with BootForge visual-reference value |
| `services/api.ts` | Transitional typed Phoenix Agent client candidate | Phoenix Agent |
| Manus/Base44/generated UI references | Visual/product reference only | Archive or manual migration target |

No Expo app is the canonical Phoenix Control Center implementation.

## Consequences

- Phoenix Mobile may use Expo/React Native.
- Phoenix Control Center must not be built on Expo/React Native.
- The root Expo app is the current best Mobile baseline because it has the broadest route set, current root scripts, pnpm metadata, Expo Router, typed routes, tRPC/React Query setup, admin/OAuth routes, and builder/wizard/knowledge flows.
- `mobile/` and `phoenix-core-mobile/` should be compared and harvested for unique screens, API clients, enterprise/mobile ideas, and device workflows.
- `website/recovery-gui/` is not canonical Web and not canonical Control Center. It is a Vite web/demo reference with BootForge/recovery visual ideas.
- `services/api.ts` may remain only if it becomes a typed Phoenix Agent client or transitional SDK. If the future Agent contract replaces it, archive or remove it in a later PR.

## Non-Goals

- No app files are moved in PR5.
- No duplicate app is deleted in PR5.
- No imports, routes, package files, or build scripts are rewritten in PR5.
