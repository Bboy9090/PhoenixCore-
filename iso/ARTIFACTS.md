# ARTIFACTS.md — Phoenix OS Build Artifact Registry

> Generated from `iso/outputs/manifest.json`. Do not edit manually.

## Active Artifacts

| Edition | Filename | SHA256 | Size | VM Boot | USB Boot | Release |
|---|---|---|---|---|---|---|
| Home Aurelia | `bwos-home.iso` | `463e8273...` | 2,276,368,384 | ✅ BOOT_PASS_DESKTOP | untested | release_blocked |
| Blue Phoenix | `bwos-aurelia.iso` | `6dcc4017...` | 2,181,836,800 | NOT_TESTED | untested | release_blocked |
| Arcwyre | `bwos-arcwyre.iso` | `3ba79189...` | 2,198,011,904 | NOT_TESTED | untested | release_blocked |
| Thunder God | `bwos-thunder-god.iso` | `4ea3fa9c...` | 2,171,047,936 | NOT_TESTED | untested | release_blocked |
| Home Legacy i386 | `bwos-home-legacy-i386.img` | `70b8efd7...` | 2,244,222,976 | NOT_TESTED | untested | release_blocked |

## Retired/Archived Editions

| Edition | Archived |
|---|---|
| forge | ✅ true |
| resilient | ✅ true |
| revival | ✅ true |

## Notes

- `bwos-home.iso` has completed VM boot and app-launch matrix validation (PR39L/PR40, 5x BOOT_PASS_DESKTOP, 3/3 repeatability, 8/8 App Launch Pass).
- All other editions remain `release_blocked` until VM boot, USB boot, and safety validation are completed.
- No artifact is currently a release candidate.
