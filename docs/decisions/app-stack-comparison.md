# App Stack Comparison

PR5 compares app stacks and assigns ownership labels. It does not move or delete source.

## Exact Files And Paths Inspected

- Root app: `package.json`, `app.config.ts`, `App.tsx`, `index.tsx`, `app/_layout.tsx`, `app/(tabs)/_layout.tsx`, `app/(tabs)/*`, `app/admin/*`, `app/oauth/callback.tsx`, `lib/_core/manus-runtime.ts`.
- `mobile/`: `mobile/package.json`, `mobile/index.tsx`, `mobile/src/App.tsx`, `mobile/src/screens/*`, `mobile/src/services/api.ts`, `mobile/src/utils/theme.ts`.
- `phoenix-core-mobile/`: `phoenix-core-mobile/package.json`, `phoenix-core-mobile/app/_layout.tsx`, `phoenix-core-mobile/app/(tabs)/*`, `phoenix-core-mobile/app/dev/theme-lab.tsx`, `phoenix-core-mobile/app/oauth/callback.tsx`, `phoenix-core-mobile/lib/api.ts`, `phoenix-core-mobile/lib/api/phoenix-enterprise-client.ts`, `phoenix-core-mobile/lib/api/multi_device_routes.py`, `phoenix-core-mobile/lib/api/usb_creation_routes.py`, `phoenix-core-mobile/lib/config.ts`.
- Web reference: `website/recovery-gui/package.json`, `website/recovery-gui/README.md`, `website/recovery-gui/src/main.tsx`, `website/recovery-gui/src/App.tsx`.
- Shared API candidate: `services/api.ts`.
- Generated-reference search: `git grep -n -i -E 'base44|manus' HEAD -- .`.

## Comparison Table

| System | Route structure | Package manager | Framework | Main entrypoint | Overlap | Future target | Preserve or harvest | Archive risk | Recommended final owner |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Root Expo app | Expo Router tabs, admin, dev, OAuth; rich builder/wizard/knowledge routes | `pnpm@9.12.0` declared; root also has npm lockfile | Expo Router, React Native, React 19, NativeWind/Tailwind, tRPC/React Query | `index.tsx`, `App.tsx`, `app/_layout.tsx` | Overlaps with both mobile apps on builder, wizard, USB, knowledge, device workflows | `apps/mobile/` | Current Mobile baseline, route taxonomy, admin/OAuth, builder/wizard/knowledge flows, query/tRPC setup | Manus runtime/config must be removed or rewritten before production | Mobile |
| `mobile/` | React Navigation tabs: Dashboard, Devices, Build, Settings | npm lockfile | Expo/React Native, React Navigation, React 18 | `mobile/index.tsx`, `mobile/src/App.tsx` | Overlaps with root and `phoenix-core-mobile` on dashboard/devices/build/API client | `apps/mobile/` harvest input | API client, dashboard/devices screens, theme system | Some files appear generated/minified with escaped newlines; not strong canonical base | Mobile harvest |
| `phoenix-core-mobile/` | Expo Router tabs plus dev/theme lab and OAuth | npm lockfile | Expo Router, React Native, React 18 | `phoenix-core-mobile/app/_layout.tsx` | Overlaps with root on builder, wizard, knowledge, OAuth; overlaps with `mobile/` on devices/monitor/API | `apps/mobile/` harvest input, then possible `archive/legacy-mobile/` | USB create flow, monitor, devices, enterprise client concepts, config, icons | Duplicate app identity and prior generated native payloads | Mobile harvest, then Archive if superseded |
| `website/recovery-gui/` | Single Vite app component with splash and dashboard | npm lockfile | Vite, React, TypeScript, Tailwind | `website/recovery-gui/src/main.tsx` | Recovery/dashboard visuals overlap with BootForge and web demo needs | `apps/web/` reference or archive | Recovery dashboard visuals, PHX splash, BootForge visual language ideas | Vite starter docs and recovery-only positioning | Web/demo reference, BootForge visual reference |
| `services/api.ts` | No UI routes; typed API client | repo TypeScript context | Axios TypeScript client | exported `api` singleton | Duplicates `mobile/src/services/api.ts`; overlaps future Phoenix Agent SDK | `services/phoenix-agent/` client or generated SDK | Type shapes for USB, hardware, metrics, recipes, safety, builds, OCLP, images, workflows, diagnostics | Could become stale if Agent API changes | Phoenix Agent transitional SDK |
| Manus/Base44/generated refs | Runtime/config/template references, no Base44 refs found | mixed | generated/runtime/template references | `lib/_core/manus-runtime.ts`, `app.config.ts`, server template files | Touches root app, OAuth, server docs/code | Archive or manual migration only | Product/visual ideas after review | Security and platform assumptions if copied blindly | Archive/reference |

## Ownership Labels

| Current system | Required PR5 label | Final owner |
| --- | --- | --- |
| Root Expo app | Canonical Mobile | Mobile |
| `mobile/` | Feature harvest candidate | Mobile |
| `phoenix-core-mobile/` | Feature harvest candidate | Mobile, then possible Archive |
| `website/recovery-gui/` | Web/demo reference only | Web, with BootForge visual-reference value |
| `services/api.ts` | Transitional typed Phoenix Agent client candidate | Phoenix Agent |
| Manus/Base44/generated references | Visual/product reference only | Archive/reference unless manually migrated |

## Recommended Harvest List

Root Expo app:

- builder, wizard, knowledge, device, video tutorial, recipe export, admin, OAuth, and theme/provider structure;
- current pnpm scripts and Expo Router route taxonomy;
- tRPC/React Query integration ideas after Phoenix Agent API contract exists;
- remove Manus runtime assumptions before production.

`mobile/`:

- device and dashboard screens;
- `mobile/src/services/api.ts` type surface, reconciled with `services/api.ts`;
- theme constants if cleaner than root equivalents.

`phoenix-core-mobile/`:

- `usb-create`, monitor, devices, knowledge, and enterprise client ideas;
- Python route prototypes only as API-design references, not app-owned backend source;
- app icons if they are unique and license-safe.

`website/recovery-gui/`:

- splash/dashboard visual ideas;
- recovery-mode mood board for BootForge or Phoenix Key;
- do not preserve recovery-only positioning as Phoenix OS doctrine.

## Open Conflicts After PR5

- Exact Mobile implementation migration sequence is still open.
- Phoenix Agent API contract is not final, so `services/api.ts` remains transitional.
- `website/recovery-gui/` is a web/demo reference, but whether its visuals are harvested by BootForge, Phoenix Key, or Phoenix Web is still open.
- Generated Manus OAuth/runtime dependencies still need removal or replacement before production.
