# PR41B — Safety Validator Test Matrix

This document defines the formal validation matrix and scenario specifications for the **PR41B Safety Validator** and host write-path logic. It establishes rigorous safety interlocks to prevent destructive write operations on system, parent, active host, or loopback block devices.

> [!CAUTION]
> **MANDATORY CORE SAFETY RULE:**
> **No operation may proceed if target classification confidence is below threshold.**
> If the host safety system cannot uniquely, securely, and with 100% confidence classify a block device as "External Removable USB," the target device *must* be treated as a system disk and locked from all write paths.

---

## 1. Severity Class Definitions
All validation anomalies and device discovery states must evaluate to one of the following severity classes:

* **`SAFETY_INFO`**: Non-blocking diagnostics and metadata logging. Used for reporting basic target features (e.g., interface speed, serial number).
* **`SAFETY_WARNING`**: Non-blocking notifications. Requires operator attention (e.g., target capacity is unusually large for USB, or partition layout is complex).
* **`SAFETY_BLOCK`**: Blocking security override. Prevents target selection or unmounting unless an explicit developer/override configuration is enabled.
* **`SAFETY_CRITICAL_BLOCK`**: Cryptographically and physically locked state. Absolutely **impossible** to bypass under any circumstances. Used for preventing writes to active boot partitions, internal macOS containers, or active root NVMe paths.

---

## 2. Block Classification Scenarios & Test Matrix

### Category 1: Active Host OS Disk Detection
* **Scenario**: Operator attempts to select the active host operating system drive as a USB target.
* **Expected Behavior**: Host queries mount tables, locates the physical drive backing `/` (root), and hard-locks the entire base device.
* **Rejection Message**: `CRITICAL_ERROR: Device [DEV_PATH] is the active host OS disk and cannot be targeted.`
* **Required Evidence**: `/proc/mounts` parsing (Linux) or `diskutil info /` parsing (macOS).
* **Pass/Fail Criteria**:
  * *Pass*: The system blocks selecting the parent physical device of `/` under all UI/CLI paths.
  * *Fail*: The disk appears in any interactive selector.
* **Severity Class**: `SAFETY_CRITICAL_BLOCK`

---

### Category 2: Mounted Filesystem Rejection
* **Scenario**: Operator selects an external device that contains one or more active mounted partitions (e.g., secondary backup disks or active document drives).
* **Expected Behavior**: Validator scans system mounts. If partitions are active, it blocks writes until partitions are safely unmounted, and explicitly rejects automatic force-unmounting without user verification.
* **Rejection Message**: `BLOCK_ERROR: Target [DEV_PATH] has active mounts: [MOUNT_LIST]. Unmount partitions first.`
* **Required Evidence**: `findmnt` output (Linux) or `mount | grep [DEV]` (macOS).
* **Pass/Fail Criteria**:
  * *Pass*: Write sequence blocks immediately when partition mount points are active.
  * *Fail*: Device unmounting triggers automatically without explicit verification.
* **Severity Class**: `SAFETY_BLOCK`

---

### Category 3: Parent-Device Rejection
* **Scenario**: Operator selects a specific partition (e.g., `/dev/sdb1` or `/dev/disk2s2`) instead of the base block device.
* **Expected Behavior**: Writing must occur strictly at the raw block sector layer. The system automatically shifts selection to the base disk and runs safety checks on the parent device.
* **Rejection Message**: `BLOCK_ERROR: Target must be a base physical device (e.g., /dev/sdb), not a partition.`
* **Required Evidence**: Sysfs node path checks (Linux) or `diskutil info` node parsing (macOS).
* **Pass/Fail Criteria**:
  * *Pass*: Selection is restricted to raw base physical devices; partition paths are rejected.
  * *Fail*: Raw writes are executed directly into a sub-partition slice, causing filesystem corruption.
* **Severity Class**: `SAFETY_BLOCK`

---

### Category 4: NVMe Namespace Protection
* **Scenario**: Operator targets internal NVMe storage controllers (SATA Express/M.2 PCIe drives).
* **Expected Behavior**: System maps NVMe bus namespaces and isolates boot storage blocks from external Thunderbolt NVMe targets.
* **Rejection Message**: `CRITICAL_ERROR: Internal NVMe disk [DEV_PATH] is protected.`
* **Required Evidence**: `nvme list` analysis (Linux) or physical bus interconnect tags matching `PCI-Express` / `Apple Fabric` (macOS).
* **Pass/Fail Criteria**:
  * *Pass*: Internal NVMe paths are completely omitted from candidate targets.
  * *Fail*: System lists internal M.2 SSDs.
