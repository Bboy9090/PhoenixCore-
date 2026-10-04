use crate::recovery_evidence_bundle::verify_recovery_evidence_bundle_v2_sha256;
use serde::Serialize;
use serde_json::Value;
use sha2::{Digest, Sha256};

const REQUIRED_TRUSTED_COMPONENTS: &[&str] = &[
    "identity_bound_plan",
    "source_identity_verification",
    "image_metadata",
    "target_safety",
    "target_identity_verification",
    "rollback_contract",
    "hardware_preflight",
    "rollback_destination_verification",
    "rollback_capture_receipt",
    "target_reenumeration_receipt",
    "data_preservation_receipt",
    "boot_metadata_receipt",
    "hardware_campaign_manifest",
];

#[derive(Debug, Clone, Serialize, PartialEq, Eq)]
pub struct FinalRecoveryPreflight {
    pub schema: &'static str,
    pub evidence_bundle_sha256: Option<String>,
    pub ready_for_restore_executor_architecture_review: bool,
    pub restore_executor_authorized: bool,
    pub executable: bool,
    pub automatic_destructive_resume: bool,
    pub satisfied_gates: Vec<String>,
    pub blocked_gates: Vec<String>,
    pub next_required_action: String,
    pub system_mutations_performed: bool,
    pub receipt_sha256: String,
}

#[derive(Serialize)]
struct UnsignedFinalRecoveryPreflight<'a> {
    schema: &'a str,
    evidence_bundle_sha256: &'a Option<String>,
    ready_for_restore_executor_architecture_review: bool,
    restore_executor_authorized: bool,
    executable: bool,
    automatic_destructive_resume: bool,
    satisfied_gates: &'a [String],
    blocked_gates: &'a [String],
    next_required_action: &'a str,
    system_mutations_performed: bool,
}

fn valid_sha256(value: Option<&str>) -> bool {
    value.is_some_and(|value| {
        value.len() == 64 && value.bytes().all(|byte| byte.is_ascii_hexdigit())
    })
}

fn gate(
    condition: bool,
    name: &str,
    satisfied: &mut Vec<String>,
    blocked: &mut Vec<String>,
) {
    if condition {
        satisfied.push(name.to_string());
    } else {
        blocked.push(name.to_string());
    }
}

fn receipt_sha256(receipt: &FinalRecoveryPreflight) -> String {
    let unsigned = UnsignedFinalRecoveryPreflight {
        schema: receipt.schema,
        evidence_bundle_sha256: &receipt.evidence_bundle_sha256,
        ready_for_restore_executor_architecture_review: receipt
            .ready_for_restore_executor_architecture_review,
        restore_executor_authorized: receipt.restore_executor_authorized,
        executable: receipt.executable,
        automatic_destructive_resume: receipt.automatic_destructive_resume,
        satisfied_gates: &receipt.satisfied_gates,
        blocked_gates: &receipt.blocked_gates,
        next_required_action: &receipt.next_required_action,
        system_mutations_performed: receipt.system_mutations_performed,
    };
    let bytes =
        serde_json::to_vec(&unsigned).expect("final recovery preflight serialization cannot fail");
    format!("{:x}", Sha256::digest(bytes))
}

pub fn verify_final_recovery_preflight_sha256(
    receipt: &FinalRecoveryPreflight,
) -> bool {
    valid_sha256(Some(&receipt.receipt_sha256))
        && receipt_sha256(receipt).eq_ignore_ascii_case(&receipt.receipt_sha256)
}

fn all_required_components_trusted(bundle: &Value) -> bool {
    let required_trusted = REQUIRED_TRUSTED_COMPONENTS.iter().all(|name| {
        bundle
            .pointer(&format!("/components/{name}/trusted"))
            .and_then(Value::as_bool)
            == Some(true)
    });

    let package_trust_ok = bundle
        .pointer("/components/package_trust")
        .and_then(Value::as_object)
        .is_some_and(|component| {
            component.get("present").and_then(Value::as_bool) == Some(false)
                || (component.get("present").and_then(Value::as_bool) == Some(true)
                    && component.get("trusted").and_then(Value::as_bool) == Some(true))
        });

    let preservation_mode = bundle
        .get("data_preservation_mode")
        .and_then(Value::as_str);
    let preservation_backup_ok = match preservation_mode {
        Some("explicit_discard") => bundle
            .get("data_preservation_backup_receipt_sha256")
            .is_none_or(Value::is_null),
        Some("preserve_existing_data") => {
            valid_sha256(
                bundle
                    .get("data_preservation_backup_receipt_sha256")
                    .and_then(Value::as_str),
            ) && bundle
                .pointer("/components/target_data_backup_receipt/present")
                .and_then(Value::as_bool)
                == Some(true)
                && bundle
                    .pointer("/components/target_data_backup_receipt/trusted")
                    .and_then(Value::as_bool)
                    == Some(true)
                && bundle
                    .pointer("/components/target_data_backup_coverage_proof/present")
                    .and_then(Value::as_bool)
                    == Some(true)
                && bundle
                    .pointer("/components/target_data_backup_coverage_proof/trusted")
                    .and_then(Value::as_bool)
                    == Some(true)
                && bundle
                    .pointer("/components/backup_destination_identity_verification/present")
                    .and_then(Value::as_bool)
                    == Some(true)
                && bundle
                    .pointer("/components/backup_destination_identity_verification/trusted")
                    .and_then(Value::as_bool)
                    == Some(true)
        }
        _ => false,
    };

    required_trusted && package_trust_ok && preservation_backup_ok
}

