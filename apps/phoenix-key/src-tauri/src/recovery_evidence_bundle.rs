use crate::restore_rollback_contract::verify_restore_target_rollback_contract_sha256;
use crate::source_identity::verify_identity_bound_plan_sha256;
use crate::target_reenumeration::{
    verify_recovery_target_reenumeration_receipt_sha256,
    RecoveryTargetReenumerationReceipt,
};
use serde::Serialize;
use serde_json::{Map, Value};
use sha2::{Digest, Sha256};
use std::collections::BTreeMap;

#[derive(Debug, Clone, Serialize, PartialEq, Eq)]
pub struct RecoveryEvidenceComponent {
    pub present: bool,
    pub schema: Option<String>,
    pub sha256: Option<String>,
    pub trusted: bool,
}

#[derive(Debug, Clone, Serialize, PartialEq, Eq)]
pub struct RecoveryEvidenceBundleV2 {
    pub schema: &'static str,
    pub source_identity_sha256: Option<String>,
    pub target_identity_sha256: Option<String>,
    pub target_stable_identity_sha256: Option<String>,
    pub rollback_contract_sha256: Option<String>,
    pub components: BTreeMap<String, RecoveryEvidenceComponent>,
    pub software_chain_complete: bool,
    pub hardware_chain_complete: bool,
    pub data_preservation_resolved: bool,
    pub boot_metadata_resolved: bool,
    pub outstanding_requirements: Vec<String>,
    pub restore_executable: bool,
    pub system_mutations_performed: bool,
    pub bundle_sha256: String,
}

fn valid_sha256(value: &str) -> bool {
    value.len() == 64 && value.bytes().all(|byte| byte.is_ascii_hexdigit())
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
    let bytes =
        serde_json::to_vec(&canonicalize_json(value)).expect("canonical JSON serialization cannot fail");
    format!("{:x}", Sha256::digest(bytes))
}

fn component(value: Option<&Value>, trusted: bool) -> RecoveryEvidenceComponent {
    let schema = value
        .and_then(|value| value.get("schema").or_else(|| value.get("schema_version")))
        .and_then(Value::as_str)
        .map(str::to_string);
    RecoveryEvidenceComponent {
        present: value.is_some(),
        schema,
        sha256: value.map(value_sha256),
        trusted: value.is_some() && trusted,
    }
}

fn same_sha256(left: Option<&str>, right: Option<&str>) -> bool {
    left.zip(right).is_some_and(|(left, right)| {
        valid_sha256(left)
            && valid_sha256(right)
            && left.eq_ignore_ascii_case(right)
    })
}

fn optional_object<'a>(root: &'a Value, key: &str) -> Option<&'a Value> {
    root.get(key).filter(|value| !value.is_null())
}

fn build_bundle_sha256(bundle: &RecoveryEvidenceBundleV2) -> String {
    let mut value =
        serde_json::to_value(bundle).expect("recovery evidence bundle serialization cannot fail");
    if let Some(object) = value.as_object_mut() {
        object.remove("bundle_sha256");
    }
    value_sha256(&value)
}

pub fn recovery_evidence_bundle_v2_sha256(value: &Value) -> Result<String, String> {
    let mut value = value.clone();
    let object = value
        .as_object_mut()
        .ok_or_else(|| "recovery evidence bundle is not a JSON object".to_string())?;
    object.remove("bundle_sha256");
    Ok(value_sha256(&value))
}

pub fn verify_recovery_evidence_bundle_v2_sha256(value: &Value) -> bool {
    if value.get("schema").and_then(Value::as_str)
        != Some("phoenix_key.recovery_evidence_bundle.v2")
    {
        return false;
    }
    let Some(expected) = value.get("bundle_sha256").and_then(Value::as_str) else {
        return false;
    };
    valid_sha256(expected)
        && recovery_evidence_bundle_v2_sha256(value)
            .is_ok_and(|actual| actual.eq_ignore_ascii_case(expected))
}

