use serde::Serialize;
use std::{
    collections::VecDeque,
    fs::{self, File},
    io::{Read, Seek, SeekFrom},
    path::{Path, PathBuf},
};

const MAX_SYSTEM_IMAGE_SCAN_DEPTH: usize = 4;
const MAX_SYSTEM_IMAGE_SCAN_ENTRIES: usize = 500;

#[derive(Debug, Clone, Serialize, PartialEq, Eq)]
pub struct WindowsBackupAnalysis {
    pub schema: &'static str,
    pub path: String,
    pub kind: String,
    pub confidence: String,
    pub user_summary: String,
    pub recommended_action: String,
    pub size_bytes: Option<u64>,
    pub detected_by: Vec<String>,
    pub has_boot_wim: bool,
    pub has_install_wim: bool,
    pub has_install_esd: bool,
    pub has_split_wim: bool,
    pub has_winre: bool,
    pub has_efi: bool,
    pub has_bcd: bool,
    pub has_setup_exe: bool,
    pub has_windows_image_backup: bool,
    pub system_image_files: Vec<String>,
    pub restore_candidate: bool,
    pub destructive_actions_performed: bool,
    pub warnings: Vec<String>,
}

#[derive(Debug, Clone, Serialize, PartialEq, Eq)]
pub struct RecoveryPlanAction {
    pub id: &'static str,
    pub phase: &'static str,
    pub mutates_system: bool,
    pub requires_authorization: bool,
    pub status: &'static str,
}

#[derive(Debug, Clone, Serialize, PartialEq, Eq)]
pub struct RecoveryTargetContract {
    pub snapshot_identity_required: bool,
    pub stable_identity_required: bool,
    pub source_target_separation_required: bool,
    pub capacity_check_required: bool,
    pub fresh_revalidation_required: bool,
}

#[derive(Debug, Clone, Serialize, PartialEq, Eq)]
pub struct RecoveryExecutionBoundary {
    pub planner_only: bool,
    pub restore_executor_available: bool,
    pub destructive_authorization_required: bool,
    pub automatic_destructive_resume_allowed: bool,
    pub system_mutations_performed: bool,
}

#[derive(Debug, Clone, Serialize, PartialEq, Eq)]
pub struct RecoverySourceContract {
    pub source_kind: String,
    pub restore_candidate: bool,
    pub content_identity_required: bool,
    pub metadata_validation_required: bool,
    pub complete_split_set_required: bool,
    pub fat32_single_file_limit_check_required: bool,
}

#[derive(Debug, Clone, Serialize, PartialEq, Eq)]
pub struct RecoveryBootContract {
    pub boot_mode: &'static str,
    pub efi_files_required: bool,
    pub bcd_required: bool,
    pub partition_manifest_required: bool,
    pub expected_boot_files: Vec<String>,
    pub expected_partition_roles: Vec<String>,
}

#[derive(Debug, Clone, Serialize, PartialEq, Eq)]
pub struct RecoveryDryRunSummary {
    pub source_ready_for_planning: bool,
    pub target_selected: bool,
    pub target_identity_verified: bool,
    pub rollback_evidence_persisted: bool,
    pub destructive_authorization_present: bool,
    pub mutation_steps_planned: usize,
    pub mutation_steps_executed: usize,
    pub executable: bool,
}

#[derive(Debug, Clone, Serialize, PartialEq, Eq)]
pub struct WindowsRecoveryPlan {
    pub schema: &'static str,
    pub source: WindowsBackupAnalysis,
    pub host_arch: String,
    pub host_os: String,
    pub host_route: String,
    pub host_explanation: String,
    pub traditional_bootcamp_supported: bool,
    pub allowed_operations: Vec<String>,
    pub blocked_operations: Vec<String>,
    pub required_gates: Vec<String>,
    pub proposed_actions: Vec<RecoveryPlanAction>,
    pub target_contract: RecoveryTargetContract,
    pub execution_boundary: RecoveryExecutionBoundary,
    pub source_contract: RecoverySourceContract,
    pub boot_contract: RecoveryBootContract,
    pub remediation_required: Vec<String>,
    pub block_reasons: Vec<String>,
    pub dry_run_summary: RecoveryDryRunSummary,
    pub next_steps: Vec<String>,
    pub dry_run: bool,
    pub destructive_actions_performed: bool,
}

