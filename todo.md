# Phoenix Core Enterprise - Feature Roadmap

## Core Infrastructure
- [x] Database schema design (devices, deployments, fleet telemetry, audit logs, users, roles)
- [ ] WebSocket integration for real-time updates
- [x] tRPC router architecture (hardware, deployments, fleet, admin, notifications)
- [x] Role-based access control (owner/admin/user procedures)
- [x] Authentication and session management

## Feature 1: AI-Driven Hardware Intelligence Engine
- [ ] Hardware detection service (USB devices, system specs, chipsets)
- [ ] Driver/firmware mapping database
- [ ] Zero-knowledge recipe generation algorithm
- [ ] Automatic compatibility validation
- [ ] Backend procedure: `hardware.detectConnected()`
- [ ] Backend procedure: `hardware.generateRecipe(deviceId)`
- [ ] Frontend: Hardware detection modal/card

## Feature 2: Unified Fleet Management "God View" Dashboard
- [x] Fleet telemetry schema (device status, last heartbeat, health metrics)
- [ ] Real-time map visualization component
- [x] Device list view with live status indicators
- [ ] Device drill-down detail panel (specs, deployment history, logs)
- [x] Backend procedure: `fleet.listDevices(filters)`
- [ ] Backend procedure: `fleet.getDeviceDetails(deviceId)`
- [ ] Backend procedure: `fleet.getDeploymentHistory(deviceId)`
- [ ] WebSocket events: device status updates, health changes
- [x] Frontend: God View dashboard page
- [ ] Frontend: Device detail modal with history timeline

## Feature 3: USB Recipe Builder
- [x] Recipe schema (OS image, drivers, tools, size estimation)
- [ ] Drag-and-drop component library
- [ ] Size calculator for USB configurations
- [ ] Recipe preview and validation
- [x] Backend procedure: `recipes.create(config)`
- [x] Backend procedure: `recipes.list(userId)`
- [x] Backend procedure: `recipes.delete(recipeId)`
- [x] Backend procedure: `recipes.estimateSize(config)`
- [x] Frontend: USB Recipe Builder page
- [ ] Frontend: Drag-and-drop interface with live size updates

## Feature 4: Hybrid Cloud-Edge "Phoenix Relay" Controls
- [x] Relay node schema (node_id, status, sync_status, cache_health)
- [x] Cloud OS image source configuration
- [x] Local caching rules and policies
- [x] Relay health monitoring
- [x] Backend procedure: `relay.listNodes()`
- [x] Backend procedure: `relay.configureNode(nodeId, config)`
- [x] Backend procedure: `relay.getNodeHealth(nodeId)`
- [x] Backend procedure: `relay.syncImageCache(nodeId)`
- [ ] WebSocket events: relay health updates, sync progress
- [x] Frontend: Phoenix Relay control panel
- [x] Frontend: Node health dashboard with cache visualization

## Feature 5: Real-Time WebSocket Progress Tracking
- [x] Deployment progress schema (job_id, status, progress_percent, logs)
- [ ] WebSocket event streaming for active jobs
- [ ] Log aggregation and streaming
- [x] Backend procedure: `deployments.getProgress(jobId)`
- [ ] Backend procedure: `deployments.streamLogs(jobId)`
- [ ] WebSocket handler: progress updates
- [ ] WebSocket handler: log streaming
- [x] Frontend: Progress tracking component with live bars
- [ ] Frontend: Log viewer with streaming support

## Feature 6: Boot Camp Driver Manager
- [x] Boot Camp driver database schema
- [x] Driver compatibility matrix (Mac hardware → drivers)
- [x] Driver search and filtering
- [ ] Automated compatibility checks
- [x] Backend procedure: `bootcamp.listDrivers(filters)`
- [x] Backend procedure: `bootcamp.getCompatibleDrivers(macModel)`
- [x] Backend procedure: `bootcamp.deployDriver(deviceId, driverId)`
- [x] Frontend: Boot Camp Driver Manager page
- [ ] Frontend: Driver browser with compatibility indicators

## Feature 7: Admin Dashboard with Role-Based Access
- [x] User management interface (list, edit, promote/demote roles)
- [x] Audit log schema and viewer
- [ ] Global deployment policies configuration
- [x] Backend procedure: `admin.listUsers()`
- [x] Backend procedure: `admin.updateUserRole(userId, role)`
- [x] Backend procedure: `admin.getAuditLogs(filters)`
- [ ] Backend procedure: `admin.updatePolicies(policies)`
- [x] Frontend: Admin dashboard page
- [x] Frontend: User management panel
- [x] Frontend: Audit log viewer
- [ ] Frontend: Policy configuration panel

## Feature 8: Notification Center
- [x] Notification schema (type, recipient, status, read_at)
- [ ] Email notification service integration
- [x] In-app notification display
- [x] Backend procedure: `notifications.list(userId)`
- [x] Backend procedure: `notifications.markAsRead(notificationId)`
- [x] Backend procedure: `notifications.getPreferences(userId)`
- [x] Backend procedure: `notifications.updatePreferences(userId, prefs)`
- [ ] WebSocket handler: new notification events
- [x] Frontend: Notification center dropdown
- [x] Frontend: Notification preferences panel

## Feature 9: Device Compatibility Wizard
- [x] Wizard step schema (identification, OS selection, recipe generation)
- [x] Device identification logic
- [x] OS recommendation engine
- [ ] Backend procedure: `wizard.identifyDevice(specs)`
- [ ] Backend procedure: `wizard.recommendOS(deviceId)`
- [ ] Backend procedure: `wizard.generateRecipe(wizardState)`
- [x] Frontend: Multi-step wizard component
- [x] Frontend: Device identification form
- [x] Frontend: OS selection interface
- [x] Frontend: Recipe preview and confirmation

## Feature 10: API and Monitoring Status Panel
- [x] Health check schema (service, status, latency, uptime)
- [x] Backend health check procedures
- [ ] Relay node connectivity monitoring
- [x] Backend procedure: `monitoring.getSystemHealth()`
- [ ] Backend procedure: `monitoring.getServiceStatus(serviceName)`
- [ ] Backend procedure: `monitoring.getRelayNodeStatus(nodeId)`
- [ ] WebSocket handler: health status updates
- [x] Frontend: Status panel with live indicators
- [ ] Frontend: Service health cards with uptime metrics

## UI/UX & Design System
- [ ] Define premium color palette and typography
- [ ] Create reusable component library (cards, buttons, modals, etc.)
- [ ] Implement smooth animations and transitions
- [ ] Design responsive layouts for all features
- [ ] Create consistent spacing and sizing system
- [ ] Build premium form components with validation

## Testing & Quality
- [ ] Unit tests for backend procedures
- [ ] Integration tests for WebSocket events
- [ ] E2E tests for critical user flows
- [ ] Performance testing for real-time updates
- [ ] Accessibility audit and fixes

## Deployment & Documentation
- [ ] Production deployment configuration
- [ ] API documentation (OpenAPI/Swagger)
- [ ] User guide and tutorials
- [ ] Admin setup guide
- [ ] Architecture documentation
