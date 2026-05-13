# Phoenix Ecosystem - Unified Repository Integration Plan

**Date:** May 11, 2026  
**Target Repository:** github.com/Bboy9090/phoenixcore  
**Status:** Integration Planning  
**Goal:** Create unified monorepo consolidating all Phoenix projects

---

## Current Project Assessment

### Project 1: PhoenixDrive Mobile (Expo/React Native)

**Location:** `/home/ubuntu/phoenix-core-mobile`  
**Status:** Production-ready  
**Components:**
- Mobile app (iOS/Android via Expo)
- Backend API (FastAPI/Flask)
- Database (Supabase PostgreSQL)
- Desktop app (Tauri + React)

**Key Files:**
- `app/` — React Native mobile app
- `server/` — FastAPI backend
- `scripts/` — Build and deployment scripts
- `docs/` — Comprehensive documentation

**Integration Points:**
- Mobile app for recipe creation and scanning
- Backend API for data synchronization
- WebSocket for real-time progress
- QR code recipe distribution

### Project 2: Phoenix Control Center (Tauri + React)

**Location:** `/home/ubuntu/phoenix-control-center`  
**Status:** Production-ready  
**Components:**
- Desktop application (Tauri + React)
- Rust backend (system monitoring)
- Advanced disk management
- Recovery point management

**Key Files:**
- `src/` — React TypeScript frontend
- `src-tauri/src/` — Rust backend modules
- `src/__tests__/` — Unit and integration tests
- `build-all-platforms.sh` — Multi-platform build script

**Integration Points:**
- System monitoring capabilities
- Disk management tools
- Recovery and backup features
- Hardware detection

### Project 3: Phoenix OS (Live-Build)

**Location:** `/home/ubuntu/phoenix-os`  
**Status:** Build foundation ready  
**Components:**
- Live-build configuration
- Package lists (KDE Plasma, tools)
- Calamares installer
- Branding and themes

**Key Files:**
- `live-build/config/` — ISO build configuration
- `live-build/package-lists/` — Package specifications
- `installer/calamares-config/` — Installer configuration
- `scripts/build-iso.sh` — Build automation

**Integration Points:**
- Pre-installed Phoenix Control Center
- Pre-installed recovery tools
- Mobile app companion integration
- System-level recovery capabilities

---

## Unified Monorepo Structure

```
phoenixcore/
├── README.md                          # Main project overview
├── ARCHITECTURE.md                    # System architecture
├── CONTRIBUTING.md                    # Contribution guidelines
├── LICENSE                            # Project license
├── package.json                       # Root workspace config
├── pnpm-workspace.yaml               # Monorepo workspace
│
├── apps/
│   ├── mobile/                        # PhoenixDrive Mobile (Expo)
│   │   ├── app/
│   │   ├── server/
│   │   ├── package.json
│   │   └── README.md
│   │
│   ├── desktop/                       # Phoenix Control Center (Tauri)
│   │   ├── src/
│   │   ├── src-tauri/
│   │   ├── package.json
│   │   └── README.md
│   │
│   └── os/                            # Phoenix OS (Live-Build)
│       ├── live-build/
│       ├── installer/
│       ├── scripts/
│       └── README.md
│
├── packages/
│   ├── shared-types/                  # Shared TypeScript types
│   │   ├── src/
│   │   └── package.json
│   │
│   ├── shared-utils/                  # Shared utilities
│   │   ├── src/
│   │   └── package.json
│   │
│   ├── api-client/                    # Unified API client
│   │   ├── src/
│   │   └── package.json
│   │
│   └── rust-core/                     # Shared Rust utilities
│       ├── src/
│       └── Cargo.toml
│
├── docs/
│   ├── architecture/
│   ├── deployment/
│   ├── development/
│   └── user-guide/
│
├── scripts/
│   ├── build-all.sh                   # Build all projects
│   ├── test-all.sh                    # Test all projects
│   ├── deploy-all.sh                  # Deploy all projects
│   └── sync-github.sh                 # GitHub synchronization
│
└── .github/
    ├── workflows/
    │   ├── ci.yml                     # CI/CD pipeline
    │   ├── build.yml                  # Build workflow
    │   └── deploy.yml                 # Deployment workflow
    └── ISSUE_TEMPLATE/
```

---

## Integration Strategy

### Phase 1: Assessment & Planning

**Completed:**
- Inventory all projects and components
- Identify integration points
- Map dependencies
- Plan monorepo structure

### Phase 2: Monorepo Setup

**Actions:**
- Create root `package.json` with workspace configuration
- Set up `pnpm-workspace.yaml` for dependency management
- Create shared packages directory
- Establish build and test scripts

**Benefits:**
- Single source of truth
- Shared dependencies
- Coordinated versioning
- Unified CI/CD

### Phase 3: Mobile App Integration

**Actions:**
- Move PhoenixDrive to `apps/mobile/`
- Update import paths
- Link to shared packages
- Maintain existing functionality

**Preserves:**
- All mobile app features
- Backend API
- Database configuration
- Deployment scripts

### Phase 4: Desktop App Integration

**Actions:**
- Move Phoenix Control Center to `apps/desktop/`
- Update import paths
- Link to shared packages
- Maintain Tauri configuration

**Preserves:**
- All desktop app features
- Rust backend modules
- Test suites
- Build scripts

### Phase 5: OS Distribution Integration