#[derive(Debug, Default)]
struct SystemImageEvidence {
    structure_markers: Vec<String>,
    image_files: Vec<String>,
    scan_limited: bool,
}

fn contains_case_insensitive(haystack: &[u8], needle: &[u8]) -> bool {
    if needle.is_empty() || haystack.len() < needle.len() {
        return false;
    }
    haystack.windows(needle.len()).any(|window| {
        window
            .iter()
            .zip(needle)
            .all(|(left, right)| left.eq_ignore_ascii_case(right))
    })
}

fn read_prefix(path: &Path, max: usize) -> Result<Vec<u8>, String> {
    let mut file =
        File::open(path).map_err(|error| format!("cannot open backup source: {error}"))?;
    let mut buffer = vec![0; max];
    let count = file
        .read(&mut buffer)
        .map_err(|error| format!("cannot read backup source: {error}"))?;
    buffer.truncate(count);
    Ok(buffer)
}

fn read_tail(path: &Path, max: usize) -> Result<Vec<u8>, String> {
    let mut file =
        File::open(path).map_err(|error| format!("cannot open backup source: {error}"))?;
    let length = file
        .metadata()
        .map_err(|error| format!("cannot inspect backup source: {error}"))?
        .len();
    let read_len = usize::try_from(length.min(max as u64)).unwrap_or(max);
    file.seek(SeekFrom::End(-(read_len as i64)))
        .map_err(|error| format!("cannot seek backup source: {error}"))?;
    let mut buffer = vec![0; read_len];
    file.read_exact(&mut buffer)
        .map_err(|error| format!("cannot read backup source tail: {error}"))?;
    Ok(buffer)
}

fn directory_contains(root: &Path, candidates: &[&str]) -> bool {
    candidates
        .iter()
        .any(|candidate| root.join(candidate).is_file())
}

fn push_unique(values: &mut Vec<String>, value: impl Into<String>) {
    let value = value.into();
    if !values.contains(&value) {
        values.push(value);
    }
}

fn inspect_system_image_tree(root: &Path) -> SystemImageEvidence {
    let mut evidence = SystemImageEvidence::default();
    let root_name = root
        .file_name()
        .and_then(|value| value.to_str())
        .unwrap_or_default();
    if root_name.eq_ignore_ascii_case("WindowsImageBackup") {
        push_unique(
            &mut evidence.structure_markers,
            "WindowsImageBackup directory name",
        );
    }

    let mut queue = VecDeque::from([(root.to_path_buf(), 0usize)]);
    let mut visited = 0usize;

    while let Some((directory, depth)) = queue.pop_front() {
        if depth > MAX_SYSTEM_IMAGE_SCAN_DEPTH || visited >= MAX_SYSTEM_IMAGE_SCAN_ENTRIES {
            evidence.scan_limited = true;
            break;
        }

        let entries = match fs::read_dir(&directory) {
            Ok(entries) => entries,
            Err(_) => continue,
        };

        for entry in entries.filter_map(Result::ok) {
            visited += 1;
            if visited > MAX_SYSTEM_IMAGE_SCAN_ENTRIES {
                evidence.scan_limited = true;
                break;
            }

            let path = entry.path();
            let name = entry.file_name().to_string_lossy().to_string();
            let lower_name = name.to_ascii_lowercase();

            if path.is_dir() {
                if matches!(lower_name.as_str(), "catalog" | "logs") {
                    push_unique(
                        &mut evidence.structure_markers,
                        format!("{name} directory"),
                    );
                }
                if depth < MAX_SYSTEM_IMAGE_SCAN_DEPTH {
                    queue.push_back((path, depth + 1));
                }
                continue;
            }

            if matches!(
                lower_name.as_str(),
                "mediaid.bin" | "backupspecs.xml" | "globalcatalog.wbcat"
            ) {
                push_unique(&mut evidence.structure_markers, name.clone());
            }

            let extension = path
                .extension()
                .and_then(|value| value.to_str())
                .unwrap_or_default()
                .to_ascii_lowercase();
            if matches!(extension.as_str(), "vhd" | "vhdx") {
                let relative = path.strip_prefix(root).unwrap_or(&path);
                push_unique(
                    &mut evidence.image_files,
                    relative.to_string_lossy().to_string(),
                );
            }
        }
    }

    evidence
}