pub fn build_recovery_evidence_bundle_v2(root: &Value) -> RecoveryEvidenceBundleV2 {
    let plan = root.get("identity_bound_plan").unwrap_or(&Value::Null);
    let source_verification = root.get("source_identity_verification").unwrap_or(&Value::Null);
    let package_trust = optional_object(root, "package_trust");
    let image_metadata = root.get("image_metadata").unwrap_or(&Value::Null);
    let target_safety = root.get("target_safety").unwrap_or(&Value::Null);
    let target_verification = root.get("target_identity_verification").unwrap_or(&Value::Null);
    let rollback_contract = root.get("rollback_contract").unwrap_or(&Value::Null);
    let hardware_preflight = root.get("hardware_preflight").unwrap_or(&Value::Null);
    let rollback_destination = optional_object(root, "rollback_destination_verification");
    let rollback_capture = optional_object(root, "rollback_capture_receipt");
    let reenumeration = optional_object(root, "target_reenumeration_receipt");
    let data_preservation = optional_object(root, "data_preservation_receipt");
    let boot_metadata = optional_object(root, "boot_metadata_receipt");

    let source_identity = plan
        .pointer("/source_identity/sha256")
        .and_then(Value::as_str);
    let target_identity = target_safety
        .get("target_identity_sha256")
        .and_then(Value::as_str);
    let target_stable_identity = target_safety
        .get("target_stable_identity_sha256")
        .and_then(Value::as_str);
    let contract_sha256 = rollback_contract
        .get("contract_sha256")
        .and_then(Value::as_str);

    let plan_trusted = verify_identity_bound_plan_sha256(plan);
    let source_trusted = source_verification.get("matches").and_then(Value::as_bool) == Some(true)
        && source_verification
            .get("reanalysis_required")
            .and_then(Value::as_bool)
            == Some(false)
        && same_sha256(
            source_identity,
            source_verification.get("observed_sha256").and_then(Value::as_str),
        );
    let package_trusted = package_trust.is_none_or(|trust| {
        trust.get("verified_for_use").and_then(Value::as_bool) == Some(true)
            && trust.get("sha256_matches").and_then(Value::as_bool) == Some(true)
    });
    let image_trusted = image_metadata
        .get("metadata_verified")
        .and_then(Value::as_bool)
        == Some(true)
        && image_metadata
            .pointer("/architecture_compatibility/compatible")
            .and_then(Value::as_bool)
            == Some(true);
    let target_trusted = target_safety
        .get("safe_to_prepare")
        .and_then(Value::as_bool)
        == Some(true)
        && target_safety
            .get("source_target_distinct")
            .and_then(Value::as_bool)
            == Some(true);
    let target_verification_trusted = target_verification
        .get("matches")
        .and_then(Value::as_bool)
        == Some(true)
        && target_verification
            .get("reanalysis_required")
            .and_then(Value::as_bool)
            == Some(false)
        && same_sha256(
            target_identity,
            target_verification
                .get("observed_snapshot_identity_sha256")
                .and_then(Value::as_str),
        )
        && same_sha256(
            target_stable_identity,
            target_verification
                .get("observed_stable_identity_sha256")
                .and_then(Value::as_str),
        );
    let rollback_contract_trusted =
        verify_restore_target_rollback_contract_sha256(rollback_contract)
            && same_sha256(
                source_identity,
                rollback_contract
                    .get("source_identity_sha256")
                    .and_then(Value::as_str),
            )
            && same_sha256(
                target_identity,
                rollback_contract
                    .get("target_identity_sha256")
                    .and_then(Value::as_str),
            )
            && same_sha256(
                target_stable_identity,
                rollback_contract
                    .get("target_stable_identity_sha256")
                    .and_then(Value::as_str),
            );
    let preflight_trusted = hardware_preflight
        .get("ready_to_capture_hardware_rollback_evidence")
        .and_then(Value::as_bool)
        == Some(true)
        && hardware_preflight.get("executable").and_then(Value::as_bool) == Some(false)
        && same_sha256(
            contract_sha256,
            hardware_preflight
                .get("rollback_contract_sha256")
                .and_then(Value::as_str),
        );

    let rollback_destination_trusted = rollback_destination.is_some_and(|value| {
        value
            .get("ready_for_hardware_rollback_capture")
            .and_then(Value::as_bool)
            == Some(true)
            && value
                .get("separate_physical_device")
                .and_then(Value::as_bool)
                == Some(true)
            && value
                .get("target_identity_matches_expected")
                .and_then(Value::as_bool)
                == Some(true)
    });

    let rollback_capture_trusted = rollback_capture.is_some_and(|value| {
        value.get("target_bytes_written").and_then(Value::as_u64) == Some(0)
            && value.get("target_write_attempted").and_then(Value::as_bool) == Some(false)
            && value
                .get("restore_unlock_ready")
                .and_then(Value::as_bool)
                == Some(false)
            && same_sha256(
                contract_sha256,
                value.get("rollback_contract_sha256").and_then(Value::as_str),
            )
            && same_sha256(
                target_identity,
                value
                    .get("target_snapshot_identity_sha256")
                    .and_then(Value::as_str),
            )
            && same_sha256(
                target_stable_identity,
                value
                    .get("target_stable_identity_sha256")
                    .and_then(Value::as_str),
            )
    });

    let reenumeration_trusted = reenumeration.is_some_and(|value| {
        serde_json::from_value::<RecoveryTargetReenumerationReceipt>(value.clone())
            .is_ok_and(|receipt| {
                verify_recovery_target_reenumeration_receipt_sha256(&receipt)
                    && receipt.system_mutations_performed == false
                    && receipt.substitution_detected == false
                    && receipt.reanalysis_required == false
            })
    });

    let data_preservation_resolved = data_preservation.is_some_and(|value| {
        value.get("resolved").and_then(Value::as_bool) == Some(true)
            && same_sha256(
                target_stable_identity,
                value
                    .get("target_stable_identity_sha256")
                    .and_then(Value::as_str),
            )
            && same_sha256(
                contract_sha256,
                value.get("rollback_contract_sha256").and_then(Value::as_str),
            )
    });

    let boot_metadata_resolved = boot_metadata.is_some_and(|value| {
        value.get("resolved").and_then(Value::as_bool) == Some(true)
            && same_sha256(
                target_stable_identity,
                value
                    .get("target_stable_identity_sha256")
                    .and_then(Value::as_str),
            )
            && same_sha256(
                contract_sha256,
                value.get("rollback_contract_sha256").and_then(Value::as_str),
            )
    });

    let software_chain_complete = plan_trusted
        && source_trusted
        && package_trusted
        && image_trusted
        && target_trusted
        && target_verification_trusted
        && rollback_contract_trusted
        && preflight_trusted;

    let hardware_chain_complete = rollback_destination_trusted
        && rollback_capture_trusted
        && reenumeration_trusted
        && data_preservation_resolved
        && boot_metadata_resolved;

    let mut outstanding_requirements = Vec::new();
    if !software_chain_complete {
        outstanding_requirements.push("software_evidence_chain_incomplete".to_string());
    }
    if !rollback_destination_trusted {
        outstanding_requirements.push("separate_rollback_destination_verification".to_string());
    }
    if !rollback_capture_trusted {
        outstanding_requirements.push("target_partition_rollback_capture".to_string());
    }
    if !reenumeration_trusted {
        outstanding_requirements.push("target_reenumeration_or_exact_snapshot_receipt".to_string());
    }
    if !data_preservation_resolved {
        outstanding_requirements.push(
            "target_data_preservation_receipt_or_explicit_discard_decision".to_string(),
        );
    }
    if !boot_metadata_resolved {
        outstanding_requirements.push("target_boot_metadata_backup_if_present".to_string());
    }

    let mut components = BTreeMap::new();
    components.insert(
        "identity_bound_plan".to_string(),
        component(Some(plan), plan_trusted),
    );
    components.insert(
        "source_identity_verification".to_string(),
        component(Some(source_verification), source_trusted),
    );
    components.insert(
        "package_trust".to_string(),
        component(package_trust, package_trusted),
    );
    components.insert(
        "image_metadata".to_string(),
        component(Some(image_metadata), image_trusted),
    );
    components.insert(
        "target_safety".to_string(),
        component(Some(target_safety), target_trusted),
    );
    components.insert(
        "target_identity_verification".to_string(),
        component(Some(target_verification), target_verification_trusted),
    );
    components.insert(
        "rollback_contract".to_string(),
        component(Some(rollback_contract), rollback_contract_trusted),
    );
    components.insert(
        "hardware_preflight".to_string(),
        component(Some(hardware_preflight), preflight_trusted),
    );
    components.insert(
        "rollback_destination_verification".to_string(),
        component(rollback_destination, rollback_destination_trusted),
    );
    components.insert(
        "rollback_capture_receipt".to_string(),
        component(rollback_capture, rollback_capture_trusted),
    );
    components.insert(
        "target_reenumeration_receipt".to_string(),
        component(reenumeration, reenumeration_trusted),
    );
    components.insert(
        "data_preservation_receipt".to_string(),
        component(data_preservation, data_preservation_resolved),
    );
    components.insert(
        "boot_metadata_receipt".to_string(),
        component(boot_metadata, boot_metadata_resolved),
    );

    let mut bundle = RecoveryEvidenceBundleV2 {
        schema: "phoenix_key.recovery_evidence_bundle.v2",
        source_identity_sha256: source_identity.map(str::to_string),
        target_identity_sha256: target_identity.map(str::to_string),
        target_stable_identity_sha256: target_stable_identity.map(str::to_string),
        rollback_contract_sha256: contract_sha256.map(str::to_string),
        components,
        software_chain_complete,
        hardware_chain_complete,
        data_preservation_resolved,
        boot_metadata_resolved,
        outstanding_requirements,
        restore_executable: false,
        system_mutations_performed: false,
        bundle_sha256: String::new(),
    };
    bundle.bundle_sha256 = build_bundle_sha256(&bundle);
    bundle
}

