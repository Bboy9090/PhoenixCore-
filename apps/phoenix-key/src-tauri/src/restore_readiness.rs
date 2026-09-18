use serde::Serialize;
use serde_json::Value;

#[derive(Debug, Clone, Serialize, PartialEq, Eq)]
pub struct RestoreReadiness {
    pub schema: &'static str,
    pub ready_for_restore_executor_design: bool,
    pub executable: bool,
    pub satisfied_gates: Vec<String>,
    pub blocked_gates: Vec<String>,
    pub selected_image_index: Option<u64>,
    pub source_architecture: Option<String>,
    pub target_architecture: Option<String>,
    pub source_identity_sha256: Option<String>,
    pub target_identity_sha256: Option<String>,
    pub system_mutations_performed: bool,
}

fn is_sha256(value: Option<&str>) -> bool {
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

pub fn assess_restore_readiness(
    identity_bound_plan: &Value,
    package_trust: &Value,
    image_metadata: &Value,
    target_safety: &Value,
    rollback_bundle: &Value,
) -> RestoreReadiness {
    let mut satisfied = Vec::new();
    let mut blocked = Vec::new();

    let source_identity = identity_bound_plan
        .pointer("/source_identity/sha256")
        .and_then(Value::as_str);
    gate(
        is_sha256(source_identity)
            && identity_bound_plan
                .pointer("/source_identity/complete")
                .and_then(Value::as_bool)
                == Some(true),
        "source_identity_complete",
        &mut satisfied,
        &mut blocked,
    );

    gate(
        package_trust
            .get("verified_for_use")
            .and_then(Value::as_bool)
            == Some(true)
            && package_trust
                .get("sha256_matches")
                .and_then(Value::as_bool)
                == Some(true),
        "source_package_trust",
        &mut satisfied,
        &mut blocked,
    );

    let selected_index = image_metadata
        .get("selected_index")
        .and_then(Value::as_u64);
    let selected_image = image_metadata.get("selected_image");
    gate(
        image_metadata
            .get("metadata_verified")
            .and_then(Value::as_bool)
            == Some(true)
            && selected_index.is_some()
            && selected_image.is_some_and(|value| !value.is_null()),
        "exact_windows_image_selected",
        &mut satisfied,
        &mut blocked,
    );

    let source_architecture = image_metadata
        .pointer("/selected_image/architecture")
        .and_then(Value::as_str)
        .map(str::to_string);
    let target_architecture = image_metadata
        .pointer("/architecture_compatibility/target_architecture")
        .and_then(Value::as_str)
        .map(str::to_string);
    gate(
        image_metadata
            .pointer("/architecture_compatibility/compatible")
            .and_then(Value::as_bool)
            == Some(true),
        "source_target_architecture_compatible",
        &mut satisfied,
        &mut blocked,
    );

    let target_identity = target_safety
        .get("target_identity_sha256")
        .and_then(Value::as_str);
    gate(
        target_safety
            .get("safe_to_prepare")
            .and_then(Value::as_bool)
            == Some(true)
            && target_safety
                .get("source_target_distinct")
                .and_then(Value::as_bool)
                == Some(true)
            && is_sha256(target_identity),
        "target_safety_and_distinct_identity",
        &mut satisfied,
        &mut blocked,
    );

    gate(
        rollback_bundle.get("complete").and_then(Value::as_bool) == Some(true)
            && rollback_bundle
                .get("repair_unlock_ready")
                .and_then(Value::as_bool)
                == Some(true)
            && rollback_bundle
                .get("system_configuration_mutated")
                .and_then(Value::as_bool)
                == Some(false)
            && is_sha256(
                rollback_bundle
                    .get("bundle_sha256")
                    .and_then(Value::as_str),
            ),
        "rollback_bundle_complete",
        &mut satisfied,
        &mut blocked,
    );

    gate(
        identity_bound_plan
            .get("destructive_actions_performed")
            .and_then(Value::as_bool)
            == Some(false),
        "planning_remained_non_destructive",
        &mut satisfied,
        &mut blocked,
    );

    RestoreReadiness {
        schema: "phoenix_key.restore_readiness.v1",
        ready_for_restore_executor_design: blocked.is_empty(),
        executable: false,
        satisfied_gates: satisfied,
        blocked_gates: blocked,
        selected_image_index: selected_index,
        source_architecture,
        target_architecture,
        source_identity_sha256: source_identity.map(str::to_string),
        target_identity_sha256: target_identity.map(str::to_string),
        system_mutations_performed: false,
    }
}

#[tauri::command]
pub fn assess_windows_restore_readiness(
    identity_bound_plan_json: String,
    package_trust_json: String,
    image_metadata_json: String,
    target_safety_json: String,
    rollback_bundle_json: String,
) -> Result<RestoreReadiness, String> {
    let parse = |label: &str, text: String| -> Result<Value, String> {
        serde_json::from_str(&text)
            .map_err(|error| format!("invalid {label} JSON: {error}"))
    };
    Ok(assess_restore_readiness(
        &parse("identity-bound plan", identity_bound_plan_json)?,
        &parse("package trust", package_trust_json)?,
        &parse("image metadata", image_metadata_json)?,
        &parse("target safety", target_safety_json)?,
        &parse("rollback bundle", rollback_bundle_json)?,
    ))
}

#[cfg(test)]
mod tests {
    use super::assess_restore_readiness;
    use serde_json::json;

    fn evidence() -> (
        serde_json::Value,
        serde_json::Value,
        serde_json::Value,
        serde_json::Value,
        serde_json::Value,
    ) {
        (
            json!({
                "source_identity": {
                    "sha256": "a".repeat(64),
                    "complete": true
                },
                "destructive_actions_performed": false
            }),
            json!({
                "verified_for_use": true,
                "sha256_matches": true
            }),
            json!({
                "metadata_verified": true,
                "selected_index": 2,
                "selected_image": {
                    "index": 2,
                    "architecture": "x64",
                    "edition_id": "Professional"
                },
                "architecture_compatibility": {
                    "target_architecture": "x64",
                    "compatible": true
                }
            }),
            json!({
                "safe_to_prepare": true,
                "source_target_distinct": true,
                "target_identity_sha256": "b".repeat(64)
            }),
            json!({
                "complete": true,
                "repair_unlock_ready": true,
                "system_configuration_mutated": false,
                "bundle_sha256": "c".repeat(64)
            }),
        )
    }

    #[test]
    fn all_evidence_can_reach_design_readiness_but_never_execution() {
        let (plan, trust, metadata, target, rollback) = evidence();
        let result =
            assess_restore_readiness(&plan, &trust, &metadata, &target, &rollback);
        assert!(result.ready_for_restore_executor_design);
        assert!(!result.executable);
        assert!(result.blocked_gates.is_empty());
        assert_eq!(result.selected_image_index, Some(2));
    }

    #[test]
    fn missing_package_trust_blocks_readiness() {
        let (plan, mut trust, metadata, target, rollback) = evidence();
        trust["verified_for_use"] = json!(false);
        let result =
            assess_restore_readiness(&plan, &trust, &metadata, &target, &rollback);
        assert!(!result.ready_for_restore_executor_design);
        assert!(result
            .blocked_gates
            .contains(&"source_package_trust".to_string()));
        assert!(!result.executable);
    }

    #[test]
    fn missing_exact_image_selection_blocks_readiness() {
        let (plan, trust, mut metadata, target, rollback) = evidence();
        metadata["selected_index"] = Value::Null;
        metadata["selected_image"] = Value::Null;
        let result =
            assess_restore_readiness(&plan, &trust, &metadata, &target, &rollback);
        assert!(result
            .blocked_gates
            .contains(&"exact_windows_image_selected".to_string()));
    }

    #[test]
    fn architecture_mismatch_blocks_readiness() {
        let (plan, trust, mut metadata, target, rollback) = evidence();
        metadata["architecture_compatibility"]["compatible"] = json!(false);
        let result =
            assess_restore_readiness(&plan, &trust, &metadata, &target, &rollback);
        assert!(result
            .blocked_gates
            .contains(&"source_target_architecture_compatible".to_string()));
    }

    #[test]
    fn same_device_target_blocks_readiness() {
        let (plan, trust, metadata, mut target, rollback) = evidence();
        target["source_target_distinct"] = json!(false);
        let result =
            assess_restore_readiness(&plan, &trust, &metadata, &target, &rollback);
        assert!(result
            .blocked_gates
            .contains(&"target_safety_and_distinct_identity".to_string()));
    }

    #[test]
    fn incomplete_rollback_bundle_blocks_readiness() {
        let (plan, trust, metadata, target, mut rollback) = evidence();
        rollback["complete"] = json!(false);
        let result =
            assess_restore_readiness(&plan, &trust, &metadata, &target, &rollback);
        assert!(result
            .blocked_gates
            .contains(&"rollback_bundle_complete".to_string()));
    }
}
