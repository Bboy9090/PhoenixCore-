# 0004: Generated UI Reference Policy

Status: Accepted

Date: 2026-05-11

## Context

The repo contains Manus-generated or Manus-template references in app config, runtime helpers, server template docs/code, deployment docs, OAuth identifiers, and generated-style app surfaces.

No `Base44` references were found during PR5 inspection, but the same policy applies if Base44 references appear later.

## Decision

Base44, Manus, or other generated prototypes are visual and product references only unless manually migrated into canonical source.

Generated UI code must not become canonical by being copied wholesale into:

- Phoenix Control Center,
- Phoenix Mobile,
- Phoenix Web,
- Phoenix Agent,
- BootForge,
- Phoenix Key.

Manual migration means:

- rewrite into the canonical stack,
- remove generator/runtime assumptions,
- replace template auth/runtime glue,
- verify security boundaries,
- add tests,
- document source and ownership.

## Specific PR5 Classifications

- Manus runtime references in the root Expo app are transitional Mobile implementation details, not a Phoenix Platform runtime contract.
- Manus OAuth/template references in `server/` are generated/transitional references, not canonical Phoenix Agent authentication.
- `services/api.ts` is a transitional typed Phoenix Agent client candidate because it defines device, hardware, metrics, recipe, safety, build, OCLP, image, workflow, and diagnostic API shapes. It must be reconciled with the future Phoenix Agent contract before being treated as canonical.

## Security Rule

Generated runtime bridges that use broad browser messaging, template OAuth, or hosted preview assumptions require explicit security review before production use.

No generated UI reference may bypass the rule:

```text
UI -> Phoenix Agent -> Rust safety gates
```