fn detect_directory(path: &Path) -> WindowsBackupAnalysis {
    let has_boot_wim = directory_contains(path, &["sources/boot.wim", "Sources/boot.wim"]);
    let has_install_wim = directory_contains(path, &["sources/install.wim", "Sources/install.wim"]);
    let has_install_esd = directory_contains(path, &["sources/install.esd", "Sources/install.esd"]);
    let has_split_wim = fs::read_dir(path.join("sources"))
        .or_else(|_| fs::read_dir(path.join("Sources")))
        .ok()
        .map(|entries| {
            entries.filter_map(Result::ok).any(|entry| {
                entry
                    .path()
                    .extension()
                    .and_then(|value| value.to_str())
                    .is_some_and(|extension| extension.eq_ignore_ascii_case("swm"))
            })
        })
        .unwrap_or(false);
    let has_winre = directory_contains(
        path,
        &[
            "Windows/System32/Recovery/Winre.wim",
            "windows/system32/recovery/winre.wim",
            "Recovery/WindowsRE/Winre.wim",
        ],
    );
    let has_efi = path.join("EFI").is_dir()
        || path.join("efi").is_dir()
        || path.join("EFI/Microsoft/Boot").is_dir();
    let has_bcd = directory_contains(
        path,
        &[
            "EFI/Microsoft/Boot/BCD",
            "efi/microsoft/boot/BCD",
            "Boot/BCD",
            "boot/BCD",
        ],
    );
    let has_setup_exe = directory_contains(path, &["setup.exe", "Setup.exe"]);
    let system_image = inspect_system_image_tree(path);
    let has_windows_image_backup = !system_image.image_files.is_empty()
        || !system_image.structure_markers.is_empty();

    let windows_image_present = has_install_wim || has_install_esd || has_split_wim;
    let system_image_restore_ready = !system_image.image_files.is_empty();
    let restore_candidate = windows_image_present || has_winre || system_image_restore_ready;
    let mut detected_by = Vec::new();
    if windows_image_present {
        detected_by.push("windows_installer_tree".to_string());
    }
    if has_winre {
        detected_by.push("winre_tree".to_string());
    }
    if has_efi {
        detected_by.push("efi_tree".to_string());
    }
    for marker in &system_image.structure_markers {
        push_unique(&mut detected_by, format!("system_image:{marker}"));
    }
    if system_image_restore_ready {
        push_unique(&mut detected_by, "system_image:virtual_disk_payload");
    }

    let (kind, confidence, user_summary, recommended_action) = if system_image_restore_ready {
        (
            "windows_system_image_backup",
            "high",
            "A Windows system-image backup was found with one or more VHD/VHDX disk images.",
            "Verify the backup set and hardware compatibility, then build a restore plan before selecting any target disk.",
        )
    } else if windows_image_present {
        (
            "extracted_windows_media",
            "high",
            "Extracted Windows installation media was found.",
            "Use this source to build or repair Windows recovery media after integrity checks pass.",
        )
    } else if has_winre {
        (
            "windows_recovery_tree",
            "high",
            "A Windows Recovery Environment payload was found.",
            "Use WinRE for repair and diagnostics; do not treat it as a full Windows installation backup.",
        )
    } else if has_windows_image_backup {
        (
            "windows_system_image_structure_incomplete",
            "medium",
            "Windows system-image backup metadata was found, but no VHD/VHDX payload was visible in the scanned directory depth.",
            "Locate or finish downloading the backup disk-image files before attempting a restore.",
        )
    } else {
        (
            "directory_unknown",
            "low",
            "This directory does not yet look like a supported Windows recovery source.",
            "Choose the Windows backup root, Windows ISO/extracted media, WinRE folder, or a VHD/VHDX image.",
        )
    };

    let mut warnings = Vec::new();
    if !restore_candidate {
        warnings.push("directory does not contain a verified restore payload".to_string());
    }
    if system_image.scan_limited {
        warnings.push(format!(
            "system-image discovery stopped after {MAX_SYSTEM_IMAGE_SCAN_ENTRIES} entries or depth {MAX_SYSTEM_IMAGE_SCAN_DEPTH}; choose a more specific backup folder for a complete analysis"
        ));
    }
    if has_windows_image_backup && !system_image_restore_ready {
        warnings.push(
            "system-image metadata is present but the VHD/VHDX payload is not visible yet".to_string(),
        );
    }

    WindowsBackupAnalysis {
        schema: "phoenix_key.windows_backup_analysis.v2",
        path: path.to_string_lossy().to_string(),
        kind: kind.to_string(),
        confidence: confidence.to_string(),
        user_summary: user_summary.to_string(),
        recommended_action: recommended_action.to_string(),
        size_bytes: None,
        detected_by,
        has_boot_wim,
        has_install_wim,
        has_install_esd,
        has_split_wim,
        has_winre,
        has_efi,
        has_bcd,
        has_setup_exe,
        has_windows_image_backup,
        system_image_files: system_image.image_files,
        restore_candidate,
        destructive_actions_performed: false,
        warnings,
    }
}

