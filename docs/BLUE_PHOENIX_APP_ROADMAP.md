# Blue Phoenix App Roadmap

## Release Reality Rule

ISO existence does not equal release readiness.

An edition can have a built ISO and still be blocked if any of the following are missing:

- VM boot validation
- USB boot validation
- App validation
- Safety validation
- Artifact registry metadata
- VM boot matrix classification
- Edition package provenance (`package-profile.source.txt`, `package-profile.installed.txt`, `package-profile.blocked.txt`)

## Platform Targets

Home is now treated as a platform family, not a single artifact:

- `home` for amd64 / current Intel and AMD systems
- `home-arm64` for Apple Silicon / M1-class systems
- `thunder-god-arm64` for the flagship Apple Silicon / ARM64 power build
- `home-legacy-i386` for legacy 32-bit Intel Macs

These are separate boot targets. One ISO cannot truthfully claim all three CPU families.
For the current build phase, the active targets are `thunder-god-arm64` and `home-legacy-i386`; the amd64 Home track and Home ARM64 foundation track are deferred.

## App Validation Track

Each edition needs an app validation record before release-candidate promotion:

- Launch-critical apps start without crashing.
- Edition-specific apps are present only where intended.
- Dangerous or destructive app actions are gated.
- Offline behavior is documented.
- Visual branding does not hide safety prompts.

## Current PR38 State

PR38 records the ISO files and their provenance metadata. It does not certify the apps inside those ISOs.
Edition staging now preserves the original package profile plus the installed and blocked package lists for auditability.

Current app validation status for generated ISO artifacts:

- `not_run`

## Next Roadmap Step

PR40 is the app launch matrix baseline. It records the current validator truth, but runtime launch evidence is still pending.
The release note for that baseline is [PR40_APP_LAUNCH_MATRIX.md](./release/PR40_APP_LAUNCH_MATRIX.md).
