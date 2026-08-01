# Phoenix Key 3.2 guarded-write release candidate

## Claim

Phoenix Key 3.2 integrates the existing Windows sacrificial-drive writer into the PhoenixCore desktop application. The candidate may write an image only to a live-proven external USB, SD, or MMC physical drive after identity-bound operator authorization. Browser and dashboard surfaces remain unable to write.

## Permanent blocks

The backend rejects a target when any of these conditions apply:

- the target is not an exact `\\.\PHYSICALDRIVE<n>` path;
- Windows identifies it as a boot or system disk;
- its bus is not USB, SD, or MMC;
- it lacks a stable serial number or unique identifier;
- it is read-only;
- the source image is missing, empty, or larger than the target;
- the operator acknowledgement or exact identity-bound authorization differs;
- the source build lacks a 40-character commit identity;
- Phoenix Key is not running elevated on Windows;
- the target identity or capacity changes before raw access; or
- the private backend execution unlock is absent.

## Execution and evidence

The writer opens only the canonical physical target, caps output at the exact image size, flushes the target, reads back the same byte range, and requires its SHA-256 to match the source. A successful receipt is stored beneath `%LOCALAPPDATA%\PhoenixKey\receipts` and records the target identity, source commit, image hash, byte counts, readback hash, and verification result.

## Validation gates

Before merge, the exact candidate head must pass:

1. Phoenix Key TypeScript compilation and production build.
2. Repository boundary checks for every safe-device invariant.
3. Artifact receipt tests reporting `write-enabled-unsigned-release-candidate`.
4. Rust unit tests for identity-bound authorization and blocked-device evidence.
5. Python writer tests for unlock, authorization, identity drift, byte caps, short writes, corrupt readback, read-only targets, and non-external buses.
6. Windows MSI and NSIS construction with an exact source commit embedded.
7. Existing repository governance, danger, artifact, and application-reality gates.

## Promotion boundary

CI can establish an unsigned write-enabled release candidate. Friends-and-family promotion additionally requires an elevated Windows sacrificial-device write receipt with full readback verification and a named-machine boot receipt. Public production release additionally requires Authenticode signing and timestamp verification.