fn detect_file(path: &Path) -> Result<WindowsBackupAnalysis, String> {
    let metadata = path
        .metadata()
        .map_err(|error| format!("cannot inspect backup source: {error}"))?;
    let prefix = read_prefix(path, 0x9000)?;
    let tail = read_tail(path, 4096)?;

    let wim = prefix.starts_with(b"MSWIM\0\0\0");
    let vhdx = prefix.starts_with(b"vhdxfile");
    let vhd = contains_case_insensitive(&tail, b"conectix");
    let iso = prefix
        .get(0x8001..0x8006)
        .is_some_and(|signature| signature == b"CD001");

    let extension = path
        .extension()
        .and_then(|value| value.to_str())
        .unwrap_or("")
        .to_ascii_lowercase();

    let (kind, detected_by, restore_candidate, confidence, summary, recommendation) = if wim {
        (
            if extension == "esd" { "esd" } else { "wim" },
            vec!["MSWIM signature".to_string()],
            true,
            "high",
            "A Windows Imaging Format payload was verified by file signature.",
            "Inspect image metadata and indexes before selecting a restore or recovery-media workflow.",
        )
    } else if vhdx {
        (
            "vhdx",
            vec!["vhdxfile signature".to_string()],
            true,
            "high",
            "A VHDX virtual disk image was verified by file signature.",
            "Inspect partitions and Windows contents read-only before planning any restore target.",
        )
    } else if vhd {
        (
            "vhd",
            vec!["conectix footer".to_string()],
            true,
            "high",
            "A legacy VHD virtual disk image was verified by footer signature.",
            "Inspect partitions and Windows contents read-only before planning any restore target.",
        )
    } else if iso {
        (
            "iso",
            vec!["ISO9660 CD001 descriptor".to_string()],
            true,
            "high",
            "A bootable-disc style ISO image was verified by ISO9660 signature.",
            "Inspect the ISO contents before deciding whether it is Windows installation or recovery media.",
        )
    } else if extension == "ffu" {
        (
            "ffu_unverified",
            vec!["filename extension only".to_string()],
            false,
            "low",
            "The file is named like an FFU image, but Phoenix Key has not verified its internal format.",
            "Do not restore it yet; add or use FFU signature validation first.",
        )
    } else if extension == "swm" {
        (
            "split_wim_unverified",
            vec!["filename extension only".to_string()],
            false,
            "low",
            "The file is named like one piece of a split WIM set, but the complete set has not been verified.",
            "Select the directory containing every SWM segment and verify the complete set.",
        )
    } else {
        (
            "file_unknown",
            Vec::new(),
            false,
            "low",
            "The file does not match a currently supported Windows recovery signature.",
            "Choose a Windows ISO, WIM/ESD, VHD/VHDX, WinRE tree, or WindowsImageBackup folder.",
        )
    };

    let warnings = match kind {
        "ffu_unverified" | "split_wim_unverified" => vec![
            "format was not accepted as restore-ready because only the filename extension matched"
                .to_string(),
        ],
        "file_unknown" => vec!["file signature is not recognized".to_string()],
        _ => Vec::new(),
    };

    Ok(WindowsBackupAnalysis {
        schema: "phoenix_key.windows_backup_analysis.v2",
        path: path.to_string_lossy().to_string(),
        kind: kind.to_string(),
        confidence: confidence.to_string(),
        user_summary: summary.to_string(),
        recommended_action: recommendation.to_string(),
        size_bytes: Some(metadata.len()),
        detected_by,
        has_boot_wim: false,
        has_install_wim: wim && extension == "wim",
        has_install_esd: wim && extension == "esd",
        has_split_wim: false,
        has_winre: false,
        has_efi: false,
        has_bcd: false,
        has_setup_exe: false,
        has_windows_image_backup: false,
        system_image_files: Vec::new(),
        restore_candidate,
        destructive_actions_performed: false,
        warnings,
    })
}

