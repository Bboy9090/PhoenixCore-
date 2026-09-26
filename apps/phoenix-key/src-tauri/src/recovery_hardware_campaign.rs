use crate::data_preservation::verify_target_data_preservation_receipt_sha256;
use crate::rollback_destination::verify_rollback_destination_verification_sha256;
use crate::target_safety::{
    verify_recovery_target_identity_verification_sha256,
    verify_recovery_target_safety_sha256,
};
use crate::target_reenumeration::{
    verify_recovery_target_reenumeration_receipt_sha256,
    RecoveryTargetReenumerationReceipt,
};
use serde::Serialize;
use serde_json::{Map, Value};
use sha2::{Digest, Sha256};

const DRIVE_SCHEMA: &str = "bws.physical-drive-evidence/v1";
const ROLLBACK_CAPTURE_SCHEMA: &str = "phoenix_key.restore_target_rollback_capture.v1";
const BOOT_METADATA_SCHEMA: &str = "phoenix_key.restore_target_boot_metadata.v1";

#[derive(Debug, Clone, Serialize, PartialEq, Eq)]
pub struct RecoveryHardwareCampaignReportV1 {
    pub schema: &'static str,
    pub target_live_observed: bool,
    pub rollback_destination_separate: bool,
    pub rollback_capture_live_zero_write: bool,
    pub reconnect_same_hardware_proven: bool,
    pub stale_snapshot_authorization_rejected: bool,
    pub post_reanalysis_fresh_identity_proven: bool,
    pub substitution_rejected: bool,
    pub boot_metadata_live_resolved: bool,
    pub data_preservation_resolved: bool,
    pub fixture_evidence_rejected: bool,
    pub campaign_complete: bool,
    pub restore_executable: bool,
    pub destructive_authorization_granted: bool,
    pub system_mutations_performed: bool,
    pub blockers: Vec<String>,
    pub report_sha256: String,
}

fn valid_sha256(value: &str) -> bool {
    value.len() == 64 && value.bytes().all(|byte| byte.is_ascii_hexdigit())
}

fn same_sha256(left: Option<&str>, right: Option<&str>) -> bool {
    left.zip(right).is_some_and(|(left, right)| {
        valid_sha256(left)
            && valid_sha256(right)
            && left.eq_ignore_ascii_case(right)
    })
}

fn canonicalize_json(value: &Value) -> Value {
    match value {
        Value::Object(object) => {
            let mut keys: Vec<&String> = object.keys().collect();
            keys.sort();
            let mut canonical = Map::new();
            for key in keys {
                canonical.insert(key.clone(), canonicalize_json(&object[key]));
            }
            Value::Object(canonical)
        }
        Value::Array(items) => {
            Value::Array(items.iter().map(canonicalize_json).collect::<Vec<_>>())
        }
        _ => value.clone(),
    }
}

fn value_sha256(value: &Value) -> String {
    let bytes = serde_json::to_vec(&canonicalize_json(value))
        .expect("hardware campaign JSON serialization cannot fail");
    format!("{:x}", Sha256::digest(bytes))
}

fn verify_embedded_sha256(value: &Value, field: &str) -> bool {
    let Some(expected) = value.get(field).and_then(Value::as_str) else {
        return false;
    };
    if !valid_sha256(expected) {
        return false;
    }
    let mut unsigned = value.clone();
    let Some(object) = unsigned.as_object_mut() else {
        return false;
    };
    object.remove(field);
    value_sha256(&unsigned).eq_ignore_ascii_case(expected)
}

fn live_drive(value: &Value) -> bool {
    value.get("schema_version").and_then(Value::as_str) == Some(DRIVE_SCHEMA)
        && verify_embedded_sha256(value, "receipt_sha256")
        && value.get("evidence_source").and_then(Value::as_str) == Some("live")
        && value.get("hardware_observed").and_then(Value::as_bool) == Some(true)
        && value.get("bytes_written").and_then(Value::as_u64) == Some(0)
        && value
            .get("physical_write_attempted")
            .and_then(Value::as_bool)
            == Some(false)
        && value
            .pointer("/disk/identity_sha256")
            .and_then(Value::as_str)
            .is_some_and(valid_sha256)
        && value
            .pointer("/disk/stable_identity_sha256")
            .and_then(Value::as_str)
            .is_some_and(valid_sha256)
}

