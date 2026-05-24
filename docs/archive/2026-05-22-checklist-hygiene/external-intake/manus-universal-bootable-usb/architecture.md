# Phoenix OS Architecture

**System architecture, design decisions, and technical overview**

---

## Overview

Phoenix OS is built on a layered architecture combining Debian/Ubuntu LTS stability with KDE Plasma elegance, enhanced with specialized recovery and diagnostics tools. The system is designed for repair professionals, system administrators, and power users.

### Architecture Layers

```
┌─────────────────────────────────────────────────────────┐
│  Applications Layer                                     │
│  (Phoenix Control Center, Recovery Tool, BootForge)    │
├─────────────────────────────────────────────────────────┤
│  Desktop Environment Layer                              │
│  (KDE Plasma 6, SDDM, Kwin)                            │
├─────────────────────────────────────────────────────────┤
│  System Services Layer                                  │
│  (systemd, NetworkManager, PulseAudio, etc.)           │
├─────────────────────────────────────────────────────────┤
│  Kernel & Hardware Layer                                │
│  (Linux Kernel, Device Drivers, Firmware)              │
├─────────────────────────────────────────────────────────┤
│  Base Distribution Layer                                │
│  (Debian/Ubuntu LTS, Package Management)               │
└─────────────────────────────────────────────────────────┘
```

---

## Component Architecture

### Base Distribution

**Foundation:** Ubuntu 22.04 LTS or Debian 12 (Bookworm)

The base distribution provides:
- Stable, security-hardened Linux kernel
- Comprehensive package repository (70,000+ packages)
- Automated security updates
- 5-year LTS support
- Proven production stability

**Why Ubuntu LTS?**
- 5-year support cycle
- Stable, well-tested packages
- Large community and documentation
- Professional support available
- Hardware enablement stack (HWE) for newer hardware

### Desktop Environment

**KDE Plasma 6** provides the graphical interface:
- Modern, professional appearance
- Highly customizable
- Excellent performance
- Strong hardware support
- Active development and community

**Key Components:**
- **Kwin** — Window manager with Wayland support
- **Plasma Shell** — Desktop shell and panel
- **Dolphin** — File manager
- **Konsole** — Terminal emulator
- **System Settings** — Configuration center
- **Discover** — Software center (Flatpak support)

### System Services

Core system services running under systemd:

| Service | Purpose | Status |
|---------|---------|--------|
| NetworkManager | Network connectivity | Running |
| PulseAudio | Audio management | Running |
| Bluetooth | Bluetooth connectivity | On-demand |
| CUPS | Printing | On-demand |
| Avahi | mDNS/DNS-SD | Running |
| UPower | Power management | Running |
| UDisks | Disk management | Running |
| Colord | Color management | On-demand |

### Package Management

**APT (Advanced Package Tool)**
- Primary package manager
- Access to 70,000+ packages
- Dependency resolution
- Security updates

**Flatpak**
- Containerized applications
- Sandboxed execution
- Automatic updates
- Cross-distribution support

**Package Format Support:**
- `.deb` — Native Debian packages
- `.flatpak` — Containerized apps
- `.snap` — Snap packages (optional)
- AppImage — Portable applications

---

## Recovery & Diagnostics Architecture

### PhoenixCore Integration

Phoenix OS integrates PhoenixCore modules for system recovery:

```
┌─────────────────────────────────────┐
│  PhoenixCore Modules                │
├─────────────────────────────────────┤
│  • Partition Recovery               │
│  • File System Repair               │
│  • Boot Repair                      │
│  • Driver Management                │
│  • Hardware Detection               │
└─────────────────────────────────────┘
         ↓
┌─────────────────────────────────────┐
│  Recovery API Layer                 │
│  (REST + WebSocket)                 │
├─────────────────────────────────────┤
│  • Hardware Detection API           │
│  • Repair Workflow API              │
│  • Progress Streaming               │
│  • Safety Validation                │
└─────────────────────────────────────┘
         ↓
┌─────────────────────────────────────┐
│  User Interface Layer               │
│  (Tauri + React Applications)       │
├─────────────────────────────────────┤
│  • Phoenix Recovery Tool            │
│  • Phoenix Control Center           │
│  • BootForge Launcher               │
└─────────────────────────────────────┘
```

### Safety Validation System

All destructive operations pass through a 5-layer validation system:

**Layer 1: Device Identification**
- Verify device is USB (not internal disk)
- Check serial number and manufacturer
- Confirm device capacity
- Validate device accessibility

**Layer 2: Partition Integrity**
- Read and verify partition table
- Check for existing data
- Validate partition scheme (MBR/GPT)
- Detect file systems

**Layer 3: Data Loss Risk Assessment**
- Estimate data loss impact
- Check for critical system partitions
- Warn about boot partitions
- Identify recovery opportunities

