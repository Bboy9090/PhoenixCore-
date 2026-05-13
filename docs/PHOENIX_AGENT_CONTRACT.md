# Phoenix Agent Contract Mapping

This document maps the current `phoenix-core-enterprise` tRPC routers and backend procedures to the canonical **Phoenix Agent** contract roles defined in the [Manifesto](file:///c:/Users/Bobby/Downloads/phoenix-core-enterprise/phoenix-core-repo/docs/vision/phoenix-os-manifesto.md).

## Agent Role Definition
The **Phoenix Agent** serves as the privileged backend bridge. It exposes safe system operations while enforcing Rust-based safety gates.

### 1. Hardware Service (`hardwareRouter`)
Exposes system identification and recipe generation capabilities.
- **Contract**: `hardware.detectConnected` -> Returns `DeviceGraph` compliant data.
- **Contract**: `hardware.generateRecipe` -> Maps hardware specs to `BootForge` recipes.

### 2. Fleet Service (`fleetRouter`)
Provides telemetry and state management for distributed hardware.
- **Contract**: `fleet.listDevices` -> Status and health tracking.
- **Contract**: `fleet.getDeviceDetails` -> Deep interrogation and deployment history.

### 3. BootForge Service (`recipeRouter`)
The composition layer for deployment media.
- **Contract**: `recipes.create` -> Defines a new `BootForge` payload.
- **Contract**: `recipes.estimateSize` -> Calculates storage requirements before write.

### 4. Deployment Service (`deploymentRouter`)
The execution and progress tracking layer.
- **Contract**: `deployments.create` -> Initiates a write/provisioning job.
- **Contract**: `deployments.getProgress` -> Real-time status retrieval.

### 5. Relay Service (`relayRouter`)
Manages the hybrid cloud-edge image cache.
- **Contract**: `relay.listNodes` -> Node health and sync status.
- **Contract**: `relay.syncImageCache` -> Triggers cloud-to-edge synchronization.

### 6. Boot Camp Service (`bootcampRouter`)
Specific contract for Mac-on-Windows driver management.
- **Contract**: `bootcamp.listDrivers` -> Compatibility lookup.
- **Contract**: `bootcamp.deployDriver` -> Managed driver injection.

### 7. Notification Service (`notificationRouter`)
System-wide alert and event delivery.
- **Contract**: `notifications.list` -> User and system alerts.
- **Contract**: `notifications.updatePreferences` -> Delivery policy management.

---

## Core Contract Namespaces (v1.1.0)

### 1. `operation` Lifecycle
All high-risk system changes must follow the three-stage lifecycle:
- `operation.preview(params)` -> Returns `ImpactReport` (Proposed changes, risks, safety requirements).
- `operation.execute(params, token)` -> Initiates the job. Returns `JobId`.
- `operation.status(jobId)` -> Returns `JobStatus` (Progress, logs, results).

### 2. `safety` Evaluation
- `safety.evaluate(action, params)` -> Pre-flight check against `DeploymentPolicy`.
- Returns `SafetyResult`: `{ allowed: boolean, requirements: ConfirmationLevel, reason?: string }`.

### 3. `device` Identity & Interrogation
- `device.identity(id)` -> Returns cryptographically verified hardware profile.
- `device.interrogate(id, module)` -> Deep probe of specific hardware components (Storage, EFI, Drivers).

### 4. `audit` Logging
- `audit.log(entry)` -> Immutable record of system-altering events.
- Fields: `timestamp`, `actorId`, `deviceId`, `action`, `outcome`, `evidenceHash`.

### 5. `report` Bundling
- `report.bundle(jobId)` -> Generates a signed `.zip` or `.json` report containing logs, hashes, and evidence.

---

## Safety Gating & Execution Doctrine

In accordance with the **Safety Doctrine**, all privileged operations MUST pass through the validation pipeline:

1. **Identity Gate**: Verify target `deviceId` matches active interrogation profile.
2. **Evaluation Gate**: Run `safety.evaluate`. Determine if `PHX-TOKEN` is required.
3. **Preview Gate**: Present `ImpactReport` to the user.
4. **Execution Gate**: Submit `confirmation_token` + `PHX-TOKEN` (if MFA required).
5. **Audit Gate**: Commit to `audit_logs` before return.

---
**Status**: 🔵 **Hardened Contract** (Namespace v1.1.0)