fn verified_reenumeration(value: &Value) -> Option<RecoveryTargetReenumerationReceipt> {
    serde_json::from_value::<RecoveryTargetReenumerationReceipt>(value.clone())
        .ok()
        .filter(verify_recovery_target_reenumeration_receipt_sha256)
}

fn report_sha256(report: &RecoveryHardwareCampaignReportV1) -> String {
    let mut value = serde_json::to_value(report)
        .expect("hardware campaign report serialization cannot fail");
    if let Some(object) = value.as_object_mut() {
        object.remove("report_sha256");
    }
    value_sha256(&value)
}

fn push_blocker(blockers: &mut Vec<String>, blocker: &str) {
    if !blockers.iter().any(|existing| existing == blocker) {
        blockers.push(blocker.to_string());
    }
}

pub fn build_recovery_hardware_campaign_report(
    evidence: &Value,
) -> RecoveryHardwareCampaignReportV1 {
    let baseline = evidence
        .get("baseline_target_drive_evidence")
        .unwrap_or(&Value::Null);
    let rollback_destination = evidence
        .get("rollback_destination_verification")
        .unwrap_or(&Value::Null);
    let rollback_capture = evidence
        .get("rollback_capture_receipt")
        .unwrap_or(&Value::Null);
    let reconnect_drive = evidence
        .get("reconnect_target_drive_evidence")
        .unwrap_or(&Value::Null);
    let reconnect_receipt = evidence
        .get("reconnect_reenumeration_receipt")
        .unwrap_or(&Value::Null);
    let post_reanalysis_safety = evidence
        .get("post_reanalysis_target_safety")
        .unwrap_or(&Value::Null);
    let post_reanalysis_verification = evidence
        .get("post_reanalysis_target_verification")
        .unwrap_or(&Value::Null);
    let substitution_drive = evidence
        .get("substitution_target_drive_evidence")
        .unwrap_or(&Value::Null);
    let substitution_receipt = evidence
        .get("substitution_reenumeration_receipt")
        .unwrap_or(&Value::Null);
    let boot_metadata = evidence
        .get("boot_metadata_receipt")
        .unwrap_or(&Value::Null);
    let data_preservation = evidence
        .get("data_preservation_receipt")
        .unwrap_or(&Value::Null);

    let baseline_live = live_drive(baseline);
    let baseline_snapshot = baseline
        .pointer("/disk/identity_sha256")
        .and_then(Value::as_str);
    let baseline_stable = baseline
        .pointer("/disk/stable_identity_sha256")
        .and_then(Value::as_str);

    let rollback_destination_separate = baseline_live
        && verify_rollback_destination_verification_sha256(rollback_destination)
        && rollback_destination
            .get("ready_for_hardware_rollback_capture")
            .and_then(Value::as_bool)
            == Some(true)
        && rollback_destination
            .get("separate_physical_device")
            .and_then(Value::as_bool)
            == Some(true)
        && rollback_destination
            .get("target_identity_matches_expected")
            .and_then(Value::as_bool)
            == Some(true)
        && rollback_destination
            .get("system_mutations_performed")
            .and_then(Value::as_bool)
            == Some(false)
        && same_sha256(
            baseline_stable,
            rollback_destination
                .get("target_stable_identity_sha256")
                .and_then(Value::as_str),
        );

    let rollback_capture_live_zero_write = baseline_live
        && rollback_capture.get("schema").and_then(Value::as_str)
            == Some(ROLLBACK_CAPTURE_SCHEMA)
        && verify_embedded_sha256(rollback_capture, "receipt_sha256")
        && rollback_capture
            .get("evidence_source")
            .and_then(Value::as_str)
            == Some("live")
        && rollback_capture
            .get("hardware_observed")
            .and_then(Value::as_bool)
            == Some(true)
        && rollback_capture
            .get("target_bytes_written")
            .and_then(Value::as_u64)
            == Some(0)
        && rollback_capture
            .get("target_write_attempted")
            .and_then(Value::as_bool)
            == Some(false)
        && rollback_capture
            .get("restore_unlock_ready")
            .and_then(Value::as_bool)
            == Some(false)
        && rollback_capture
            .get("system_mutations_performed")
            .and_then(Value::as_bool)
            == Some(false)
        && same_sha256(
            baseline_snapshot,
            rollback_capture
                .get("target_snapshot_identity_sha256")
                .and_then(Value::as_str),
        )
        && same_sha256(
            baseline_stable,
            rollback_capture
                .get("target_stable_identity_sha256")
                .and_then(Value::as_str),
        );

    let rollback_contract_sha256 = rollback_capture
        .get("rollback_contract_sha256")
        .and_then(Value::as_str)
        .filter(|value| valid_sha256(value));

    let reconnect_live = live_drive(reconnect_drive);
    let reconnect_snapshot = reconnect_drive
        .pointer("/disk/identity_sha256")
        .and_then(Value::as_str);
    let reconnect_stable = reconnect_drive
        .pointer("/disk/stable_identity_sha256")
        .and_then(Value::as_str);
    let reconnect_receipt = verified_reenumeration(reconnect_receipt);

    let reconnect_same_hardware_proven = reconnect_live
        && same_sha256(baseline_stable, reconnect_stable)
        && reconnect_receipt.as_ref().is_some_and(|receipt| {
            receipt.same_stable_hardware
                && !receipt.substitution_detected
                && receipt.reanalysis_required
                && (receipt.snapshot_changed || receipt.target_path_changed)
                && same_sha256(
                    baseline_stable,
                    Some(receipt.expected_stable_identity_sha256.as_str()),
                )
                && same_sha256(
                    reconnect_stable,
                    receipt.observed_stable_identity_sha256.as_deref(),
                )
                && !receipt.system_mutations_performed
        });

    let stale_snapshot_authorization_rejected = reconnect_receipt
        .as_ref()
        .is_some_and(|receipt| {
            reconnect_same_hardware_proven && receipt.stale_authorization_rejected
        });

    let post_reanalysis_fresh_identity_proven = reconnect_same_hardware_proven
        && verify_recovery_target_safety_sha256(post_reanalysis_safety)
        && verify_recovery_target_identity_verification_sha256(post_reanalysis_verification)
        && post_reanalysis_safety
            .get("safe_to_prepare")
            .and_then(Value::as_bool)
            == Some(true)
        && post_reanalysis_safety
            .get("source_target_distinct")
            .and_then(Value::as_bool)
            == Some(true)
        && same_sha256(
            reconnect_snapshot,
            post_reanalysis_safety
                .get("target_identity_sha256")
                .and_then(Value::as_str),
        )
        && same_sha256(
            reconnect_stable,
            post_reanalysis_safety
                .get("target_stable_identity_sha256")
                .and_then(Value::as_str),
        )
        && post_reanalysis_verification
            .get("matches")
            .and_then(Value::as_bool)
            == Some(true)
        && post_reanalysis_verification
            .get("reanalysis_required")
            .and_then(Value::as_bool)
            == Some(false)
        && same_sha256(
            reconnect_snapshot,
            post_reanalysis_verification
                .get("observed_snapshot_identity_sha256")
                .and_then(Value::as_str),
        )
        && same_sha256(
            reconnect_stable,
            post_reanalysis_verification
                .get("observed_stable_identity_sha256")
                .and_then(Value::as_str),
        )
        && post_reanalysis_verification
            .get("system_mutations_performed")
            .and_then(Value::as_bool)
            == Some(false);

    let substitution_live = live_drive(substitution_drive);
    let substitution_stable = substitution_drive
        .pointer("/disk/stable_identity_sha256")
        .and_then(Value::as_str);
    let substitution_receipt = verified_reenumeration(substitution_receipt);

    let substitution_rejected = substitution_live
        && baseline_stable
            .zip(substitution_stable)
            .is_some_and(|(expected, observed)| {
                valid_sha256(expected)
                    && valid_sha256(observed)
                    && !expected.eq_ignore_ascii_case(observed)
            })
        && substitution_receipt.as_ref().is_some_and(|receipt| {
            !receipt.same_stable_hardware
                && receipt.substitution_detected
                && receipt.reanalysis_required
                && same_sha256(
                    baseline_stable,
                    Some(receipt.expected_stable_identity_sha256.as_str()),
                )
                && same_sha256(
                    substitution_stable,
                    receipt.observed_stable_identity_sha256.as_deref(),
                )
                && !receipt.system_mutations_performed
        });

    let boot_metadata_live_resolved = boot_metadata
        .get("schema")
        .and_then(Value::as_str)
        == Some(BOOT_METADATA_SCHEMA)
        && verify_embedded_sha256(boot_metadata, "receipt_sha256")
        && boot_metadata
            .get("evidence_source")
            .and_then(Value::as_str)
            == Some("live")
        && boot_metadata
            .get("hardware_observed")
            .and_then(Value::as_bool)
            == Some(true)
        && boot_metadata.get("resolved").and_then(Value::as_bool) == Some(true)
        && boot_metadata
            .get("target_bytes_written")
            .and_then(Value::as_u64)
            == Some(0)
        && boot_metadata
            .get("target_write_attempted")
            .and_then(Value::as_bool)
            == Some(false)
        && boot_metadata
            .get("partition_mount_or_assignment_attempted")
            .and_then(Value::as_bool)
            == Some(false)
        && boot_metadata
            .get("system_mutations_performed")
            .and_then(Value::as_bool)
            == Some(false)
        && same_sha256(
            baseline_stable,
            boot_metadata
                .get("target_stable_identity_sha256")
                .and_then(Value::as_str),
        )
        && same_sha256(
            rollback_contract_sha256,
            boot_metadata
                .get("rollback_contract_sha256")
                .and_then(Value::as_str),
        );

    let data_preservation_resolved =
        verify_target_data_preservation_receipt_sha256(data_preservation)
        && data_preservation
        .get("schema")
        .and_then(Value::as_str)
        == Some("phoenix_key.target_data_preservation_receipt.v1")
        && data_preservation
            .get("resolved")
            .and_then(Value::as_bool)
            == Some(true)
        && data_preservation
            .get("restore_unlock_ready")
            .and_then(Value::as_bool)
            == Some(false)
        && data_preservation
            .get("system_mutations_performed")
            .and_then(Value::as_bool)
            == Some(false)
        && same_sha256(
            baseline_stable,
            data_preservation
                .get("target_stable_identity_sha256")
                .and_then(Value::as_str),
        )
        && same_sha256(
            rollback_contract_sha256,
            data_preservation
                .get("rollback_contract_sha256")
                .and_then(Value::as_str),
        );

    let fixture_evidence_rejected = [
        baseline,
        rollback_capture,
        reconnect_drive,
        substitution_drive,
        boot_metadata,
    ]
    .iter()
    .all(|value| {
        value.get("evidence_source").and_then(Value::as_str) != Some("fixture")
            && value.get("platform").and_then(Value::as_str) != Some("fixture")
    });

    let mut blockers = Vec::new();
    if !baseline_live {
        push_blocker(&mut blockers, "live_baseline_target_evidence_required");
    }
    if !rollback_destination_separate {
        push_blocker(&mut blockers, "separate_rollback_destination_not_proven");
    }
    if !rollback_capture_live_zero_write {
        push_blocker(&mut blockers, "live_zero_write_gpt_rollback_capture_required");
    }
    if !reconnect_same_hardware_proven {
        push_blocker(&mut blockers, "physical_reconnect_same_hardware_not_proven");
    }
    if !stale_snapshot_authorization_rejected {
        push_blocker(&mut blockers, "stale_snapshot_authorization_rejection_not_proven");
    }
    if !post_reanalysis_fresh_identity_proven {
        push_blocker(&mut blockers, "post_reconnect_reanalysis_not_proven");
    }
    if !substitution_rejected {
        push_blocker(&mut blockers, "hardware_substitution_rejection_not_proven");
    }
    if !boot_metadata_live_resolved {
        push_blocker(&mut blockers, "live_target_boot_metadata_not_resolved");
    }
    if !data_preservation_resolved {
        push_blocker(&mut blockers, "target_data_preservation_not_resolved");
    }
    if !fixture_evidence_rejected {
        push_blocker(&mut blockers, "fixture_evidence_cannot_satisfy_hardware_campaign");
    }

    let campaign_complete = blockers.is_empty();
    let mut report = RecoveryHardwareCampaignReportV1 {
        schema: "phoenix_key.recovery_hardware_campaign_report.v1",
        target_live_observed: baseline_live,
        rollback_destination_separate,
        rollback_capture_live_zero_write,
        reconnect_same_hardware_proven,
        stale_snapshot_authorization_rejected,
        post_reanalysis_fresh_identity_proven,
        substitution_rejected,
        boot_metadata_live_resolved,
        data_preservation_resolved,
        fixture_evidence_rejected,
        campaign_complete,
        restore_executable: false,
        destructive_authorization_granted: false,
        system_mutations_performed: false,
        blockers,
        report_sha256: String::new(),
    };
    report.report_sha256 = report_sha256(&report);
    report
}