pub fn assess_final_recovery_preflight(bundle: &Value) -> FinalRecoveryPreflight {
    let mut satisfied = Vec::new();
    let mut blocked = Vec::new();

    gate(
        bundle.get("schema").and_then(Value::as_str)
            == Some("phoenix_key.recovery_evidence_bundle.v2")
            && verify_recovery_evidence_bundle_v2_sha256(bundle),
        "evidence_bundle_checksum_valid",
        &mut satisfied,
        &mut blocked,
    );

    gate(
        bundle
            .get("software_chain_complete")
            .and_then(Value::as_bool)
            == Some(true),
        "software_evidence_chain_complete",
        &mut satisfied,
        &mut blocked,
    );
    gate(
        bundle
            .get("hardware_chain_complete")
            .and_then(Value::as_bool)
            == Some(true),
        "hardware_evidence_chain_complete",
        &mut satisfied,
        &mut blocked,
    );
    gate(
        bundle
            .get("data_preservation_resolved")
            .and_then(Value::as_bool)
            == Some(true),
        "target_data_handling_resolved",
        &mut satisfied,
        &mut blocked,
    );
    gate(
        bundle
            .get("boot_metadata_resolved")
            .and_then(Value::as_bool)
            == Some(true),
        "boot_metadata_resolved",
        &mut satisfied,
        &mut blocked,
    );
    gate(
        bundle
            .get("outstanding_requirements")
            .and_then(Value::as_array)
            .is_some_and(Vec::is_empty),
        "no_outstanding_evidence_requirements",
        &mut satisfied,
        &mut blocked,
    );
    gate(
        bundle.get("restore_executable").and_then(Value::as_bool) == Some(false)
            && bundle
                .get("system_mutations_performed")
                .and_then(Value::as_bool)
                == Some(false),
        "non_executable_boundary_intact",
        &mut satisfied,
        &mut blocked,
    );
    gate(
        valid_sha256(
            bundle
                .get("source_identity_sha256")
                .and_then(Value::as_str),
        ) && valid_sha256(
            bundle
                .get("target_identity_sha256")
                .and_then(Value::as_str),
        ) && valid_sha256(
            bundle
                .get("target_stable_identity_sha256")
                .and_then(Value::as_str),
        ) && valid_sha256(
            bundle
                .get("rollback_contract_sha256")
                .and_then(Value::as_str),
        ),
        "critical_identities_present",
        &mut satisfied,
        &mut blocked,
    );
    gate(
        all_required_components_trusted(bundle),
        "critical_components_trusted",
        &mut satisfied,
        &mut blocked,
    );

    let ready = blocked.is_empty();
    let mut receipt = FinalRecoveryPreflight {
        schema: "phoenix_key.final_recovery_preflight.v1",
        evidence_bundle_sha256: bundle
            .get("bundle_sha256")
            .and_then(Value::as_str)
            .filter(|value| valid_sha256(Some(value)))
            .map(str::to_string),
        ready_for_restore_executor_architecture_review: ready,
        restore_executor_authorized: false,
        executable: false,
        automatic_destructive_resume: false,
        satisfied_gates: satisfied,
        blocked_gates: blocked,
        next_required_action: if ready {
            "separate_restore_executor_architecture_review".to_string()
        } else {
            "complete_recovery_evidence_chain".to_string()
        },
        system_mutations_performed: false,
        receipt_sha256: String::new(),
    };
    receipt.receipt_sha256 = receipt_sha256(&receipt);
    receipt
}

#[tauri::command]
pub fn assess_final_windows_recovery_preflight(
    evidence_bundle_json: String,
) -> Result<FinalRecoveryPreflight, String> {
    let bundle: Value = serde_json::from_str(&evidence_bundle_json)
        .map_err(|error| format!("invalid Recovery Evidence Bundle v2 JSON: {error}"))?;
    Ok(assess_final_recovery_preflight(&bundle))
}