#[tauri::command]
pub fn build_windows_recovery_evidence_bundle_v2(
    evidence_json: String,
) -> Result<RecoveryEvidenceBundleV2, String> {
    let evidence: Value = serde_json::from_str(&evidence_json)
        .map_err(|error| format!("invalid recovery evidence JSON: {error}"))?;
    Ok(build_recovery_evidence_bundle_v2(&evidence))
}

#[cfg(test)]
mod tests {
    use super::{
        build_bundle_sha256, build_recovery_evidence_bundle_v2,
        verify_recovery_evidence_bundle_v2_sha256,
    };
    use crate::restore_preflight::assess_restore_hardware_preflight;
    use crate::restore_rollback_contract::build_restore_target_rollback_contract;
    use crate::source_identity::identity_bound_plan_sha256;
    use crate::target_reenumeration::compare_recovery_target_reenumeration;
    use serde_json::{json, Value};

    fn software_evidence() -> Value {
        let mut plan = json!({
            "schema": "phoenix_key.windows_recovery_plan.v4",
            "execution_boundary": {
                "planner_only": true,
                "restore_executor_available": false,
                "system_mutations_performed": false
            },
            "dry_run_summary": {
                "executable": false,
                "mutation_steps_executed": 0
            },
            "source_identity": {
                "sha256": "a".repeat(64),
                "complete": true,
                "source_kind": "file_sha256",
                "canonical_path": "C:/recovery/install.wim",
                "size_bytes": 4096
            },
            "destructive_actions_performed": false
        });
        plan["plan_sha256"] = Value::String(identity_bound_plan_sha256(&plan).unwrap());

        let source = json!({
            "matches": true,
            "reanalysis_required": false,
            "expected_sha256": "a".repeat(64),
            "observed_sha256": "a".repeat(64)
        });
        let trust = json!({
            "verified_for_use": true,
            "sha256_matches": true,
            "observed_sha256": "a".repeat(64)
        });
        let metadata = json!({
            "path": "C:/recovery/install.wim",
            "metadata_verified": true,
            "selected_index": 1,
            "selected_image": {
                "index": 1,
                "edition_id": "Professional",
                "image_size_bytes": 20_000
            },
            "architecture_compatibility": {
                "target_architecture": "x64",
                "compatible": true
            }
        });
        let target = json!({
            "safe_to_prepare": true,
            "source_target_distinct": true,
            "target_identity_sha256": "b".repeat(64),
            "target_stable_identity_sha256": "c".repeat(64),
            "target_size_bytes": 64_000,
            "source_size_bytes": 4096
        });
        let verification = json!({
            "matches": true,
            "snapshot_matches": true,
            "stable_identity_matches": true,
            "reanalysis_required": false,
            "system_mutations_performed": false,
            "expected_snapshot_identity_sha256": "b".repeat(64),
            "observed_snapshot_identity_sha256": "b".repeat(64),
            "expected_stable_identity_sha256": "c".repeat(64),
            "observed_stable_identity_sha256": "c".repeat(64)
        });
        let rollback =
            serde_json::to_value(build_restore_target_rollback_contract(&plan, &target).unwrap())
                .unwrap();
        let preflight = serde_json::to_value(assess_restore_hardware_preflight(
            &plan,
            &source,
            &trust,
            &metadata,
            &target,
            &verification,
            &rollback,
        ))
        .unwrap();

        json!({
            "identity_bound_plan": plan,
            "source_identity_verification": source,
            "package_trust": trust,
            "image_metadata": metadata,
            "target_safety": target,
            "target_identity_verification": verification,
            "rollback_contract": rollback,
            "hardware_preflight": preflight
        })
    }

