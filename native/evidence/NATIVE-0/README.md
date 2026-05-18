# NATIVE-0 Evidence Folder

This folder stores verifiable boot artifacts for milestone `NATIVE-0`:

- `boot-serial-<arch>.log`: QEMU serial capture for each architecture.
- `boot-debugcon-<arch>.log`: x86 debug console capture (empty on non-x86).
- `run-command-<arch>.txt`: Exact launch command and timestamp.
- `status-<arch>.txt`: PASS/INCONCLUSIVE marker per architecture.
- `status.txt`: latest run summary snapshot.

The proof now validates **two-stage handoff**:
- Stage 1: `BOOTX64.EFI` native boot manager
- Stage 2: `KERNELX64.EFI` kernel stub entry

Generate evidence with:

```bash
/Users/bj90-m1/PhoenixCore-/scripts/native-native0-bootproof.sh
```

Optional architecture override:

```bash
NATIVE_ARCH=aarch64 /Users/bj90-m1/PhoenixCore-/scripts/native-native0-bootproof.sh
```