#[cfg(test)]
mod tests {
    use super::{
        assess_final_recovery_preflight, verify_final_recovery_preflight_sha256,
    };
    use crate::recovery_evidence_bundle::recovery_evidence_bundle_v2_sha256;
    use serde_json::{json, Value};

    fn trusted_component(schema: &str) -> Value {
        json!({
            "present": true,
            "schema": schema,
            "sha256": "a".repeat(64),
            "trusted": true
        })
    }

    fn complete_bundle() -> Value {
        let trusted = trusted_component;
        let mut bundle = json!({
            "schema": "phoenix_key.recovery_evidence_bundle.v2",
            "source_identity_sha256": "a".repeat(64),
            "target_identity_sha256": "b".repeat(64),
            "target_stable_identity_sha256": "c".repeat(64),
            "rollback_contract_sha256": "d".repeat(64),
            "components": {
                "identity_bound_plan": trusted("phoenix_key.windows_recovery_plan.v4"),
                "source_identity_verification": trusted("phoenix_key.source_identity_verification.v1"),
                "package_trust": trusted("phoenix_key.package_trust.v1"),
                "image_metadata": trusted("phoenix_key.windows_image_metadata.v1"),
                "target_safety": trusted("phoenix_key.recovery_target_safety.v1"),
                "target_identity_verification": trusted("phoenix_key.recovery_target_identity_verification.v1"),
                "rollback_contract": trusted("phoenix_key.restore_target_rollback_contract.v1"),
                "hardware_preflight": trusted("phoenix_key.restore_hardware_preflight.v1"),
                "rollback_destination_verification": trusted("phoenix_key.rollback_destination_verification.v1"),
                "rollback_capture_receipt": trusted("phoenix_key.restore_target_rollback_capture.v1"),
                "target_reenumeration_receipt": trusted("phoenix_key.recovery_target_reenumeration_receipt.v1"),
                "target_data_backup_receipt": {
                    "present": false,
                    "schema": null,
                    "sha256": null,
                    "trusted": false
                },
                "data_preservation_receipt": trusted("phoenix_key.target_data_preservation_receipt.v1"),
                "boot_metadata_receipt": trusted("phoenix_key.restore_target_boot_metadata.v1"),
                "hardware_campaign_manifest": trusted("phoenix_key.windows_recovery_hardware_campaign.v1")
            },
            "software_chain_complete": true,
            "hardware_chain_complete": true,
            "data_preservation_mode": "explicit_discard",
            "data_preservation_backup_receipt_sha256": null,
            "data_preservation_resolved": true,
            "boot_metadata_resolved": true,
            "outstanding_requirements": [],
            "restore_executable": false,
            "system_mutations_performed": false
        });
        let digest = recovery_evidence_bundle_v2_sha256(&bundle).unwrap();
        bundle["bundle_sha256"] = json!(digest);
        bundle
    }

    fn resign(bundle: &mut Value) {
        bundle.as_object_mut().unwrap().remove("bundle_sha256");
        let digest = recovery_evidence_bundle_v2_sha256(bundle).unwrap();
        bundle["bundle_sha256"] = json!(digest);
    }

    #[test]
    fn complete_bundle_opens_architecture_review_but_never_execution() {
        let result = assess_final_recovery_preflight(&complete_bundle());
        assert!(result.ready_for_restore_executor_architecture_review);
        assert!(!result.restore_executor_authorized);
        assert!(!result.executable);
        assert!(!result.automatic_destructive_resume);
        assert!(!result.system_mutations_performed);
        assert!(result.blocked_gates.is_empty());
        assert_eq!(
            result.next_required_action,
            "separate_restore_executor_architecture_review"
        );
        assert_eq!(result.receipt_sha256.len(), 64);
        assert!(verify_final_recovery_preflight_sha256(&result));
    }

    #[test]
    fn final_receipt_checksum_detects_tampering() {
        let mut result = assess_final_recovery_preflight(&complete_bundle());
        assert!(verify_final_recovery_preflight_sha256(&result));
        result.executable = true;
        assert!(!verify_final_recovery_preflight_sha256(&result));
    }

    #[test]
    fn tampered_bundle_checksum_blocks_handoff() {
        let mut bundle = complete_bundle();
        bundle["hardware_chain_complete"] = json!(false);
        let result = assess_final_recovery_preflight(&bundle);
        assert!(!result.ready_for_restore_executor_architecture_review);
        assert!(result
            .blocked_gates
            .contains(&"evidence_bundle_checksum_valid".to_string()));
    }

    #[test]
    fn incomplete_hardware_chain_blocks_even_with_fresh_bundle_checksum() {
        let mut bundle = complete_bundle();
        bundle["hardware_chain_complete"] = json!(false);
        resign(&mut bundle);
        let result = assess_final_recovery_preflight(&bundle);
        assert!(!result.ready_for_restore_executor_architecture_review);
        assert!(result
            .blocked_gates
            .contains(&"hardware_evidence_chain_complete".to_string()));
    }

