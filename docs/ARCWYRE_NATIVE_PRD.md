# ARCWYRE Native PRD (Cross-Reference)

**Status:** Conceptual / Architecture Track
**Project:** ARCWYRE Native (The Sovereign Operating System)

## 1. Executive Summary

ARCWYRE Native is a from-scratch, independent operating system branch built without the dependencies of the Linux kernel or legacy userlands. It represents the long-term "Sovereign OS" goal of the ARCWYRE ecosystem.

## 2. Why ARCWYRE Native Exists
- **Total Independence**: Elimination of upstream dependency risks and legacy licensing conflicts.
- **Auditability**: A codebase small enough to be fully audited by a single architect.
- **Performance**: Zero-overhead execution for recovery and high-fidelity computing.
- **Hardened Security**: A "Truth-First" execution model where every syscall is strictly gated and verified.

## 3. What it IS
- A custom-built kernel (ARCWYRE Kernel) written in Rust/Assembly.
- A UEFI-first, x86_64 target execution environment.
- A QEMU-first development policy (validated in virtualization before physical deployment).
- A specialized system for recovery, machine management, and sovereign computing.

## 4. What it is NOT
- A general-purpose Linux replacement (initially).
- A "Daily Driver" for standard web browsing or gaming.
- A POSIX-compliant monolith (it follows a modern, capability-based design).

## 5. Development Strategy
- **Track 1**: Development of ARCWYRE Core (Rust) in the `PhoenixCore-` repo for use in ARCWYRE OS Desktop.
- **Track 2**: Extraction and porting of these "Core" crates to the ARCWYRE Native kernel environment.
- **Track 3**: Bootstrapping the Native userland using the ARCWYRE Control Center UI tokens and logic.

## 6. Kernel Roadmap Summary
- **Stage 1**: Bootloader (UEFI) + Basic Memory Management + Serial Debug.
- **Stage 2**: Capability-based Task Scheduling + Inter-Process Communication (IPC).
- **Stage 3**: Basic Disk I/O (NVMe/SATA) + FS (FAT32/ARC_FS).
- **Stage 4**: ARCWYRE Core Integration (Safety gates & Imaging primitives).
- **Stage 5**: Native UI (FrameBuffer) + ARCWYRE Forge implementation.

## 7. Relationship to ARCWYRE Core
The **ARCWYRE Core** (currently in the `PhoenixCore-` repo) is the shared intelligence of the platform. By writing the core in pure, zero-dependency Rust where possible, the same logic that powers the Desktop edition can be migrated directly into the Native kernel space.
