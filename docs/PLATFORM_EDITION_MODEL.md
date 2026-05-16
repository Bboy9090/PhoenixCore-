# PLATFORM EDITION MODEL: Bobby’s Worldwide OS

This document outlines the architectural relationship between the Bobby’s Worldwide OS (BWOS) parent platform and its various editions.

## 1. Parent Platform vs. Editions

**Bobby’s Worldwide OS (BWOS)** is the singular, authoritative operating system platform. It contains all core safety rules, recovery agents, disk management logic, and forensic audit pipelines.

**Editions** are not separate OS forks. They are **metadata-driven profiles** that customize the presentation, package selection, and default configuration of the BWOS platform.

### Key Principles
- **One Core, Many Skins**: All editions run the exact same `bwos-core` Rust binaries.
- **Safety Inheritance**: Safety rules are defined at the platform level. Editions *inherit* these rules and cannot weaken them.
- **Visual Identity**: Editions provide unique CSS, branding, and wallpapers to tailor the experience to specific use cases (e.g., Industrial vs. Cyber-security).

## 2. The Role of Phoenix and ARCWYRE

The names **Phoenix OS** and **ARCWYRE** are now treated as visual editions and brand identities under the BWOS umbrella:
- **Blue Phoenix**: A legacy/heritage edition preserving the original visual style.
- **ARCWYRE**: A professional edition focused on modern cyber-security and data recovery.

## 3. Edition Lifecycle
1. **Definition**: Edition manifests (`edition.yaml`) are created in the `editions/` directory.
2. **Validation**: Scripts verify that the edition complies with platform safety requirements.
3. **Synthesis**: The build system applies the edition metadata to the core BWOS image to produce a final ISO.