* **Severity Class**: `SAFETY_CRITICAL_BLOCK`

---

### Category 5: Internal macOS APFS Container Protection
* **Scenario**: Operator targets an Apple File System (APFS) internal container scheme on a Mac.
* **Expected Behavior**: `diskutil` checks discover the APFS Container structure and lock the backing store.
* **Rejection Message**: `CRITICAL_ERROR: Base disk belongs to the internal APFS Container Scheme and is locked.`
* **Required Evidence**: `diskutil apfs list` output.
* **Pass/Fail Criteria**:
  * *Pass*: Any backing store mapped to an APFS System container is blocked.
  * *Fail*: Write attempts succeed on `disk0` or containers.
* **Severity Class**: `SAFETY_CRITICAL_BLOCK`

---

### Category 6: USB Removable-Device Validation
* **Scenario**: Operator connects a target external USB drive.
* **Expected Behavior**: System checks physical attributes (removable media flag, USB interface type, serial number, speed descriptor).
* **Rejection Message**: `BLOCK_ERROR: Target [DEV_PATH] is not classified as a valid USB removable device.`
* **Required Evidence**: `cat /sys/block/[DEV]/removable` (Linux) or `Protocol: USB` tag (macOS).
* **Pass/Fail Criteria**:
  * *Pass*: Device is identified as removable USB and allowed for building.
  * *Fail*: External SATA/Thunderbolt non-removable disks are accepted as standard targets.
* **Severity Class**: `SAFETY_INFO` / `SAFETY_WARNING`

---

### Category 7: Loopback / Virtual-Device Rejection
* **Scenario**: Operator targets a virtual drive (`/dev/loopX` or `diskimages`).
* **Expected Behavior**: Loopback and virtual disk nodes are intercepted and blocked from physical flash paths.
* **Rejection Message**: `BLOCK_ERROR: Loopback or virtual storage device [DEV_PATH] cannot be targeted.`
* **Required Evidence**: `/sys/devices/virtual/` checking (Linux) or `diskutil info` virtual state tags (macOS).
* **Pass/Fail Criteria**:
  * *Pass*: Virtual disks are locked.
  * *Fail*: Loopback drives are accepted for raw raw physical flash writes.
* **Severity Class**: `SAFETY_BLOCK`

---

### Category 8: Multi-Disk Ambiguity Handling
* **Scenario**: Multiple external USB storage drives with identical capacities, vendor names, and model names are plugged in.
* **Expected Behavior**: System enforces targeting via unique hardware serial paths and serial numbers (no selection by name).
* **Rejection Message**: `BLOCK_ERROR: Ambiguity detected. Multiple identical devices present. Target by serial path.`
* **Required Evidence**: `/dev/disk/by-id/` list (Linux) or raw device UUID/serial parsing (macOS).
* **Pass/Fail Criteria**:
  * *Pass*: Operator is forced to select using unique serial numbers to avoid writing to the wrong USB.
  * *Fail*: Selection relies on simple names, leading to target confusion.
* **Severity Class**: `SAFETY_BLOCK`

---

### Category 9: Live-Session Self-Target Prevention
* **Scenario**: Operator boots the Live OS environment on physical hardware and attempts to write to the active USB flash boot media itself.
* **Expected Behavior**: Live boot scripts resolve the backing block device of the running system and exclude it from the tool.
* **Rejection Message**: `CRITICAL_ERROR: Cannot overwrite active live-boot media [DEV_PATH].`
* **Required Evidence**: `/run/live/medium` or `/sysblock` match logic.
* **Pass/Fail Criteria**:
  * *Pass*: Live boot drive is strictly omitted.
  * *Fail*: System allows re-writing to the currently active flash drive.
* **Severity Class**: `SAFETY_CRITICAL_BLOCK`

---

### Category 10: Confirmation-Gate Escalation
* **Scenario**: Destructive flash write initiated on an allowed target.
* **Expected Behavior**: High-severity prompt displaying target model, capacity, and serial path, requiring manual input of a randomly generated 6-digit confirmation key.
* **Rejection Message**: `BLOCK_ERROR: Confirmation key mismatch. Operation cancelled.`
* **Required Evidence**: Generated confirmation code matching user text input.
* **Pass/Fail Criteria**:
  * *Pass*: Operation is locked until matching input is received.
  * *Fail*: Clicking 'OK' on standard dialog executes writes.
* **Severity Class**: `SAFETY_BLOCK`

---

