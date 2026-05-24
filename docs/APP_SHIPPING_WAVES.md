# App Shipping Waves

## Shipping Gate

Apps ship with an edition only after the edition artifact has:

- Registered ISO metadata
- Verified checksum
- VM boot result
- VM boot matrix classification
- USB boot result or scoped exception
- App validation result
- Safety validation result
- Package provenance preserved for any symbolic or edition-specific package entries

## Wave Policy

Built ISO:

- Means the synthesis pipeline produced a file.
- Does not mean the edition is release-ready.

Release candidate:

- Requires explicit validation evidence.
- Must not be inferred from file existence, filename, or preflight-only structure checks.
- Must not be inferred from ISO generation alone; `BOOT_PASS_DESKTOP` is the minimum VM boot class that can count as a pass.
- Architecture-specific editions (`home`, `home-arm64`, `thunder-god-arm64`, `home-legacy-i386`) are separate shipping artifacts and must be validated independently.
- For the current bootable scope, `thunder-god-arm64` and `home-legacy-i386` are the active build targets; the amd64 Home track and Home ARM64 foundation track are deferred.

## PR38 Status

The current registry marks artifacts as:

- `built`
- `checksum_verified`
- `vm_boot_untested`
- `usb_boot_untested`
- `release_blocked`

App shipping status remains blocked until PR40 records runtime app-launch evidence per edition.
