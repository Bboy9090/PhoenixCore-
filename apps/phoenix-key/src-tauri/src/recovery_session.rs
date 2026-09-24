use crate::recovery_evidence_bundle::{
    build_recovery_evidence_bundle_v2, recovery_evidence_bundle_v2_sha256,
    verify_recovery_evidence_bundle_v2_sha256,
};
use serde::Serialize;
use serde_json::{Map, Value};
use sha2::{Digest, Sha256};

#[derive(Debug, Clone, Serialize, PartialEq, Eq)]
pub struct RecoverySessionStateV1 {
    pub schema: &'static str,
    pub session_id: String,
    pub phase: String,
    pub bundle_sha256: String,
    pub source_identity_sha256: Option<String>,
    pub target_stable_identity_sha256: Option<String>,
    pub rollback_contract_sha256: Option<String>,
    pub software_chain_complete: bool,
    pub hardware_chain_complete: bool,
    pub stale_evidence_detected: bool,
    pub hardware_substitution_detected: bool,
    pub read_only_resume_allowed: bool,
    pub automatic_destructive_resume_allowed: bool,
    pub restore_executable: bool,
    pub next_required_actions: Vec<String>,
    pub system_mutations_performed: bool,
    pub state_sha256: String,
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
        serde_json::to_vec(&canonicalize_json(value)).expect("session JSON serialization cannot fail");
    format!("{:x}", Sha256::digest(bytes))
}

fn component_trusted(bundle: &Value, key: &str) -> bool {
    bundle
        .pointer(&format!("/components/{key}/trusted"))
        .and_then(Value::as_bool)
        == Some(true)
}

fn unique_actions(actions: impl IntoIterator<Item = String>) -> Vec<String> {
    let mut result = Vec::new();
    for action in actions {
        if !result.iter().any(|existing| existing == &action) {
            result.push(action);
        }
    }
    result
}

fn state_sha256(state: &RecoverySessionStateV1) -> String {
    let mut value =
        serde_json::to_value(state).expect("recovery session state serialization cannot fail");
    if let Some(object) = value.as_object_mut() {
        object.remove("state_sha256");
    }
    value_sha256(&value)
}

pub fn build_recovery_session_state(
    bundle: &Value,
    reenumeration_receipt: Option<&Value>,
) -> Result<RecoverySessionStateV1, String> {
    if !verify_recovery_evidence_bundle_v2_sha256(bundle) {
        return Err("recovery evidence bundle checksum is invalid".to_string());
    }

    let bundle_sha256 = bundle
        .get("bundle_sha256")
        .and_then(Value::as_str)
        .ok_or_else(|| "recovery evidence bundle SHA-256 is missing".to_string())?
        .to_string();
    let software_chain_complete = bundle
        .get("software_chain_complete")
        .and_then(Value::as_bool)
        == Some(true);
    let hardware_chain_complete = bundle
        .get("hardware_chain_complete")
        .and_then(Value::as_bool)
        == Some(true);

    let stale_evidence_detected = reenumeration_receipt.is_some_and(|value| {
        value.get("reanalysis_required").and_then(Value::as_bool) == Some(true)
    });
    let hardware_substitution_detected = reenumeration_receipt.is_some_and(|value| {
        value.get("substitution_detected").and_then(Value::as_bool) == Some(true)
    });

    let phase = if hardware_substitution_detected {
        "hardware_substitution_blocked"
    } else if stale_evidence_detected {
        "target_reanalysis_required"
    } else if hardware_chain_complete {
        "hardware_evidence_complete"
    } else if component_trusted(bundle, "rollback_capture_receipt") {
        if component_trusted(bundle, "boot_metadata_receipt")
            && component_trusted(bundle, "data_preservation_receipt")
        {
            "awaiting_remaining_hardware_evidence"
        } else if component_trusted(bundle, "boot_metadata_receipt") {
            "awaiting_data_preservation"
        } else if component_trusted(bundle, "data_preservation_receipt") {
            "awaiting_boot_metadata"
        } else {
            "rollback_captured"
        }
    } else if component_trusted(bundle, "rollback_destination_verification") {
        "rollback_destination_verified"
    } else if component_trusted(bundle, "hardware_preflight") {
        "software_preflight_complete"
    } else if component_trusted(bundle, "rollback_contract") {
        "rollback_planned"
    } else if component_trusted(bundle, "target_identity_verification") {
        "target_verified"
    } else if component_trusted(bundle, "image_metadata") {
        "image_verified"
    } else if component_trusted(bundle, "source_identity_verification") {
        "source_verified"
    } else if component_trusted(bundle, "identity_bound_plan") {
        "planned"
    } else {
        "source_pending"
    }
    .to_string();

    let next_required_actions = if hardware_substitution_detected {
        vec![
            "disconnect_unrecognized_target".to_string(),
            "reselect_intended_target_hardware".to_string(),
            "rerun_target_safety_from_scratch".to_string(),
        ]
    } else if stale_evidence_detected {
        vec![
            "rerun_target_safety".to_string(),
            "fresh_target_identity_verification".to_string(),
            "rebuild_rollback_contract".to_string(),
            "rebuild_hardware_preflight".to_string(),
        ]
    } else {
        unique_actions(
            bundle
                .get("outstanding_requirements")
                .and_then(Value::as_array)
                .into_iter()
                .flatten()
                .filter_map(Value::as_str)
                .map(str::to_string),
        )
    };

    let mut state = RecoverySessionStateV1 {
        schema: "phoenix_key.recovery_session_state.v1",
        session_id: bundle_sha256.chars().take(24).collect(),
        phase,
        bundle_sha256,
        source_identity_sha256: bundle
            .get("source_identity_sha256")
            .and_then(Value::as_str)
            .map(str::to_string),
        target_stable_identity_sha256: bundle
            .get("target_stable_identity_sha256")
            .and_then(Value::as_str)
            .map(str::to_string),
        rollback_contract_sha256: bundle
            .get("rollback_contract_sha256")
            .and_then(Value::as_str)
            .map(str::to_string),
        software_chain_complete,
        hardware_chain_complete,
        stale_evidence_detected,
        hardware_substitution_detected,
        read_only_resume_allowed: !hardware_substitution_detected,
        automatic_destructive_resume_allowed: false,
        restore_executable: false,
        next_required_actions,
        system_mutations_performed: false,
        state_sha256: String::new(),
    };
    state.state_sha256 = state_sha256(&state);
    Ok(state)
}