    #[test]
    fn executable_claim_blocks_even_with_fresh_bundle_checksum() {
        let mut bundle = complete_bundle();
        bundle["restore_executable"] = json!(true);
        resign(&mut bundle);
        let result = assess_final_recovery_preflight(&bundle);
        assert!(!result.ready_for_restore_executor_architecture_review);
        assert!(result
            .blocked_gates
            .contains(&"non_executable_boundary_intact".to_string()));
        assert!(!result.restore_executor_authorized);
        assert!(!result.executable);
    }

    #[test]
    fn untrusted_critical_component_blocks_handoff() {
        let mut bundle = complete_bundle();
        bundle["components"]["rollback_capture_receipt"]["trusted"] = json!(false);
        resign(&mut bundle);
        let result = assess_final_recovery_preflight(&bundle);
        assert!(!result.ready_for_restore_executor_architecture_review);
        assert!(result
            .blocked_gates
            .contains(&"critical_components_trusted".to_string()));
    }

    #[test]
    fn present_untrusted_package_trust_blocks_handoff() {
        let mut bundle = complete_bundle();
        bundle["components"]["package_trust"]["trusted"] = json!(false);
        resign(&mut bundle);
        let result = assess_final_recovery_preflight(&bundle);
        assert!(!result.ready_for_restore_executor_architecture_review);
        assert!(result
            .blocked_gates
            .contains(&"critical_components_trusted".to_string()));
    }

    #[test]
    fn intentionally_absent_package_trust_remains_allowed() {
        let mut bundle = complete_bundle();
        bundle["components"]["package_trust"]["present"] = json!(false);
        bundle["components"]["package_trust"]["trusted"] = json!(false);
        bundle["components"]["package_trust"]["schema"] = Value::Null;
        bundle["components"]["package_trust"]["sha256"] = Value::Null;
        resign(&mut bundle);
        let result = assess_final_recovery_preflight(&bundle);
        assert!(result.ready_for_restore_executor_architecture_review);
        assert!(result.blocked_gates.is_empty());
    }

    #[test]
    fn preserve_mode_requires_trusted_backup_component() {
        let mut bundle = complete_bundle();
        bundle["data_preservation_mode"] = json!("preserve_existing_data");
        bundle["data_preservation_backup_receipt_sha256"] = json!("e".repeat(64));
        resign(&mut bundle);

        let blocked = assess_final_recovery_preflight(&bundle);
        assert!(!blocked.ready_for_restore_executor_architecture_review);
        assert!(blocked
            .blocked_gates
            .contains(&"critical_components_trusted".to_string()));

        bundle["components"]["target_data_backup_receipt"] = trusted_component(
            "phoenix_key.target_data_backup_receipt.v1",
        );
        resign(&mut bundle);
        let ready = assess_final_recovery_preflight(&bundle);
        assert!(ready.ready_for_restore_executor_architecture_review);
        assert!(!ready.restore_executor_authorized);
        assert!(!ready.executable);
    }

    #[test]
    fn outstanding_requirement_blocks_handoff() {
        let mut bundle = complete_bundle();
        bundle["outstanding_requirements"] = json!(["physical_hardware_proof"]);
        resign(&mut bundle);
        let result = assess_final_recovery_preflight(&bundle);
        assert!(!result.ready_for_restore_executor_architecture_review);
        assert!(result
            .blocked_gates
            .contains(&"no_outstanding_evidence_requirements".to_string()));
    }

    #[test]
    fn preserve_mode_requires_both_independent_proof_components() {
        let mut bundle = complete_bundle();
        bundle["data_preservation_mode"] = json!("preserve_existing_data");
        bundle["data_preservation_backup_receipt_sha256"] = json!("e".repeat(64));
        bundle["components"]["target_data_backup_receipt"] =
            trusted_component("phoenix_key.target_data_backup_receipt.v1");
        resign(&mut bundle);

        let blocked = assess_final_recovery_preflight(&bundle);
        assert!(!blocked.ready_for_restore_executor_architecture_review);
        assert!(blocked
            .blocked_gates
            .contains(&"critical_components_trusted".to_string()));

        bundle["components"]["target_data_backup_coverage_proof"] =
            trusted_component("phoenix_key.target_data_backup_coverage_proof.v1");
        bundle["components"]["backup_destination_identity_verification"] =
            trusted_component("phoenix_key.backup_destination_identity_verification.v1");
        resign(&mut bundle);

        let resolved = assess_final_recovery_preflight(&bundle);
        assert!(resolved.ready_for_restore_executor_architecture_review);
        assert!(resolved.blocked_gates.is_empty());
        assert!(!resolved.restore_executor_authorized);
        assert!(!resolved.executable);
    }

}