pub fn analyze_backup_path(path: impl AsRef<Path>) -> Result<WindowsBackupAnalysis, String> {
    let path = path.as_ref();
    if !path.exists() {
        return Err("backup source does not exist".to_string());
    }
    if path.is_dir() {
        Ok(detect_directory(path))
    } else if path.is_file() {
        detect_file(path)
    } else {
        Err("backup source is neither a regular file nor a directory".to_string())
    }
}

pub fn build_recovery_plan(path: impl AsRef<Path>) -> Result<WindowsRecoveryPlan, String> {
    let source = analyze_backup_path(path)?;
    let host_arch = std::env::consts::ARCH.to_string();
    let host_os = std::env::consts::OS.to_string();
    let apple_silicon = host_os == "macos" && matches!(host_arch.as_str(), "aarch64" | "arm64");
    let traditional_bootcamp_supported =
        host_os == "macos" && !apple_silicon && host_arch == "x86_64";

    let (host_route, host_explanation) = if apple_silicon {
        (
            "apple_silicon_windows_arm",
            "Apple Silicon does not support traditional Boot Camp. Phoenix Key must route this Mac to Windows ARM recovery media, VHDX inspection, or a virtual-machine workflow.",
        )
    } else if traditional_bootcamp_supported {
        (
            "intel_mac_bootcamp",
            "This Intel Mac can be evaluated for traditional Boot Camp repair or restore after model, partition-map, free-space, and firmware checks pass.",
        )
    } else if host_os == "windows" {
        (
            "windows_native_recovery",
            "Phoenix Key is running on Windows and can analyze recovery sources natively; destructive restore operations remain separately gated.",
        )
    } else {
        (
            "cross_platform_analysis",
            "This host can analyze and prepare recovery sources, but machine-specific Windows restore operations require an explicitly supported target workflow.",
        )
    };

    let mut allowed_operations = vec![
        "inspect_backup".to_string(),
        "generate_recovery_report".to_string(),
        "verify_source_integrity".to_string(),
    ];
    let mut blocked_operations = Vec::new();
    let mut next_steps = vec![
        "Verify the source checksum or backup integrity before any target is selected.".to_string(),
        "Keep backup source and restore target as separate devices whenever possible.".to_string(),
    ];

    if source.restore_candidate {
        allowed_operations.push("plan_recovery_media".to_string());
        next_steps.push("Inspect the candidate payload read-only and identify its Windows edition, architecture, partitions, and boot files.".to_string());
    } else {
        blocked_operations.push("restore_source_not_verified".to_string());
        next_steps.push("Resolve every source warning before enabling restore planning.".to_string());
    }

    if source.kind == "windows_system_image_backup" {
        allowed_operations.push("plan_system_image_restore".to_string());
        next_steps.push("Match the backup's partition layout and boot mode to the intended target before creating a restore contract.".to_string());
    }

    if traditional_bootcamp_supported {
        allowed_operations.push("plan_bootcamp_repair".to_string());
        allowed_operations.push("plan_bootcamp_restore".to_string());
        next_steps.push("Identify the exact Intel Mac model and Boot Camp driver package before restore execution is considered.".to_string());
    } else {
        blocked_operations.push("traditional_bootcamp_restore".to_string());
    }

    if apple_silicon {
        allowed_operations.push("plan_windows_arm_recovery_media".to_string());
        allowed_operations.push("plan_vhdx_vm_recovery".to_string());
        next_steps.push("Do not create or label an internal partition as Boot Camp on Apple Silicon.".to_string());
    }

    let restore_action_status = if source.restore_candidate {
        "blocked_executor_unavailable"
    } else {
        "blocked_source_not_verified"
    };

    let mut remediation_required = Vec::new();
    if source.has_install_esd {
        remediation_required.push(
            "ESD sources must remain intact; Phoenix Key will not invent an unsupported ESD-to-WIM conversion."
                .to_string(),
        );
    }
    if source.has_split_wim {
        remediation_required.push(
            "Verify the complete contiguous SWM segment set before any media or restore workflow."
                .to_string(),
        );
    }
    if !source.restore_candidate {
        remediation_required.push(
            "Resolve source verification warnings before target selection is allowed.".to_string(),
        );
    }

    let mut block_reasons = vec![
        "restore_executor_not_available".to_string(),
        "target_not_selected".to_string(),
        "target_identity_not_verified".to_string(),
        "rollback_evidence_not_persisted".to_string(),
        "destructive_authorization_not_present".to_string(),
    ];
    if !source.restore_candidate {
        block_reasons.push("source_not_verified_for_restore".to_string());
    }

    let expected_boot_files = if source.has_efi || source.has_bcd {
        vec![
            r"EFI\Microsoft\Boot\bootmgfw.efi".to_string(),
            r"EFI\Microsoft\Boot\BCD".to_string(),
        ]
    } else {
        vec![
            r"EFI\Microsoft\Boot\bootmgfw.efi".to_string(),
            r"EFI\Boot\bootx64.efi".to_string(),
        ]
    };

    let source_contract = RecoverySourceContract {
        source_kind: source.kind.clone(),
        restore_candidate: source.restore_candidate,
        content_identity_required: true,
        metadata_validation_required: true,
        complete_split_set_required: source.has_split_wim,
        fat32_single_file_limit_check_required: source.has_install_wim || source.has_install_esd,
    };
    let dry_run_summary = RecoveryDryRunSummary {
        source_ready_for_planning: source.restore_candidate,
        target_selected: false,
        target_identity_verified: false,
        rollback_evidence_persisted: false,
        destructive_authorization_present: false,
        mutation_steps_planned: 1,
        mutation_steps_executed: 0,
        executable: false,
    };

    Ok(WindowsRecoveryPlan {
        schema: "phoenix_key.windows_recovery_plan.v4",
        source,
        host_arch,
        host_os,
        host_route: host_route.to_string(),
        host_explanation: host_explanation.to_string(),
        traditional_bootcamp_supported,
        allowed_operations,
        blocked_operations,
        required_gates: vec![
            "source_integrity".to_string(),
            "source_architecture_and_edition".to_string(),
            "fresh_device_enumeration".to_string(),
            "target_identity".to_string(),
            "target_not_source".to_string(),
            "free_space".to_string(),
            "partition_manifest".to_string(),
            "efi_and_boot_mode_compatibility".to_string(),
            "rollback_manifest".to_string(),
            "explicit_destructive_authorization".to_string(),
            "fresh_prewrite_identity_recheck".to_string(),
        ],
        proposed_actions: vec![
            RecoveryPlanAction {
                id: "inspect_source",
                phase: "analysis",
                mutates_system: false,
                requires_authorization: false,
                status: "complete",
            },
            RecoveryPlanAction {
                id: "verify_source_integrity",
                phase: "validation",
                mutates_system: false,
                requires_authorization: false,
                status: "required",
            },
            RecoveryPlanAction {
                id: "verify_target_identity",
                phase: "target_validation",
                mutates_system: false,
                requires_authorization: false,
                status: "required",
            },
            RecoveryPlanAction {
                id: "capture_rollback_evidence",
                phase: "rollback",
                mutates_system: false,
                requires_authorization: false,
                status: "required",
            },
            RecoveryPlanAction {
                id: "restore_execution",
                phase: "execution",
                mutates_system: true,
                requires_authorization: true,
                status: restore_action_status,
            },
        ],
        target_contract: RecoveryTargetContract {
            snapshot_identity_required: true,
            stable_identity_required: true,
            source_target_separation_required: true,
            capacity_check_required: true,
            fresh_revalidation_required: true,
        },
        execution_boundary: RecoveryExecutionBoundary {
            planner_only: true,
            restore_executor_available: false,
            destructive_authorization_required: true,
            automatic_destructive_resume_allowed: false,
            system_mutations_performed: false,
        },
        source_contract,
        boot_contract: RecoveryBootContract {
            boot_mode: "uefi",
            efi_files_required: true,
            bcd_required: true,
            partition_manifest_required: true,
            expected_boot_files,
            expected_partition_roles: vec![
                "efi_system_partition".to_string(),
                "windows_os_partition".to_string(),
                "recovery_partition_if_present".to_string(),
            ],
        },
        remediation_required,
        block_reasons,
        dry_run_summary,
        next_steps,
        dry_run: true,
        destructive_actions_performed: false,
    })
}

