# OS Scripts

Future home for Phoenix OS image build, validation, release, and packaging scripts.

Scripts here should be reproducible, non-destructive by default, and explicit about host requirements.

Current build instrumentation entrypoints:

- `build-logger.sh` for structured build events, phase timing, and summary generation
- `build-heartbeat.sh` for periodic alive snapshots without fake ETA or progress
- `watch-build.sh` for a safe live status view of the current build

The telemetry files are written under `os/phoenix-os/build/telemetry/<build-id>/` and summarized into `os/phoenix-os/build/build-summary.json` plus `os/phoenix-os/build/build-summary.md`.

No OS scripts are added in PR 3.
