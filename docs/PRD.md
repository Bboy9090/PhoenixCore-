# Command Control Center - Product Requirements Document

## Product Overview

**Product Name:** Command Control Center (Public UI)
**Internal Name:** PhoenixCore
**Parent Platform:** Bobby's Worldwide OS (BWOS)
**Package ID:** com.bobbysworld.command
**Edition Model:** Multi-edition platform (ARCWYRE, Thunder God, Forge, Blue Phoenix)

Command is the public-facing control center for Bobby's Worldwide OS, providing system monitoring, app readiness status, service health, and edition identity management. It serves as the primary dashboard for all BWOS editions.

## Target Users

- **System Administrators**: Monitor system health and manage recovery operations
- **IT Professionals**: Troubleshoot hardware and software issues
- **Power Users**: Access advanced system diagnostics and controls
- **Edition Users**: Experience edition-specific branding and features (ARCWYRE, Thunder God, Forge, Blue Phoenix)

## Core Features

### 1. System Overview Panel

**Purpose:** Real-time system monitoring and diagnostics

**Features:**
- CPU usage and model information
- Memory usage (total, used, available)
- Disk usage for all mounted volumes
- Network interface status and bandwidth
- OS version and kernel information
- System uptime and architecture

**Data Source:** `phoenix-core` Rust library (`dashboard::system` module)

### 2. App Readiness Panel

**Purpose:** Display status of installed applications and their readiness

**Features:**
- Read app registry or metadata files
- Show installed applications with versions
- Display app health status (healthy, degraded, unavailable)
- Indicate launcher compatibility
- Quick access to app launch

**Data Source:** `app.metadata.json` and edition package manifests

### 3. Service Status Panel

**Purpose:** Monitor core PhoenixCore services

**Features:**
- Backend service health (FastAPI server)
- Core library status (Rust engine)
- Safety gate status (enabled/disabled policies)
- Workflow engine status
- Build monitor status
- Log export service

**Data Source:** Health endpoints from backend services and Rust core

### 4. Edition Identity Panel

**Purpose:** Display current edition branding and configuration

**Features:**
- Edition name and type (ARCWYRE, Thunder God, Forge, Blue Phoenix)
- Edition tagline and description
- Theme colors and branding
- Enabled features list
- Safety policy summary
- Edition-specific package list

**Data Source:** Edition YAML manifests (`editions/*/edition.yaml`)

## Technical Architecture

### Frontend Stack
- **Framework:** React 18 with TypeScript
- **Build Tool:** Vite
- **Styling:** Tailwind CSS
- **Desktop Shell:** Tauri (optional)

### Backend Stack
- **Core Library:** Rust (phoenix-core crate)
- **API Server:** FastAPI (Python)
- **Data Format:** JSON for APIs, YAML for configuration

### Data Flow
1. Frontend requests system info via API
2. API calls Rust core library (`phoenix-core`)
3. Core library uses `sysinfo` crate for system metrics
4. Edition data loaded from YAML manifests
5. Response formatted as JSON and returned to frontend

## MVP Scope

### In Scope
- System overview with real-time metrics
- App readiness panel with static metadata
- Service status with basic health checks
- Edition identity with YAML-based configuration
- Responsive UI with edition-specific theming

### Out of Scope (V2+)
- Advanced analytics and historical metrics
- Remote monitoring and fleet management
- Custom dashboard widget creation
- Deep hardware diagnostics beyond recovery needs
- Settings synchronization across devices
- Localization and internationalization

## Safety & Security

### Safety Gates
- Read-only operations for system monitoring
- No destructive disk operations in MVP
- Dry-run mode required for recovery operations
- Inherit edition safety policies from manifests

### Security Considerations
- API authentication for production deployments
- Input validation for all user inputs
- Secure storage of sensitive configuration
- Audit logging for all system operations

## Success Metrics

### Phase 1 (MVP)
- Build completes successfully on all platforms
- All tests pass (Python + Rust)
- System info displays accurately
- Edition branding loads correctly
- Performance: Dashboard loads in < 2 seconds

### Phase 2 (Future)
- User engagement metrics
- Error rate < 1%
- System resource usage < 100MB RAM
- API response time < 500ms

## Dependencies

### Required
- Python 3.10+
- Rust 1.94+
- Node.js 18+ with pnpm
- sysinfo 0.29 (Rust crate)
- FastAPI (Python backend)

### Optional
- PyQt6 (for legacy Python GUI)
- Tauri (for desktop shell)

## Release Criteria

See [RELEASE_CHECKLIST.md](RELEASE_CHECKLIST.md) for full production release requirements.

### Minimum Viable Release
- ✅ All build commands complete without errors
- ✅ All tests pass (Python + Rust)
- ✅ Documentation is complete and accurate
- ✅ System info panel displays real data
- ✅ Edition identity loads from YAML
- ✅ Health check script validates system state
- ✅ Smoke tests verify all entry points

## Future Roadmap

### V1.1 - Enhanced Monitoring
- Historical metrics and trending
- Customizable dashboard widgets
- Export metrics to CSV/JSON

### V1.2 - Advanced Features
- Remote monitoring capabilities
- Service restart/management
- Log aggregation and search

### V2.0 - Platform Integration
- Settings sync across devices
- Localization support
- Plugin system for extensions
- Cloud backup integration

## References

- [ARCHITECTURE.md](ARCHITECTURE.md) - System architecture
- [ROADMAP.md](ROADMAP.md) - Development roadmap
- [APP_CONTRACT.md](APP_CONTRACT.md) - Launcher contract
- [EDITION_MANIFEST_SPEC.md](EDITION_MANIFEST_SPEC.md) - Edition format
- [contracts/](contracts/) - API contracts and boundaries