#[tauri::command]
pub fn assess_windows_recovery_hardware_campaign(
    evidence_json: String,
) -> Result<RecoveryHardwareCampaignReportV1, String> {
    let evidence: Value = serde_json::from_str(&evidence_json)
        .map_err(|error| format!("invalid hardware campaign evidence JSON: {error}"))?;
    Ok(build_recovery_hardware_campaign_report(&evidence))
}

#[cfg(test)]
mod tests {
    use super::{
        build_recovery_hardware_campaign_report, value_sha256, DRIVE_SCHEMA,
        ROLLBACK_CAPTURE_SCHEMA,
    };
    use crate::target_reenumeration::compare_recovery_target_reenumeration;
    use serde_json::{json, Value};

    fn with_digest(mut value: Value, field: &str) -> Value {
        let digest = value_sha256(&value);
        value[field] = Value::String(digest);
        value
    }

    fn drive(target: &str, snapshot: &str, stable: &str, live: bool) -> Value {
        with_digest(
            json!({
                "schema_version": DRIVE_SCHEMA,
                "evidence_source": if live { "live" } else { "fixture" },
                "platform": if live { "windows" } else { "fixture" },
                "hardware_observed": live,
                "bytes_written": 0,
                "physical_write_attempted": false,
                "disk": {
                    "target": target,
                    "identity_sha256": snapshot,
                    "stable_identity_sha256": stable
                }
            }),
            "receipt_sha256",
        )
    }

