# BWOS Platform Factory: Epics and Child Issues

This document defines the 9 Epics and 36 Child Issues comprising the planning layer of the PhoenixCore / BWOS monorepo. 

---

## Epic 1: epic(os)
**Title:** Stabilize Home Aurelia boot, presentation markers, and clean shutdown
**Milestone:** `M0 Home Aurelia ISO Stability`
**Labels:** `type:epic`, `stack:os`, `priority:p0`

### Issue 1.1: Validate kernel boot configurations and GRUB structures
- **Scope:** Base OS boot configuration files and boot loader menus.
- **Definition of Done:** Boot scripts and configuration parameters are validated to ensure compliance with hardware platform requirements. GRUB and systemd-boot configurations are free of hardcoded paths and point correctly to target Kernels.
- **Validation Commands:** 
  ```bash
  python -m unittest discover -s .github/workflows/scripts -p "test_boot_configs.py"
  ```
- **Blocked-by Dependencies:** None
- **Safety Notes:** Do not modify the existing target bootloader partitions directly. Ensure validation is performed inside sandboxed environment or via dry-run parsing.

### Issue 1.2: Standardize presentation markers and boot screen assets
- **Scope:** Boot graphics, boot splashes, and UI presentation layout configurations.
- **Definition of Done:** Ensure that all brand assets, splash graphics, and boot flags meet modern design guidelines and exist in designated system directories.
- **Validation Commands:** 
  ```bash
  dir system/assets/splashes/
  # Run visual asset check script and pipe results
  python .github/workflows/scripts/validate_assets.py --path system/assets/splashes/ --out report.log
  ```
- **Blocked-by Dependencies:** Issue 1.1
- **Safety Notes:** Do not rename any Tauri app IDs or brand IDs in the frontend configurations.

### Issue 1.3: Implement clean shutdown protocols and state saves
- **Scope:** Shutdown and reboot service daemon hooks.
- **Definition of Done:** Clean shutdown service script successfully intercepts ACPI power-down requests, closes database connections, flushes state caches to disk, and records a safe-shutdown hash.
- **Validation Commands:** 
  ```bash
  python system/scripts/shutdown_daemon.py --dry-run
  ```
- **Blocked-by Dependencies:** Issue 1.1
- **Safety Notes:** Ensure the safe state save mechanism does not perform destructive deletion of adjacent OS files.

### Issue 1.4: End-to-end boot sanity testing on reference hardware
- **Scope:** Quality gate and integration testing.
- **Definition of Done:** Reference hardware boot logs are captured, analyzed, and verified to contain zero fatal boot flags or partition mount failures.
- **Validation Commands:** 
  ```bash
  # Check system boot logs for errors
  powershell -Command "Get-Content system/logs/boot.log | Select-String 'FATAL', 'ERROR'"
  # Compute sha256 of verified boot log for gate release
  powershell -Command "(Get-FileHash system/logs/boot.log -Algorithm SHA256).Hash"
  ```
- **Blocked-by Dependencies:** Issue 1.1, Issue 1.2, Issue 1.3
- **Safety Notes:** Must require actual logs, hashes, or screenshots before marking as verified. Do not claim absolute release readiness.

---

## Epic 2: epic(thunder-god)
**Title:** Build and validate Thunder God ARM64 flagship ISO
**Milestone:** `M0 Home Aurelia ISO Stability`
**Labels:** `type:epic`, `stack:os`, `priority:p0`

### Issue 2.1: Establish ARM64 UEFI boot shim configurations
- **Scope:** Bootloader structures for ARM64 target platforms.
- **Definition of Done:** ARM64 UEFI boot configurations are correctly written as GRUB EFI loaders, ensuring proper secure-boot parameters and device-tree mapping files.
- **Validation Commands:** 
  ```bash
  python .github/workflows/scripts/validate_efi.py --arch arm64 --config boot/efi/arm64.conf
  ```
- **Blocked-by Dependencies:** None
- **Safety Notes:** Do not perform direct disk edits or override local UEFI NVRAM variables.

### Issue 2.2: Map memory and device tree structures for Snapdragon Elite reference boards
- **Scope:** Snapdragon ARM64 hardware compatibility layer.
- **Definition of Done:** Compiled Device Tree Source (DTS) files exist for the target Snapdragon system boards, mapped to valid memory registers.
- **Validation Commands:** 
  ```bash
  dtc -I dts -O dtb -o boot/dts/snapdragon_elite.dtb boot/dts/snapdragon_elite.dts
  ```
- **Blocked-by Dependencies:** Issue 2.1
- **Safety Notes:** Ensure DTS maps strictly adhere to reference documentation; do not overwrite host machine firmware.

