# PR40 App Launch Matrix Baseline

**Status:** pending runtime evidence
**Date:** 2026-05-23

## Goal

Record actual launch behavior for the active BWOS / Blue Phoenix OS app set and
separate that runtime truth from package-list or manifest truth.

## Current Scope

Active flagship app manifests:

- `command`
- `harbor`
- `compass`
- `relay`
- `safe`
- `workshop`
- `bootforge`
- `market`

Core launch suite packages currently validated in the active profiles:

- `firefox-esr`
- `kcalc`
- `dolphin`
- `konsole`
- `systemsettings`
- `kwrite`
- `gwenview`

## What Is Proven Right Now

Preflight validators pass:

- `os/phoenix-os/scripts/validate-launch-apps.sh`
- `os/phoenix-os/scripts/validate-launch-experience.sh`

Observed validator state:

- core packages are explicitly listed in the active profiles
- no placeholder or TODO desktop launchers are present in staged app locations
- the flagship manifest set exists and is marked `launch_critical: true`
- no duplicate launcher commands were reported by the experience validator
- no experimental menu sprawl was detected in active launcher surfaces

## What Is Not Yet Proven

This PR does **not** yet claim runtime launch success for the active app set.
Still needed:

- actual app launch execution in the live desktop session
- visible confirmation that each flagship app opens and responds
- failure capture for any app that crashes or hangs on launch
- screenshot or log evidence tied to the edition / artifact hash

## Truth Boundary

Package presence is not launch success.
Manifest presence is not launch success.
Only observed runtime behavior counts as launch evidence.

## Next Step

Promote this baseline into a real launch matrix by capturing runtime launch
evidence on a known-good desktop boot artifact, then recording the observed
result for each flagship app.