    #[test]
    fn software_bundle_is_complete_but_never_executable() {
        let bundle = build_recovery_evidence_bundle_v2(&software_evidence());
        assert!(bundle.software_chain_complete);
        assert!(!bundle.hardware_chain_complete);
        assert!(!bundle.restore_executable);
        assert!(!bundle.system_mutations_performed);
        assert_eq!(bundle.bundle_sha256.len(), 64);
        assert!(bundle
            .outstanding_requirements
            .contains(&"target_partition_rollback_capture".to_string()));
        assert!(bundle
            .outstanding_requirements
            .contains(&"target_data_preservation_receipt_or_explicit_discard_decision".to_string()));
    }

    #[test]
    fn serialized_bundle_digest_verifies_and_detects_tampering() {
        let bundle = build_recovery_evidence_bundle_v2(&software_evidence());
        let mut value = serde_json::to_value(bundle).unwrap();
        assert!(verify_recovery_evidence_bundle_v2_sha256(&value));
        value["software_chain_complete"] = json!(false);
        assert!(!verify_recovery_evidence_bundle_v2_sha256(&value));
    }

    #[test]
    fn bundle_digest_changes_when_component_changes() {
        let mut evidence = software_evidence();
        let first = build_recovery_evidence_bundle_v2(&evidence);
        evidence["image_metadata"]["selected_index"] = json!(2);
        let second = build_recovery_evidence_bundle_v2(&evidence);
        assert_ne!(first.bundle_sha256, second.bundle_sha256);
        assert_eq!(first.bundle_sha256, build_bundle_sha256(&first));
    }

