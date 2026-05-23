# Command Control Center - App Contract

This document defines the contract between Command (the public UI) and the PhoenixCore platform (internal engine), as well as integration with the Bobby's Worldwide OS launcher.

## Overview

**Public Name:** Command Control Center
**Internal Name:** PhoenixCore Control Center
**Package ID:** `com.bobbysworld.command`
**App Category:** System Utilities / Monitoring
**Platform:** Bobby's Worldwide OS (BWOS)

## Launcher Integration

### App Metadata Location

Command provides its metadata at:
- **Primary:** `/app.metadata.json` (repository root)
- **Alternative:** `apps/phoenix-control-center/app.metadata.json`

### Metadata Schema

```json
{
  "packageId": "com.bobbysworld.command",
  "name": "Command",
  "displayName": "Command Control Center",
  "internalName": "PhoenixCore Control Center",
  "version": "1.0.0",
  "category": "system-utilities",
  "description": "System monitoring and control center for Bobby's Worldwide OS",
  "icon": "assets/command-icon.svg",
  "entrypoints": {
    "gui": "python main.py --gui",
    "cli": "python main.py",
    "web": "pnpm run --filter phoenix-control-center dev"
  },
  "healthCheck": {
    "script": "./scripts/healthcheck.sh",
    "endpoint": "http://localhost:5000/health"
  },
  "dependencies": {
    "python": ">=3.10",
    "rust": ">=1.94",
    "node": ">=18"
  },
  "capabilities": [
    "system.monitor",
    "hardware.read",
    "edition.identity.read",
    "app.registry.read",
    "service.status.read"
  ],
  "editions": [
    "arcwyre",
    "thunder-god",
    "forge",
    "blue-phoenix"
  ]
}
```

### Launcher Discovery

The BWOS launcher discovers Command via:

1. **Manifest Scan**: Reads `app.metadata.json` files
2. **Package ID**: Uses `packageId` as unique identifier
3. **Category Filter**: Groups by `category` field
4. **Edition Support**: Checks `editions` array for compatibility

### Launch Protocol

```bash
# GUI Launch
bwos-launcher launch com.bobbysworld.command --mode gui

# CLI Launch
bwos-launcher launch com.bobbysworld.command --mode cli

# Web Launch
bwos-launcher launch com.bobbysworld.command --mode web --port 3000
```

## Core Integration

### PhoenixCore Library Interface

Command integrates with PhoenixCore via:

#### 1. Rust FFI (Foreign Function Interface)

**Library:** `phoenix-core` crate (Rust)
**Binding:** Python via `PyO3` or direct CLI invocation

```rust
// Rust Core API
pub fn get_system_info() -> Result<SystemInfo, String>
pub fn get_cpu_usage() -> Result<f32, String>
pub fn get_memory_usage() -> Result<f32, String>
pub fn get_disk_info() -> Result<Vec<DiskInfo>, String>
pub fn get_network_interfaces() -> Result<Vec<NetworkInterface>, String>
```

#### 2. FastAPI Backend

**Endpoint:** `http://localhost:5000/api/v1`
**Transport:** JSON over HTTP
**Authentication:** JWT (production) or API key (development)

```typescript
// API Contracts
GET  /api/v1/system/info        -> SystemInfo
GET  /api/v1/system/cpu         -> { usage: number }
GET  /api/v1/system/memory      -> { usage: number, total: number, used: number }
GET  /api/v1/system/disks       -> DiskInfo[]
GET  /api/v1/system/network     -> NetworkInterface[]
GET  /api/v1/health             -> { status: "healthy" | "degraded" | "unhealthy" }
```

### Edition Manifest Integration

Command reads edition configuration from:

**Location:** `editions/*/edition.yaml`
**Format:** YAML
**Schema:** See `docs/EDITION_MANIFEST_SPEC.md`

```yaml
# Example: editions/arcwyre/edition.yaml
id: arcwyre
display_name: "Bobby's Worldwide OS: ARCWYRE Edition"
theme:
  colors:
    primary: "#00E5FF"
    secondary: "#94A3B8"
features:
  - "cyber_security_audit"
  - "modern_dev_tools"
```

**Loading Process:**
1. Detect current edition via environment variable `BWOS_EDITION` or system file
2. Load YAML manifest from `editions/${EDITION_ID}/edition.yaml`
3. Apply theme colors to UI
4. Enable/disable features based on `features` array

### App Registry Integration

Command displays installed apps via:

**Registry Location:**
- **Linux:** `~/.config/bwos/apps.json`
- **macOS:** `~/Library/Application Support/BWOS/apps.json`
- **Windows:** `%APPDATA%\BWOS\apps.json`

**Schema:**
```json
{
  "apps": [
    {
      "packageId": "com.bobbysworld.app-name",
      "name": "App Name",
      "version": "1.0.0",
      "status": "healthy" | "degraded" | "unavailable",
      "lastCheck": "2026-05-23T15:52:47Z"
    }
  ]
}
```

### Service Health Protocol

Command monitors services via health check endpoints:

```typescript
// Service Health Response
interface ServiceHealth {
  name: string;
  status: "healthy" | "degraded" | "unhealthy";
  uptime?: number;
  version?: string;
  lastCheck: string;
  details?: {
    [key: string]: any;
  };
}
```

