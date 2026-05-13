# BootForge Ownership Boundaries

## Overview
This document defines the integration boundaries between the legacy BootForge subsystem and the modern Phoenix Platform architecture.

## 1. Component Ownership

### BootForge (Orchestration & Media)
*   **Media Definition**: Owns the "Recipe" format (ISO/USB configuration).
*   **Media Building**: Orchestrates the assembly of bootable environments (WinPE, Linux, macOS installers).
*   **Historical Workflows**: Maintains compatibility with legacy deployment scripts and patches.
*   **Media Verification**: Owns the checksumming and signing of generated artifacts.

### Phoenix Agent (Execution & Governance)
*   **Operation Lifecycle**: Manages the state of an imaging operation (Request -> Finish).
*   **Safety Enforcement**: Evaluates safety gates before allowing hardware access.
*   **Device Identity**: Maps imaging operations to specific, verified hardware IDs.
*   **Audit Logging**: Records every step of the imaging process for compliance.

### Phoenix Control Center (UI/UX)
*   **Recipe Designer**: Provides the drag-and-drop interface for composing deployments.
*   **Fleet Visualization**: Displays real-time progress of imaging tasks across multiple devices.
*   **Approval Hub**: Surface safety warnings and requires explicit user confirmation for dangerous operations.

### Rust Imaging Crates (Low-Level Implementation)
*   **`phoenix-imaging`**: Primitive disk I/O, sector-level copying, and image mounting.
*   **`phoenix-fs-fat32` / `phoenix-wim`**: Filesystem-specific drivers for media preparation.
*   **`phoenix-safety`**: Low-level platform interrogation (detecting if a disk is "Internal" vs "Removable").

## 2. Integration Flow

1.  **UI**: User designs a recipe in Control Center.
2.  **BootForge**: Compiles the recipe into an imaging manifest.
3.  **Agent**: Receives the manifest, validates device identity, and runs safety checks.
4.  **Rust Crates**: Performs the physical disk operations as directed by the Agent.
5.  **Agent**: Streams progress back to the Control Center.
6.  **Agent**: Finalizes the audit log and report bundle.

## 3. Boundary Rules
*   **No Direct Access**: The UI never talks to Rust imaging crates directly; all calls must pass through the Phoenix Agent.
*   **Safety First**: Rust crates must fail-safe if the Agent does not provide a valid safety token.
*   **State Separation**: BootForge defines *what* to build; Phoenix Agent defines *how* it is safely executed.