    #[test]
    fn reenumeration_that_requires_reanalysis_cannot_complete_hardware_chain() {
        let mut evidence = software_evidence();
        let receipt = compare_recovery_target_reenumeration(
            &json!({
                "disk": {
                    "target": "\\\\.\\PHYSICALDRIVE9",
                    "identity_sha256": "f".repeat(64),
                    "stable_identity_sha256": "c".repeat(64)
                }
            }),
            Some("\\\\.\\PHYSICALDRIVE7"),
            &"b".repeat(64),
            &"c".repeat(64),
        );
        evidence["target_reenumeration_receipt"] =
            serde_json::to_value(receipt).unwrap();
        let bundle = build_recovery_evidence_bundle_v2(&evidence);
        assert!(!bundle.hardware_chain_complete);
        assert!(bundle
            .outstanding_requirements
            .contains(&"target_reenumeration_or_exact_snapshot_receipt".to_string()));
    }

    #[test]
    fn tampered_plan_breaks_software_chain() {
        let mut evidence = software_evidence();
        evidence["identity_bound_plan"]["source_identity"]["size_bytes"] = json!(8192);
        let bundle = build_recovery_evidence_bundle_v2(&evidence);
        assert!(!bundle.software_chain_complete);
        assert!(!bundle.restore_executable);
    }
}