    fn rollback_capture(snapshot: &str, stable: &str, live: bool) -> Value {
        with_digest(
            json!({
                "schema": ROLLBACK_CAPTURE_SCHEMA,
                "evidence_source": if live { "live" } else { "fixture" },
                "hardware_observed": live,
                "target_snapshot_identity_sha256": snapshot,
                "target_stable_identity_sha256": stable,
                "rollback_contract_sha256": "d".repeat(64),
                "target_bytes_written": 0,
                "target_write_attempted": false,
                "restore_unlock_ready": false,
                "system_mutations_performed": false
            }),
            "receipt_sha256",
        )
    }

    fn complete_evidence(live: bool) -> Value {
        let baseline = drive(
            "\\\\.\\PHYSICALDRIVE7",
            &"a".repeat(64),
            &"b".repeat(64),
            live,
        );
        let reconnect = drive(
            "\\\\.\\PHYSICALDRIVE9",
            &"c".repeat(64),
            &"b".repeat(64),
            live,
        );
        let substitution = drive(
            "\\\\.\\PHYSICALDRIVE11",
            &"e".repeat(64),
            &"f".repeat(64),
            live,
        );
        let reconnect_receipt = compare_recovery_target_reenumeration(
            &reconnect,
            Some("\\\\.\\PHYSICALDRIVE7"),
            &"a".repeat(64),
            &"b".repeat(64),
        );
        let substitution_receipt = compare_recovery_target_reenumeration(
            &substitution,
            Some("\\\\.\\PHYSICALDRIVE7"),
            &"a".repeat(64),
            &"b".repeat(64),
        );
        let boot = with_digest(
            json!({
                "schema": "phoenix_key.restore_target_boot_metadata.v1",
                "evidence_source": if live { "live" } else { "fixture" },
                "hardware_observed": live,
                "target_stable_identity_sha256": "b".repeat(64),
                "resolved": true,
                "target_bytes_written": 0,
                "target_write_attempted": false,
                "partition_mount_or_assignment_attempted": false,
                "system_mutations_performed": false
            }),
            "receipt_sha256",
        );
        json!({
            "baseline_target_drive_evidence": baseline,
            "rollback_destination_verification": {
                "ready_for_hardware_rollback_capture": true,
                "separate_physical_device": true,
                "target_identity_matches_expected": true,
                "target_stable_identity_sha256": "b".repeat(64),
                "system_mutations_performed": false
            },
            "rollback_capture_receipt": rollback_capture(&"a".repeat(64), &"b".repeat(64), live),
            "reconnect_target_drive_evidence": reconnect,
            "reconnect_reenumeration_receipt": reconnect_receipt,
            "post_reanalysis_target_safety": {
                "safe_to_prepare": true,
                "source_target_distinct": true,
                "target_identity_sha256": "c".repeat(64),
                "target_stable_identity_sha256": "b".repeat(64)
            },
            "post_reanalysis_target_verification": {
                "matches": true,
                "reanalysis_required": false,
                "observed_snapshot_identity_sha256": "c".repeat(64),
                "observed_stable_identity_sha256": "b".repeat(64),
                "system_mutations_performed": false
            },
            "substitution_target_drive_evidence": substitution,
            "substitution_reenumeration_receipt": substitution_receipt,
            "boot_metadata_receipt": boot,
            "data_preservation_receipt": {
                "schema": "phoenix_key.target_data_preservation_receipt.v1",
                "resolved": true,
                "target_stable_identity_sha256": "b".repeat(64),
                "restore_unlock_ready": false,
                "system_mutations_performed": false
            }
        })
    }

