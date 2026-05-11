# Phoenix Tests

`tests/` is the canonical home for cross-cutting repository tests.

Existing tests remain unchanged in PR 3. Future migration work should add tests before moving behavior across app, service, crate, or OS boundaries.

Expected future coverage:

- Rust workspace contracts.
- Phoenix Agent API contracts.
- BootForge workflow fixtures.
- Phoenix Control Center command bindings.
- OS package/build validation.
- Safety gate and report generation behavior.
