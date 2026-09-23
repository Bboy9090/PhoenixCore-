import React, { useEffect, useMemo, useState } from "react";
import { invoke } from "@tauri-apps/api/tauri";
import { open } from "@tauri-apps/api/dialog";
import "./recovery-center.css";

type DistributionProfile = {
  store_safe: boolean;
  external_helper_execution: boolean;
  cloud_acquisition: boolean;
  native_recovery_analysis: boolean;
};

type RecoveryAnalysis = {
  schema: string;
  path: string;
  kind: string;
  confidence: string;
  user_summary: string;
  recommended_action: string;
  restore_candidate: boolean;
  has_windows_image_backup: boolean;
  system_image_files: string[];
  metadata_image_files: string[];
  warnings: string[];
  detected_by: string[];
};

type SourceIdentity = {
  sha256: string;
  size_bytes: number;
  source_kind: string;
  complete: boolean;
};

type SourceIdentityVerification = {
  schema: string;
  expected_sha256: string;
  observed_sha256: string;
  matches: boolean;
  reanalysis_required: boolean;
};

type PackageTrust = {
  verified_for_use: boolean;
  observed_sha256: string;
  expected_sha256: string | null;
  sha256_matches: boolean;
  trust_route: string;
  block_reasons: string[];
  authenticode?: {
    checked: boolean;
    status: string;
    signer_subject?: string | null;
  };
};

type WindowsImage = {
  index: number;
  name?: string | null;
  architecture?: string | null;
  edition_id?: string | null;
  metadata_complete: boolean;
};

type ImageMetadata = {
  metadata_verified: boolean;
  selected_index: number | null;
  selected_image?: WindowsImage | null;
  images: WindowsImage[];
  selection_required: boolean;
  restore_eligible: boolean;
  block_reasons: string[];
  architecture_compatibility?: {
    source_architecture?: string | null;
    target_architecture?: string | null;
    compatible: boolean;
    block_reasons: string[];
  };
};

type GoogleDrivePickerStatus = {
  configured: boolean;
  scope: string;
  selection_mode: string;
  system_browser_required: boolean;
  oauth_token_persisted: boolean;
  cloud_mutation_allowed: boolean;
};

type GoogleDriveProgress = {
  phase: string;
  downloaded_size_bytes: number;
  provider_size_bytes: number;
  resume_offset_bytes: number;
  percent: number;
  cancel_requested?: boolean;
};

type GoogleDriveReceipt = {
  provider_name?: string;
  provider_size_bytes?: number;
  observed_sha256?: string;
  staged_path?: string | null;
  partial_path?: string | null;
  downloaded_size_bytes?: number;
  cancelled?: boolean;
  complete?: boolean;
  identity_lock_verified?: boolean;
  authorization_scope: string;
  selection_mode: string;
  oauth_token_persisted: boolean;
  oauth_token_exposed_to_ui: boolean;
  recovery_eligible: boolean;
  block_reasons: string[];
};

type Fat32MediaPlan = {
  filesystem: string;
  uefi_boot_files: string[];
  uefi_boot_evidence_present: boolean;
  image_mode: string;
  fat32_max_file_bytes: number;
  split_size_mb: number;
  split_required: boolean;
  split_command_preview?: string[] | null;
  split_segments: Array<{
    name: string;
    size_bytes: number;
    wim_header_valid: boolean;
    fat32_size_safe: boolean;
  }>;
  oversized_files: Array<{ path: string; size_bytes: number }>;
  unsupported_oversized_files: Array<{ path: string; size_bytes: number }>;
  ready_for_fat32_copy_now: boolean;
  ready_for_fat32_copy_after_split: boolean;
  block_reasons: string[];
  source_modified: boolean;
  target_disk_modified: boolean;
  execution_performed: boolean;
};

type RecoveryTargetSafety = {
  safe_to_prepare: boolean;
  target?: string | null;
  target_identity_sha256?: string | null;
  target_stable_identity_sha256?: string | null;
  target_size_bytes?: number | null;
  source_size_bytes: number;
  source_physical_target?: string | null;
  source_physical_identity_sha256?: string | null;
  source_target_distinct?: boolean | null;
  block_reasons: string[];
};

type RecoveryTargetIdentityVerification = {
  expected_snapshot_identity_sha256: string;
  observed_snapshot_identity_sha256?: string | null;
  expected_stable_identity_sha256: string;
  observed_stable_identity_sha256?: string | null;
  snapshot_matches: boolean;
  stable_identity_matches: boolean;
  matches: boolean;
  classification: string;
  reanalysis_required: boolean;
  system_mutations_performed: boolean;
};

type RecoveryTargetReenumerationReceipt = {
  schema: string;
  expected_target?: string | null;
  observed_target?: string | null;
  expected_snapshot_identity_sha256: string;
  observed_snapshot_identity_sha256?: string | null;
  expected_stable_identity_sha256: string;
  observed_stable_identity_sha256?: string | null;
  same_stable_hardware: boolean;
  snapshot_changed: boolean;
  target_path_changed: boolean;
  stale_authorization_rejected: boolean;
  reanalysis_required: boolean;
  substitution_detected: boolean;
  classification: string;
  system_mutations_performed: boolean;
  receipt_sha256: string;
  receipt_path?: string | null;
  receipt_persisted?: boolean;
};

type StableTargetLocatorResult = {
  schema: string;
  expected_stable_identity_sha256: string;
  classification: string;
  unique_match: boolean;
  ambiguous: boolean;
  match_count: number;
  match?: {
    target: string;
    disk_number: number;
    friendly_name?: string | null;
    serial_number?: string | null;
    unique_id?: string | null;
    bus_type: string;
    size_bytes: number;
    identity_sha256: string;
    stable_identity_sha256?: string | null;
    is_boot: boolean;
    is_system: boolean;
    write_candidate: boolean;
    write_block_reasons: string[];
  } | null;
  read_only: boolean;
  system_mutations_performed: boolean;
};

type RestoreRollbackContract = {
  schema: string;
  source_identity_sha256: string;
  target_identity_sha256: string;
  target_stable_identity_sha256: string;
  target_size_bytes: number;
  required_artifacts: string[];
  artifact_destination_requirement: string;
  fresh_target_revalidation_required: boolean;
  restore_unlock_ready: boolean;
  restore_unlock_scope: string[];
  always_blocked_by_this_contract: string[];
  system_mutations_performed: boolean;
  contract_sha256: string;
};

type RestoreHardwarePreflight = {
  schema: string;
  ready_to_capture_hardware_rollback_evidence: boolean;
  executable: boolean;
  satisfied_gates: string[];
  blocked_gates: string[];
  required_hardware_evidence: string[];
  source_identity_sha256?: string | null;
  image_path?: string | null;
  target_identity_sha256?: string | null;
  target_stable_identity_sha256?: string | null;
  rollback_contract_sha256?: string | null;
  system_mutations_performed: boolean;
};

type RollbackDestinationVerification = {
  schema: string;
  target?: string | null;
  target_snapshot_identity_sha256?: string | null;
  target_stable_identity_sha256?: string | null;
  expected_target_stable_identity_sha256: string;
  destination_path: string;
  destination_physical_target?: string | null;
  destination_stable_identity_sha256?: string | null;
  target_identity_matches_expected: boolean;
  separate_physical_device: boolean;
  ready_for_hardware_rollback_capture: boolean;
  block_reasons: string[];
  system_mutations_performed: boolean;
};

type RestoreRollbackCaptureReceipt = {
  schema: string;
  target: string;
  target_snapshot_identity_sha256: string;
  target_stable_identity_sha256: string;
  rollback_destination_stable_identity_sha256: string;
  rollback_contract_sha256: string;
  output_directory: string;
  captured_requirements: string[];
  remaining_requirements: string[];
  artifacts: Record<string, {
    path: string;
    size_bytes: number;
    sha256: string;
  }>;
  partition_manifest_sha256: string;
  restore_unlock_ready: boolean;
  restore_unlock_scope: string[];
  always_blocked_by_this_capture: string[];
  target_bytes_written: number;
  target_write_attempted: boolean;
  rollback_destination_files_written: boolean;
  system_mutations_performed: boolean;
  receipt_sha256: string;
};

type RecoveryEvidenceBundleV2 = {
  schema: string;
  source_identity_sha256?: string | null;
  target_identity_sha256?: string | null;
  target_stable_identity_sha256?: string | null;
  rollback_contract_sha256?: string | null;
  components: Record<string, {
    present: boolean;
    schema?: string | null;
    sha256?: string | null;
    trusted: boolean;
  }>;
  software_chain_complete: boolean;
  hardware_chain_complete: boolean;
  data_preservation_resolved: boolean;
  boot_metadata_resolved: boolean;
  outstanding_requirements: string[];
  restore_executable: boolean;
  system_mutations_performed: boolean;
  bundle_sha256: string;
};

type TargetDataPreservationReceipt = {
  schema: string;
  mode: string;
  target_stable_identity_sha256: string;
  rollback_contract_sha256: string;
  acknowledgement: string;
  resolved: boolean;
  block_reasons: string[];
  required_next_evidence: string[];
  restore_unlock_ready: boolean;
  system_mutations_performed: boolean;
  receipt_sha256: string;
};

type RecoverySessionStateV1 = {
  schema: string;
  session_id: string;
  phase: string;
  bundle_sha256: string;
  source_identity_sha256?: string | null;
  target_stable_identity_sha256?: string | null;
  rollback_contract_sha256?: string | null;
  software_chain_complete: boolean;
  hardware_chain_complete: boolean;
  stale_evidence_detected: boolean;
  hardware_substitution_detected: boolean;
  read_only_resume_allowed: boolean;
  automatic_destructive_resume_allowed: boolean;
  restore_executable: boolean;
  next_required_actions: string[];
  system_mutations_performed: boolean;
  state_sha256: string;
  session_path?: string | null;
  session_persisted?: boolean;
  destructive_authorization_persisted?: boolean;
};

type RecoveryDiagnosticsExportV1 = {
  schema: string;
  evidence_bundle: RecoveryEvidenceBundleV2;
  session_state: RecoverySessionStateV1;
  sanitized_evidence: Record<string, unknown>;
  redacted_fields: string[];
  destructive_authorization_included: boolean;
  restore_executable: boolean;
  system_mutations_performed: boolean;
  export_sha256: string;
  export_path?: string | null;
  export_persisted?: boolean;
};

type RestoreTargetBootMetadataReceipt = {
  schema: string;
  target: string;
  target_snapshot_identity_sha256: string;
  target_stable_identity_sha256: string;
  rollback_contract_sha256: string;
  rollback_capture_receipt_sha256: string;
  output_directory: string;
  partition_inventory: Array<{
    partition_number: number;
    gpt_type?: string | null;
    role: string;
    drive_letter?: string | null;
    offset_bytes: number;
    size_bytes: number;
    already_accessible: boolean;
  }>;
  artifacts: Record<string, unknown>;
  resolved: boolean;
  missing_or_unverified: string[];
  restore_unlock_ready: boolean;
  target_bytes_written: number;
  target_write_attempted: boolean;
  partition_mount_or_assignment_attempted: boolean;
  system_mutations_performed: boolean;
  receipt_sha256: string;
};

type RecoveryPlan = {
  schema: string;
  source: RecoveryAnalysis;
  host_arch: string;
  host_os: string;
  host_route: string;
  host_explanation: string;
  traditional_bootcamp_supported: boolean;
  allowed_operations: string[];
  blocked_operations: string[];
  required_gates: string[];
  proposed_actions: Array<{
    id: string;
    phase: string;
    mutates_system: boolean;
    requires_authorization: boolean;
    status: string;
  }>;
  target_contract: {
    snapshot_identity_required: boolean;
    stable_identity_required: boolean;
    source_target_separation_required: boolean;
    capacity_check_required: boolean;
    fresh_revalidation_required: boolean;
  };
  execution_boundary: {
    planner_only: boolean;
    restore_executor_available: boolean;
    destructive_authorization_required: boolean;
    automatic_destructive_resume_allowed: boolean;
    system_mutations_performed: boolean;
  };
  source_contract: {
    source_kind: string;
    restore_candidate: boolean;
    content_identity_required: boolean;
    metadata_validation_required: boolean;
    complete_split_set_required: boolean;
    fat32_single_file_limit_check_required: boolean;
  };
  boot_contract: {
    boot_mode: string;
    efi_files_required: boolean;
    bcd_required: boolean;
    partition_manifest_required: boolean;
    expected_boot_files: string[];
    expected_partition_roles: string[];
  };
  remediation_required: string[];
  block_reasons: string[];
  dry_run_summary: {
    source_ready_for_planning: boolean;
    target_selected: boolean;
    target_identity_verified: boolean;
    rollback_evidence_persisted: boolean;
    destructive_authorization_present: boolean;
    mutation_steps_planned: number;
    mutation_steps_executed: number;
    executable: boolean;
  };
  next_steps: string[];
  dry_run: boolean;
  destructive_actions_performed: boolean;
  source_identity?: SourceIdentity;
  source_identity_gate?: string;
  plan_sha256?: string;
};