## 3. Host Block-Level Command Examples & Diagnostics

### Host Root Device Identification

#### macOS Target Check Example
```bash
# Query the active host OS root mount details
$ diskutil info /
   Device Identifier:        disk1s1s1
   Device Node:              /dev/disk1s1s1
   Part of Whole:            disk1
   Device / Media Name:      Macintosh HD
   Volume Name:              Macintosh HD
   APFS Container:           disk1
   Device Location:          Internal

# BACKING STORE PARENT "disk1" MUST BE SAFETY_CRITICAL_BLOCK TARGET
```

#### Linux Target Check Example
```bash
# Query mount map for active root /
$ findmnt -n -o SOURCE /
/dev/nvme0n1p2

# parent node "nvme0n1" resolved by matching /sys/block/
# PARENT "nvme0n1" MUST BE SAFETY_CRITICAL_BLOCK TARGET
```

---

### lsblk Device Mapping Example (Linux Host)
```bash
$ lsblk -o NAME,TYPE,SIZE,RM,RO,MOUNTPOINT
NAME        TYPE   SIZE RM RO MOUNTPOINT
loop0       loop   2.1G  0  1 /run/live/rofs           <-- SAFETY_BLOCK (Virtual)
sda         disk 465.8G  0  0                          <-- SAFETY_CRITICAL_BLOCK (Internal SATA)
├─sda1      part   512M  0  0 /boot/efi
└─sda2      part 465.3G  0  0 /                        <-- Host OS Mount
sdb         disk  14.9G  1  0                          <-- ALLOWED (USB Removable Flash)
└─sdb1      part  14.9G  1  0 /media/phoenix/DATA      <-- SAFETY_BLOCK (Active Mount Point)
nvme0n1     disk 953.9G  0  0                          <-- SAFETY_CRITICAL_BLOCK (Internal NVMe)
```

---

### diskutil Partition Container Map (macOS Host)
```bash
$ diskutil list
/dev/disk0 (internal, physical):
   #:      TYPE NAME                    SIZE       IDENTIFIER
   0:      GUID_partition_scheme       *500.3 GB   disk0       <-- SAFETY_CRITICAL_BLOCK
   1:      EFI EFI                      314.6 MB   disk0s1
   2:      Apple_APFS Container disk1   500.0 GB   disk0s2     <-- Backing Container Store

/dev/disk1 (synthesized):
   #:      TYPE NAME                    SIZE       IDENTIFIER
   0:      APFS Container Scheme -500.0 GB   disk1       <-- Synthesized Container HD
   1:      APFS Volume Macintosh HD     15.2 GB    disk1s1
   2:      APFS Volume Macintosh HD_Data412.8 GB   disk1s2

/dev/disk2 (external, physical):
   #:      TYPE NAME                    SIZE       IDENTIFIER
   0:      GUID_partition_scheme        *16.0 GB   disk2       <-- ALLOWED (Target USB)
   1:      DOS_FAT_32 BOOTFORGE         16.0 GB    disk2s1     <-- Partitions Blocked
```

---

## 4. Known Catastrophic Failure Classes Prevented by PR41B

1. **Host Bootloader Overwrite (Internal Target)**:
   * *Mechanism*: Raw disk sector writer fails to filter internal devices and overrides `/dev/sda` (or `disk0`) sector tables.
   * *Consequence*: The host machine's GRUB/ESP configuration or Apple macOS partition map is completely zeroed out, resulting in a bricked development host upon reboot.
   * *PR41B Interlock*: Active Root Device Lockout + Internal NVMe/SATA Hardware Bus Filtering.
2. **System Partition Corruptive Format (Partition Target)**:
   * *Mechanism*: Write path permits direct target paths to partitions (`/dev/sdb1`), writing the raw ESP and Live OS blocks into a slice instead of base sectors.
   * *Consequence*: Filesystem tables become unaligned, resulting in boot device unreadability and corruption of neighboring slices.
   * *PR41B Interlock*: Parent-Device Selection Enforcement (automatic base disk derivation).
3. **Sustained Write Lockups (Active Mount Override)**:
   * *Mechanism*: Fashing proceeds while the operating system is actively writing metadata or files to an existing partition mount point.
   * *Consequence*: Sudden physical sector changes trigger system kernel panic on the host (e.g., macOS APFS Kernel Panic or Linux ext4 File System Abort).
   * *PR41B Interlock*: Strict Mounted Filesystem Rejection (no auto-override).

---

**Lead Safety Architect**: `Antigravity AI Agent`  
*Current Schema Version:* `1.0.0`
