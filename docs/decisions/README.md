# PhoenixCore Decision Records

This directory contains architecture and product ownership decisions for Phoenix Platform.

PR5 resolves duplicated app-stack ownership without moving implementation files.

## Rules

- Decision records document ownership and future direction.
- They do not move source, delete duplicate apps, or rewrite architecture.
- When a decision supersedes an unresolved item in `docs/ownership/`, the decision record wins for future PR planning.
- Implementation PRs must still include tests, migration notes, and rollback notes.

## PR5 Records

- `0001-app-stack-ownership.md` - ownership labels for root Expo app, `mobile/`, `phoenix-core-mobile/`, `website/recovery-gui/`, `services/api.ts`, and generated UI references.
- `0002-control-center-canonical-stack.md` - Phoenix Control Center stack decision.
- `0003-mobile-web-boundaries.md` - Mobile and Web boundaries.
- `0004-generated-ui-reference-policy.md` - generated prototype/reference policy.
- `app-stack-comparison.md` - observed app-stack comparison and final ownership table.
