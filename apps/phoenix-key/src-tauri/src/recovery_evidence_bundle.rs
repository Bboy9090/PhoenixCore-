use crate::data_preservation::verify_target_data_preservation_receipt_sha256;
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

fn valid_source_commit(value: &str) -> bool {
    value.len() == 40 && value.bytes().all(|byte| byte.is_ascii_hexdigit())
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

fn verify_embedded_receipt_sha256(value: &Value, schema: &str) -> bool {
    if value.get("schema").and_then(Value::as_str) != Some(schema) {
        return false;
    }
    let Some(expected) = value.get("receipt_sha256").and_then(Value::as_str) else {
        return false;
    };
    if !valid_sha256(expected) {
        return false;
    }
    let mut unsigned = value.clone();
    let Some(object) = unsigned.as_object_mut() else {
        return false;
    };
    object.remove("receipt_sha256");
    value_sha256(&unsigned).eq_ignore_ascii_case(expected)
}

fn verify_hardware_campaign_manifest(
    value: &Value,
    target_stable_identity: Option<&str>,
    rollback_capture: Option<&Value>,
    boot_metadata: Option<&Value>,
) -> bool {
    if value.get("schema").and_then(Value::as_str)
        != Some("phoenix_key.windows_recovery_hardware_campaign.v1")
    {
        return false;
    }
    let Some(expected) = value.get("manifest_sha256").and_then(Value::as_str) else {
        return false;
    };
    if !valid_sha256(expected) {
        return false;
    }
    let mut unsigned = value.clone();
    let Some(object) = unsigned.as_object_mut() else {
        return false;
    };
    object.remove("manifest_sha256");
    if !value_sha256(&unsigned).eq_ignore_ascii_case(expected) {
        return false;
    }

    let required_gates = [
        "baseline_live_hardware",
        "rollback_live_zero_write",
        "reconnect_same_hardware",
        "reenumeration_observed",
        "substitution_rejection_proven",
        "boot_metadata_live_read_only",
    ];
    let gates_complete = required_gates.iter().all(|gate| {
        value
            .pointer(&format!("/gates/{gate}"))
            .and_then(Value::as_bool)
            == Some(true)
    });

    let campaign_revision_matches = value
        .get("source_commit")
        .and_then(Value::as_str)
        .filter(|commit| valid_source_commit(commit))
        .is_some_and(|manifest_commit| {
            [
                "/baseline/source_commit",
                "/rollback_capture/source_commit",
                "/reconnect/source_commit",
                "/substitution/source_commit",
                "/boot_metadata/source_commit",
            ]
            .iter()
            .all(|path| {
                value
                    .pointer(path)
                    .and_then(Value::as_str)
                    .is_some_and(|recorded_commit| {
                        manifest_commit.eq_ignore_ascii_case(recorded_commit)
                    })
            })
        });

    let rollback_matches = rollback_capture.is_some_and(|receipt| {
        same_sha256(
            value
                .pointer("/rollback_capture/receipt_sha256")
                .and_then(Value::as_str),
            receipt.get("receipt_sha256").and_then(Value::as_str),
        ) && value
            .get("source_commit")
            .and_then(Value::as_str)
            .zip(
                value
                    .pointer("/rollback_capture/source_commit")
                    .and_then(Value::as_str),
            )
            .zip(receipt.get("source_commit").and_then(Value::as_str))
            .is_some_and(|((manifest_commit, recorded_commit), receipt_commit)| {
                valid_source_commit(manifest_commit)
                    && manifest_commit.eq_ignore_ascii_case(recorded_commit)
                    && manifest_commit.eq_ignore_ascii_case(receipt_commit)
            })
    });
    let boot_matches = boot_metadata.is_some_and(|receipt| {
        same_sha256(
            value
                .pointer("/boot_metadata/receipt_sha256")
                .and_then(Value::as_str),
            receipt.get("receipt_sha256").and_then(Value::as_str),
        ) && value
            .get("source_commit")
            .and_then(Value::as_str)
            .zip(
                value
                    .pointer("/boot_metadata/source_commit")
                    .and_then(Value::as_str),
            )
            .zip(receipt.get("source_commit").and_then(Value::as_str))
            .is_some_and(|((manifest_commit, recorded_commit), receipt_commit)| {
                valid_source_commit(manifest_commit)
                    && manifest_commit.eq_ignore_ascii_case(recorded_commit)
                    && manifest_commit.eq_ignore_ascii_case(receipt_commit)
            })
    });

    value
        .get("hardware_campaign_complete")
        .and_then(Value::as_bool)
        == Some(true)
        && value
            .get("source_commit")
            .and_then(Value::as_str)
            .is_some_and(valid_source_commit)
        && campaign_revision_matches
        && gates_complete
        && value
            .get("restore_executor_authorized")
            .and_then(Value::as_bool)
            == Some(false)
        && value
            .get("system_mutations_performed")
            .and_then(Value::as_bool)
            == Some(false)
        && same_sha256(
            target_stable_identity,
            value
                .pointer("/baseline/stable_identity_sha256")
                .and_then(Value::as_str),
        )
        && rollback_matches
        && boot_matches
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
    let hardware_campaign_manifest = optional_object(root, "hardware_campaign_manifest");

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
        verify_embedded_receipt_sha256(
            value,
            "phoenix_key.restore_target_rollback_capture.v1",
        )
            && value.get("target_bytes_written").and_then(Value::as_u64) == Some(0)
            && value.get("target_write_attempted").and_then(Value::as_bool) == Some(false)
            && value
                .get("restore_unlock_ready")
                .and_then(Value::as_bool)
                == Some(false)
            && value
                .get("system_mutations_performed")
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
        verify_target_data_preservation_receipt_sha256(value)
            && value.get("resolved").and_then(Value::as_bool) == Some(true)
            && value
                .get("restore_unlock_ready")
                .and_then(Value::as_bool)
                == Some(false)
            && value
                .get("system_mutations_performed")
                .and_then(Value::as_bool)
                == Some(false)
            && value
                .get("block_reasons")
                .and_then(Value::as_array)
                .is_some_and(Vec::is_empty)
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
        verify_embedded_receipt_sha256(
            value,
            "phoenix_key.restore_target_boot_metadata.v1",
        )
            && value.get("resolved").and_then(Value::as_bool) == Some(true)
            && value
                .get("restore_unlock_ready")
                .and_then(Value::as_bool)
                == Some(false)
            && value.get("target_bytes_written").and_then(Value::as_u64) == Some(0)
            && value
                .get("target_write_attempted")
                .and_then(Value::as_bool)
                == Some(false)
            && value
                .get("partition_mount_or_assignment_attempted")
                .and_then(Value::as_bool)
                == Some(false)
            && value
                .get("system_mutations_performed")
                .and_then(Value::as_bool)
                == Some(false)
            && value
                .get("missing_or_unverified")
                .and_then(Value::as_array)
                .is_some_and(Vec::is_empty)
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

    let hardware_campaign_trusted = hardware_campaign_manifest.is_some_and(|value| {
        verify_hardware_campaign_manifest(
            value,
            target_stable_identity,
            rollback_capture,
            boot_metadata,
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
        && boot_metadata_resolved
        && hardware_campaign_trusted;

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
    if !hardware_campaign_trusted {
        outstanding_requirements.push("physical_hardware_campaign_manifest".to_string());
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
    components.insert(
        "hardware_campaign_manifest".to_string(),
        component(hardware_campaign_manifest, hardware_campaign_trusted),
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
pub fn load_windows_recovery_hardware_campaign_manifest(
    manifest_path: String,
) -> Result<Value, String> {
    let text = std::fs::read_to_string(&manifest_path)
        .map_err(|error| format!("cannot read hardware campaign manifest: {error}"))?;
    let value: Value = serde_json::from_str(&text)
        .map_err(|error| format!("invalid hardware campaign manifest JSON: {error}"))?;

    if value.get("schema").and_then(Value::as_str)
        != Some("phoenix_key.windows_recovery_hardware_campaign.v1")
    {
        return Err("unsupported hardware campaign manifest schema".to_string());
    }
    let expected = value
        .get("manifest_sha256")
        .and_then(Value::as_str)
        .ok_or_else(|| "hardware campaign manifest SHA-256 is missing".to_string())?;
    if !valid_sha256(expected) {
        return Err("hardware campaign manifest SHA-256 is invalid".to_string());
    }
    let mut unsigned = value.clone();
    unsigned
        .as_object_mut()
        .ok_or_else(|| "hardware campaign manifest is not a JSON object".to_string())?
        .remove("manifest_sha256");
    if !value_sha256(&unsigned).eq_ignore_ascii_case(expected) {
        return Err("hardware campaign manifest checksum does not match".to_string());
    }

    Ok(value)
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
        build_bundle_sha256, build_recovery_evidence_bundle_v2, value_sha256,
        verify_hardware_campaign_manifest, verify_recovery_evidence_bundle_v2_sha256,
    };
    use crate::data_preservation::{
        build_target_data_preservation_receipt, EXPLICIT_DISCARD_ACKNOWLEDGEMENT,
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

    fn signed_python_receipt(mut value: Value) -> Value {
        value["receipt_sha256"] = Value::Null;
        value.as_object_mut().unwrap().remove("receipt_sha256");
        let digest = value_sha256(&value);
        value["receipt_sha256"] = json!(digest);
        value
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
        assert!(bundle
            .outstanding_requirements
            .contains(&"physical_hardware_campaign_manifest".to_string()));
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
    fn tampered_data_preservation_receipt_is_not_resolved() {
        let mut evidence = software_evidence();
        let receipt = build_target_data_preservation_receipt(
            &evidence["target_safety"],
            &evidence["rollback_contract"],
            "explicit_discard",
            EXPLICIT_DISCARD_ACKNOWLEDGEMENT,
        )
        .unwrap();
        let mut value = serde_json::to_value(receipt).unwrap();
        value["resolved"] = json!(false);
        evidence["data_preservation_receipt"] = value;

        let bundle = build_recovery_evidence_bundle_v2(&evidence);
        assert!(!bundle.data_preservation_resolved);
        assert!(!bundle.components["data_preservation_receipt"].trusted);
    }

    #[test]
    fn boot_metadata_requires_valid_checksum_and_read_only_locks() {
        let mut evidence = software_evidence();
        let contract_sha = evidence["rollback_contract"]["contract_sha256"]
            .as_str()
            .unwrap()
            .to_string();
        let stable = evidence["target_safety"]["target_stable_identity_sha256"]
            .as_str()
            .unwrap()
            .to_string();
        let snapshot = evidence["target_safety"]["target_identity_sha256"]
            .as_str()
            .unwrap()
            .to_string();

        let receipt = signed_python_receipt(json!({
            "schema": "phoenix_key.restore_target_boot_metadata.v1",
            "evidence_source": "live",
            "hardware_observed": true,
            "target": "fixture-target",
            "target_snapshot_identity_sha256": snapshot,
            "target_stable_identity_sha256": stable,
            "rollback_contract_sha256": contract_sha,
            "rollback_capture_receipt_sha256": "d".repeat(64),
            "output_directory": "D:/rollback/boot",
            "partition_inventory": [],
            "artifacts": {},
            "resolved": true,
            "missing_or_unverified": [],
            "restore_unlock_ready": false,
            "target_bytes_written": 0,
            "target_write_attempted": false,
            "partition_mount_or_assignment_attempted": false,
            "system_mutations_performed": false
        }));
        evidence["boot_metadata_receipt"] = receipt.clone();
        let valid = build_recovery_evidence_bundle_v2(&evidence);
        assert!(valid.boot_metadata_resolved);
        assert!(valid.components["boot_metadata_receipt"].trusted);

        let mut tampered = receipt;
        tampered["target_write_attempted"] = json!(true);
        evidence["boot_metadata_receipt"] = tampered;
        let blocked = build_recovery_evidence_bundle_v2(&evidence);
        assert!(!blocked.boot_metadata_resolved);
        assert!(!blocked.components["boot_metadata_receipt"].trusted);
    }

    #[test]
    fn hardware_campaign_manifest_requires_all_physical_gates_and_exact_receipts() {
        let rollback = json!({
            "receipt_sha256": "d".repeat(64),
            "source_commit": "a".repeat(40)
        });
        let boot = json!({
            "receipt_sha256": "e".repeat(64),
            "source_commit": "a".repeat(40)
        });
        let mut manifest = json!({
            "schema": "phoenix_key.windows_recovery_hardware_campaign.v1",
            "campaign_id": "campaign-001",
            "source_commit": "a".repeat(40),
            "baseline": {
                "stable_identity_sha256": "c".repeat(64),
                "source_commit": "a".repeat(40)
            },
            "rollback_capture": {
                "receipt_sha256": "d".repeat(64),
                "source_commit": "a".repeat(40)
            },
            "reconnect": {
                "source_commit": "a".repeat(40)
            },
            "substitution": {
                "source_commit": "a".repeat(40)
            },
            "boot_metadata": {
                "receipt_sha256": "e".repeat(64),
                "source_commit": "a".repeat(40)
            },
            "gates": {
                "baseline_live_hardware": true,
                "rollback_live_zero_write": true,
                "reconnect_same_hardware": true,
                "reenumeration_observed": true,
                "substitution_rejection_proven": true,
                "boot_metadata_live_read_only": true
            },
            "hardware_campaign_complete": true,
            "restore_executor_authorized": false,
            "system_mutations_performed": false
        });
        let digest = value_sha256(&manifest);
        manifest["manifest_sha256"] = json!(digest);

        assert!(verify_hardware_campaign_manifest(
            &manifest,
            Some(&"c".repeat(64)),
            Some(&rollback),
            Some(&boot),
        ));

        manifest["gates"]["substitution_rejection_proven"] = json!(false);
        manifest.as_object_mut().unwrap().remove("manifest_sha256");
        let digest = value_sha256(&manifest);
        manifest["manifest_sha256"] = json!(digest);

        assert!(!verify_hardware_campaign_manifest(
            &manifest,
            Some(&"c".repeat(64)),
            Some(&rollback),
            Some(&boot),
        ));
    }

    #[test]
    fn hardware_campaign_manifest_rejects_revision_mismatch() {
        let rollback = json!({
            "receipt_sha256": "d".repeat(64),
            "source_commit": "a".repeat(40)
        });
        let boot = json!({
            "receipt_sha256": "e".repeat(64),
            "source_commit": "a".repeat(40)
        });
        let mut manifest = json!({
            "schema": "phoenix_key.windows_recovery_hardware_campaign.v1",
            "source_commit": "a".repeat(40),
            "baseline": {
                "stable_identity_sha256": "c".repeat(64),
                "source_commit": "b".repeat(40)
            },
            "rollback_capture": {
                "receipt_sha256": "d".repeat(64),
                "source_commit": "a".repeat(40)
            },
            "reconnect": {
                "source_commit": "a".repeat(40)
            },
            "substitution": {
                "source_commit": "a".repeat(40)
            },
            "boot_metadata": {
                "receipt_sha256": "e".repeat(64),
                "source_commit": "a".repeat(40)
            },
            "gates": {
                "baseline_live_hardware": true,
                "rollback_live_zero_write": true,
                "reconnect_same_hardware": true,
                "reenumeration_observed": true,
                "substitution_rejection_proven": true,
                "boot_metadata_live_read_only": true
            },
            "hardware_campaign_complete": true,
            "restore_executor_authorized": false,
            "system_mutations_performed": false
        });
        let digest = value_sha256(&manifest);
        manifest["manifest_sha256"] = json!(digest);

        assert!(!verify_hardware_campaign_manifest(
            &manifest,
            Some(&"c".repeat(64)),
            Some(&rollback),
            Some(&boot),
        ));
    }

    #[test]
    fn hardware_campaign_manifest_rejects_mixed_evidence_revision() {
        let rollback = json!({
            "receipt_sha256": "d".repeat(64),
            "source_commit": "b".repeat(40)
        });
        let boot = json!({
            "receipt_sha256": "e".repeat(64),
            "source_commit": "a".repeat(40)
        });
        let mut manifest = json!({
            "schema": "phoenix_key.windows_recovery_hardware_campaign.v1",
            "source_commit": "a".repeat(40),
            "baseline": {
                "stable_identity_sha256": "c".repeat(64),
                "source_commit": "a".repeat(40)
            },
            "rollback_capture": {
                "receipt_sha256": "d".repeat(64),
                "source_commit": "b".repeat(40)
            },
            "boot_metadata": {
                "receipt_sha256": "e".repeat(64),
                "source_commit": "a".repeat(40)
            },
            "gates": {
                "baseline_live_hardware": true,
                "rollback_live_zero_write": true,
                "reconnect_same_hardware": true,
                "reenumeration_observed": true,
                "substitution_rejection_proven": true,
                "boot_metadata_live_read_only": true
            },
            "hardware_campaign_complete": true,
            "restore_executor_authorized": false,
            "system_mutations_performed": false
        });
        let digest = value_sha256(&manifest);
        manifest["manifest_sha256"] = json!(digest);

        assert!(!verify_hardware_campaign_manifest(
            &manifest,
            Some(&"c".repeat(64)),
            Some(&rollback),
            Some(&boot),
        ));
    }

    #[test]
    fn hardware_campaign_manifest_rejects_mixed_reconnect_revision() {
        let rollback = json!({
            "receipt_sha256": "d".repeat(64),
            "source_commit": "a".repeat(40)
        });
        let boot = json!({
            "receipt_sha256": "e".repeat(64),
            "source_commit": "a".repeat(40)
        });
        let mut manifest = json!({
            "schema": "phoenix_key.windows_recovery_hardware_campaign.v1",
            "source_commit": "a".repeat(40),
            "baseline": {
                "stable_identity_sha256": "c".repeat(64),
                "source_commit": "a".repeat(40)
            },
            "rollback_capture": {
                "receipt_sha256": "d".repeat(64),
                "source_commit": "a".repeat(40)
            },
            "reconnect": {
                "source_commit": "b".repeat(40)
            },
            "substitution": {
                "source_commit": "a".repeat(40)
            },
            "boot_metadata": {
                "receipt_sha256": "e".repeat(64),
                "source_commit": "a".repeat(40)
            },
            "gates": {
                "baseline_live_hardware": true,
                "rollback_live_zero_write": true,
                "reconnect_same_hardware": true,
                "reenumeration_observed": true,
                "substitution_rejection_proven": true,
                "boot_metadata_live_read_only": true
            },
            "hardware_campaign_complete": true,
            "restore_executor_authorized": false,
            "system_mutations_performed": false
        });
        let digest = value_sha256(&manifest);
        manifest["manifest_sha256"] = json!(digest);

        assert!(!verify_hardware_campaign_manifest(
            &manifest,
            Some(&"c".repeat(64)),
            Some(&rollback),
            Some(&boot),
        ));
    }

    #[test]
    fn hardware_campaign_manifest_rejects_wrong_receipt_binding() {
        let rollback = json!({
            "receipt_sha256": "d".repeat(64),
            "source_commit": "a".repeat(40)
        });
        let boot = json!({
            "receipt_sha256": "e".repeat(64),
            "source_commit": "a".repeat(40)
        });
        let mut manifest = json!({
            "schema": "phoenix_key.windows_recovery_hardware_campaign.v1",
            "source_commit": "a".repeat(40),
            "baseline": {
                "stable_identity_sha256": "c".repeat(64),
                "source_commit": "a".repeat(40)
            },
            "rollback_capture": {
                "receipt_sha256": "0".repeat(64),
                "source_commit": "a".repeat(40)
            },
            "reconnect": {
                "source_commit": "a".repeat(40)
            },
            "substitution": {
                "source_commit": "a".repeat(40)
            },
            "boot_metadata": {
                "receipt_sha256": "e".repeat(64),
                "source_commit": "a".repeat(40)
            },
            "gates": {
                "baseline_live_hardware": true,
                "rollback_live_zero_write": true,
                "reconnect_same_hardware": true,
                "reenumeration_observed": true,
                "substitution_rejection_proven": true,
                "boot_metadata_live_read_only": true
            },
            "hardware_campaign_complete": true,
            "restore_executor_authorized": false,
            "system_mutations_performed": false
        });
        let digest = value_sha256(&manifest);
        manifest["manifest_sha256"] = json!(digest);

        assert!(!verify_hardware_campaign_manifest(
            &manifest,
            Some(&"c".repeat(64)),
            Some(&rollback),
            Some(&boot),
        ));
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