#[tauri::command]
pub fn build_windows_recovery_session_state(
    evidence_json: String,
) -> Result<RecoverySessionStateV1, String> {
    let evidence: Value = serde_json::from_str(&evidence_json)
        .map_err(|error| format!("invalid recovery evidence JSON: {error}"))?;
    let bundle = build_recovery_evidence_bundle_v2(&evidence);
    let bundle_value = serde_json::to_value(bundle)
        .map_err(|error| format!("cannot serialize recovery evidence bundle: {error}"))?;
    let reenumeration = evidence
        .get("target_reenumeration_receipt")
        .filter(|value| !value.is_null());
    build_recovery_session_state(&bundle_value, reenumeration)
}

#[cfg(test)]
mod tests {
    use super::build_recovery_session_state;
    use crate::recovery_evidence_bundle::recovery_evidence_bundle_v2_sha256;
    use serde_json::{json, Value};

    fn component(trusted: bool) -> Value {
        json!({
            "present": trusted,
            "schema": null,
            "sha256": if trusted { Some("a".repeat(64)) } else { None },
            "trusted": trusted
        })
    }

    fn bundle() -> Value {
        let mut value = json!({
            "schema": "phoenix_key.recovery_evidence_bundle.v2",
            "source_identity_sha256": "a".repeat(64),
            "target_identity_sha256": "b".repeat(64),
            "target_stable_identity_sha256": "c".repeat(64),
            "rollback_contract_sha256": "d".repeat(64),
            "components": {
                "identity_bound_plan": component(true),
                "source_identity_verification": component(true),
                "package_trust": component(true),
                "image_metadata": component(true),
                "target_safety": component(true),
                "target_identity_verification": component(true),
                "rollback_contract": component(true),
                "hardware_preflight": component(true),
                "rollback_destination_verification": component(false),
                "rollback_capture_receipt": component(false),
                "target_reenumeration_receipt": component(false),
                "data_preservation_receipt": component(false),
                "boot_metadata_receipt": component(false)
            },
            "software_chain_complete": true,
            "hardware_chain_complete": false,
            "data_preservation_resolved": false,
            "boot_metadata_resolved": false,
            "outstanding_requirements": [
                "separate_rollback_destination_verification",
                "target_partition_rollback_capture"
            ],
            "restore_executable": false,
            "system_mutations_performed": false
        });
        value["bundle_sha256"] =
            Value::String(recovery_evidence_bundle_v2_sha256(&value).unwrap());
        value
    }

    #[test]
    fn software_complete_session_resumes_at_preflight_boundary() {
        let state = build_recovery_session_state(&bundle(), None).unwrap();
        assert_eq!(state.phase, "software_preflight_complete");
        assert!(state.software_chain_complete);
        assert!(!state.hardware_chain_complete);
        assert!(state.read_only_resume_allowed);
        assert!(!state.automatic_destructive_resume_allowed);
        assert!(!state.restore_executable);
        assert_eq!(state.state_sha256.len(), 64);
    }

    #[test]
    fn reenumeration_staleness_overrides_progress() {
        let receipt = json!({
            "reanalysis_required": true,
            "substitution_detected": false
        });
        let state =
            build_recovery_session_state(&bundle(), Some(&receipt)).unwrap();
        assert_eq!(state.phase, "target_reanalysis_required");
        assert!(state.stale_evidence_detected);
        assert!(state
            .next_required_actions
            .contains(&"rerun_target_safety".to_string()));
        assert!(!state.restore_executable);
    }

    #[test]
    fn hardware_substitution_blocks_resume() {
        let receipt = json!({
            "reanalysis_required": true,
            "substitution_detected": true
        });
        let state =
            build_recovery_session_state(&bundle(), Some(&receipt)).unwrap();
        assert_eq!(state.phase, "hardware_substitution_blocked");
        assert!(state.hardware_substitution_detected);
        assert!(!state.read_only_resume_allowed);
        assert!(!state.restore_executable);
    }

    #[test]
    fn tampered_bundle_is_rejected() {
        let mut value = bundle();
        value["software_chain_complete"] = json!(false);
        assert!(build_recovery_session_state(&value, None).is_err());
    }
}