    #[test]
    fn complete_live_campaign_can_pass_without_unlocking_restore() {
        let report = build_recovery_hardware_campaign_report(&complete_evidence(true));
        assert!(report.campaign_complete);
        assert!(report.fixture_evidence_rejected);
        assert!(report.blockers.is_empty());
        assert!(!report.restore_executable);
        assert!(!report.destructive_authorization_granted);
        assert!(!report.system_mutations_performed);
        assert_eq!(report.report_sha256.len(), 64);
    }

    #[test]
    fn fixture_receipts_never_satisfy_hardware_campaign() {
        let report = build_recovery_hardware_campaign_report(&complete_evidence(false));
        assert!(!report.campaign_complete);
        assert!(!report.target_live_observed);
        assert!(!report.rollback_capture_live_zero_write);
        assert!(!report.boot_metadata_live_resolved);
        assert!(!report.fixture_evidence_rejected);
        assert!(report
            .blockers
            .contains(&"fixture_evidence_cannot_satisfy_hardware_campaign".to_string()));
        assert!(!report.restore_executable);
    }

    #[test]
    fn missing_substitution_proof_blocks_campaign() {
        let mut evidence = complete_evidence(true);
        evidence["substitution_target_drive_evidence"] = Value::Null;
        evidence["substitution_reenumeration_receipt"] = Value::Null;
        let report = build_recovery_hardware_campaign_report(&evidence);
        assert!(!report.campaign_complete);
        assert!(report
            .blockers
            .contains(&"hardware_substitution_rejection_not_proven".to_string()));
    }

    #[test]
    fn reconnect_without_stale_authorization_rejection_blocks_campaign() {
        let mut evidence = complete_evidence(true);
        evidence["reconnect_target_drive_evidence"] = drive(
            "\\\\.\\PHYSICALDRIVE7",
            &"a".repeat(64),
            &"b".repeat(64),
            true,
        );
        evidence["reconnect_reenumeration_receipt"] =
            serde_json::to_value(compare_recovery_target_reenumeration(
                &evidence["reconnect_target_drive_evidence"],
                Some("\\\\.\\PHYSICALDRIVE7"),
                &"a".repeat(64),
                &"b".repeat(64),
            ))
            .unwrap();
        let report = build_recovery_hardware_campaign_report(&evidence);
        assert!(!report.campaign_complete);
        assert!(!report.stale_snapshot_authorization_rejected);
    }
}