**Actions:**
- Move Phoenix OS to `apps/os/`
- Update build paths
- Link to shared packages
- Pre-configure integration

**Preserves:**
- Live-build configuration
- Calamares installer
- Package lists
- Build automation

### Phase 6: Shared Libraries

**Create:**
- `packages/shared-types/` — TypeScript interfaces
- `packages/shared-utils/` — Utility functions
- `packages/api-client/` — Unified API client
- `packages/rust-core/` — Shared Rust code

**Benefits:**
- Reduce code duplication
- Ensure consistency
- Simplify maintenance
- Enable code sharing

### Phase 7: GitHub Synchronization

**Actions:**
- Initialize Git repository
- Commit all projects
- Create GitHub repository
- Push to github.com/Bboy9090/phoenixcore
- Configure CI/CD workflows

---

## Shared Components

### TypeScript Types (`packages/shared-types/`)

```typescript
// System types used across all apps
export interface SystemInfo { ... }
export interface DiskInfo { ... }
export interface RecipeInfo { ... }
export interface HardwareProfile { ... }
```

### Utilities (`packages/shared-utils/`)

```typescript
// Shared utility functions
export function formatBytes(bytes: number): string { ... }
export function calculateUsagePercent(used: number, total: number): number { ... }
export function validateRecipe(recipe: RecipeInfo): boolean { ... }
```

### API Client (`packages/api-client/`)

```typescript
// Unified API client for all apps
export class PhoenixAPIClient {
  async getSystemInfo(): Promise<SystemInfo> { ... }
  async createRecipe(recipe: RecipeInfo): Promise<string> { ... }
  async scanDisk(device: string): Promise<ScanResult> { ... }
}
```

### Rust Core (`packages/rust-core/`)

```rust
// Shared Rust utilities
pub mod system;
pub mod disk;
pub mod hardware;
pub mod recovery;
```

---

## Build & Deployment

### Unified Build Script

```bash
#!/bin/bash
# Build all Phoenix projects

# Build shared packages
pnpm -r --filter="./packages/*" build

# Build mobile app
pnpm -r --filter="./apps/mobile" build

# Build desktop app
pnpm -r --filter="./apps/desktop" tauri:build

# Build OS ISO
pnpm -r --filter="./apps/os" build-iso
```

### CI/CD Pipeline

**GitHub Actions Workflows:**
- `ci.yml` — Run tests on every push
- `build.yml` — Build all projects
- `deploy.yml` — Deploy to production

**Triggers:**
- Pull requests → Run tests
- Merge to main → Build and deploy
- Tag release → Create GitHub release

---

## Dependency Management

### Root `package.json`

```json
{
  "name": "phoenixcore",
  "version": "2.0.0",
  "workspaces": [
    "apps/*",
    "packages/*"
  ],
  "scripts": {
    "build": "pnpm -r build",
    "test": "pnpm -r test",
    "deploy": "pnpm -r deploy"
  }
}
```

### Workspace Benefits

- Single `node_modules` installation
- Shared dependencies
- Coordinated versioning
- Efficient CI/CD

---

## Migration Checklist

### Pre-Migration

- [ ] Backup all projects
- [ ] Verify all tests passing
- [ ] Document current state
- [ ] Create migration branch

### Migration

- [ ] Create monorepo structure
- [ ] Move mobile app to `apps/mobile/`
- [ ] Move desktop app to `apps/desktop/`
- [ ] Move OS to `apps/os/`
- [ ] Create shared packages
- [ ] Update import paths
- [ ] Update build scripts
- [ ] Update CI/CD configuration

### Post-Migration

- [ ] Verify all builds successful
- [ ] Run full test suite
- [ ] Test on all platforms
- [ ] Update documentation
- [ ] Create GitHub repository
- [ ] Push to GitHub
- [ ] Announce to community

---

## GitHub Repository Setup

### Repository Configuration

```
Repository: github.com/Bboy9090/phoenixcore
Visibility: Public
License: GPL-3.0
Topics: linux, system-tools, recovery, mobile-app, desktop-app
```

### Branch Strategy

- `main` — Production-ready code
- `develop` — Development branch
- `feature/*` — Feature branches
- `release/*` — Release branches

### Protection Rules

- Require pull request reviews
- Require status checks to pass
- Require branches to be up to date
- Dismiss stale pull request approvals

---

## Timeline

| Phase | Duration | Status |
|-------|----------|--------|
| Assessment & Planning | 1 hour | ✅ Complete |
| Monorepo Setup | 1 hour | ⏳ Next |
| Mobile Integration | 1 hour | ⏳ Pending |
| Desktop Integration | 1 hour | ⏳ Pending |
| OS Integration | 1 hour | ⏳ Pending |
| Shared Libraries | 1 hour | ⏳ Pending |
| GitHub Sync | 1 hour | ⏳ Pending |
| **Total** | **7 hours** | **⏳ In Progress** |

---

## Success Criteria

- All projects building successfully
- All tests passing
- Shared code reducing duplication by 30%+
- Single GitHub repository with all projects
- CI/CD pipeline working
- Documentation complete
- Community ready to contribute

---

## Next Steps

1. Create monorepo structure
2. Move projects to `apps/` directory
3. Create shared packages
4. Update all import paths
5. Test all builds
6. Create GitHub repository
7. Push and verify

**Status:** Ready to proceed with Phase 2

Phoenix Ecosystem — Unified, Integrated, Production-Ready 🔥
