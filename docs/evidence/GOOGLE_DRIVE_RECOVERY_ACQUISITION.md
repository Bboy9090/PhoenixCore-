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

## Explicit desktop Picker boundary

The convergence branch now also includes `google_drive_picker_recovery.py` and Recovery Center integration.

The desktop flow:
- requests exactly `https://www.googleapis.com/auth/drive.file`
- opens Google Picker in the system browser rather than an embedded webview
- uses a random IPv4 loopback callback
- uses PKCE S256 and a random OAuth state value
- requires exactly one explicitly selected file ID
- rejects callbacks that return a broader scope
- exchanges the authorization code without a client secret
- never returns the access token to React and never persists the token
- neutralizes path separators, Windows-invalid characters, control characters, and excessive filename length before local staging
- immediately captures the downloaded file's Phoenix Key SHA-256 source identity
- requires the acquisition SHA-256 to equal the source-identity SHA-256 before setting `identity_lock_verified=true`
- leaves `recovery_eligible=false` until the normal Recovery Center analysis/trust gates run

The OAuth client ID is public application configuration, not a secret. Phoenix Key accepts a build-time `PHOENIX_KEY_GOOGLE_DRIVE_CLIENT_ID` with a runtime override for development. The Picker UI stays disabled when no valid desktop client ID is configured.

## Remaining product integration

- create/configure the production Google Cloud desktop OAuth client and consent-screen metadata
- large-file, cancellation, timeout, and network-interruption evidence using sacrificial cloud fixtures
- explicit progress/cancel UX for long cloud downloads
- signed/notarized desktop release evidence using the configured production OAuth client

The PR remains draft while these product-level gates are incomplete.