pub fn fixture_candidates(root: impl AsRef<Path>) -> Result<Vec<PathBuf>, String> {
    let root = root.as_ref();
    if !root.is_dir() {
        return Err("fixture root is not a directory".to_string());
    }
    let mut candidates = Vec::new();
    for entry in fs::read_dir(root).map_err(|error| format!("cannot read fixture root: {error}"))? {
        let entry = entry.map_err(|error| format!("cannot read fixture entry: {error}"))?;
        let path = entry.path();
        if path.is_dir() {
            let analysis = detect_directory(&path);
            if analysis.restore_candidate
                || analysis.has_efi
                || analysis.has_bcd
                || analysis.has_windows_image_backup
            {
                candidates.push(path);
            }
        } else if path.is_file() {
            let extension = path
                .extension()
                .and_then(|value| value.to_str())
                .unwrap_or("")
                .to_ascii_lowercase();
            if matches!(
                extension.as_str(),
                "iso" | "wim" | "esd" | "swm" | "vhd" | "vhdx" | "ffu"
            ) {
                candidates.push(path);
            }
        }
    }
    candidates.sort();
    Ok(candidates)
}

#[cfg(test)]
mod tests {
    use super::{analyze_backup_path, build_recovery_plan};
    use std::{fs, io::Write};