### Issue 2.3: Define hardware drivers staging layer for ARM64 kernel
- **Scope:** Peripheral driver inclusion list.
- **Definition of Done:** Maintain a JSON matrix detailing exactly which Snapdragon drivers (Network, GPU, Storage controller) are validated, verifying package IDs are not altered.
- **Validation Commands:** 
  ```bash
  python .github/workflows/scripts/validate_driver_matrix.py --input system/drivers/arm64_matrix.json
  ```
- **Blocked-by Dependencies:** Issue 2.2
- **Safety Notes:** Do not install unverified experimental drivers onto the host operating system.

### Issue 2.4: ARM64 ISO build validation gate
- **Scope:** Compilation & integrity gate.
- **Definition of Done:** Validate that the ARM64 build manifests compile correctly, verify generated build file hashes, and output full verification logs. (Do not build actual ISOs in CI).
- **Validation Commands:** 
  ```bash
  powershell -Command "(Get-FileHash manifests/arm64_iso_manifest.json).Hash"
  ```
- **Blocked-by Dependencies:** Issue 2.1, Issue 2.2, Issue 2.3
- **Safety Notes:** Must require validation hash outputs. Do not claim production release readiness.

---

## Epic 3: epic(arcwyre)
**Title:** Build ARCWYRE read-only technician diagnostics MVP
**Milestone:** `M1 ARCWYRE / BootForge Recovery Toolkit`
**Labels:** `type:epic`, `stack:arcwyre`, `priority:p1`

### Issue 3.1: Define read-only mount policies for diagnostic drives
- **Scope:** Mount security layer policies.
- **Definition of Done:** Hardcoded read-only mount profile manifests are written for the ARCWYRE diagnostics environment, ensuring no write operations can occur.
- **Validation Commands:** 
  ```bash
  python .github/workflows/scripts/validate_mount_policies.py --policy security/mount_policy.json
  ```
- **Blocked-by Dependencies:** None
- **Safety Notes:** Absolutely no write or format commands should be accessible via this policy file.

### Issue 3.2: Build disk health checker interface using smartctl APIs
- **Scope:** Smart diagnostics wrapper script.
- **Definition of Done:** Python wrapper successfully calls SMART status commands in a read-only fashion, converting logs to structured JSON data.
- **Validation Commands:** 
  ```bash
  python diagnostics/scripts/smart_checker.py --dry-run
  ```
- **Blocked-by Dependencies:** Issue 3.1
- **Safety Notes:** Do not issue destructive low-level repair or wipe requests (e.g. `smartctl --format`).

### Issue 3.3: Implement CPU and memory utilization logging utilities
- **Scope:** System diagnostics tracking dashboard.
- **Definition of Done:** Read-only system logger records resource limits and outputs an execution matrix mapping performance metrics.
- **Validation Commands:** 
  ```bash
  python diagnostics/scripts/sys_monitor.py --interval 1 --count 5
  ```
- **Blocked-by Dependencies:** None
- **Safety Notes:** Ensure utility does not consume high CPU priority or trigger system lockups.

### Issue 3.4: Diagnostics MVP output validation script
- **Scope:** Execution integrity proof.
- **Definition of Done:** System diagnostics utility runs a complete mock assessment and outputs signed diagnostic hashes, capturing logs and diagnostic test results.
- **Validation Commands:** 
  ```bash
  python diagnostics/scripts/test_diagnostics_suite.py --verify --output diagnostics_report.json
  powershell -Command "(Get-FileHash diagnostics_report.json).Hash"
  ```
- **Blocked-by Dependencies:** Issue 3.1, Issue 3.2, Issue 3.3
- **Safety Notes:** Verify generated diagnostic data contains verified signatures and timestamps.

---

## Epic 4: epic(bootforge)
**Title:** Build BootForge Recovery Toolkit MVP
**Milestone:** `M1 ARCWYRE / BootForge Recovery Toolkit`
**Labels:** `type:epic`, `stack:bootforge`, `priority:p1`

### Issue 4.1: Core GPT partitioning schema validation engine in `usb_creator.py`
- **Scope:** Safe schema check in partition utility.
- **Definition of Done:** Ensure `usb_creator.py` checks that requested GPT layout schemas conform to partition rules, rejecting destructive or overlapping boundary sizes.
- **Validation Commands:** 
  ```bash
  python -m unittest usb_creator.py
  ```
- **Blocked-by Dependencies:** None
- **Safety Notes:** Do not perform raw block disk edits. Use virtual loopback devices or mocks for layout checks.