**Monitored Services:**
- **Backend API:** `http://localhost:5000/health`
- **Rust Core:** Via library status check
- **Safety Engine:** Via `phoenix-safety` crate
- **Workflow Engine:** Via `phoenix-workflow-engine` crate

## Data Contracts

### SystemInfo Schema

```typescript
interface SystemInfo {
  hostname: string;
  os_version: string;
  kernel: string;
  uptime: number;
  cpu_count: number;
  cpu_model: string;
  total_memory: number;
  architecture: string;
}
```

### DiskInfo Schema

```typescript
interface DiskInfo {
  device: string;
  mount_point: string;
  filesystem: string;
  total_size: number;
  used_size: number;
  available_size: number;
  usage_percent: number;
  is_read_only: boolean;
}
```

### NetworkInterface Schema

```typescript
interface NetworkInterface {
  name: string;
  ip_address: string;
  mac_address: string;
  status: string;
  bytes_received: number;
  bytes_sent: number;
}
```

### EditionInfo Schema

```typescript
interface EditionInfo {
  id: string;
  display_name: string;
  edition_type: "professional" | "premium" | "industrial" | "legacy";
  tagline: string;
  theme: {
    colors: {
      primary: string;
      secondary: string;
      accent: string;
      background: string;
      surface: string;
      text: string;
    };
  };
  features: string[];
  safety: {
    allow_destructive_disk_ops_by_default: boolean;
    require_dry_run_for_recovery_ops: boolean;
  };
}
```

## Safety Constraints

### Read-Only Operations

Command operates in read-only mode by default:
- ✅ Read system information
- ✅ Read disk usage
- ✅ Read network status
- ✅ Read app registry
- ✅ Read service health
- ❌ Modify disk partitions
- ❌ Delete files
- ❌ Restart services (without confirmation)

### Dry-Run Mode

For operations that modify state:
```typescript
// API Request
POST /api/v1/operations/disk-scan
{
  "device": "/dev/sda",
  "dryRun": true  // Preview operation without executing
}

// Response
{
  "operation": "disk-scan",
  "target": "/dev/sda",
  "dryRun": true,
  "estimatedChanges": [
    "Scan 1,234 files",
    "Detect 5 errors",
    "Recommend repair actions"
  ],
  "safetyGates": [
    "confirm_device_identity",
    "acknowledge_risks"
  ]
}
```

### Safety Gate Inheritance

Command inherits safety gates from edition manifests:
```yaml
# editions/arcwyre/edition.yaml
safety:
  allow_destructive_disk_ops_by_default: false
  require_dry_run_for_recovery_ops: true
  inherit_agent_permissions: true
  inherit_audit_rules: true
```

## Versioning & Compatibility

### Semantic Versioning

Command follows SemVer: `MAJOR.MINOR.PATCH`

- **MAJOR**: Breaking changes to launcher contract or core API
- **MINOR**: New features, backward compatible
- **PATCH**: Bug fixes, no API changes

### API Compatibility

```typescript
// Version negotiation
GET /api/v1/version
{
  "api_version": "1.0.0",
  "core_version": "1.0.0",
  "compatible_clients": ["^1.0.0"],
  "deprecated_endpoints": []
}
```

### Edition Compatibility

Command supports all BWOS editions:
- ARCWYRE Edition (professional)
- Thunder God Edition (premium)
- Forge Edition (industrial)
- Blue Phoenix Edition (legacy)

## Deployment Contracts

### Environment Variables

```bash
# Required
BWOS_EDITION=arcwyre              # Current edition ID
BWOS_DATA_DIR=/var/lib/bwos       # Data directory
BWOS_CONFIG_DIR=/etc/bwos         # Config directory

# Optional
BWOS_API_URL=http://localhost:5000  # Backend API URL
BWOS_LOG_LEVEL=info                 # Logging level
BWOS_THEME_OVERRIDE=/path/theme.css # Custom theme
```

### File System Layout

```
/
├── /opt/bwos/
│   ├── command/              # Command installation
│   │   ├── bin/             # Executables
│   │   ├── lib/             # Libraries
│   │   └── share/           # Static assets
│   └── editions/            # Edition manifests
├── /etc/bwos/
│   ├── config.yaml          # System config
│   └── apps.json            # App registry
├── /var/lib/bwos/
│   ├── data/                # Runtime data
│   └── logs/                # Application logs
└── /var/run/bwos/
    └── command.pid          # PID file
```

## Error Handling

### Error Response Format

```typescript
interface ErrorResponse {
  error: {
    code: string;
    message: string;
    details?: any;
    timestamp: string;
    requestId: string;
  };
}
```

### Error Codes

- `ERR_CORE_UNAVAILABLE`: PhoenixCore library not loaded
- `ERR_EDITION_NOT_FOUND`: Edition manifest not found
- `ERR_PERMISSION_DENIED`: Operation requires elevation
- `ERR_SAFETY_GATE_BLOCKED`: Safety gate prevents operation
- `ERR_SERVICE_UNHEALTHY`: Service health check failed

## References

- [PRD.md](PRD.md) - Product requirements
- [EDITION_MANIFEST_SPEC.md](EDITION_MANIFEST_SPEC.md) - Edition format
- [contracts/phoenix-agent-api.md](contracts/phoenix-agent-api.md) - API specification
- [contracts/operation-lifecycle.md](contracts/operation-lifecycle.md) - Operation states
- [contracts/safety-gates.md](contracts/safety-gates.md) - Safety policies
