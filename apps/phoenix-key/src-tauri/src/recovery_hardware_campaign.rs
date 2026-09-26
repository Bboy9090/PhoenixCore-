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

const EVIDENCE_PACKAGE_SCHEMA: &str = "phoenix_key.recovery_hardware_campaign_evidence_package.v1";
const DRIVE_SCHEMA: &str = "bws.physical-drive-evidence/v1";
const ROLLBACK_CAPTURE_SCHEMA: &str = "phoenix_key.restore_target_rollback_capture.v1";
const BOOT_METADATA_SCHEMA: &str = "phoenix_key.restore_target_boot_metadata.v1";

#[derive(Debug, Clone, Serialize, PartialEq, Eq)]
pub struct RecoveryHardwareCampaignReportV1 {
    pub schema: &'static str,
    pub evidence_package_verified: bool,
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

fn verify_evidence_package(value: &Value) -> bool {
    value.get("schema").and_then(Value::as_str) == Some(EVIDENCE_PACKAGE_SCHEMA)
        && verify_embedded_sha256(value, "package_sha256")
        && value
            .get("fixture_evidence_allowed")
            .and_then(Value::as_bool)
            == Some(false)
        && value.get("restore_executable").and_then(Value::as_bool) == Some(false)
        && value
            .get("destructive_authorization_granted")
            .and_then(Value::as_bool)
            == Some(false)
        && value
            .get("system_mutations_performed")
            .and_then(Value::as_bool)
            == Some(false)
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
    let evidence_package_verified = verify_evidence_package(evidence);
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
    if !evidence_package_verified {
        push_blocker(
            &mut blockers,
            "hardware_authority_evidence_package_invalid",
        );
    }
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
        evidence_package_verified,
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
        EVIDENCE_PACKAGE_SCHEMA, ROLLBACK_CAPTURE_SCHEMA,
    };
    use crate::data_preservation::{
        build_target_data_preservation_receipt, EXPLICIT_DISCARD_ACKNOWLEDGEMENT,
    };
    use crate::restore_rollback_contract::build_restore_target_rollback_contract;
    use crate::rollback_destination::assess_rollback_destination;
    use crate::source_identity::identity_bound_plan_sha256;
    use crate::target_reenumeration::compare_recovery_target_reenumeration;
    use crate::target_safety::{assess_recovery_target, verify_recovery_target_identity};
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
                    "stable_identity_sha256": stable,
                    "size_bytes": 64_000u64,
                    "is_boot": false,
                    "is_system": false,
                    "write_candidate": true,
                    "write_block_reasons": []
                }
            }),
            "receipt_sha256",
        )
    }

    fn rollback_capture(
        snapshot: &str,
        stable: &str,
        rollback_contract_sha256: &str,
        live: bool,
    ) -> Value {
        with_digest(
            json!({
                "schema": ROLLBACK_CAPTURE_SCHEMA,
                "evidence_source": if live { "live" } else { "fixture" },
                "hardware_observed": live,
                "target_snapshot_identity_sha256": snapshot,
                "target_stable_identity_sha256": stable,
                "rollback_contract_sha256": rollback_contract_sha256,
                "target_bytes_written": 0,
                "target_write_attempted": false,
                "restore_unlock_ready": false,
                "system_mutations_performed": false
            }),
            "receipt_sha256",
        )
    }

    fn plan() -> Value {
        let mut plan = json!({
            "schema": "phoenix_key.windows_recovery_plan.v4",
            "source_identity": {
                "sha256": "9".repeat(64),
                "complete": true,
                "source_kind": "file_sha256",
                "canonical_path": "C:/recovery/install.wim",
                "size_bytes": 1024
            },
            "execution_boundary": {
                "planner_only": true,
                "restore_executor_available": false,
                "system_mutations_performed": false
            },
            "dry_run_summary": {
                "executable": false,
                "mutation_steps_executed": 0
            },
            "destructive_actions_performed": false
        });
        plan["plan_sha256"] = Value::String(identity_bound_plan_sha256(&plan).unwrap());
        plan
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
        let baseline_safety = assess_recovery_target(
            &baseline,
            1024,
            Some("\\\\.\\PHYSICALDRIVE8"),
            Some(&"8".repeat(64)),
        );
        let rollback_contract =
            build_restore_target_rollback_contract(&plan(), &serde_json::to_value(&baseline_safety).unwrap())
                .unwrap();
        let rollback_contract_sha256 = rollback_contract.contract_sha256.clone();
        let rollback_destination = assess_rollback_destination(
            &baseline,
            &json!({
                "source": {
                    "physical_target": "\\\\.\\PHYSICALDRIVE12",
                    "stable_identity_sha256": "7".repeat(64)
                }
            }),
            "E:/PhoenixKeyRollback",
            &"b".repeat(64),
        );
        let reconnect_safety = assess_recovery_target(
            &reconnect,
            1024,
            Some("\\\\.\\PHYSICALDRIVE8"),
            Some(&"8".repeat(64)),
        );
        let reconnect_verification =
            verify_recovery_target_identity(&reconnect, &"c".repeat(64), &"b".repeat(64));
        let data_preservation = build_target_data_preservation_receipt(
            &serde_json::to_value(&baseline_safety).unwrap(),
            &serde_json::to_value(&rollback_contract).unwrap(),
            "explicit_discard",
            EXPLICIT_DISCARD_ACKNOWLEDGEMENT,
        )
        .unwrap();

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
                "rollback_contract_sha256": rollback_contract_sha256.clone(),
                "resolved": true,
                "target_bytes_written": 0,
                "target_write_attempted": false,
                "partition_mount_or_assignment_attempted": false,
                "system_mutations_performed": false
            }),
            "receipt_sha256",
        );
        let mut package = json!({
            "schema": EVIDENCE_PACKAGE_SCHEMA,
            "baseline_target_drive_evidence": baseline,
            "rollback_destination_verification": rollback_destination,
            "rollback_capture_receipt": rollback_capture(
                &"a".repeat(64),
                &"b".repeat(64),
                &rollback_contract_sha256,
                live,
            ),
            "reconnect_target_drive_evidence": reconnect,
            "reconnect_reenumeration_receipt": reconnect_receipt,
            "post_reanalysis_target_safety": reconnect_safety,
            "post_reanalysis_target_verification": reconnect_verification,
            "substitution_target_drive_evidence": substitution,
            "substitution_reenumeration_receipt": substitution_receipt,
            "boot_metadata_receipt": boot,
            "data_preservation_receipt": data_preservation,
            "fixture_evidence_allowed": false,
            "restore_executable": false,
            "destructive_authorization_granted": false,
            "system_mutations_performed": false
        });
        package["package_sha256"] = Value::String(value_sha256(&package));
        package
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
    fn evidence_package_checksum_is_mandatory() {
        let mut evidence = complete_evidence(true);
        assert!(build_recovery_hardware_campaign_report(&evidence).evidence_package_verified);

        evidence["fixture_evidence_allowed"] = json!(true);
        let report = build_recovery_hardware_campaign_report(&evidence);
        assert!(!report.evidence_package_verified);
        assert!(!report.campaign_complete);
        assert!(report
            .blockers
            .contains(&"hardware_authority_evidence_package_invalid".to_string()));
    }

    #[test]
    fn tampered_package_after_assembly_is_rejected() {
        let mut evidence = complete_evidence(true);
        evidence["baseline_target_drive_evidence"]["disk"]["size_bytes"] = json!(128_000u64);
        let report = build_recovery_hardware_campaign_report(&evidence);
        assert!(!report.evidence_package_verified);
        assert!(!report.campaign_complete);
    }

    #[test]
    fn tampered_intermediate_receipts_block_campaign() {
        for key in [
            "rollback_destination_verification",
            "post_reanalysis_target_safety",
            "post_reanalysis_target_verification",
            "data_preservation_receipt",
        ] {
            let mut evidence = complete_evidence(true);
            if key == "rollback_destination_verification" {
                evidence[key]["separate_physical_device"] = json!(false);
            } else if key == "post_reanalysis_target_safety" {
                evidence[key]["safe_to_prepare"] = json!(false);
            } else if key == "post_reanalysis_target_verification" {
                evidence[key]["matches"] = json!(false);
            } else {
                evidence[key]["resolved"] = json!(false);
            }
            evidence["package_sha256"] = Value::String(value_sha256(&{
                let mut unsigned = evidence.clone();
                unsigned.as_object_mut().unwrap().remove("package_sha256");
                unsigned
            }));
            let report = build_recovery_hardware_campaign_report(&evidence);
            assert!(report.evidence_package_verified);
            assert!(!report.campaign_complete, "{key} tampering must block");
        }
    }

    #[test]
    fn rollback_contract_mismatch_blocks_boot_and_preservation_gates() {
        let mut evidence = complete_evidence(true);
        evidence["boot_metadata_receipt"]["rollback_contract_sha256"] =
            json!("6".repeat(64));
        evidence["boot_metadata_receipt"]["receipt_sha256"] = Value::String(value_sha256(&{
            let mut unsigned = evidence["boot_metadata_receipt"].clone();
            unsigned.as_object_mut().unwrap().remove("receipt_sha256");
            unsigned
        }));
        evidence["package_sha256"] = Value::String(value_sha256(&{
            let mut unsigned = evidence.clone();
            unsigned.as_object_mut().unwrap().remove("package_sha256");
            unsigned
        }));
        let report = build_recovery_hardware_campaign_report(&evidence);
        assert!(!report.campaign_complete);
        assert!(!report.boot_metadata_live_resolved);

        let mut evidence = complete_evidence(true);
        evidence["data_preservation_receipt"]["rollback_contract_sha256"] =
            json!("6".repeat(64));
        evidence["package_sha256"] = Value::String(value_sha256(&{
            let mut unsigned = evidence.clone();
            unsigned.as_object_mut().unwrap().remove("package_sha256");
            unsigned
        }));
        let report = build_recovery_hardware_campaign_report(&evidence);
        assert!(!report.campaign_complete);
        assert!(!report.data_preservation_resolved);
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