### Issue 4.2: Automate Dortania OCLP API downloader integration
- **Scope:** Dortania API integration inside `usb_creator.py`.
- **Definition of Done:** Correctly retrieve latest patcher GUI URLs, verify download integrity via checksum verification against API metadata, and secure files.
- **Validation Commands:** 
  ```bash
  python usb_creator.py --download-oclp
  ```
- **Blocked-by Dependencies:** None
- **Safety Notes:** Check downloader for invalid redirection URLs and ensure downloads are stored securely.

### Issue 4.3: Map Apple BootCamp support package repository endpoints
- **Scope:** Hardware repository map configurations.
- **Definition of Done:** Retrieve support drivers matching MacBook target models (e.g. `MacBookPro11,1`, `iMac15,1`) from official secure directories without corrupting names.
- **Validation Commands:** 
  ```bash
  python .github/workflows/scripts/validate_bootcamp_matrix.py --config dashboard/src/App.jsx
  ```
- **Blocked-by Dependencies:** None
- **Safety Notes:** Ensure drivers are verified and no new editions or package naming conversions occur.

### Issue 4.4: USB formatting dry-run validation
- **Scope:** Safe toolkit verification gate.
- **Definition of Done:** BootForge creator can perform a complete mock USB build, printing step logs, mock file extraction signatures, and verified folder checks without rewriting physical local partitions.
- **Validation Commands:** 
  ```bash
  python usb_creator.py --create C:\Users\Bobby\.gemini\antigravity\scratch\phoenixcore\downloads --dry-run
  ```
- **Blocked-by Dependencies:** Issue 4.1, Issue 4.2, Issue 4.3
- **Safety Notes:** Absolutely DO NOT execute partition format commands on real hosts during automation.

---

## Epic 5: epic(compatibility)
**Title:** Plan governed Windows app compatibility layer
**Milestone:** `M2 Compatibility Center`
**Labels:** `type:epic`, `stack:compatibility`, `priority:p1`

### Issue 5.1: Design sandboxing boundaries and directory permission filters
- **Scope:** Win32 sandbox configuration profiles.
- **Definition of Done:** Design comprehensive sandboxing rules defining directory exclusions (e.g. `C:\Windows`, `C:\Program Files`) and read-only filters for running legacy applications.
- **Validation Commands:** 
  ```bash
  python .github/workflows/scripts/validate_sandbox_profiles.py --profile compatibility/profiles/strict_sandbox.json
  ```
- **Blocked-by Dependencies:** None
- **Safety Notes:** Do not perform partition edits. Do not modify system privileges of running OS users.

### Issue 5.2: Specify compatibility registry shims for Win32 applications
- **Scope:** Registry emulation mapping configs.
- **Definition of Done:** Registry shim manifest maps critical Windows API keys to virtual paths, preventing legacy applications from writing directly to the host registry.
- **Validation Commands:** 
  ```bash
  python .github/workflows/scripts/validate_shims.py --shims compatibility/registry/shims_manifest.json
  ```
- **Blocked-by Dependencies:** Issue 5.1
- **Safety Notes:** Do not write directly to the system registry database.

### Issue 5.3: Draft system call intercept policies and security boundary specifications
- **Scope:** Governance policy architecture documentation.
- **Definition of Done:** Write structured Markdown governance documents outlining specific system-call authorization rules, detailing security review requirements for apps.
- **Validation Commands:** 
  ```bash
  # Ensure file is formatted correctly and has header structure
  python .github/workflows/scripts/validate_docs.py --file compatibility/docs/security_boundary.md
  ```
- **Blocked-by Dependencies:** None
- **Safety Notes:** This issue is research/specification-only. Do not write executable driver exploits.

### Issue 5.4: Sandbox isolation policy validation
- **Scope:** Policy testing gate.
- **Definition of Done:** Verify that the compatibility JSON schemas conform to the App Reality Matrix, and ensure that no un-governed applications are allowed access.
- **Validation Commands:** 
  ```bash
  python .github/workflows/scripts/verify_matrix_alignment.py --matrix manifests/app_matrix.json --profile compatibility/profiles/strict_sandbox.json
  ```
- **Blocked-by Dependencies:** Issue 5.1, Issue 5.2, Issue 5.3
- **Safety Notes:** Must require validation hashes of compatibility configuration layers.

---

## Epic 6: epic(command)
**Title:** Build Command dashboard for artifacts, boot matrix, and system truth
**Milestone:** `M3 Command + App Reality Matrix`
**Labels:** `type:epic`, `stack:command`, `priority:p1`