const isDesktopRuntime = () => "__TAURI__" in window;

const friendlyKind: Record<string, string> = {
  windows_system_image_backup: "Windows system-image backup",
  windows_system_image_structure_incomplete: "Incomplete Windows system-image backup",
  extracted_windows_media: "Extracted Windows installer",
  windows_recovery_tree: "Windows Recovery Environment",
  iso: "Windows disc image / ISO candidate",
  wim: "Windows image (WIM)",
  esd: "Windows image (ESD)",
  vhd: "Windows virtual disk (VHD)",
  vhdx: "Windows virtual disk (VHDX)",
  ffu_unverified: "Unverified FFU file",
  split_wim_unverified: "Unverified split WIM segment",
  file_unknown: "Unknown file",
  directory_unknown: "Unknown folder",
};

const friendlyOperation: Record<string, string> = {
  inspect_backup: "Inspect the backup",
  generate_recovery_report: "Create a recovery report",
  verify_source_integrity: "Verify source integrity",
  plan_recovery_media: "Plan recovery media",
  plan_system_image_restore: "Plan an exact system-image restore",
  plan_bootcamp_repair: "Plan an Intel Mac Boot Camp repair",
  plan_bootcamp_restore: "Plan an Intel Mac Boot Camp restore",
  plan_windows_arm_recovery_media: "Plan Windows ARM recovery media",
  plan_vhdx_vm_recovery: "Plan VHDX / virtual-machine recovery",
};

function readableToken(value: string) {
  return friendlyOperation[value] || value.split("_").join(" ");
}

function joinRecoveryPath(root: string, relative: string) {
  const separator = root.includes("\\") ? "\\" : "/";
  const cleanRoot = root.replace(/[\\/]+$/, "");
  const cleanRelative = relative.replace(/^[\\/]+/, "").replace(/[\\/]+/g, separator);
  return `${cleanRoot}${separator}${cleanRelative}`;
}

function metadataImagePathForAnalysis(root: string, analysis: RecoveryAnalysis) {
  const candidates = analysis.metadata_image_files ?? [];
  if (candidates.length === 1) {
    return joinRecoveryPath(root, candidates[0]);
  }
  if (candidates.length > 1) {
    return "";
  }
  if (["wim", "esd", "vhd", "vhdx", "iso"].includes(analysis.kind)) {
    return root;
  }
  return "";
}

