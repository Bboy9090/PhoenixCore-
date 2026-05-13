# BootForge Migration Strategy

## 1. Current State (Legacy/Partial Integration)
*   **Imaging**: Legacy Python code (`BootForge PyQt/CLI`) performs disk operations using system tools (dd, diskpart, hdiutil).
*   **Recipes**: Simple configuration files with manual verification.
*   **UI**: Separate desktop application from the Phoenix Control Center.

## 2. Transition Phase (PR14 - PR20)
*   **Contractual Decoupling**: Establish the Agent/BootForge/Imaging boundaries (Done in PR14).
*   **SDK Hardening**: Update `shared/sdk.ts` with the new operation lifecycle types.
*   **Rust Porting**: Incrementally move low-level I/O logic from Python to the `phoenix-imaging` Rust crate.
*   **Agent Integration**: Wrap legacy Python tools in a Phoenix Agent shim to enforce safety gates during the transition.

## 3. Future State (Full Integration)
*   **Unified UI**: All imaging orchestration occurs within the Phoenix Control Center.
*   **Native Execution**: The Phoenix Agent executes operations using the high-performance Rust imaging library.
*   **Universal Safety**: All platforms (Windows, macOS, Linux) use the same safety gate engine and audit model.

## 4. Key Migration Milestones
1.  **Milestone A**: Agent can "Proxy" a BootForge legacy request with full safety gating.
2.  **Milestone B**: `phoenix-imaging` crate supports block-level writing for all 3 major OSs.
3.  **Milestone C**: Retirement of the standalone BootForge PyQt application in favor of the Control Center.
