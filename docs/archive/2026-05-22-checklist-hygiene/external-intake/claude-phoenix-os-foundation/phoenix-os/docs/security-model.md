# Phoenix OS — Security Model

## Philosophy

Phoenix OS is deployed in high-stakes environments: repair shops, client machines, post-incident recovery scenarios. The security model prioritizes **safety of client data** and **prevention of accidental destruction** above convenience. Every design decision that touches disk access, privilege escalation, or network exposure is evaluated against this priority.

---

## Live Session Security

### User Account

The live session runs as user `phoenix` (UID 1000). This account:

- Has **no password** (live environment convenience)
- Has `sudo` access via `/etc/sudoers.d/phoenix-live` (for tool execution)
- Does **not** have a root shell pre-opened
- Home directory is RAM-backed (`tmpfs`) and lost on reboot

### SSH Daemon

`openssh-server` is **not installed** in the live image. Remote access to a live session requires explicit installation via:

```bash
sudo apt install openssh-server
sudo systemctl start ssh
```

This is intentional. A repair technician's live session should never be accidentally SSH-accessible on a client network.

### Firewall

`ufw` is installed and enabled with the following default policy in the live session:

```
Default: deny (incoming), allow (outgoing), disabled (routed)
```

No ports are opened by default.

---

## Disk Access Safety Model

This is the most critical section of the security model. Phoenix OS is regularly used with machines that contain irreplaceable client data.

### Principle 1: No Automatic Disk Targeting

No Phoenix OS tool, script, or application will **automatically select** an internal disk as a target for any operation. This applies to:

- Formatting
- Partitioning
- Writing images
- Wiping (secure erase, zero-fill)
- Cloning operations

Every disk operation that modifies data requires a human to **explicitly identify** the target device by path (e.g., `/dev/sdb`) AND confirm that path in a second step.

### Principle 2: Confirmation Gates

All destructive operations in Phoenix tools display a confirmation dialog that includes:

1. The full device path (`/dev/sdX`)
2. The device model and serial number (from `udev`/`smartctl`)
3. The disk size
4. A description of what will happen (e.g., "This will erase ALL data on this device")
5. A text field where the user must **type the device path** to confirm

This design is modeled on the `rm -rf` confirmation pattern used by production deployment tools. Muscle memory can click through checkboxes; it cannot auto-type `/dev/sdb`.

### Principle 3: Internal Disk Mount Policy

The live session `udev` rules and `udisks2` policy are configured to:

- Mount removable devices (USB, SD card) automatically in read-write mode (standard behavior)
- Mount internal SATA/NVMe devices **without** the automount flag
- Require explicit user action (Dolphin click or CLI `mount`) to mount internal partitions

Internal partitions that are mounted by the user are mounted **read-only by default** unless the user explicitly overrides this.

The udev rule file: `/etc/udev/rules.d/90-phoenix-disk-policy.rules`

### Principle 4: Audit Logging

All disk operations performed through Phoenix tools are logged to:

```
/var/log/phoenix/disk-ops.log
```

Log format:
```
[ISO 8601 timestamp] [user] [tool] [operation] [device] [target-serial] [status]
```

Example:
```
2025-09-14T14:32:01Z phoenix gparted format /dev/sdb WD-WX21A2FA3K45 CONFIRMED
2025-09-14T14:32:15Z phoenix gparted format /dev/sdb WD-WX21A2FA3K45 COMPLETED
```

In the live session, this log is RAM-backed. Repair technicians should copy it to persistent storage if they need a record.

### Principle 5: Privileged Tool Wrappers

Tools that require root for disk access (GParted, TestDisk, dd, etc.) are invoked through polkit policies that:

- Require authentication (or sudo password) for the session
- Log the invocation to the disk-ops audit log
- Do not persist elevated privileges beyond the tool's lifetime

---

## Package Integrity

The live ISO uses standard Ubuntu APT signing. All packages installed during the build come from:

1. Ubuntu 24.04 LTS official mirrors (signed with Ubuntu archive key)
2. Locally-built Phoenix .deb packages (signed with Phoenix build key in CI)

The build script verifies APT key signatures during `lb build`. No unsigned packages are installed.

---

## Secure Boot

**Current status:** Secure Boot is not enforced in MVP builds. The ISO boots with UEFI Secure Boot **disabled**.

**Roadmap for Phase 2:**

- Use Ubuntu's `shim` + `grub-efi-amd64-signed` chain
- Phoenix OS kernel modules signed with a MOK (Machine Owner Key)
- ISO itself signed for UEFI verification
- Phoenix Key hardware ships with Phoenix MOK pre-enrolled

---

## Network Security in Repair Scenarios

When Phoenix OS is used on a client network (common in on-site repair):

- No listening services by default (SSH off, no VNC, no web UI)
- NetworkManager does not auto-connect to open Wi-Fi networks
- DNS resolution uses the client's network DHCP DNS (appropriate for on-site)
- Phoenix Key communication is USB HID-only (no network protocol)

---

## Data Handling Policy

Phoenix OS itself does not collect, transmit, or store user data. Specifically:

- No telemetry in the live session
- No crash reporting (opt-in telemetry planned for Phase 3 installed builds only)
- Phoenix Key session data stays on the key and local machine; no cloud sync
- Recovery operations produce output files only to user-specified destinations

---

## Reporting Security Issues

Security vulnerabilities in Phoenix OS should be reported to: `security@phoenix-os.io` (to be established before public release).

Do not file public GitHub issues for security vulnerabilities. Use responsible disclosure.