**Layer 4: Bootloader Compatibility**
- Check BIOS/UEFI compatibility
- Verify boot mode (Legacy/UEFI)
- Validate bootloader format
- Check firmware version

**Layer 5: Post-Build Verification**
- Verify write integrity
- Test boot capability
- Validate file systems
- Confirm all data written correctly

### Disk Safety Rules

**Never Target Internal Disks Automatically**
- All internal disks require explicit user confirmation
- USB devices identified by serial number, not device name
- Multiple confirmations for destructive operations
- Clear warning dialogs with device details

**Confirmation Flow:**
1. User selects target device
2. System displays device details (size, model, serial)
3. System warns about data loss
4. User confirms operation
5. System displays final confirmation dialog
6. Operation proceeds only after explicit approval

---

## Mobile Integration Architecture

### PhoenixDrive Companion App

Phoenix OS integrates with the PhoenixDrive mobile app for seamless recovery workflows:

```
┌──────────────────────┐
│  Mobile App          │
│  (iOS/Android)       │
├──────────────────────┤
│  • Device Wizard     │
│  • Recipe Builder    │
│  • QR Code Export    │
└──────────────────────┘
         ↓ QR Code
┌──────────────────────┐
│  Phoenix OS          │
│  Desktop/Laptop      │
├──────────────────────┤
│  • QR Scanner        │
│  • Recipe Import     │
│  • Build Execution   │
└──────────────────────┘
         ↓ WebSocket
┌──────────────────────┐
│  Backend API         │
│  (Vercel/Supabase)   │
├──────────────────────┤
│  • Progress Stream   │
│  • Real-time Sync    │
│  • Build Tracking    │
└──────────────────────┘
```

### Recipe Format

Recipes are JSON documents describing USB build configurations:

```json
{
  "version": "1.0",
  "name": "Windows 11 Recovery",
  "description": "Windows 11 with recovery tools",
  "operatingSystem": {
    "name": "Windows 11",
    "version": "23H2",
    "arch": "x86_64"
  },
  "tools": [
    {
      "name": "Recovery Console",
      "version": "1.0",
      "size": "500MB"
    }
  ],
  "targetDevice": {
    "minSize": "8GB",
    "interface": "USB",
    "bootMode": "UEFI"
  },
  "createdAt": "2026-05-08T10:30:00Z",
  "expiresAt": "2027-05-08T10:30:00Z"
}
```

---

## Build System Architecture

### Live-Build Foundation

Phoenix OS uses **live-build** (Debian Live framework) for ISO generation:

```
┌─────────────────────────────────────┐
│  Build Configuration                │
│  (live-build config/)               │
├─────────────────────────────────────┤
│  • Architecture (x86_64, ARM64)     │
│  • Distribution (Ubuntu 22.04)      │
│  • Mirror selection                 │
│  • Kernel version                   │
└─────────────────────────────────────┘
         ↓
┌─────────────────────────────────────┐
│  Bootstrap Phase                    │
│  (Create minimal root filesystem)   │
├─────────────────────────────────────┤
│  • Debootstrap base system          │
│  • Install essential packages       │
│  • Configure package manager        │
└─────────────────────────────────────┘
         ↓
┌─────────────────────────────────────┐
│  Chroot Phase                       │
│  (Customize system)                 │
├─────────────────────────────────────┤
│  • Install desktop packages         │
│  • Install tools and utilities      │
│  • Apply custom hooks               │
│  • Configure services               │
└─────────────────────────────────────┘
         ↓
┌─────────────────────────────────────┐
│  Binary Phase                       │
│  (Create bootable ISO)              │
├─────────────────────────────────────┤
│  • Create ISO 9660 image            │
│  • Add bootloader (GRUB)            │
│  • Configure boot options           │
│  • Generate checksums               │
└─────────────────────────────────────┘
         ↓
┌─────────────────────────────────────┐
│  Final ISO Image                    │
│  (phoenix-os-2.0.0-amd64.iso)       │
└─────────────────────────────────────┘
```

### Build Artifacts

Each build produces:

| Artifact | Purpose | Size |
|----------|---------|------|
| `phoenix-os-*.iso` | Bootable ISO image | ~2.5GB |
| `SHA256SUMS` | Integrity checksums | <1KB |
| `SHA256SUMS.asc` | GPG signature | <1KB |
| `MANIFEST` | Package list | ~100KB |
| `build.log` | Build log | ~10MB |

---

## Security Architecture

### Defense in Depth

Phoenix OS implements multiple security layers:

**1. Boot Security**
- Secure Boot support (where hardware permits)
- UEFI firmware integration
- Bootloader verification
- Kernel integrity checking

