# ARCWYRE Platform Architecture

## 1. Vision: The Unified Recovery Spine
ARCWYRE is designed as a modular, hardware-aware platform that provides a consistent recovery experience across different boot environments. It bridges the gap between existing Linux-based tools and a future sovereign OS.

## 2. Platform Tracks

### A. ARCWYRE OS Desktop (Linux-Based)
**Focus:** Immediate utility, hardware compatibility, and tool accessibility.
- **Base:** Debian/Live-Build foundation.
- **Desktop:** KDE Plasma (Sacred Minimal variant).
- **Core Engine:** Integrated `ARCWYRE Core` (Rust) for disk imaging and diagnostics.
- **Purpose:** Provide a production-ready environment for data recovery, machine repair, and system provisioning *today*.

### B. ARCWYRE Native (Sovereign OS)
**Focus:** Long-term independence, security, and "From-Scratch" performance.
- **Base:** Custom `ARCWYRE Kernel`.
- **Userland:** Custom shell and recovery environment.
- **Boot Path:** Pure UEFI/x86_64 target (initially).
- **Purpose:** Rebuild the operating system foundation without legacy monolith dependencies.

## 3. Shared Components (The "Core")
The `PhoenixCore-` repository (transitional name) houses the shared libraries and agents that power both tracks:

- **ARCWYRE Agent:** The execution daemon that talks to hardware.
- **ARCWYRE Control Center:** The unified dashboard (React/FastAPI).
- **BootForge Engine:** The logic for creating bootable media (ISOs/USBs).
- **ArcWatch:** The diagnostic and audit-trail subsystem.

## 4. Communication Layer
- **Local:** Transactional JSON-line streaming between the Agent (Rust) and the Control Center (Python/FastAPI).
- **Remote:** Secure, authenticated management via the ARCWYRE mobile client (Expo).

## 5. Security & Safety Model
- **"Truth-First" Audit:** Every destructive operation is logged and requires multi-step verification.
- **Polkit Gating:** System-level disk mutation is restricted to the ARCWYRE platform agents.
- **Read-Only Defaults:** Media is mounted read-only by default to prevent accidental data loss.
