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
  warnings: string[];
  detected_by: string[];
};

type SourceIdentity = {
  sha256: string;
  size_bytes: number;
  source_kind: string;
  complete: boolean;
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
  next_steps: string[];
  dry_run: boolean;
  destructive_actions_performed: boolean;
  source_identity?: SourceIdentity;
  source_identity_gate?: string;
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

export default function RecoveryCenter({
  distributionProfile,
}: {
  distributionProfile: DistributionProfile | null;
}) {
  const [sourcePath, setSourcePath] = useState("");
  const [analysis, setAnalysis] = useState<RecoveryAnalysis | null>(null);
  const [plan, setPlan] = useState<RecoveryPlan | null>(null);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState(
    "Choose the Windows backup or recovery source you want Phoenix Key to inspect. Analysis does not change disks.",
  );
  const [showTechnical, setShowTechnical] = useState(false);
  const [expectedSha256, setExpectedSha256] = useState("");
  const [selectedImageIndex, setSelectedImageIndex] = useState("");
  const [targetArchitecture, setTargetArchitecture] = useState("");
  const [packageTrust, setPackageTrust] = useState<PackageTrust | null>(null);
  const [imageMetadata, setImageMetadata] = useState<ImageMetadata | null>(null);
  const [targetDrive, setTargetDrive] = useState("");
  const [targetSafety, setTargetSafety] = useState<RecoveryTargetSafety | null>(null);
  const [targetVerification, setTargetVerification] = useState<RecoveryTargetIdentityVerification | null>(null);
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

  const canAnalyze = isDesktopRuntime() && sourcePath.trim().length > 0 && !busy;
  const sourceState = useMemo(() => {
    if (!analysis) return "Not analyzed";
    if (analysis.restore_candidate && analysis.warnings.length === 0) return "Ready to plan";
    if (analysis.restore_candidate) return "Plan with warnings";
    return "Blocked until fixed";
  }, [analysis]);

  function resetResult(nextPath: string) {
    setSourcePath(nextPath);
    setAnalysis(null);
    setPlan(null);
    setShowTechnical(false);
    setExpectedSha256("");
    setSelectedImageIndex("");
    setTargetArchitecture("");
    setPackageTrust(null);
    setImageMetadata(null);
    setTargetDrive("");
    setTargetSafety(null);
    setTargetVerification(null);
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
      setTargetArchitecture(result.host_arch || "");
      setPackageTrust(null);
      setImageMetadata(null);
      setMessage("Recovery plan created and bound to the current source identity. No disk was changed.");
    } catch (error) {
      setPlan(null);
      setMessage(String(error));
    } finally {
      setBusy(false);
    }
  }

  async function verifyPackageTrust() {
    if (storeSafe) {
      setMessage("External package-trust helpers are disabled in the store-safe distribution.");
      return;
    }
    if (!plan || !expectedSha256.trim() || busy) return;
    setBusy(true);
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
    if (!plan || busy) return;
    const indexText = selectedImageIndex.trim();
    const parsedIndex = indexText ? Number(indexText) : undefined;
    if (indexText && (!Number.isInteger(parsedIndex) || (parsedIndex || 0) <= 0)) {
      setMessage("Windows image index must be a positive whole number.");
      return;
    }
    setBusy(true);
    setMessage("Reading Windows image index, edition, and architecture metadata with no mount or modification…");
    try {
      const result = await invoke<ImageMetadata>("inspect_windows_image_metadata", {
        imagePath: sourcePath.trim(),
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
    if (!plan || plan.host_os !== "windows" || !targetDrive.trim() || busy) return;
    setBusy(true);
    setMessage("Re-enumerating the Windows target and proving source/target separation read-only…");
    try {
      const result = await invoke<RecoveryTargetSafety>("inspect_recovery_target_safety", {
        targetDrive: targetDrive.trim(),
        sourcePath: sourcePath.trim(),
      });
      setTargetSafety(result);
      setTargetVerification(null);
      setMessage(
        result.safe_to_prepare
          ? "Target identity, capacity, and source/target separation are verified for planning."
          : "Target safety inspection completed, but the target remains blocked.",
      );
    } catch (error) {
      setTargetSafety(null);
      setTargetVerification(null);
      setMessage(`Target safety inspection could not complete. Nothing was changed. ${String(error)}`);
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
            <div><span>Disk image files</span><strong>{analysis.system_image_files.length}</strong></div>
          </div>

          {analysis.warnings.length > 0 && (
            <div className="warning-box">
              <strong>Fix before restoring</strong>
              {analysis.warnings.map((warning) => <p key={warning}>{warning}</p>)}
            </div>
          )}

          {analysis.system_image_files.length > 0 && (
            <div className="recovery-list">
              <strong>Backup disk images found</strong>
              {analysis.system_image_files.map((path) => <div key={path}>{path}</div>)}
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
              <label className="path-field">
                <span>Image index</span>
                <input
                  value={selectedImageIndex}
                  onChange={(event) => {
                    setSelectedImageIndex(event.target.value);
                    setImageMetadata(null);
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
                  }}
                  placeholder="x64 or arm64"
                />
              </label>
              <button className="plan-button" type="button" onClick={inspectImageMetadata} disabled={busy}>
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
                </div>
              )}
            </div>
          )}

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
