# Repository Scripts

`scripts/` contains repo-level automation that is not owned by a single app, service, crate, or OS image profile.

Current scripts remain in place. Future PRs should separate:

- repository maintenance scripts,
- development environment helpers,
- release helpers,
- OS build scripts, which belong under `os/phoenix-os/scripts/`.

Platform-specific build helpers may live here when they coordinate multiple edition
targets, such as `build-home-platform-matrix.sh` for the Home amd64/arm64/i386 set.

No script behavior changes in PR 3.