export default function RecoveryCenter({
  distributionProfile,
}: {
  distributionProfile: DistributionProfile | null;
}) {
  const [sourcePath, setSourcePath] = useState("");
  const [analysis, setAnalysis] = useState<RecoveryAnalysis | null>(null);
  const [plan, setPlan] = useState<RecoveryPlan | null>(null);
  const [sourceVerification, setSourceVerification] = useState<SourceIdentityVerification | null>(null);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState(
    "Choose the Windows backup or recovery source you want Phoenix Key to inspect. Analysis does not change disks.",
  );
  const [showTechnical, setShowTechnical] = useState(false);
  const [expectedSha256, setExpectedSha256] = useState("");
  const [selectedImageIndex, setSelectedImageIndex] = useState("");
  const [imagePath, setImagePath] = useState("");
  const [targetArchitecture, setTargetArchitecture] = useState("");
  const [packageTrust, setPackageTrust] = useState<PackageTrust | null>(null);
  const [imageMetadata, setImageMetadata] = useState<ImageMetadata | null>(null);
  const [targetDrive, setTargetDrive] = useState("");
  const [targetSafety, setTargetSafety] = useState<RecoveryTargetSafety | null>(null);
  const [targetVerification, setTargetVerification] = useState<RecoveryTargetIdentityVerification | null>(null);
  const [reenumeratedTargetDrive, setReenumeratedTargetDrive] = useState("");
  const [stableTargetLocator, setStableTargetLocator] = useState<StableTargetLocatorResult | null>(null);
  const [targetReenumerationReceipt, setTargetReenumerationReceipt] = useState<RecoveryTargetReenumerationReceipt | null>(null);
  const [restoreRollbackContract, setRestoreRollbackContract] = useState<RestoreRollbackContract | null>(null);
  const [restoreHardwarePreflight, setRestoreHardwarePreflight] = useState<RestoreHardwarePreflight | null>(null);
  const [rollbackDestinationPath, setRollbackDestinationPath] = useState("");
  const [rollbackDestinationVerification, setRollbackDestinationVerification] = useState<RollbackDestinationVerification | null>(null);
  const [rollbackCaptureReceipt, setRollbackCaptureReceipt] = useState<RestoreRollbackCaptureReceipt | null>(null);
  const [dataPreservationMode, setDataPreservationMode] = useState("preserve_existing_data");
  const [dataPreservationAcknowledgement, setDataPreservationAcknowledgement] = useState("");
  const [dataPreservationReceipt, setDataPreservationReceipt] = useState<TargetDataPreservationReceipt | null>(null);
  const [bootMetadataReceipt, setBootMetadataReceipt] = useState<RestoreTargetBootMetadataReceipt | null>(null);
  const [recoveryEvidenceBundle, setRecoveryEvidenceBundle] = useState<RecoveryEvidenceBundleV2 | null>(null);
  const [recoverySessionState, setRecoverySessionState] = useState<RecoverySessionStateV1 | null>(null);
  const [recoveryDiagnosticsExport, setRecoveryDiagnosticsExport] = useState<RecoveryDiagnosticsExportV1 | null>(null);
  const [drivePickerStatus, setDrivePickerStatus] = useState<GoogleDrivePickerStatus | null>(null);
  const [driveReceipt, setDriveReceipt] = useState<GoogleDriveReceipt | null>(null);
  const [driveOperationId, setDriveOperationId] = useState<string | null>(null);
  const [driveProgress, setDriveProgress] = useState<GoogleDriveProgress | null>(null);
  const [fat32MediaPlan, setFat32MediaPlan] = useState<Fat32MediaPlan | null>(null);
  const storeSafe = distributionProfile?.store_safe === true;

  useEffect(() => {
    if (!isDesktopRuntime() || storeSafe) return;
    invoke<GoogleDrivePickerStatus>("google_drive_picker_status")
      .then(setDrivePickerStatus)
      .catch(() => setDrivePickerStatus(null));
  }, [storeSafe]);

  useEffect(() => {
    setRecoveryEvidenceBundle(null);
  }, [
    plan,
    sourceVerification,
    packageTrust,
    imageMetadata,
    targetSafety,
    targetVerification,
    restoreRollbackContract,
    restoreHardwarePreflight,
    rollbackDestinationVerification,
    rollbackCaptureReceipt,
    targetReenumerationReceipt,
    dataPreservationReceipt,
    bootMetadataReceipt,
  ]);

  useEffect(() => {
    setRecoverySessionState(null);
    setRecoveryDiagnosticsExport(null);
  }, [recoveryEvidenceBundle]);

  const canAnalyze = isDesktopRuntime() && sourcePath.trim().length > 0 && !busy;
  void metadataImageCandidateCount;
  const sourceState = useMemo(() => {
    if (!analysis) return "Not analyzed";
    if (analysis.restore_candidate && analysis.warnings.length === 0) return "Ready to plan";
    if (analysis.restore_candidate) return "Plan with warnings";
    return "Blocked until fixed";
  }, [analysis]);
  const systemImageFiles = analysis?.system_image_files ?? [];
  const metadataImageFiles = analysis?.metadata_image_files ?? [];
  const metadataImageCandidateCount = metadataImageFiles.length;

  function resetResult(nextPath: string) {
    setSourcePath(nextPath);
    setAnalysis(null);
    setPlan(null);
    setSourceVerification(null);
    setShowTechnical(false);
    setExpectedSha256("");
    setSelectedImageIndex("");
    setImagePath("");
    setTargetArchitecture("");
    setPackageTrust(null);
    setImageMetadata(null);
    setTargetDrive("");
    setTargetSafety(null);
    setTargetVerification(null);
    setReenumeratedTargetDrive("");
    setStableTargetLocator(null);
    setTargetReenumerationReceipt(null);
    setRestoreRollbackContract(null);
      setRestoreHardwarePreflight(null);
      setRollbackDestinationVerification(null);
      setRollbackCaptureReceipt(null);
    setRollbackDestinationPath("");
    setDataPreservationMode("preserve_existing_data");
    setDataPreservationAcknowledgement("");
    setDataPreservationReceipt(null);
    setBootMetadataReceipt(null);
    setRecoveryEvidenceBundle(null);
    setRecoverySessionState(null);
    setRecoveryDiagnosticsExport(null);
    setDriveReceipt(null);
    setDriveProgress(null);
    setFat32MediaPlan(null);
    setMessage("Source changed. Analyze it again before planning anything.");
  }

  async function chooseSource(directory: boolean) {
    if (!isDesktopRuntime() || busy) return;
    try {
      const selected = await open({
        directory,
        multiple: false,
        title: directory ? "Choose Windows backup folder" : "Choose Windows recovery image",
        filters: directory ? undefined : [{
          name: "Windows recovery sources",
          extensions: ["iso", "wim", "esd", "swm", "vhd", "vhdx", "ffu"],
        }],
      });
      if (typeof selected === "string") resetResult(selected);
    } catch (error) {
      setMessage(`Source picker could not open. Nothing was changed. ${String(error)}`);
    }
  }

  async function chooseGoogleDriveSource() {
    if (storeSafe) {
      setMessage("Google Drive acquisition is disabled in the store-safe distribution.");
      return;
    }
    if (!isDesktopRuntime() || busy || !drivePickerStatus?.configured) return;
    try {
      const selected = await open({
        directory: true,
        multiple: false,
        title: "Choose a local staging folder for the Drive recovery file",
      });
      if (typeof selected !== "string") return;
      const operationId = globalThis.crypto.randomUUID();
      setBusy(true);
      setDriveOperationId(operationId);
      setDriveProgress(null);
      setMessage(
        "Opening Google Picker in your system browser. Select one recovery file; Phoenix Key will download and identity-lock it locally…",
      );
      const poll = window.setInterval(() => {
        invoke<GoogleDriveProgress>("google_drive_acquisition_status", {
          operationId,
        })
          .then(setDriveProgress)
          .catch(() => undefined);
      }, 500);
      try {
        const result = await invoke<GoogleDriveReceipt>(
          "acquire_google_drive_picker_recovery",
          { destinationDir: selected, operationId },
        );
        setDriveReceipt(result);
        if (result.cancelled) {
          setMessage(
            "Drive acquisition cancelled. Partial bytes were preserved for a safe resume; no cloud file was modified.",
          );
        } else if (result.staged_path) {
          resetResult(result.staged_path);
          setDriveReceipt(result);
          setMessage(
            "Drive file staged locally and SHA-256 identity lock verified. Analyze the local copy before any recovery planning.",
          );
        }
      } finally {
        window.clearInterval(poll);
        setDriveOperationId(null);
      }
    } catch (error) {
      setDriveReceipt(null);
      setMessage(
        `Google Drive selection did not complete. No cloud file was modified. ${String(error)}`,
      );
    } finally {
      setBusy(false);
    }
  }

  async function cancelGoogleDriveSource() {
    if (!driveOperationId) return;
    try {
      await invoke("cancel_google_drive_acquisition", {
        operationId: driveOperationId,
      });
      setMessage(
        "Cancellation requested. Phoenix Key will stop at the next safe chunk boundary and keep resumable partial bytes.",
      );
    } catch (error) {
      setMessage(`Cancellation request failed. ${String(error)}`);
    }
  }

  async function analyze() {
    if (!canAnalyze) return;
    setBusy(true);
    setPlan(null);
    setMessage("Inspecting the source read-only. No target disk is being touched…");
    try {
      const result = await invoke<RecoveryAnalysis>("analyze_windows_recovery_source", {
        sourcePath: sourcePath.trim(),
      });
      setAnalysis(result);
      setImagePath(metadataImagePathForAnalysis(sourcePath.trim(), result));
      setMessage(
        result.restore_candidate
          ? "Analysis complete. Review what Phoenix Key found before building a plan."
          : "Analysis complete, but this source is not safe to plan for restore yet.",
      );
    } catch (error) {
      setAnalysis(null);
      setMessage(String(error));
    } finally {
      setBusy(false);
    }
  }

  async function buildPlan() {
    if (!analysis || !analysis.restore_candidate || busy) return;
    setBusy(true);
    setMessage("Building a read-only recovery plan for this computer…");
    try {
      const result = await invoke<RecoveryPlan>("plan_windows_recovery_source", {
        sourcePath: sourcePath.trim(),
      });
      setPlan(result);
      setSourceVerification(null);
      setImagePath(metadataImagePathForAnalysis(sourcePath.trim(), result.source));
      setTargetArchitecture(result.host_arch || "");
      setPackageTrust(null);
      setImageMetadata(null);
      setTargetSafety(null);
      setTargetVerification(null);
      setRestoreRollbackContract(null);
      setRestoreHardwarePreflight(null);
      setRollbackDestinationVerification(null);
      setRollbackCaptureReceipt(null);
      setMessage("Recovery plan created and bound to the current source identity. No disk was changed.");
    } catch (error) {
      setPlan(null);
      setMessage(String(error));
    } finally {
      setBusy(false);
    }
  }

  async function reverifySourceIdentity() {
    if (!plan?.source_identity?.sha256 || busy) return;
    setBusy(true);
    setSourceVerification(null);
    setRestoreHardwarePreflight(null);
    setRollbackDestinationVerification(null);
    setRollbackCaptureReceipt(null);
    setMessage("Freshly re-hashing the recovery source and comparing it with the identity-bound plan…");
    try {
      const result = await invoke<SourceIdentityVerification>(
        "verify_windows_recovery_source_identity",
        {
          sourcePath: sourcePath.trim(),
          expectedSha256: plan.source_identity.sha256,
        },
      );
      setSourceVerification(result);
      if (!result.matches) {
        setPackageTrust(null);
        setImageMetadata(null);
        setTargetSafety(null);
        setTargetVerification(null);
        setRestoreRollbackContract(null);
      setRestoreHardwarePreflight(null);
      setRollbackDestinationVerification(null);
      setRollbackCaptureReceipt(null);
      }
      setMessage(
        result.matches
          ? "Fresh source identity revalidation passed. The recovery source still matches the plan."
          : "Recovery source identity changed. All downstream trust and target evidence was invalidated; rebuild the plan before proceeding.",
      );
    } catch (error) {
      setSourceVerification(null);
      setPackageTrust(null);
      setImageMetadata(null);
      setTargetSafety(null);
      setTargetVerification(null);
      setRestoreRollbackContract(null);
      setRestoreHardwarePreflight(null);
      setRollbackDestinationVerification(null);
      setRollbackCaptureReceipt(null);
      setMessage(
        `Fresh source identity verification could not complete. Downstream evidence was cleared. Nothing was changed. ${String(error)}`,
      );
    } finally {
      setBusy(false);
    }
  }

  async function verifyPackageTrust() {
    if (storeSafe) {
      setMessage("External package-trust helpers are disabled in the store-safe distribution.");
      return;
    }
    if (!plan || !sourceVerification?.matches || !expectedSha256.trim() || busy) return;
    setBusy(true);
    setRestoreHardwarePreflight(null);
    setRollbackDestinationVerification(null);
    setRollbackCaptureReceipt(null);
    setMessage("Hashing the recovery package and checking signature evidence read-only…");
    try {
      const result = await invoke<PackageTrust>("inspect_recovery_package_trust", {
        packagePath: sourcePath.trim(),
        expectedSha256: expectedSha256.trim(),
        expectedSignerContains: null,
      });
      setPackageTrust(result);
      setMessage(
        result.verified_for_use
          ? "Package trust verified for the supplied SHA-256."
          : "Package inspection completed, but trust requirements are not satisfied.",
      );
    } catch (error) {
      setPackageTrust(null);
      setRestoreHardwarePreflight(null);
      setRollbackDestinationVerification(null);
      setRollbackCaptureReceipt(null);
      setMessage(`Package trust inspection could not complete. Nothing was changed. ${String(error)}`);
    } finally {
      setBusy(false);
    }
  }

  async function inspectImageMetadata() {
    if (storeSafe) {
      setMessage("External image-metadata helpers are disabled in the store-safe distribution.");
      return;
    }
    if (!plan || !sourceVerification?.matches || busy) return;
    const selectedImagePath = imagePath.trim() || sourcePath.trim();
    if (analysis?.system_image_files.length && !imagePath.trim()) {
      setMessage("Choose the exact VHD/VHDX payload from this backup before inspecting Windows metadata.");
      return;
    }
    const indexText = selectedImageIndex.trim();
    const parsedIndex = indexText ? Number(indexText) : undefined;
    if (indexText && (!Number.isInteger(parsedIndex) || (parsedIndex || 0) <= 0)) {
      setMessage("Windows image index must be a positive whole number.");
      return;
    }
    setBusy(true);
    setTargetSafety(null);
    setTargetVerification(null);
    setRestoreRollbackContract(null);
    setRestoreHardwarePreflight(null);
    setRollbackDestinationVerification(null);
    setRollbackCaptureReceipt(null);
    setMessage("Reading Windows image index, edition, and architecture metadata with no mount or modification…");
    try {
      const result = await invoke<ImageMetadata>("inspect_windows_image_metadata", {
        imagePath: selectedImagePath,
        selectedIndex: parsedIndex,
        targetArchitecture: targetArchitecture.trim() || null,
      });
      setImageMetadata(result);
      if (!selectedImageIndex && result.images.length === 1) {
        setSelectedImageIndex(String(result.images[0].index));
      }
      setMessage(
        result.restore_eligible
          ? "Exact Windows image metadata and architecture compatibility are verified."
          : "Image metadata inspection completed. Review the blocked gates before restore planning.",
      );
    } catch (error) {
      setImageMetadata(null);
      setTargetSafety(null);
      setTargetVerification(null);
      setRestoreRollbackContract(null);
      setRestoreHardwarePreflight(null);
      setRollbackDestinationVerification(null);
      setRollbackCaptureReceipt(null);
      setMessage(`Windows image metadata inspection could not complete. Nothing was changed. ${String(error)}`);
    } finally {
      setBusy(false);
    }
  }

  async function inspectFat32MediaReadiness() {
    if (storeSafe) {
      setMessage("FAT32 helper execution is disabled in the store-safe distribution.");
      return;
    }
    if (!analysis || analysis.kind !== "extracted_windows_media" || busy) return;
    setBusy(true);
    setFat32MediaPlan(null);
    setMessage(
      "Checking the extracted Windows media for FAT32 file limits, split-WIM requirements, and UEFI boot evidence…",
    );
    try {
      const result = await invoke<Fat32MediaPlan>("plan_fat32_windows_media", {
        sourceRoot: sourcePath.trim(),
      });
      setFat32MediaPlan(result);
      setMessage(
        result.ready_for_fat32_copy_now
          ? "FAT32/UEFI media readiness verified. No files or disks were changed."
          : result.ready_for_fat32_copy_after_split
            ? "Media is UEFI-capable, but install.wim must be split before a FAT32 copy. The DISM command is a preview only."
            : "FAT32/UEFI readiness is blocked. Review the evidence before preparing media.",
      );
    } catch (error) {
      setFat32MediaPlan(null);
      setMessage(
        `FAT32/UEFI media inspection could not complete. Nothing was changed. ${String(error)}`,
      );
    } finally {
      setBusy(false);
    }
  }

  async function inspectTargetSafety() {
    if (storeSafe) {
      setMessage("Physical-target inspection is disabled in the store-safe distribution.");
      return;
    }
    if (
      !plan ||
      !sourceVerification?.matches ||
      plan.host_os !== "windows" ||
      !targetDrive.trim() ||
      busy
    ) return;
    setBusy(true);
    setMessage("Re-enumerating the Windows target and proving source/target separation read-only…");
    try {
      const result = await invoke<RecoveryTargetSafety>("inspect_recovery_target_safety", {
        targetDrive: targetDrive.trim(),
        sourcePath: sourcePath.trim(),
      });
      setTargetSafety(result);
      setTargetVerification(null);
      setReenumeratedTargetDrive(result.target || targetDrive.trim());
      setStableTargetLocator(null);
      setTargetReenumerationReceipt(null);
      setRestoreRollbackContract(null);
      setRestoreHardwarePreflight(null);
      setRollbackDestinationVerification(null);
      setRollbackCaptureReceipt(null);
      setMessage(
        result.safe_to_prepare
          ? "Target identity, capacity, and source/target separation are verified for planning."
          : "Target safety inspection completed, but the target remains blocked.",
      );
    } catch (error) {
      setTargetSafety(null);
      setTargetVerification(null);
      setRestoreRollbackContract(null);
      setRestoreHardwarePreflight(null);
      setRollbackDestinationVerification(null);
      setRollbackCaptureReceipt(null);
      setMessage(`Target safety inspection could not complete. Nothing was changed. ${String(error)}`);
    } finally {
      setBusy(false);
    }
  }

  async function planRestoreRollbackRequirements() {
    if (storeSafe) {
      setMessage("Restore-target rollback planning is disabled in the store-safe distribution.");
      return;
    }
    if (
      !plan ||
      !sourceVerification?.matches ||
      !targetSafety?.safe_to_prepare ||
      !targetVerification?.matches ||
      busy
    ) return;
    setBusy(true);
    setRestoreRollbackContract(null);
      setRestoreHardwarePreflight(null);
      setRollbackDestinationVerification(null);
      setRollbackCaptureReceipt(null);
    setMessage("Building an identity-bound rollback requirements contract. No target data is being changed…");
    try {
      const result = await invoke<RestoreRollbackContract>(
        "plan_restore_target_rollback_contract",
        {
          identityBoundPlanJson: JSON.stringify(plan),
          targetSafetyJson: JSON.stringify(targetSafety),
        },
      );
      setRestoreRollbackContract(result);
      setRestoreHardwarePreflight(null);
      setRollbackDestinationVerification(null);
      setRollbackCaptureReceipt(null);
      setMessage(
        "Restore rollback requirements are now identity-bound to this source and target. Execution remains locked until real backup artifacts exist.",
      );
    } catch (error) {
      setRestoreRollbackContract(null);
      setRestoreHardwarePreflight(null);
      setRollbackDestinationVerification(null);
      setRollbackCaptureReceipt(null);
      setMessage(
        `Restore rollback requirements could not be planned. Nothing was changed. ${String(error)}`,
      );
    } finally {
      setBusy(false);
    }
  }

  async function assessRestoreHardwarePreflight() {
    if (storeSafe) {
      setMessage("Physical restore preflight is disabled in the store-safe distribution.");
      return;
    }
    const fileSourceRequiresTrust = plan?.source_identity?.source_kind === "file_sha256";
    if (
      !plan ||
      !sourceVerification?.matches ||
      !imageMetadata ||
      !targetSafety?.safe_to_prepare ||
      !targetVerification?.matches ||
      !restoreRollbackContract ||
      (fileSourceRequiresTrust && !packageTrust?.verified_for_use) ||
      busy
    ) return;

    setBusy(true);
      setRestoreHardwarePreflight(null);
      setRollbackDestinationVerification(null);
      setRollbackCaptureReceipt(null);
    setMessage(
      "Assessing the complete software evidence chain up to the physical rollback-capture boundary. No restore or disk mutation will run…",
    );
    try {
      const result = await invoke<RestoreHardwarePreflight>(
        "assess_windows_restore_hardware_preflight",
        {
          identityBoundPlanJson: JSON.stringify(plan),
          sourceIdentityVerificationJson: JSON.stringify(sourceVerification),
          packageTrustJson: JSON.stringify(packageTrust ?? {}),
          imageMetadataJson: JSON.stringify(imageMetadata),
          targetSafetyJson: JSON.stringify(targetSafety),
          targetIdentityVerificationJson: JSON.stringify(targetVerification),
          rollbackContractJson: JSON.stringify(restoreRollbackContract),
        },
      );
      setRestoreHardwarePreflight(result);
      setRollbackDestinationVerification(null);
      setRollbackCaptureReceipt(null);
      setMessage(
        result.ready_to_capture_hardware_rollback_evidence
          ? "Software preflight passed. The next legitimate boundary is real rollback evidence captured from the physical target; restore execution remains unavailable."
          : "Software preflight is blocked. Resolve the listed evidence gates before capturing target rollback artifacts.",
      );
    } catch (error) {
      setRestoreHardwarePreflight(null);
      setRollbackDestinationVerification(null);
      setRollbackCaptureReceipt(null);
      setMessage(
        `Restore hardware preflight could not complete. Nothing was changed. ${String(error)}`,
      );
    } finally {
      setBusy(false);
    }
  }

  async function chooseRollbackDestination() {
    if (!restoreHardwarePreflight?.ready_to_capture_hardware_rollback_evidence || busy) return;
    try {
      const selected = await open({
        directory: true,
        multiple: false,
        title: "Choose a rollback evidence folder on a different physical disk",
      });
      if (typeof selected !== "string") return;
      setRollbackDestinationPath(selected);
      setRollbackDestinationVerification(null);
      setRollbackCaptureReceipt(null);
      setMessage(
        "Rollback folder selected. Verify its physical disk is different from the restore target before capturing any evidence.",
      );
    } catch (error) {
      setMessage(`Rollback destination picker could not open. Nothing was changed. ${String(error)}`);
    }
  }

  async function verifyRollbackDestination() {
    if (storeSafe) {
      setMessage("Physical rollback-destination verification is disabled in the store-safe distribution.");
      return;
    }
    const expectedTargetStableIdentity =
      restoreHardwarePreflight?.target_stable_identity_sha256 ||
      targetSafety?.target_stable_identity_sha256 ||
      "";
    if (
      !restoreHardwarePreflight?.ready_to_capture_hardware_rollback_evidence ||
      !targetDrive.trim() ||
      !rollbackDestinationPath.trim() ||
      !expectedTargetStableIdentity ||
      busy
    ) return;

    setBusy(true);
    setRollbackDestinationVerification(null);
    setRollbackCaptureReceipt(null);
    setMessage(
      "Proving the rollback folder is on a different physical disk from the restore target. No files or disks are being modified…",
    );
    try {
      const result = await invoke<RollbackDestinationVerification>(
        "inspect_restore_rollback_destination",
        {
          targetDrive: targetDrive.trim(),
          rollbackDestinationPath: rollbackDestinationPath.trim(),
          expectedTargetStableIdentitySha256: expectedTargetStableIdentity,
        },
      );
      setRollbackDestinationVerification(result);
      setRollbackCaptureReceipt(null);
      setMessage(
        result.ready_for_hardware_rollback_capture
          ? "Rollback destination is physically separate and target identity is still current. Real hardware rollback capture is now the next boundary."
          : "Rollback destination verification is blocked. Choose a different physical disk or re-verify the restore target.",
      );
    } catch (error) {
      setRollbackDestinationVerification(null);
      setRollbackCaptureReceipt(null);
      setMessage(
        `Rollback destination verification could not complete. Nothing was changed. ${String(error)}`,
      );
    } finally {
      setBusy(false);
    }
  }

  async function captureRollbackArtifacts() {
    if (storeSafe) {
      setMessage("Restore rollback artifact capture is disabled in the store-safe distribution.");
      return;
    }
    if (
      !rollbackDestinationVerification?.ready_for_hardware_rollback_capture ||
      !restoreRollbackContract ||
      !targetDrive.trim() ||
      !rollbackDestinationPath.trim() ||
      busy
    ) return;

    setBusy(true);
    setRollbackCaptureReceipt(null);
    setMessage(
      "Reading GPT partition metadata from the restore target and writing rollback artifacts only to the verified separate folder. The restore target remains read-only…",
    );
    try {
      const result = await invoke<RestoreRollbackCaptureReceipt>(
        "capture_restore_target_rollback_artifacts",
        {
          targetDrive: targetDrive.trim(),
          rollbackDestinationPath: rollbackDestinationPath.trim(),
          rollbackContractJson: JSON.stringify(restoreRollbackContract),
        },
      );
      setRollbackCaptureReceipt(result);
      setBootMetadataReceipt(null);
      setMessage(
        result.target_bytes_written === 0 && !result.target_write_attempted
          ? "GPT rollback artifacts captured with zero target writes. Restore remains locked until the remaining hardware/data-preservation requirements are satisfied."
          : "Rollback capture returned an unsafe write observation and must not be trusted.",
      );
    } catch (error) {
      setRollbackCaptureReceipt(null);
      setMessage(
        `Restore rollback capture could not complete. The restore target was not intentionally modified. ${String(error)}`,
      );
    } finally {
      setBusy(false);
    }
  }

  async function captureTargetBootMetadata() {
    if (storeSafe) {
      setMessage("External target boot-metadata capture is disabled in the store-safe distribution.");
      return;
    }
    if (!rollbackCaptureReceipt || !restoreRollbackContract || busy) return;

    setBusy(true);
    setBootMetadataReceipt(null);
    setMessage(
      "Capturing boot metadata only from target partitions Windows already exposes. Phoenix Key will not mount, assign, or write any target partition…",
    );
    try {
      const result = await invoke<RestoreTargetBootMetadataReceipt>(
        "capture_restore_target_boot_metadata",
        {
          rollbackCaptureReceiptJson: JSON.stringify(rollbackCaptureReceipt),
          rollbackContractJson: JSON.stringify(restoreRollbackContract),
        },
      );
      setBootMetadataReceipt(result);
      setMessage(
        result.resolved
          ? "Accessible target boot metadata was backed up to the separate rollback folder. Restore execution remains locked."
          : "Boot-metadata capture is incomplete because one or more boot/recovery partitions are not already accessible. Phoenix Key did not mount them.",
      );
    } catch (error) {
      setBootMetadataReceipt(null);
      setMessage(
        `External target boot-metadata capture could not complete. No target partition was mounted or modified. ${String(error)}`,
      );
    } finally {
      setBusy(false);
    }
  }

  async function createDataPreservationDecision() {
    if (!targetSafety?.safe_to_prepare || !restoreRollbackContract || busy) return;

    setBusy(true);
    setDataPreservationReceipt(null);
    setMessage(
      dataPreservationMode === "explicit_discard"
        ? "Binding the explicit data-loss decision to this exact target hardware and rollback contract. No disk mutation will run…"
        : "Recording that target data must be preserved. This remains blocked until a real backup receipt exists…",
    );
    try {
      const result = await invoke<TargetDataPreservationReceipt>(
        "create_target_data_preservation_decision",
        {
          targetSafetyJson: JSON.stringify(targetSafety),
          rollbackContractJson: JSON.stringify(restoreRollbackContract),
          mode: dataPreservationMode,
          acknowledgement: dataPreservationAcknowledgement,
        },
      );
      setDataPreservationReceipt(result);
      setMessage(
        result.resolved
          ? "Target data decision is resolved for this exact hardware and rollback contract. Restore execution remains locked."
          : "Target data decision is still blocked. The required evidence or acknowledgement is shown below.",
      );
    } catch (error) {
      setDataPreservationReceipt(null);
      setMessage(
        `Target data-preservation decision could not be recorded. Nothing was changed. ${String(error)}`,
      );
    } finally {
      setBusy(false);
    }
  }

  async function buildRecoveryEvidenceBundle() {
    if (
      !plan ||
      !sourceVerification ||
      !imageMetadata ||
      !targetSafety ||
      !targetVerification ||
      !restoreRollbackContract ||
      !restoreHardwarePreflight ||
      busy
    ) return;

    setBusy(true);
    setRecoveryEvidenceBundle(null);
    setMessage(
      "Binding the current recovery evidence into one checksummed session bundle. No disk or source mutation will run…",
    );
    try {
      const result = await invoke<RecoveryEvidenceBundleV2>(
        "build_windows_recovery_evidence_bundle_v2",
        {
          evidenceJson: JSON.stringify({
            identity_bound_plan: plan,
            source_identity_verification: sourceVerification,
            package_trust: packageTrust,
            image_metadata: imageMetadata,
            target_safety: targetSafety,
            target_identity_verification: targetVerification,
            rollback_contract: restoreRollbackContract,
            hardware_preflight: restoreHardwarePreflight,
            rollback_destination_verification: rollbackDestinationVerification,
            rollback_capture_receipt: rollbackCaptureReceipt,
            target_reenumeration_receipt: targetReenumerationReceipt,
            data_preservation_receipt: dataPreservationReceipt,
            boot_metadata_receipt: bootMetadataReceipt,
          }),
        },
      );
      setRecoveryEvidenceBundle(result);
      setMessage(
        result.hardware_chain_complete
          ? "Recovery evidence bundle is complete for the currently implemented evidence classes. Restore execution remains intentionally unavailable."
          : "Recovery evidence bundle created. Missing evidence is listed explicitly; restore execution remains unavailable.",
      );
    } catch (error) {
      setRecoveryEvidenceBundle(null);
      setMessage(
        `Recovery evidence bundle could not be created. Nothing was changed. ${String(error)}`,
      );
    } finally {
      setBusy(false);
    }
  }

  async function persistRecoverySessionState() {
    if (
      !plan ||
      !sourceVerification ||
      !imageMetadata ||
      !targetSafety ||
      !targetVerification ||
      !restoreRollbackContract ||
      !restoreHardwarePreflight ||
      busy
    ) return;

    setBusy(true);
    setRecoverySessionState(null);
    setMessage(
      "Persisting the current read-only recovery session state. No destructive authorization or disk mutation will be saved…",
    );
    try {
      const result = await invoke<RecoverySessionStateV1>(
        "persist_windows_recovery_session_state",
        {
          evidenceJson: JSON.stringify({
            identity_bound_plan: plan,
            source_identity_verification: sourceVerification,
            package_trust: packageTrust,
            image_metadata: imageMetadata,
            target_safety: targetSafety,
            target_identity_verification: targetVerification,
            rollback_contract: restoreRollbackContract,
            hardware_preflight: restoreHardwarePreflight,
            rollback_destination_verification: rollbackDestinationVerification,
            rollback_capture_receipt: rollbackCaptureReceipt,
            target_reenumeration_receipt: targetReenumerationReceipt,
            data_preservation_receipt: dataPreservationReceipt,
            boot_metadata_receipt: bootMetadataReceipt,
          }),
        },
      );
      setRecoverySessionState(result);
      setMessage(
        result.stale_evidence_detected || result.hardware_substitution_detected
          ? "Recovery session persisted in a blocked state. Fresh hardware analysis is required before continuing."
          : "Read-only recovery session persisted. Destructive authorization was not saved.",
      );
    } catch (error) {
      setRecoverySessionState(null);
      setMessage(
        `Recovery session state could not be persisted. Nothing was changed on the recovery source or target. ${String(error)}`,
      );
    } finally {
      setBusy(false);
    }
  }

  async function persistRecoveryDiagnosticsExport() {
    if (
      !plan ||
      !sourceVerification ||
      !imageMetadata ||
      !targetSafety ||
      !targetVerification ||
      !restoreRollbackContract ||
      !restoreHardwarePreflight ||
      busy
    ) return;

    setBusy(true);
    setRecoveryDiagnosticsExport(null);
    setMessage(
      "Building a sanitized recovery diagnostics package. Local paths, hardware serials, provider IDs, command output, and typed acknowledgements will be redacted…",
    );
    try {
      const result = await invoke<RecoveryDiagnosticsExportV1>(
        "persist_windows_recovery_diagnostics_export",
        {
          evidenceJson: JSON.stringify({
            identity_bound_plan: plan,
            source_identity_verification: sourceVerification,
            package_trust: packageTrust,
            image_metadata: imageMetadata,
            target_safety: targetSafety,
            target_identity_verification: targetVerification,
            rollback_contract: restoreRollbackContract,
            hardware_preflight: restoreHardwarePreflight,
            rollback_destination_verification: rollbackDestinationVerification,
            rollback_capture_receipt: rollbackCaptureReceipt,
            target_reenumeration_receipt: targetReenumerationReceipt,
            data_preservation_receipt: dataPreservationReceipt,
            boot_metadata_receipt: bootMetadataReceipt,
          }),
        },
      );
      setRecoveryDiagnosticsExport(result);
      setMessage(
        "Sanitized recovery diagnostics export persisted locally. No destructive authorization was included.",
      );
    } catch (error) {
      setRecoveryDiagnosticsExport(null);
      setMessage(
        `Recovery diagnostics export could not be persisted. Nothing was changed on the recovery source or target. ${String(error)}`,
      );
    } finally {
      setBusy(false);
    }
  }

  async function locateReenumeratedTarget() {
    if (storeSafe) {
      setMessage("Stable target discovery is disabled in the store-safe distribution.");
      return;
    }
    if (!targetSafety?.target_stable_identity_sha256 || busy) return;

    setBusy(true);
    setStableTargetLocator(null);
    setTargetReenumerationReceipt(null);
    setMessage(
      "Enumerating Windows disks read-only and locating the frozen stable hardware identity…",
    );
    try {
      const result = await invoke<StableTargetLocatorResult>(
        "locate_windows_recovery_target_by_stable_identity",
        {
          expectedStableIdentitySha256: targetSafety.target_stable_identity_sha256,
        },
      );
      setStableTargetLocator(result);
      if (result.unique_match && result.match?.target) {
        setReenumeratedTargetDrive(result.match.target);
        setMessage(
          `Stable hardware identity found at ${result.match.target}. Compare re-enumeration identity next; old authorization is not carried forward.`,
        );
      } else if (result.ambiguous) {
        setMessage(
          "More than one disk produced the same stable identity. Automatic target selection is blocked.",
        );
      } else {
        setMessage(
          "The previously verified stable hardware identity was not found. Do not continue restore planning.",
        );
      }
    } catch (error) {
      setStableTargetLocator(null);
      setMessage(
        `Stable target discovery could not complete. Nothing was changed. ${String(error)}`,
      );
    } finally {
      setBusy(false);
    }
  }

  async function inspectTargetReenumeration() {
    if (storeSafe) {
      setMessage("Physical-target re-enumeration inspection is disabled in the store-safe distribution.");
      return;
    }
    if (
      !targetSafety?.safe_to_prepare ||
      !targetSafety.target_identity_sha256 ||
      !targetSafety.target_stable_identity_sha256 ||
      !reenumeratedTargetDrive.trim() ||
      busy
    ) return;

    setBusy(true);
    setTargetReenumerationReceipt(null);
    setMessage(
      "Capturing the current Windows disk identity and comparing it with the frozen target baseline. No disk mutation will run…",
    );
    try {
      const result = await invoke<RecoveryTargetReenumerationReceipt>(
        "inspect_windows_recovery_target_reenumeration",
        {
          currentTargetDrive: reenumeratedTargetDrive.trim(),
          expectedTargetDrive: targetSafety.target || targetDrive.trim(),
          expectedSnapshotIdentitySha256: targetSafety.target_identity_sha256,
          expectedStableIdentitySha256: targetSafety.target_stable_identity_sha256,
        },
      );
      setTargetReenumerationReceipt(result);
      if (result.reanalysis_required) {
        setTargetVerification(null);
        setRestoreRollbackContract(null);
        setRestoreHardwarePreflight(null);
        setRollbackDestinationVerification(null);
        setRollbackCaptureReceipt(null);
      }
      setMessage(
        result.classification === "same_hardware_reenumerated"
          ? "Same physical hardware verified after Windows re-enumeration. The old snapshot authorization was rejected; run full target safety analysis again before proceeding."
          : result.classification === "hardware_substitution_detected"
            ? "A different physical device was detected. Restore planning remains blocked."
            : result.classification === "exact_snapshot_match"
              ? "Target still has the exact same snapshot and stable hardware identity."
              : "Target identity could not be fully proven. Reanalysis is required.",
      );
    } catch (error) {
      setTargetReenumerationReceipt(null);
      setMessage(
        `Target re-enumeration inspection could not complete. Nothing was changed. ${String(error)}`,
      );
    } finally {
      setBusy(false);
    }
  }

  async function reverifyTargetIdentity() {
    if (storeSafe) {
      setMessage("Physical-target verification is disabled in the store-safe distribution.");
      return;
    }
    if (
      !targetSafety?.safe_to_prepare ||
      !targetSafety.target_identity_sha256 ||
      !targetSafety.target_stable_identity_sha256 ||
      !targetDrive.trim() ||
      busy
    ) return;
    setBusy(true);
    setTargetVerification(null);
    setTargetReenumerationReceipt(null);
    setRestoreHardwarePreflight(null);
    setRollbackDestinationVerification(null);
    setRollbackCaptureReceipt(null);
    setMessage("Freshly re-scanning the target and checking both snapshot and stable hardware identity…");
    try {
      const result = await invoke<RecoveryTargetIdentityVerification>(
        "verify_windows_recovery_target_identity",
        {
          targetDrive: targetDrive.trim(),
          expectedSnapshotIdentitySha256: targetSafety.target_identity_sha256,
          expectedStableIdentitySha256: targetSafety.target_stable_identity_sha256,
        },
      );
      setTargetVerification(result);
      if (!result.matches) setRestoreRollbackContract(null);
      setMessage(
        result.matches
          ? "Fresh target revalidation passed. Snapshot and stable hardware identity both match."
          : result.classification === "same_hardware_reenumerated"
            ? "The same physical hardware appears to have been re-enumerated under a different snapshot identity. Re-run full target safety analysis before proceeding."
            : "Target hardware changed or could not be proven. Stop and re-run the full target safety analysis before proceeding.",
      );
    } catch (error) {
      setTargetVerification(null);
      setMessage(`Fresh target revalidation could not complete. Nothing was changed. ${String(error)}`);
    } finally {
      setBusy(false);
    }
  }


  return (
    <div className="recovery-center" aria-busy={busy}>
      <section className="panel recovery-intro">
        <div className="panel-heading">
          <div>
            <p className="eyebrow">WINDOWS RECOVERY FORGE</p>
            <h3>Start by understanding the backup.</h3>
          </div>
          <span className="read-only-pill">READ ONLY</span>
        </div>
        <p className="recovery-lead">
          Phoenix Key inspects the source first, explains what it is, and tells you what this computer can safely do with it. Restore execution is intentionally separate.
        </p>
        {storeSafe && (
          <div className="warning-box">
            <strong>Store-safe edition</strong>
            <p>Native recovery-source analysis and planning remain available. Hardware scans, cloud acquisition, external helpers, and physical media writing are disabled in this sandboxed distribution.</p>
          </div>
        )}
        {!isDesktopRuntime() && (
          <div className="warning-box">
            <strong>Desktop app required</strong>
            <p>Local backup inspection is not available in the browser shell. Open Phoenix Key Desktop.</p>
          </div>
        )}
        <div className="source-actions" aria-label="Choose recovery source">
          <button className="scan-button" type="button" onClick={() => chooseSource(true)} disabled={!isDesktopRuntime() || busy}>Choose Backup Folder</button>
          <button className="plan-button" type="button" onClick={() => chooseSource(false)} disabled={!isDesktopRuntime() || busy}>Choose Image File</button>
          <button
            className="plan-button"
            type="button"
            onClick={chooseGoogleDriveSource}
            disabled={storeSafe || !isDesktopRuntime() || busy || !drivePickerStatus?.configured}
            title={storeSafe ? "Disabled in the store-safe distribution" : drivePickerStatus?.configured ? "Open Google Picker in your system browser" : "This build is missing its Google Drive desktop OAuth client ID"}
          >
            Choose from Google Drive
          </button>
        </div>
        <label className="path-field">
          <span>Selected source</span>
          <input
            value={sourcePath}
            onChange={(event) => resetResult(event.target.value)}
            placeholder="Choose a folder or image above, or paste a path"
            aria-describedby="recovery-source-help"
          />
        </label>
        <p id="recovery-source-help" className="field-help">
          Supported analysis includes WindowsImageBackup folders, ISO, WIM/ESD, VHD/VHDX, WinRE, and extracted Windows media. A filename alone never proves a backup is safe to restore.
        </p>
        <button className="scan-button" onClick={analyze} disabled={!canAnalyze}>
          {busy && !analysis ? "Analyzing…" : "Analyze Backup Safely"}
        </button>
        <div className="recovery-status" role="status" aria-live="polite" aria-atomic="true">{message}</div>
        {driveOperationId && (
          <div className="recovery-list">
            <strong>Google Drive acquisition</strong>
            <progress max={100} value={driveProgress?.percent ?? 0}>
              {driveProgress?.percent ?? 0}%
            </progress>
            <div>
              {driveProgress?.phase || "waiting"} · {driveProgress?.downloaded_size_bytes ?? 0}
              {" / "}
              {driveProgress?.provider_size_bytes ?? 0} bytes
            </div>
            <button
              className="plan-button"
              type="button"
              onClick={cancelGoogleDriveSource}
              disabled={driveProgress?.cancel_requested === true}
            >
              {driveProgress?.cancel_requested ? "Cancelling…" : "Cancel Download"}
            </button>
          </div>
        )}
        {drivePickerStatus && !drivePickerStatus.configured && (
          <p className="field-help">
            Google Drive Picker is unavailable in this build until its desktop OAuth client ID is configured.
          </p>
        )}
        {driveReceipt && (
          <div className={driveReceipt.cancelled ? "warning-box" : "recovery-list good-list"}>
            <strong>
              {driveReceipt.cancelled
                ? "Google Drive acquisition cancelled safely"
                : "Google Drive acquisition verified"}
            </strong>
            {driveReceipt.provider_name && <div>File: {driveReceipt.provider_name}</div>}
            {driveReceipt.staged_path && <div>Local path: {driveReceipt.staged_path}</div>}
            {driveReceipt.partial_path && <div>Resumable partial: {driveReceipt.partial_path}</div>}
            <div>Size: {driveReceipt.provider_size_bytes ?? 0} bytes</div>
            <div>Downloaded: {driveReceipt.downloaded_size_bytes ?? 0} bytes</div>
            {driveReceipt.observed_sha256 && <div>SHA-256: {driveReceipt.observed_sha256}</div>}
            <div>Identity lock: {driveReceipt.identity_lock_verified ? "verified" : "blocked"}</div>
            <div>Cloud original modified: no</div>
            <div>OAuth token persisted: {driveReceipt.oauth_token_persisted ? "yes" : "no"}</div>
          </div>
        )}
      </section>

      {analysis && (
        <section className="panel recovery-result">
          <div className="panel-heading">
            <div>
              <p className="eyebrow">WHAT WE FOUND</p>
              <h3>{friendlyKind[analysis.kind] || readableToken(analysis.kind)}</h3>
            </div>
            <span className={`confidence-pill confidence-${analysis.confidence}`}>
              {analysis.confidence} confidence
            </span>
          </div>

          <div className="recovery-summary-card">
            <strong>{analysis.user_summary}</strong>
            <p>{analysis.recommended_action}</p>
          </div>

          <div className="recovery-facts">
            <div><span>Current state</span><strong>{sourceState}</strong></div>
            <div><span>System image</span><strong>{analysis.has_windows_image_backup ? "Detected" : "No"}</strong></div>
            <div><span>Disk image files</span><strong>{systemImageFiles.length}</strong></div>
          </div>

          {analysis.warnings.length > 0 && (
            <div className="warning-box">
              <strong>Fix before restoring</strong>
              {analysis.warnings.map((warning) => <p key={warning}>{warning}</p>)}
            </div>
          )}

          {systemImageFiles.length > 0 && (
            <div className="recovery-list">
              <strong>Backup disk images found</strong>
              {systemImageFiles.map((path) => <div key={path}>{path}</div>)}
            </div>
          )}

          {analysis.kind === "extracted_windows_media" && (
            <div className="recovery-list">
              <strong>FAT32 / UEFI installation-media readiness</strong>
              <p className="field-help">
                Phoenix Key checks the entire extracted media tree for FAT32's file-size limit and verifies whether a Microsoft split-WIM layout is required. This check does not copy, format, split, or write anything.
              </p>
              <button
                className="plan-button"
                type="button"
                onClick={inspectFat32MediaReadiness}
                disabled={busy}
              >
                Check FAT32 / UEFI Readiness
              </button>
              {fat32MediaPlan && (
                <div
                  className={
                    fat32MediaPlan.ready_for_fat32_copy_now ||
                    fat32MediaPlan.ready_for_fat32_copy_after_split
                      ? "good-list"
                      : "warning-box"
                  }
                >
                  <strong>
                    {fat32MediaPlan.ready_for_fat32_copy_now
                      ? "Ready for a FAT32 media-copy stage"
                      : fat32MediaPlan.ready_for_fat32_copy_after_split
                        ? "Ready after splitting install.wim"
                        : "FAT32 media preparation blocked"}
                  </strong>
                  <p>UEFI boot evidence: {fat32MediaPlan.uefi_boot_evidence_present ? "present" : "missing"}</p>
                  <p>Windows image layout: {readableToken(fat32MediaPlan.image_mode)}</p>
                  <p>Split WIM required: {fat32MediaPlan.split_required ? "yes" : "no"}</p>
                  {fat32MediaPlan.split_command_preview && (
                    <p>DISM preview: {fat32MediaPlan.split_command_preview.join(" ")}</p>
                  )}
                  {fat32MediaPlan.unsupported_oversized_files.map((item) => (
                    <p key={item.path}>Oversized: {item.path} · {item.size_bytes} bytes</p>
                  ))}
                  {fat32MediaPlan.block_reasons.map((reason) => (
                    <p key={reason}>— {readableToken(reason)}</p>
                  ))}
                  <p>Source modified: no · target disk modified: no</p>
                </div>
              )}
            </div>
          )}

          <button
            className="plan-button"
            onClick={buildPlan}
            disabled={busy || !analysis.restore_candidate}
            title={!analysis.restore_candidate ? "Resolve the source warnings first" : undefined}
          >
            {busy ? "Building Plan…" : "Build Safe Recovery Plan"}
          </button>
        </section>
      )}

      {plan && (
        <section className="panel recovery-plan">
          <div className="panel-heading">
            <div>
              <p className="eyebrow">WHAT THIS COMPUTER CAN DO</p>
              <h3>{readableToken(plan.host_route)}</h3>
            </div>
            <span className="read-only-pill">DRY RUN</span>
          </div>
          <p className="recovery-lead">{plan.host_explanation}</p>

          <div className="recovery-list">
            <strong>Source identity & restore evidence</strong>
            <div>
              Source SHA-256: {plan.source_identity?.sha256 || "Identity unavailable — restore remains locked"}
            </div>
            <div>
              Identity state: {plan.source_identity?.complete ? "Complete and bound to this plan" : "Incomplete"}
            </div>
            <div>
              Pre-mutation rule: {plan.source_identity_gate || "Fresh identity recheck required"}
            </div>
            <div>
              Dry-run plan SHA-256: {plan.plan_sha256 || "Plan integrity digest unavailable"}
            </div>
          </div>

          <div className="recovery-columns">
            <div className="recovery-list">
              <strong>Package trust</strong>
              <label className="path-field">
                <span>Expected SHA-256 from the trusted source</span>
                <input
                  value={expectedSha256}
                  onChange={(event) => {
                    setExpectedSha256(event.target.value);
                    setPackageTrust(null);
                  }}
                  placeholder="64-character SHA-256"
                  autoCapitalize="none"
                  autoCorrect="off"
                  spellCheck={false}
                  aria-describedby="recovery-hash-help"
                />
              </label>
              <p id="recovery-hash-help" className="field-help">Use the SHA-256 published with the trusted recovery source. Phoenix Key compares it locally and does not modify the package.</p>
              <button
                className="plan-button"
                type="button"
                onClick={verifyPackageTrust}
                disabled={busy || expectedSha256.trim().length !== 64}
              >
                Verify Package Trust
              </button>
              {packageTrust && (
                <div className={packageTrust.verified_for_use ? "good-list" : "warning-box"}>
                  <strong>{packageTrust.verified_for_use ? "Verified" : "Blocked"}</strong>
                  <p>Observed SHA-256: {packageTrust.observed_sha256}</p>
                  <p>Trust route: {readableToken(packageTrust.trust_route)}</p>
                  {packageTrust.authenticode?.checked && (
                    <p>Signature: {packageTrust.authenticode.status}{packageTrust.authenticode.signer_subject ? ` · ${packageTrust.authenticode.signer_subject}` : ""}</p>
                  )}
                  {packageTrust.block_reasons.map((reason) => <p key={reason}>— {readableToken(reason)}</p>)}
                </div>
              )}
            </div>

            <div className="recovery-list">
              <strong>Windows image selection</strong>
              {systemImageFiles.length > 0 && (
                <label className="path-field">
                  <span>Verified backup image payload</span>
                  <select
                    value={imagePath}
                    onChange={(event) => {
                      setImagePath(event.target.value);
                      setSelectedImageIndex("");
                      setImageMetadata(null);
                      setTargetSafety(null);
                      setTargetVerification(null);
                      setRestoreRollbackContract(null);
      setRestoreHardwarePreflight(null);
      setRollbackDestinationVerification(null);
      setRollbackCaptureReceipt(null);
                    }}
                  >
                    <option value="">Choose an exact VHD/VHDX payload</option>
                    {systemImageFiles.map((relative) => {
                      const fullPath = joinRecoveryPath(sourcePath.trim(), relative);
                      return <option key={relative} value={fullPath}>{relative}</option>;
                    })}
                  </select>
                </label>
              )}
              {systemImageFiles.length === 0 && (
                <p className="field-help">Image source: {imagePath || sourcePath}</p>
              )}
              <label className="path-field">
                <span>Image index</span>
                <input
                  value={selectedImageIndex}
                  onChange={(event) => {
                    setSelectedImageIndex(event.target.value);
                    setImageMetadata(null);
                    setTargetSafety(null);
                    setTargetVerification(null);
                    setRestoreRollbackContract(null);
                    setRestoreHardwarePreflight(null);
                    setRollbackDestinationVerification(null);
                    setRollbackCaptureReceipt(null);
                  }}
                  inputMode="numeric"
                  placeholder="Leave blank to enumerate"
                />
              </label>
              <label className="path-field">
                <span>Target architecture</span>
                <input
                  value={targetArchitecture}
                  onChange={(event) => {
                    setTargetArchitecture(event.target.value);
                    setImageMetadata(null);
                    setTargetSafety(null);
                    setTargetVerification(null);
                    setRestoreRollbackContract(null);
                    setRestoreHardwarePreflight(null);
                    setRollbackDestinationVerification(null);
                    setRollbackCaptureReceipt(null);
                  }}
                  placeholder="x64 or arm64"
                />
              </label>
              <button
                className="plan-button"
                type="button"
                onClick={inspectImageMetadata}
                disabled={busy || !sourceVerification?.matches || (systemImageFiles.length > 0 && !imagePath)}
              >
                Inspect Edition & Architecture
              </button>
              {imageMetadata && (
                <div className={imageMetadata.restore_eligible ? "good-list" : "warning-box"}>
                  <strong>{imageMetadata.restore_eligible ? "Image compatible" : "Selection blocked"}</strong>
                  {imageMetadata.selected_image ? (
                    <p>
                      Index {imageMetadata.selected_image.index}: {imageMetadata.selected_image.name || "Unnamed image"} · {imageMetadata.selected_image.edition_id || "edition unknown"} · {imageMetadata.selected_image.architecture || "architecture unknown"}
                    </p>
                  ) : (
                    <p>{imageMetadata.images.length} image index{imageMetadata.images.length === 1 ? "" : "es"} discovered; select one explicitly.</p>
                  )}
                  {imageMetadata.images.length > 1 && imageMetadata.images.map((image) => (
                    <p key={image.index}>Index {image.index}: {image.name || "Unnamed"} · {image.edition_id || "edition unknown"} · {image.architecture || "architecture unknown"}</p>
                  ))}
                  {imageMetadata.block_reasons.map((reason) => <p key={reason}>— {readableToken(reason)}</p>)}
                </div>
              )}
            </div>
          </div>

          {plan.host_os === "windows" && (
            <div className="recovery-list">
              <strong>Windows physical target</strong>
              <p className="field-help">
                This is a read-only identity/capacity check. Use an exact PHYSICALDRIVE number from Windows disk enumeration; Phoenix Key will also prove the source is on a different physical disk.
              </p>
              <label className="path-field">
                <span>Target disk</span>
                <input
                  value={targetDrive}
                  onChange={(event) => {
                    setTargetDrive(event.target.value);
                    setTargetSafety(null);
                    setTargetVerification(null);
                    setReenumeratedTargetDrive("");
                    setTargetReenumerationReceipt(null);
                    setRestoreRollbackContract(null);
      setRestoreHardwarePreflight(null);
      setRollbackDestinationVerification(null);
      setRollbackCaptureReceipt(null);
                  }}
                  placeholder="PHYSICALDRIVE7"
                />
              </label>
              <button
                className="plan-button"
                type="button"
                onClick={inspectTargetSafety}
                disabled={busy || !targetDrive.trim()}
              >
                Verify Target Safety
              </button>
              {targetSafety && (
                <div className={targetSafety.safe_to_prepare ? "good-list" : "warning-box"}>
                  <strong>{targetSafety.safe_to_prepare ? "Target safe for preparation" : "Target blocked"}</strong>
                  <p>Target: {targetSafety.target || "unresolved"}</p>
                  <p>Snapshot identity: {targetSafety.target_identity_sha256 || "missing"}</p>
                  <p>Stable hardware identity: {targetSafety.target_stable_identity_sha256 || "missing"}</p>
                  <p>Capacity: {targetSafety.target_size_bytes ?? 0} bytes · source: {targetSafety.source_size_bytes} bytes</p>
                  <p>Source device: {targetSafety.source_physical_target || "unproven"}</p>
                  <p>Source stable identity: {targetSafety.source_physical_identity_sha256 || "unproven"}</p>
                  <p>Distinct physical devices: {targetSafety.source_target_distinct === true ? "yes" : "no / unproven"}</p>
                  {targetSafety.block_reasons.map((reason) => <p key={reason}>— {readableToken(reason)}</p>)}
                  {targetSafety.safe_to_prepare && (
                    <button
                      className="plan-button"
                      type="button"
                      onClick={reverifyTargetIdentity}
                      disabled={
                        busy ||
                        !targetSafety.target_identity_sha256 ||
                        !targetSafety.target_stable_identity_sha256
                      }
                    >
                      Freshly Re-Verify Exact Target
                    </button>
                  )}
                  {targetSafety.safe_to_prepare && (
                    <div className="recovery-list">
                      <strong>Reconnect / re-enumeration proof</strong>
                      <p className="field-help">
                        After a real unplug/replug, enter the target's current PHYSICALDRIVE path here. Phoenix Key compares it against the frozen baseline without carrying old authorization forward.
                      </p>
                      <button
                        className="plan-button"
                        type="button"
                        onClick={locateReenumeratedTarget}
                        disabled={busy || !targetSafety.target_stable_identity_sha256}
                      >
                        Locate Same Hardware Automatically
                      </button>
                      {stableTargetLocator && (
                        <div className={stableTargetLocator.unique_match ? "good-list" : "warning-box"}>
                          <p>Locator result: {readableToken(stableTargetLocator.classification)}</p>
                          <p>Matches: {stableTargetLocator.match_count}</p>
                          {stableTargetLocator.match && (
                            <p>
                              Found: {stableTargetLocator.match.target} · {stableTargetLocator.match.bus_type} · {stableTargetLocator.match.size_bytes} bytes
                            </p>
                          )}
                          <p>System mutations performed: {stableTargetLocator.system_mutations_performed ? "yes" : "no"}</p>
                        </div>
                      )}
                      <label className="path-field">
                        <span>Current target after reconnect</span>
                        <input
                          value={reenumeratedTargetDrive}
                          onChange={(event) => {
                            setReenumeratedTargetDrive(event.target.value);
                            setStableTargetLocator(null);
                            setTargetReenumerationReceipt(null);
                          }}
                          placeholder="PHYSICALDRIVE9"
                        />
                      </label>
                      <button
                        className="plan-button"
                        type="button"
                        onClick={inspectTargetReenumeration}
                        disabled={
                          busy ||
                          !reenumeratedTargetDrive.trim() ||
                          !targetSafety.target_identity_sha256 ||
                          !targetSafety.target_stable_identity_sha256
                        }
                      >
                        Compare Re-Enumeration Identity
                      </button>
                    </div>
                  )}
                  {targetSafety.safe_to_prepare && (
                    <button
                      className="plan-button"
                      type="button"
                      onClick={planRestoreRollbackRequirements}
                      disabled={busy}
                    >
                      Plan Full-Restore Rollback Requirements
                    </button>
                  )}
                  {restoreRollbackContract && (
                    <div className="warning-box">
                      <strong>Full-restore rollback remains locked</strong>
                      <p>Contract: {restoreRollbackContract.contract_sha256}</p>
                      <p>Artifact destination: {readableToken(restoreRollbackContract.artifact_destination_requirement)}</p>
                      <p>Fresh target revalidation required: {restoreRollbackContract.fresh_target_revalidation_required ? "yes" : "no"}</p>
                      <p>Restore unlock ready: {restoreRollbackContract.restore_unlock_ready ? "yes" : "no"}</p>
                      <p>System mutations performed: {restoreRollbackContract.system_mutations_performed ? "yes" : "no"}</p>
                      <strong>Required before full restore can ever unlock</strong>
                      {restoreRollbackContract.required_artifacts.map((artifact) => (
                        <p key={artifact}>— {readableToken(artifact)}</p>
                      ))}
                      {restoreRollbackContract.always_blocked_by_this_contract.map((operation) => (
                        <p key={operation}>Blocked now: {readableToken(operation)}</p>
                      ))}
                      <button
                        className="plan-button"
                        type="button"
                        onClick={assessRestoreHardwarePreflight}
                        disabled={
                          busy ||
                          !sourceVerification?.matches ||
                          !imageMetadata ||
                          !targetVerification?.matches ||
                          (plan.source_identity?.source_kind === "file_sha256" && !packageTrust?.verified_for_use)
                        }
                      >
                        Assess Restore Hardware Preflight
                      </button>
                    </div>
                  )}
                  {restoreHardwarePreflight && (
                    <div className={restoreHardwarePreflight.ready_to_capture_hardware_rollback_evidence ? "good-list" : "warning-box"}>
                      <strong>
                        {restoreHardwarePreflight.ready_to_capture_hardware_rollback_evidence
                          ? "Software gates passed — hardware evidence is next"
                          : "Restore preflight blocked"}
                      </strong>
                      <p>Executable: {restoreHardwarePreflight.executable ? "yes" : "no"}</p>
                      <p>System mutations performed: {restoreHardwarePreflight.system_mutations_performed ? "yes" : "no"}</p>
                      <p>Image: {restoreHardwarePreflight.image_path || "unproven"}</p>
                      <p>Rollback contract: {restoreHardwarePreflight.rollback_contract_sha256 || "unproven"}</p>
                      {restoreHardwarePreflight.blocked_gates.map((gate) => (
                        <p key={gate}>Blocked: {readableToken(gate)}</p>
                      ))}
                      <strong>Physical evidence still required</strong>
                      {restoreHardwarePreflight.required_hardware_evidence.map((artifact) => (
                        <p key={artifact}>— {readableToken(artifact)}</p>
                      ))}
                      {restoreHardwarePreflight.ready_to_capture_hardware_rollback_evidence && (
                        <>
                          <button
                            className="plan-button"
                            type="button"
                            onClick={chooseRollbackDestination}
                            disabled={busy}
                          >
                            Choose Separate Rollback Folder
                          </button>
                          {rollbackDestinationPath && (
                            <>
                              <p>Rollback folder: {rollbackDestinationPath}</p>
                              <button
                                className="plan-button"
                                type="button"
                                onClick={verifyRollbackDestination}
                                disabled={busy}
                              >
                                Verify Physical Separation
                              </button>
                            </>
                          )}
                        </>
                      )}
                    </div>
                  )}
                  {rollbackDestinationVerification && (
                    <div className={rollbackDestinationVerification.ready_for_hardware_rollback_capture ? "good-list" : "warning-box"}>
                      <strong>
                        {rollbackDestinationVerification.ready_for_hardware_rollback_capture
                          ? "Rollback destination verified"
                          : "Rollback destination blocked"}
                      </strong>
                      <p>Restore target: {rollbackDestinationVerification.target || "unproven"}</p>
                      <p>Rollback disk: {rollbackDestinationVerification.destination_physical_target || "unproven"}</p>
                      <p>Separate physical device: {rollbackDestinationVerification.separate_physical_device ? "yes" : "no"}</p>
                      <p>Target identity still current: {rollbackDestinationVerification.target_identity_matches_expected ? "yes" : "no"}</p>
                      <p>System mutations performed: {rollbackDestinationVerification.system_mutations_performed ? "yes" : "no"}</p>
                      {rollbackDestinationVerification.block_reasons.map((reason) => (
                        <p key={reason}>— {readableToken(reason)}</p>
                      ))}
                      {rollbackDestinationVerification.ready_for_hardware_rollback_capture && (
                        <button
                          className="plan-button"
                          type="button"
                          onClick={captureRollbackArtifacts}
                          disabled={busy}
                        >
                          Capture Read-Only GPT Rollback Artifacts
                        </button>
                      )}
                    </div>
                  )}
                  {rollbackCaptureReceipt && (
                    <div className={
                      rollbackCaptureReceipt.target_bytes_written === 0 &&
                      !rollbackCaptureReceipt.target_write_attempted
                        ? "good-list"
                        : "warning-box"
                    }>
                      <strong>GPT rollback capture receipt</strong>
                      <p>Output: {rollbackCaptureReceipt.output_directory}</p>
                      <p>Receipt SHA-256: {rollbackCaptureReceipt.receipt_sha256}</p>
                      <p>Target bytes written: {rollbackCaptureReceipt.target_bytes_written}</p>
                      <p>Target write attempted: {rollbackCaptureReceipt.target_write_attempted ? "yes" : "no"}</p>
                      <p>Rollback files written: {rollbackCaptureReceipt.rollback_destination_files_written ? "yes" : "no"}</p>
                      <p>Restore unlock ready: {rollbackCaptureReceipt.restore_unlock_ready ? "yes" : "no"}</p>
                      <strong>Captured</strong>
                      {rollbackCaptureReceipt.captured_requirements.map((item) => (
                        <p key={item}>— {readableToken(item)}</p>
                      ))}
                      <strong>Still required</strong>
                      {rollbackCaptureReceipt.remaining_requirements.map((item) => (
                        <p key={item}>— {readableToken(item)}</p>
                      ))}
                    </div>
                  )}
                  {rollbackCaptureReceipt && (
                    <div className="recovery-list">
                      <strong>External target boot-metadata backup</strong>
                      <p className="field-help">
                        Back up EFI/BCD/WinRE metadata only where the target partitions are already accessible. Phoenix Key will not mount or assign an inaccessible partition just to satisfy this gate.
                      </p>
                      <button
                        className="plan-button"
                        type="button"
                        onClick={captureTargetBootMetadata}
                        disabled={busy || !restoreRollbackContract}
                      >
                        Capture Target Boot Metadata
                      </button>
                      {bootMetadataReceipt && (
                        <div className={bootMetadataReceipt.resolved ? "good-list" : "warning-box"}>
                          <p>Resolved: {bootMetadataReceipt.resolved ? "yes" : "no"}</p>
                          <p>Receipt SHA-256: {bootMetadataReceipt.receipt_sha256}</p>
                          <p>Output: {bootMetadataReceipt.output_directory}</p>
                          <p>Target bytes written: {bootMetadataReceipt.target_bytes_written}</p>
                          <p>Partition mount/assignment attempted: {bootMetadataReceipt.partition_mount_or_assignment_attempted ? "yes" : "no"}</p>
                          <p>Restore unlock ready: {bootMetadataReceipt.restore_unlock_ready ? "yes" : "no"}</p>
                          {bootMetadataReceipt.missing_or_unverified.map((item) => (
                            <p key={item}>Blocked: {readableToken(item)}</p>
                          ))}
                          <p>System mutations performed: {bootMetadataReceipt.system_mutations_performed ? "yes" : "no"}</p>
                        </div>
                      )}
                    </div>
                  )}
                  {restoreRollbackContract && (
                    <div className="recovery-list">
                      <strong>Target data-preservation gate</strong>
                      <p className="field-help">
                        Choose whether existing target data must be preserved or whether you explicitly accept losing it. This records intent only; it never unlocks restore execution.
                      </p>
                      <label className="path-field">
                        <span>Data handling</span>
                        <select
                          value={dataPreservationMode}
                          onChange={(event) => {
                            setDataPreservationMode(event.target.value);
                            setDataPreservationAcknowledgement("");
                            setDataPreservationReceipt(null);
                          }}
                          disabled={busy}
                        >
                          <option value="preserve_existing_data">Preserve existing target data</option>
                          <option value="explicit_discard">Explicitly accept target data loss</option>
                        </select>
                      </label>
                      {dataPreservationMode === "explicit_discard" ? (
                        <label className="path-field">
                          <span>Exact acknowledgement</span>
                          <input
                            value={dataPreservationAcknowledgement}
                            onChange={(event) => {
                              setDataPreservationAcknowledgement(event.target.value);
                              setDataPreservationReceipt(null);
                            }}
                            placeholder="I ACCEPT DATA LOSS ON THIS TARGET"
                          />
                        </label>
                      ) : (
                        <p className="field-help">
                          Preserve mode intentionally stays unresolved until Phoenix Key has a real target-data backup receipt.
                        </p>
                      )}
                      <button
                        className="plan-button"
                        type="button"
                        onClick={createDataPreservationDecision}
                        disabled={busy || !targetSafety?.safe_to_prepare}
                      >
                        Record Data-Preservation Decision
                      </button>
                      {dataPreservationReceipt && (
                        <div className={dataPreservationReceipt.resolved ? "good-list" : "warning-box"}>
                          <p>Mode: {readableToken(dataPreservationReceipt.mode)}</p>
                          <p>Resolved: {dataPreservationReceipt.resolved ? "yes" : "no"}</p>
                          <p>Receipt SHA-256: {dataPreservationReceipt.receipt_sha256}</p>
                          <p>Restore unlock ready: {dataPreservationReceipt.restore_unlock_ready ? "yes" : "no"}</p>
                          {dataPreservationReceipt.block_reasons.map((reason) => (
                            <p key={reason}>Blocked: {readableToken(reason)}</p>
                          ))}
                          {dataPreservationReceipt.required_next_evidence.map((item) => (
                            <p key={item}>Required: {readableToken(item)}</p>
                          ))}
                          <p>System mutations performed: {dataPreservationReceipt.system_mutations_performed ? "yes" : "no"}</p>
                        </div>
                      )}
                    </div>
                  )}
                  {targetVerification && (
                    <div className={targetVerification.matches ? "good-list" : "warning-box"}>
                      <strong>{targetVerification.matches ? "Fresh identity match" : "Reanalysis required"}</strong>
                      <p>Snapshot identity match: {targetVerification.snapshot_matches ? "yes" : "no"}</p>
                      <p>Stable hardware identity match: {targetVerification.stable_identity_matches ? "yes" : "no"}</p>
                      <p>Classification: {readableToken(targetVerification.classification)}</p>
                      <p>Observed snapshot: {targetVerification.observed_snapshot_identity_sha256 || "missing"}</p>
                      <p>Observed stable identity: {targetVerification.observed_stable_identity_sha256 || "missing"}</p>
                      <p>System mutations performed: {targetVerification.system_mutations_performed ? "yes" : "no"}</p>
                    </div>
                  )}
                  {targetReenumerationReceipt && (
                    <div className={
                      targetReenumerationReceipt.substitution_detected ||
                      targetReenumerationReceipt.reanalysis_required
                        ? "warning-box"
                        : "good-list"
                    }>
                      <strong>Target re-enumeration receipt</strong>
                      <p>Classification: {readableToken(targetReenumerationReceipt.classification)}</p>
                      <p>Expected target: {targetReenumerationReceipt.expected_target || "unproven"}</p>
                      <p>Observed target: {targetReenumerationReceipt.observed_target || "unproven"}</p>
                      <p>Same stable hardware: {targetReenumerationReceipt.same_stable_hardware ? "yes" : "no"}</p>
                      <p>Snapshot changed: {targetReenumerationReceipt.snapshot_changed ? "yes" : "no"}</p>
                      <p>Target path changed: {targetReenumerationReceipt.target_path_changed ? "yes" : "no"}</p>
                      <p>Stale authorization rejected: {targetReenumerationReceipt.stale_authorization_rejected ? "yes" : "no"}</p>
                      <p>Substitution detected: {targetReenumerationReceipt.substitution_detected ? "yes" : "no"}</p>
                      <p>Reanalysis required: {targetReenumerationReceipt.reanalysis_required ? "yes" : "no"}</p>
                      <p>Receipt SHA-256: {targetReenumerationReceipt.receipt_sha256}</p>
                      <p>Receipt persisted: {targetReenumerationReceipt.receipt_persisted ? "yes" : "no"}</p>
                      {targetReenumerationReceipt.receipt_path && (
                        <p>Saved receipt: {targetReenumerationReceipt.receipt_path}</p>
                      )}
                      <p>System mutations performed: {targetReenumerationReceipt.system_mutations_performed ? "yes" : "no"}</p>
                    </div>
                  )}
                  {restoreHardwarePreflight && (
                    <div className="recovery-list">
                      <strong>Recovery evidence bundle v2</strong>
                      <p className="field-help">
                        Bind the current plan, identities, image metadata, rollback contract, and any captured hardware receipts into one checksummed session record.
                      </p>
                      <button
                        className="plan-button"
                        type="button"
                        onClick={buildRecoveryEvidenceBundle}
                        disabled={
                          busy ||
                          !sourceVerification ||
                          !imageMetadata ||
                          !targetSafety ||
                          !targetVerification ||
                          !restoreRollbackContract
                        }
                      >
                        Build Recovery Evidence Bundle
                      </button>
                      {recoveryEvidenceBundle && (
                        <div className={
                          recoveryEvidenceBundle.software_chain_complete
                            ? "good-list"
                            : "warning-box"
                        }>
                          <p>Bundle SHA-256: {recoveryEvidenceBundle.bundle_sha256}</p>
                          <p>Software chain complete: {recoveryEvidenceBundle.software_chain_complete ? "yes" : "no"}</p>
                          <p>Hardware chain complete: {recoveryEvidenceBundle.hardware_chain_complete ? "yes" : "no"}</p>
                          <p>Restore executable: {recoveryEvidenceBundle.restore_executable ? "yes" : "no"}</p>
                          <p>System mutations performed: {recoveryEvidenceBundle.system_mutations_performed ? "yes" : "no"}</p>
                          <strong>Outstanding requirements</strong>
                          {recoveryEvidenceBundle.outstanding_requirements.length === 0 ? (
                            <p>None for the currently modeled evidence classes.</p>
                          ) : recoveryEvidenceBundle.outstanding_requirements.map((item) => (
                            <p key={item}>— {readableToken(item)}</p>
                          ))}
                        </div>
                      )}
                      {recoveryEvidenceBundle && (
                        <>
                          <button
                            className="plan-button"
                            type="button"
                            onClick={persistRecoverySessionState}
                            disabled={busy}
                          >
                            Persist Read-Only Recovery Session
                          </button>
                          {recoverySessionState && (
                            <div className={
                              recoverySessionState.stale_evidence_detected ||
                              recoverySessionState.hardware_substitution_detected
                                ? "warning-box"
                                : "good-list"
                            }>
                              <strong>Recovery session state</strong>
                              <p>Session: {recoverySessionState.session_id}</p>
                              <p>Phase: {readableToken(recoverySessionState.phase)}</p>
                              <p>State SHA-256: {recoverySessionState.state_sha256}</p>
                              <p>Read-only resume allowed: {recoverySessionState.read_only_resume_allowed ? "yes" : "no"}</p>
                              <p>Automatic destructive resume allowed: {recoverySessionState.automatic_destructive_resume_allowed ? "yes" : "no"}</p>
                              <p>Destructive authorization persisted: {recoverySessionState.destructive_authorization_persisted ? "yes" : "no"}</p>
                              <p>Restore executable: {recoverySessionState.restore_executable ? "yes" : "no"}</p>
                              <p>Session persisted: {recoverySessionState.session_persisted ? "yes" : "no"}</p>
                              {recoverySessionState.session_path && (
                                <p>Saved session: {recoverySessionState.session_path}</p>
                              )}
                              <strong>Next required actions</strong>
                              {recoverySessionState.next_required_actions.map((item) => (
                                <p key={item}>— {readableToken(item)}</p>
                              ))}
                            </div>
                          )}
                          <button
                            className="plan-button"
                            type="button"
                            onClick={persistRecoveryDiagnosticsExport}
                            disabled={busy}
                          >
                            Export Sanitized Recovery Diagnostics
                          </button>
                          {recoveryDiagnosticsExport && (
                            <div className="good-list">
                              <strong>Sanitized diagnostics export</strong>
                              <p>Export SHA-256: {recoveryDiagnosticsExport.export_sha256}</p>
                              <p>Redacted fields: {recoveryDiagnosticsExport.redacted_fields.length}</p>
                              <p>Destructive authorization included: {recoveryDiagnosticsExport.destructive_authorization_included ? "yes" : "no"}</p>
                              <p>Restore executable: {recoveryDiagnosticsExport.restore_executable ? "yes" : "no"}</p>
                              <p>Export persisted: {recoveryDiagnosticsExport.export_persisted ? "yes" : "no"}</p>
                              {recoveryDiagnosticsExport.export_path && (
                                <p>Saved export: {recoveryDiagnosticsExport.export_path}</p>
                              )}
                              <p>System mutations performed: {recoveryDiagnosticsExport.system_mutations_performed ? "yes" : "no"}</p>
                            </div>
                          )}
                        </>
                      )}
                    </div>
                  )}
                </div>
              )}
            </div>
          )}

          {plan.source_identity && (
            <div className="recovery-list">
              <strong>Fresh source identity gate</strong>
              <p>Planned identity: {plan.source_identity.sha256}</p>
              <p>Source kind: {readableToken(plan.source_identity.source_kind)}</p>
              <button
                className="plan-button"
                type="button"
                onClick={reverifySourceIdentity}
                disabled={busy || !plan.source_identity.sha256}
              >
                Freshly Re-Verify Source Identity
              </button>
              {sourceVerification && (
                <div className={sourceVerification.matches ? "good-list" : "warning-box"}>
                  <strong>{sourceVerification.matches ? "Fresh source identity match" : "Source changed — reanalysis required"}</strong>
                  <p>Expected: {sourceVerification.expected_sha256}</p>
                  <p>Observed: {sourceVerification.observed_sha256}</p>
                  <p>Reanalysis required: {sourceVerification.reanalysis_required ? "yes" : "no"}</p>
                </div>
              )}
            </div>
          )}

          <div className="recovery-columns">
            <div className="recovery-list">
              <strong>Dry-run contract</strong>
              <div>Source ready for planning: {plan.dry_run_summary.source_ready_for_planning ? "yes" : "no"}</div>
              <div>Target selected: {plan.dry_run_summary.target_selected ? "yes" : "no"}</div>
              <div>Target identity verified: {plan.dry_run_summary.target_identity_verified ? "yes" : "no"}</div>
              <div>Rollback evidence persisted: {plan.dry_run_summary.rollback_evidence_persisted ? "yes" : "no"}</div>
              <div>Destructive authorization present: {plan.dry_run_summary.destructive_authorization_present ? "yes" : "no"}</div>
              <div>Mutation steps planned: {plan.dry_run_summary.mutation_steps_planned}</div>
              <div>Mutation steps executed: {plan.dry_run_summary.mutation_steps_executed}</div>
              <div>Executable now: {plan.dry_run_summary.executable ? "yes" : "no"}</div>
            </div>
            <div className="recovery-list">
              <strong>Source & boot contract</strong>
              <div>Source kind: {friendlyKind[plan.source_contract.source_kind] || readableToken(plan.source_contract.source_kind)}</div>
              <div>Content identity required: {plan.source_contract.content_identity_required ? "yes" : "no"}</div>
              <div>Metadata validation required: {plan.source_contract.metadata_validation_required ? "yes" : "no"}</div>
              <div>Complete SWM set required: {plan.source_contract.complete_split_set_required ? "yes" : "no"}</div>
              <div>FAT32 single-file limit check: {plan.source_contract.fat32_single_file_limit_check_required ? "required" : "not applicable"}</div>
              <div>Boot mode: {plan.boot_contract.boot_mode.toUpperCase()}</div>
              <div>EFI files required: {plan.boot_contract.efi_files_required ? "yes" : "no"}</div>
              <div>BCD required: {plan.boot_contract.bcd_required ? "yes" : "no"}</div>
            </div>
          </div>

          {(plan.remediation_required.length > 0 || plan.block_reasons.length > 0) && (
            <div className="recovery-columns">
              <div className="recovery-list">
                <strong>Required remediation</strong>
                {plan.remediation_required.length === 0
                  ? <div>None identified at source-analysis stage</div>
                  : plan.remediation_required.map((item) => <div key={item}>— {item}</div>)}
              </div>
              <div className="recovery-list blocked-list">
                <strong>Current execution blocks</strong>
                {plan.block_reasons.map((reason) => <div key={reason}>— {readableToken(reason)}</div>)}
              </div>
            </div>
          )}

          <div className="recovery-columns">
            <div className="recovery-list">
              <strong>Expected boot artifacts</strong>
              {plan.boot_contract.expected_boot_files.map((item) => <div key={item}>{item}</div>)}
            </div>
            <div className="recovery-list">
              <strong>Expected partition roles</strong>
              {plan.boot_contract.expected_partition_roles.map((item) => <div key={item}>{readableToken(item)}</div>)}
            </div>
          </div>

          <div className="recovery-columns">
            <div className="recovery-list">
              <strong>Execution boundary</strong>
              <div>Planner only: {plan.execution_boundary.planner_only ? "yes" : "no"}</div>
              <div>Restore executor available: {plan.execution_boundary.restore_executor_available ? "yes" : "no"}</div>
              <div>Explicit destructive authorization required: {plan.execution_boundary.destructive_authorization_required ? "yes" : "no"}</div>
              <div>Automatic destructive resume after restart: {plan.execution_boundary.automatic_destructive_resume_allowed ? "allowed" : "forbidden"}</div>
              <div>System mutations performed: {plan.execution_boundary.system_mutations_performed ? "yes" : "no"}</div>
            </div>
            <div className="recovery-list">
              <strong>Target contract</strong>
              <div>Snapshot identity required: {plan.target_contract.snapshot_identity_required ? "yes" : "no"}</div>
              <div>Stable hardware identity required: {plan.target_contract.stable_identity_required ? "yes" : "no"}</div>
              <div>Source/target separation required: {plan.target_contract.source_target_separation_required ? "yes" : "no"}</div>
              <div>Capacity proof required: {plan.target_contract.capacity_check_required ? "yes" : "no"}</div>
              <div>Fresh pre-mutation revalidation required: {plan.target_contract.fresh_revalidation_required ? "yes" : "no"}</div>
            </div>
          </div>

          <div className="recovery-list">
            <strong>Auditable proposed actions</strong>
            {plan.proposed_actions.map((action) => (
              <div key={action.id}>
                {action.mutates_system ? "BLOCKED" : "READ-ONLY"} · {readableToken(action.id)} · {readableToken(action.phase)} · {readableToken(action.status)}
                {action.requires_authorization ? " · authorization required" : ""}
              </div>
            ))}
          </div>

          <div className="recovery-columns">
            <div className="recovery-list good-list">
              <strong>Available planning routes</strong>
              {plan.allowed_operations.map((operation) => <div key={operation}>✓ {readableToken(operation)}</div>)}
            </div>
            <div className="recovery-list blocked-list">
              <strong>Blocked routes</strong>
              {plan.blocked_operations.length === 0
                ? <div>None at this analysis stage</div>
                : plan.blocked_operations.map((operation) => <div key={operation}>— {readableToken(operation)}</div>)}
            </div>
          </div>

          <div className="recovery-list numbered-list">
            <strong>Recommended next steps</strong>
            {plan.next_steps.map((step, index) => <div key={step}><span>{index + 1}</span>{step}</div>)}
          </div>

          <div className="safety-card recovery-safety">
            <strong>No disk changes were made</strong>
            <p>This Recovery Center stage cannot erase, partition, inject drivers, repair BCD, or restore Windows. Those capabilities require a separate verified target contract and explicit authorization.</p>
          </div>

          <button
            className="technical-toggle"
            type="button"
            aria-expanded={showTechnical}
            aria-controls="recovery-technical-evidence"
            onClick={() => setShowTechnical((value) => !value)}
          >
            {showTechnical ? "Hide Technical Evidence" : "Show Technical Evidence"}
          </button>
          {showTechnical && <pre id="recovery-technical-evidence" className="plan-output" tabIndex={0}>{JSON.stringify(plan, null, 2)}</pre>}
        </section>
      )}
    </div>
  );
}