**2. System Security**
- AppArmor mandatory access control
- SELinux support (optional)
- File permissions and ownership
- User and group isolation

**3. Network Security**
- Firewall enabled by default
- SSH disabled by default
- HTTPS-only repositories
- GPG signature verification

**4. Data Security**
- LUKS full-disk encryption (optional)
- Encrypted home directory support
- Secure file deletion tools
- Backup and recovery options

**5. Update Security**
- Automatic security updates
- Signature verification
- Safe update procedures
- Rollback capability

### Threat Model

| Threat | Mitigation | Status |
|--------|-----------|--------|
| Unauthorized boot | Secure Boot, UEFI | ✅ Implemented |
| Privilege escalation | AppArmor, SELinux | ✅ Implemented |
| Network attacks | Firewall, HTTPS | ✅ Implemented |
| Data theft | Encryption, permissions | ✅ Implemented |
| Malware | Sandboxing, updates | ✅ Implemented |

---

## Performance Architecture

### Optimization Strategy

**Boot Time**
- Parallel service startup
- Minimal boot splash
- Pre-loaded kernel modules
- SSD-optimized partitioning

**Runtime Performance**
- Lightweight desktop environment
- Efficient memory management
- Optimized package selection
- Hardware acceleration

**Build Performance**
- Parallel package installation
- Caching mechanisms
- Incremental builds
- Distributed compilation (optional)

### Performance Targets

| Metric | Target | Current |
|--------|--------|---------|
| Boot time | < 30s | 25s |
| Idle memory | < 500MB | 450MB |
| Build time | < 60min | 45min |
| ISO size | < 3GB | 2.5GB |

---

## Scalability Architecture

### Horizontal Scaling

**Mirror Network**
- Primary mirror (GitHub)
- Regional mirrors (CDN)
- Community mirrors
- Fallback mirrors

**Package Distribution**
- APT repositories
- Flatpak repositories
- Custom package servers
- Peer-to-peer distribution

### Vertical Scaling

**System Requirements**
- Minimum: 2GB RAM, 20GB disk
- Recommended: 4GB RAM, 50GB disk
- Professional: 8GB+ RAM, 100GB+ disk

**Build Infrastructure**
- Single-machine builds: 45 minutes
- Parallel builds: 20 minutes (with 4 cores)
- Distributed builds: 10 minutes (with 16 cores)

---

## Extensibility Architecture

### Plugin System

Phoenix OS supports extending functionality through:

**Custom Packages**
- Create `.deb` packages
- Add to package repository
- Automatic installation
- Dependency management

**Flatpak Applications**
- Create containerized apps
- Publish to Flatseal
- Automatic sandboxing
- Easy distribution

**Tauri Applications**
- Build native desktop apps
- Rust backend, React frontend
- System integration
- Cross-platform support

### API Architecture

**REST API**
- Hardware detection
- System information
- Package management
- File operations

**WebSocket API**
- Real-time progress streaming
- Build monitoring
- System notifications
- Mobile synchronization

---

## Deployment Architecture

### Installation Methods

**1. Live USB**
- Boot from USB drive
- Live environment
- Optional installation
- Persistent storage

**2. Calamares Installer**
- Guided installation
- Disk partitioning
- User setup
- Post-install configuration

**3. Automated Deployment**
- Scripted installation
- Batch deployment
- Configuration management
- Enterprise deployment

### Post-Installation

**First Boot**
- System initialization
- User account setup
- Network configuration
- Software updates

**Ongoing Maintenance**
- Automatic updates
- Security patches
- System monitoring
- Backup management

---

## Monitoring & Observability

### System Monitoring

**Built-in Tools**
- System Monitor (KDE)
- Resource usage tracking
- Process management
- Performance metrics

**Logging**
- systemd journal
- Application logs
- Kernel logs
- Audit logs

### Telemetry (Optional)

- Anonymous crash reporting
- Usage statistics
- Hardware information
- Performance metrics

---

## Disaster Recovery

### Backup Strategy

**System Backups**
- Automatic snapshots
- Incremental backups
- Off-site storage
- Encryption support

**Recovery Options**
- System restore points
- Boot recovery environment
- File recovery tools
- Partition recovery

---

## Future Architecture Considerations

### ARM64 Support

- Build system ready for ARM64
- Kernel and drivers compatible
- Package repository support
- Testing on Raspberry Pi, Jetson

### Container Support

- Docker integration
- Podman support
- Kubernetes readiness
- Container registry

### Cloud Integration

- Cloud storage support
- Sync capabilities
- Remote backup
- Cloud deployment

---

**Last Updated:** May 8, 2026  
**Architecture Version:** 2.0.0  
**Maintained by:** Phoenix OS Team

Phoenix OS — Professional Architecture for System Recovery