    fn temp_case(name: &str) -> std::path::PathBuf {
        let path = std::env::temp_dir().join(format!(
            "phoenix-key-windows-recovery-{name}-{}",
            std::process::id()
        ));
        let _ = fs::remove_dir_all(&path);
        fs::create_dir_all(&path).unwrap();
        path
    }

    #[test]
    fn detects_wim_by_signature_not_extension() {
        let root = temp_case("wim");
        let path = root.join("backup.bin");
        fs::write(&path, b"MSWIM\0\0\0fixture").unwrap();
        let analysis = analyze_backup_path(&path).unwrap();
        assert_eq!(analysis.kind, "wim");
        assert_eq!(analysis.confidence, "high");
        assert!(analysis.restore_candidate);
        assert_eq!(analysis.detected_by, vec!["MSWIM signature"]);
        assert!(!analysis.destructive_actions_performed);
        fs::remove_dir_all(root).unwrap();
    }

    #[test]
    fn rejects_extension_only_ffu_as_restore_ready() {
        let root = temp_case("ffu");
        let path = root.join("backup.ffu");
        fs::write(&path, b"not-an-ffu").unwrap();
        let analysis = analyze_backup_path(&path).unwrap();
        assert_eq!(analysis.kind, "ffu_unverified");
        assert_eq!(analysis.confidence, "low");
        assert!(!analysis.restore_candidate);
        fs::remove_dir_all(root).unwrap();
    }

    #[test]
    fn detects_extracted_windows_tree() {
        let root = temp_case("tree");
        fs::create_dir_all(root.join("sources")).unwrap();
        fs::create_dir_all(root.join("EFI/Microsoft/Boot")).unwrap();
        fs::write(root.join("sources/install.wim"), b"fixture").unwrap();
        fs::write(root.join("sources/boot.wim"), b"fixture").unwrap();
        fs::write(root.join("setup.exe"), b"fixture").unwrap();
        fs::write(root.join("EFI/Microsoft/Boot/BCD"), b"fixture").unwrap();

        let analysis = analyze_backup_path(&root).unwrap();
        assert_eq!(analysis.kind, "extracted_windows_media");
        assert!(analysis.has_install_wim);
        assert!(analysis.has_boot_wim);
        assert!(analysis.has_setup_exe);
        assert!(analysis.has_efi);
        assert!(analysis.has_bcd);
        assert!(analysis.restore_candidate);
        fs::remove_dir_all(root).unwrap();
    }

