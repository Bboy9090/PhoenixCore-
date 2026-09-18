import React, { useMemo, useState } from "react";
import { invoke } from "@tauri-apps/api/tauri";
import { open } from "@tauri-apps/api/dialog";
import "./recovery-center.css";

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

type RecoveryTargetSafety = {
  safe_to_prepare: boolean;
  target?: string | null;
  target_identity_sha256?: string | null;
  target_size_bytes?: number | null;
  source_size_bytes: number;
  source_physical_target?: string | null;
  source_target_distinct?: boolean | null;
  block_reasons: string[];
};


type RecoveryTargetDevice = {
  drive_path?: string | null;
  display_name?: string | null;
  size_gb?: number | null;
  is_system?: boolean;
  is_boot_drive?: boolean;
  is_removable?: boolean;
  is_external?: boolean;
  block_reasons?: string[];
};

type DriveScan = {
  devices: RecoveryTargetDevice[];
  scan_warnings: string[];
};

type TargetSafety = {
  safe_to_prepare: boolean;
  target?: string | null;
  target_identity_sha256?: string | null;
  target_size_bytes?: number | null;
  source_size_bytes: number;
  source_physical_target?: string | null;
  source_target_distinct?: boolean | null;
  block_reasons: string[];
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

export default function RecoveryCenter() {
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
  const [targetScan, setTargetScan] = useState<DriveScan | null>(null);
  const [selectedTarget, setSelectedTarget] = useState("");
  const [targetSafety, setTargetSafety] = useState<TargetSafety | null>(null);
  const [targetDrive, setTargetDrive] = useState("");
  const [targetSafety, setTargetSafety] = useState<RecoveryTargetSafety | null>(null);

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

  async function inspectTargetSafety() {
    if (!plan || plan.host_os !== "windows" || !targetDrive.trim() || busy) return;
    setBusy(true);
    setMessage("Re-enumerating the Windows target and proving source/target separation read-only…");
    try {
      const result = await invoke<RecoveryTargetSafety>("inspect_recovery_target_safety", {
        targetDrive: targetDrive.trim(),
        sourcePath: sourcePath.trim(),
      });
      setTargetSafety(result);
      setMessage(
        result.safe_to_prepare
          ? "Target identity, capacity, and source/target separation are verified for planning."
          : "Target safety inspection completed, but the target remains blocked.",
      );
    } catch (error) {
      setTargetSafety(null);
      setMessage(`Target safety inspection could not complete. Nothing was changed. ${String(error)}`);
    } finally {
      setBusy(false);
    }
  }


  async function scanRecoveryTargets() {
    if (!plan || busy) return;
    setBusy(true);
    setMessage("Scanning physical disks read-only. No disk is being changed…");
    try {
      const result = await invoke<DriveScan>("scan_media_targets");
      setTargetScan(result);
      setTargetSafety(null);
      const physical = result.devices.filter((device) => device.drive_path);
      if (!selectedTarget && physical.length === 1 && physical[0].drive_path) {
        setSelectedTarget(physical[0].drive_path);
      }
      setMessage(
        physical.length > 0
          ? "Found " + physical.length + " physical target candidate" + (physical.length === 1 ? "" : "s") + ". Select the exact disk to inspect."
          : "No physical target disks were returned by the read-only scanner.",
      );
    } catch (error) {
      setTargetScan(null);
      setTargetSafety(null);
      setMessage("Target scan could not complete. Nothing was changed. " + String(error));
    } finally {
      setBusy(false);
    }
  }

  async function inspectTargetSafety() {
    if (!plan || !selectedTarget || busy) return;
    setBusy(true);
    setMessage("Rechecking source and target physical identities read-only…");
    try {
      const result = await invoke<TargetSafety>("inspect_recovery_target_safety", {
        targetDrive: selectedTarget,
        sourcePath: sourcePath.trim(),
      });
      setTargetSafety(result);
      setMessage(
        result.safe_to_prepare
          ? "Target identity, capacity, topology, and source separation passed the preparation gate."
          : "Target inspection completed, but destructive restore preparation remains blocked.",
      );
    } catch (error) {
      setTargetSafety(null);
      setMessage("Target safety inspection could not complete. Nothing was changed. " + String(error));
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
        {!isDesktopRuntime() && (
          <div className="warning-box">
            <strong>Desktop app required</strong>
            <p>Local backup inspection is not available in the browser shell. Open Phoenix Key Desktop.</p>
          </div>
        )}
        <div className="source-actions" aria-label="Choose recovery source">
          <button className="scan-button" type="button" onClick={() => chooseSource(true)} disabled={!isDesktopRuntime() || busy}>Choose Backup Folder</button>
          <button className="plan-button" type="button" onClick={() => chooseSource(false)} disabled={!isDesktopRuntime() || busy}>Choose Image File</button>
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
                  <p>Identity: {targetSafety.target_identity_sha256 || "missing"}</p>
                  <p>Capacity: {targetSafety.target_size_bytes ?? 0} bytes · source: {targetSafety.source_size_bytes} bytes</p>
                  <p>Source device: {targetSafety.source_physical_target || "unproven"}</p>
                  <p>Distinct physical devices: {targetSafety.source_target_distinct === true ? "yes" : "no / unproven"}</p>
                  {targetSafety.block_reasons.map((reason) => <p key={reason}>— {readableToken(reason)}</p>)}
                </div>
              )}
            </div>
          )}


          <div className="recovery-list">
            <strong>Target safety</strong>
            <p className="field-help">
              Scan first. Phoenix Key never assumes Disk 0 and does not treat a drive letter as physical-disk proof.
            </p>
            <button className="plan-button" type="button" onClick={scanRecoveryTargets} disabled={busy}>
              Scan Physical Disks Read Only
            </button>
            {targetScan && targetScan.devices.filter((device) => device.drive_path).length > 0 && (
              <label className="path-field">
                <span>Exact physical target</span>
                <select
                  value={selectedTarget}
                  onChange={(event) => {
                    setSelectedTarget(event.target.value);
                    setTargetSafety(null);
                  }}
                >
                  <option value="">Choose a detected disk</option>
                  {targetScan.devices.filter((device) => device.drive_path).map((device) => (
                    <option key={device.drive_path || ""} value={device.drive_path || ""}>
                      {device.display_name || device.drive_path} · {device.size_gb || 0} GB
                      {device.is_system || device.is_boot_drive ? " · current system/boot disk" : ""}
                    </option>
                  ))}
                </select>
              </label>
            )}
            <button
              className="plan-button"
              type="button"
              onClick={inspectTargetSafety}
              disabled={busy || !selectedTarget}
            >
              Verify Source ≠ Target & Capacity
            </button>
            {targetSafety && (
              <div className={targetSafety.safe_to_prepare ? "good-list" : "warning-box"}>
                <strong>{targetSafety.safe_to_prepare ? "Target preparation gate passed" : "Target blocked"}</strong>
                <p>Target: {targetSafety.target || selectedTarget}</p>
                <p>Identity: {targetSafety.target_identity_sha256 || "not proven"}</p>
                <p>Source and target distinct: {targetSafety.source_target_distinct === true ? "Yes" : "Not proven"}</p>
                {targetSafety.block_reasons.map((reason) => <p key={reason}>— {readableToken(reason)}</p>)}
              </div>
            )}
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