### Issue 6.1: React dashboard layout for system status metrics
- **Scope:** Dashboard UI core pages in React.
- **Definition of Done:** Design modern, glassmorphic layout displaying target USB status, active selected models, and downloader log outputs.
- **Validation Commands:** 
  ```bash
  cd dashboard
  npm run lint
  ```
- **Blocked-by Dependencies:** None
- **Safety Notes:** Do not rename internal crates or Tauri app package boundaries.

### Issue 6.2: Parse and render boot matrix configuration profiles
- **Scope:** Frontend configuration adapter component.
- **Definition of Done:** App reads local boot matrix JSON data, rendering compatibility warnings and technical requirements for chosen Macbook profiles.
- **Validation Commands:** 
  ```bash
  # Validate JSON structure before loading in app
  python -m json.tool dashboard/public/boot_matrix.json
  ```
- **Blocked-by Dependencies:** Issue 6.1
- **Safety Notes:** Do not create fake application placeholder UI elements.

### Issue 6.3: Form controls for selecting target rescue models and downloader tools
- **Scope:** Dashboard interactive controls.
- **Definition of Done:** Select dropdowns and input checkboxes in React allow selecting Macbook model versions and OCLP releases, printing exact configuration selections.
- **Validation Commands:** 
  ```bash
  # Check test files pass
  cd dashboard
  npm run test -- --watch=false
  ```
- **Blocked-by Dependencies:** Issue 6.1
- **Safety Notes:** Ensure UI forms do not trigger unvalidated local disk command strings.

### Issue 6.4: Dashboard local development build verify
- **Scope:** Dashboard packaging sanity.
- **Definition of Done:** React dashboard builds successfully into optimized static assets without warnings or dependency faults.
- **Validation Commands:** 
  ```bash
  cd dashboard
  npm run build
  # Verify size output and capture checksums
  powershell -Command "(Get-FileHash dashboard/dist/index.html).Hash"
  ```
- **Blocked-by Dependencies:** Issue 6.1, Issue 6.2, Issue 6.3
- **Safety Notes:** Keep Tauri ID unchanged. Output verified dist hashes and log outputs.

---

## Epic 7: epic(apps)
**Title:** Implement PR40 App Launch Matrix
**Milestone:** `M3 Command + App Reality Matrix`
**Labels:** `type:epic`, `stack:apps`, `priority:p1`

### Issue 7.1: Formulate JSON schema for App Launch Matrix configurations
- **Scope:** App matrix structural data type.
- **Definition of Done:** Create a rigorous JSON schema validating parameters such as sandbox boundaries, runtime layers, environmental bindings, and security hashes.
- **Validation Commands:** 
  ```bash
  python .github/workflows/scripts/validate_schema.py --schema apps/schema/launch_matrix.schema.json
  ```
- **Blocked-by Dependencies:** None
- **Safety Notes:** Do not change package IDs or naming conventions for Tauri components.

### Issue 7.2: Develop PR40 config parser and validation script
- **Scope:** PR40 config validator utility.
- **Definition of Done:** Python script successfully reads app launch matrix configs, ensuring every registered package matches correct formats and has signed release keys.
- **Validation Commands:** 
  ```bash
  python .github/workflows/scripts/validate_pr40_matrix.py --matrix apps/configs/pr40_matrix.json
  ```
- **Blocked-by Dependencies:** Issue 7.1
- **Safety Notes:** Ensure parser raises immediate errors if unregistered apps attempt to register as system apps.

### Issue 7.3: Implement environment variable mappings for sandboxed app launchers
- **Scope:** Process launcher environmental manager.
- **Definition of Done:** Environment mapping profiles dictate safe environmental keys, filtering out user profiles and credential parameters from sandboxed runtime.
- **Validation Commands:** 
  ```bash
  python .github/workflows/scripts/validate_env_shims.py --env apps/configs/safe_env.json
  ```
- **Blocked-by Dependencies:** Issue 7.1
- **Safety Notes:** Do not expose active user session environment keys during verification.

### Issue 7.4: App Launch Matrix integration verification
- **Scope:** End-to-end integration check.
- **Definition of Done:** The active apps dashboard registers launch matrix targets and outputs execution matrices detailing verified paths and checksums.
- **Validation Commands:** 
  ```bash
  python apps/scripts/verify_integration.py --matrix apps/configs/pr40_matrix.json --output apps_integration.log
  powershell -Command "(Get-FileHash apps_integration.log).Hash"
  ```
- **Blocked-by Dependencies:** Issue 7.1, Issue 7.2, Issue 7.3
- **Safety Notes:** Require hashes and integration log exports before completion.

---

## Epic 8: epic(ci)
**Title:** Add validation and release-gate GitHub Actions
**Milestone:** `M4 Release Gate + Public Alpha`
**Labels:** `type:epic`, `stack:ci`, `priority:p1`

