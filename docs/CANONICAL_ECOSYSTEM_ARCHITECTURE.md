# Canonical PhoenixCore Ecosystem Architecture

## Organization

**Bobby's Workshop**  
Established 2026

```text
Bobby's Workshop
├── Blue Phoenix Studios
│   ├── Phoenix Prime Kernel
│   ├── ARCWYRE Native
│   ├── ARCWYRE Eternum
│   └── ARCWYRE Live
└── PhoenixCore
    ├── PhoenixCore Mobile
    ├── PhoenixCore Desktop
    ├── Phoenix USB Creator
    ├── Device Diagnosis Engine
    ├── Repair Planning Engine
    ├── OS Compatibility Engine
    ├── Boot Media Builder
    ├── Repair Session Manager
    ├── Device Identity Service
    ├── Technician Workspace
    ├── Installer and Deployment Manager
    └── Recovery Vault
```

## Repository ownership

This repository owns ecosystem applications, repair planning, compatibility decisions, media creation, and companion workflows. It does not own Phoenix Prime Kernel or the native operating-system source.

## Core user journey

```text
problem detected
→ PhoenixCore Mobile or Desktop diagnosis
→ device identity and capability discovery
→ repair/install plan
→ Phoenix USB Creator or Boot Media Builder
→ ARCWYRE Live execution
→ TruthLog evidence
→ Continuity session preservation
```

## Shared repair session

Every job uses one `repair_session_id` across mobile diagnosis, desktop preparation, signed USB manifest, ARCWYRE Live execution, repair logs, installation results, and the final technician report.

## Safety law

Supported public workflows include authorized diagnostics, backup, restore, firmware installation, boot repair, disk imaging, driver management, OS installation, and owner-approved wiping.

The ecosystem must not provide unauthorized defeat of activation locks, FRP, MDM, credentials, ownership protections, or anti-theft systems.

## Naming law

Use the exact public names listed in this document. Do not create drifting aliases or place `Blue Phoenix Studios` inside individual product names.
