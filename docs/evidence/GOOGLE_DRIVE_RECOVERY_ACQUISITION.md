# Phoenix Key — Google Drive Recovery Acquisition

Date: 2026-09-19  
Branch: `convergence/windows-recovery-forge-macos-v2`  
PR: #150

## Purpose

Add a read-only acquisition boundary in front of the existing cloud staging and recovery identity pipeline.

The acquisition layer does not modify Google Drive content and does not make a downloaded payload recovery-eligible by itself.

## Implemented core

`scripts/hardware/acquire_google_drive_recovery.py` provides:

- authenticated Google Drive v3 reads using an access token supplied through `PHOENIX_KEY_GOOGLE_DRIVE_ACCESS_TOKEN`
- folder enumeration through read-only `files.list`
- stored-binary metadata inspection before download
- `capabilities.canDownload` enforcement
- rejection of Google Workspace-native documents and folders as recovery payloads
- provider size validation
- resumable binary download using an HTTP byte range
- fail-closed behavior when a server does not honor the requested resume offset
- provider MD5 verification when Drive exposes `md5Checksum`
- local SHA-256 generation after the complete transfer
- atomic promotion from `.partial` to the selected local destination only after size/checksum validation
- receipts that explicitly state `cloud_original_modified=false`

The access token is not accepted as a command-line argument and is never included in receipts.

## Trust boundary

A successful Drive transfer proves acquisition completeness and, when Drive exposes an MD5 checksum, provider-transfer integrity.

It does **not** automatically prove that the payload is an approved recovery source.

The acquisition receipt therefore emits:

- `identity_lock_ready=true`
- `recovery_eligible=false`
- `identity_lock_required_before_recovery`

The downloaded local artifact must enter the existing SHA-256 source-identity and recovery-analysis pipeline before any recovery or destructive path can use it.

## Automated gates

`tests/test_google_drive_recovery_acquisition.py` covers:

- token-required behavior
- paginated folder listing
- GET-only request behavior
- complete download with provider MD5 and local SHA-256
- valid byte-range resume
- rejection when the server ignores the resume range
- rejection of non-downloadable files
- rejection of Google Workspace-native files
- malformed file-ID rejection before network access

`.github/workflows/cloud-recovery-staging.yml` now runs the acquisition tests on Ubuntu and Windows and scans the acquisition/staging source for Drive mutation calls and non-GET HTTP methods.

## Remaining product integration

- user-facing Google OAuth authorization
- Google Picker or equivalent explicit file/folder selection
- narrow-scope authorization strategy for public distribution
- handoff from acquisition receipt to local SHA-256 identity lock
- Recovery Center UI progress/cancel/resume states
- large-file and network-interruption evidence using sacrificial cloud fixtures

The PR remains draft while these product-level gates are incomplete.