### Issue 8.1: Configure continuous monorepo syntax and format check pipeline
- **Scope:** Base codebase syntax check.
- **Definition of Done:** GitHub Action verifies python format, JSON structure, and JSX styling across all active stacks.
- **Validation Commands:** 
  ```bash
  python -m py_compile .github/workflows/scripts/*.py
  ```
- **Blocked-by Dependencies:** None
- **Safety Notes:** Do not modify existing codebase directories; this is an inspection-only pipeline.

### Issue 8.2: Integrate boot configuration matrix validation action
- **Scope:** Hardware boot profile checker CI integration.
- **Definition of Done:** Automated runner executes validation parsers on device-tree source files and Macbook model maps in CI runtime.
- **Validation Commands:** 
  ```bash
  # Check test configurations
  python -m unittest discover -s .github/workflows/scripts -p "test_matrix*.py"
  ```
- **Blocked-by Dependencies:** Issue 8.1
- **Safety Notes:** Ensure action executes strictly within containerized limits, requiring no virtualization overhead.

### Issue 8.3: Configure safety and governance static analysis scanners in CI
- **Scope:** Static security scan pipelines.
- **Definition of Done:** CI pipeline scans scripts and codebases, detecting destructive commands (`dd`, raw partitioning) and blocking unauthorized package/Tauri ID renames.
- **Validation Commands:** 
  ```bash
  python .github/workflows/scripts/scan_governance.py --check-dir .
  ```
- **Blocked-by Dependencies:** Issue 8.1
- **Safety Notes:** If any destructive commands are found, trigger a hard failure and halt execution immediately.

### Issue 8.4: Establish release candidate criteria checking automated gate
- **Scope:** Final Release Candidate criteria verifier.
- **Definition of Done:** Check that all files in `manifests/` have valid checksums, no un-governed changes are present, and output an official gating report containing system logs and check hashes.
- **Validation Commands:** 
  ```bash
  python .github/workflows/scripts/verify_release_gate.py --manifest manifests/release_manifest.json
  ```
- **Blocked-by Dependencies:** Issue 8.1, Issue 8.2, Issue 8.3
- **Safety Notes:** Must require validation hashes. Do not claim final production release readiness automatically.

---

## Epic 9: epic(native)
**Title:** Keep Native research-only and non-shipping
**Milestone:** `M5 Native Research Track`
**Labels:** `type:epic`, `stack:native`, `priority:p2`

### Issue 9.1: Isolate native-research packages in Cargo workspace/manifest structures
- **Scope:** Workspace configuration files.
- **Definition of Done:** Native research-only crates are explicitly grouped in a distinct workspace boundary, and isolated from shipping packages.
- **Validation Commands:** 
  ```bash
  python .github/workflows/scripts/check_workspace_isolation.py --workspace Cargo.toml
  ```
- **Blocked-by Dependencies:** None
- **Safety Notes:** Absolutely do not create new Cargo editions or rename existing crates.

### Issue 9.2: Set up pre-commit hook to prevent native symbols leaking to shipping code
- **Scope:** Monorepo commit controls.
- **Definition of Done:** Standard pre-commit configuration blocks staging or committing research-only headers into main binary branches.
- **Validation Commands:** 
  ```bash
  python .github/workflows/scripts/validate_pre_commit.py --config .pre-commit-config.yaml
  ```
- **Blocked-by Dependencies:** Issue 9.1
- **Safety Notes:** Check only; do not perform automated code rewrites.

### Issue 9.3: Implement unit test isolation assertions for native crates
- **Scope:** Test suites verification logic.
- **Definition of Done:** Assertions are written ensuring that research-only tracks cannot be resolved or linked by production App launchers.
- **Validation Commands:** 
  ```bash
  python .github/workflows/scripts/test_isolation_boundaries.py
  ```
- **Blocked-by Dependencies:** Issue 9.1
- **Safety Notes:** Ensure tests do not access target platform features outside sandboxed memory limits.

### Issue 9.4: Non-shipping track verification script
- **Scope:** Verification isolation proof.
- **Definition of Done:** Run dependency-tree validation checking that no shipping Tauri dependencies depend on research packages, outputting a clear dependency verification map.
- **Validation Commands:** 
  ```bash
  python .github/workflows/scripts/verify_native_gate.py --shipping-manifest package.json --research-dir native_research/
  ```
- **Blocked-by Dependencies:** Issue 9.1, Issue 9.2, Issue 9.3
- **Safety Notes:** Require generated validation dependency logs and sha256 outputs.
