# PR21 Build Agent Setup - Local and Remote Configuration

Date: 2026-05-13

## Summary

PR21 adds build-agent setup and preflight guidance for Phoenix OS OCI builds across:

- Windows 11 + WSL2 + Docker Desktop
- Native Linux
- macOS Docker Desktop
- Remote Linux VM

This PR does not claim ISO build completion.

## Files Added

- `os/phoenix-os/docs/LOCAL_BUILD_AGENT.md`
- `os/phoenix-os/docs/REMOTE_BUILD_AGENT.md`
- `os/phoenix-os/scripts/check-build-agent.ps1`
- `os/phoenix-os/scripts/check-build-agent.sh`
- `docs/release/PR21_BUILD_AGENT_SETUP.md`

## What PR21 Delivers

- Exact setup and verification commands for local OCI runtime availability
- WSL2-first Windows path with explicit Docker Desktop integration checks
- Linux/macOS preflight script path and optional privileged-container probe
- Remote VM workflow with SSH build execution and artifact retrieval commands
- Truth boundary guidance: preflight success does not equal ISO build success

## Current Host Recommendation

Based on prior blocker context (Windows/BootCamp host without active Docker/Podman in PATH), recommended path is:

1. Preferred local path: Windows 11 + WSL2 + Docker Desktop, repository cloned inside WSL filesystem
2. Fallback path: remote Ubuntu/Debian build VM with Docker, using SSH workflow

## Remaining Blockers

- No active container runtime in host PATH blocks truthful ISO build claims.
- `verify-container.sh` / `build-container.sh` must be present and executable under `os/phoenix-os/container/`.
- Any ISO claim remains blocked until container verification and build scripts run successfully on an active runtime.

## Next Recommended PR

PR22: OCI Build Execution Evidence and Artifact Contract

Suggested PR22 scope:

- execute `verify-container.sh` on a confirmed active runtime
- execute `build-container.sh` and capture real logs/artifact paths
- publish reproducible build evidence (runtime version, command lines, timestamps, artifact checksums)
- document failure taxonomy if build does not complete
