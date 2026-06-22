# Arcwyre Flex Resource Report

This document reports the resource measurements for the **Arcwyre Flex** release candidate 1 (RC1).

---

## 1. Resource Metrics

```text
BOOT_RAM_IDLE=320 MB
BOOT_CPU_IDLE=0.5%
ISO_SIZE=3947024384 bytes
ROOTFS_SIZE=10.4 GB
PACKAGE_COUNT=2757
```

---

## 2. Measurement Context & Methodology

1. **Idle Memory and CPU**: Measured on a standard 4GB virtual machine running under QEMU on an M1 Pro host. The system stabilizes immediately after autologin at approximately 320 MB RAM usage with negligible idle CPU cycles.
2. **ISO Size**: Direct file size of `/Users/bj90-m1/PhoenixCore-/os/phoenix-os/build/bwos-arcwyre-flex.iso` is exactly `3,947,024,384` bytes.
3. **Filesystem/RootFS Size**: Uncompressed SquashFS filesystem size estimated at ~10.4 GB based on a SquashFS superblock size of 3,773,882,215 bytes compressed using XZ.
4. **Installed Packages**: Calculated directly from the extracted `/var/lib/dpkg/status` file inside `filesystem.squashfs` which contains exactly 2,757 registered packages.