    #[test]
    fn detects_windows_image_backup_with_vhdx_payload() {
        let parent = temp_case("system-image");
        let root = parent.join("WindowsImageBackup");
        let backup = root
            .join("BJ-PC")
            .join("Backup 2025-02-13 104757");
        fs::create_dir_all(root.join("BJ-PC/Catalog")).unwrap();
        fs::create_dir_all(&backup).unwrap();
        fs::write(root.join("BJ-PC/MediaId.bin"), b"fixture").unwrap();
        fs::write(backup.join("BackupSpecs.xml"), b"fixture").unwrap();
        fs::write(backup.join("system.vhdx"), b"vhdxfilefixture").unwrap();

        let analysis = analyze_backup_path(&root).unwrap();
        assert_eq!(analysis.kind, "windows_system_image_backup");
        assert_eq!(analysis.confidence, "high");
        assert!(analysis.has_windows_image_backup);
        assert!(analysis.restore_candidate);
        assert_eq!(analysis.system_image_files.len(), 1);
        assert!(analysis.system_image_files[0].ends_with("system.vhdx"));
        fs::remove_dir_all(parent).unwrap();
    }

    #[test]
    fn system_image_metadata_without_virtual_disk_stays_blocked() {
        let parent = temp_case("system-image-incomplete");
        let root = parent.join("WindowsImageBackup");
        fs::create_dir_all(root.join("BJ-PC/Catalog")).unwrap();
        fs::write(root.join("BJ-PC/MediaId.bin"), b"fixture").unwrap();

        let analysis = analyze_backup_path(&root).unwrap();
        assert_eq!(
            analysis.kind,
            "windows_system_image_structure_incomplete"
        );
        assert!(analysis.has_windows_image_backup);
        assert!(!analysis.restore_candidate);
        assert!(!analysis.warnings.is_empty());
        fs::remove_dir_all(parent).unwrap();
    }

    #[test]
    fn recovery_plan_is_always_dry_run_and_non_destructive() {
        let root = temp_case("plan");
        let path = root.join("fixture.wim");
        let mut file = fs::File::create(&path).unwrap();
        file.write_all(b"MSWIM\0\0\0fixture").unwrap();
        let plan = build_recovery_plan(&path).unwrap();
        assert!(plan.dry_run);
        assert!(!plan.destructive_actions_performed);
        assert!(plan
            .required_gates
            .contains(&"fresh_prewrite_identity_recheck".to_string()));
        assert!(plan
            .required_gates
            .contains(&"target_not_source".to_string()));
        assert!(!plan.host_route.is_empty());
        assert_eq!(plan.schema, "phoenix_key.windows_recovery_plan.v4");
        assert!(plan.target_contract.stable_identity_required);
        assert!(plan.target_contract.fresh_revalidation_required);
        assert!(plan.execution_boundary.planner_only);
        assert!(!plan.execution_boundary.restore_executor_available);
        assert!(!plan.execution_boundary.automatic_destructive_resume_allowed);
        assert!(plan.source_contract.content_identity_required);
        assert!(plan.source_contract.metadata_validation_required);
        assert_eq!(plan.boot_contract.boot_mode, "uefi");
        assert!(plan.boot_contract.efi_files_required);
        assert!(plan.boot_contract.bcd_required);
        assert!(!plan.dry_run_summary.executable);
        assert_eq!(plan.dry_run_summary.mutation_steps_planned, 1);
        assert_eq!(plan.dry_run_summary.mutation_steps_executed, 0);
        assert!(plan.block_reasons.contains(&"target_not_selected".to_string()));
        assert!(plan
            .block_reasons
            .contains(&"restore_executor_not_available".to_string()));
        let restore = plan
            .proposed_actions
            .iter()
            .find(|action| action.id == "restore_execution")
            .expect("restore execution boundary must be explicit");
        assert!(restore.mutates_system);
        assert!(restore.requires_authorization);
        assert_eq!(restore.status, "blocked_executor_unavailable");
        fs::remove_dir_all(root).unwrap();
    }
}
