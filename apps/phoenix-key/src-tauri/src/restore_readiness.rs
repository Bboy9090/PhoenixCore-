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
    pub source_edition_id: Option<String>,
    pub selected_image_size_bytes: Option<u64>,
    pub target_architecture: Option<String>,
    pub source_identity_sha256: Option<String>,
    pub target_identity_sha256: Option<String>,
    pub target_stable_identity_sha256: Option<String>,
    pub system_mutations_performed: bool,
}

fn is_sha256(value: Option<&str>) -> bool {
    value.is_some_and(|value| {
        value.len() == 64 && value.bytes().all(|byte| byte.is_ascii_hexdigit())
    })
}

fn same_sha256(left: Option<&str>, right: Option<&str>) -> bool {
    is_sha256(left)
        && is_sha256(right)
        && left
            .zip(right)
            .is_some_and(|(left, right)| left.eq_ignore_ascii_case(right))
}

fn normalized_path(value: &str) -> String {
    value.replace('\\', "/").trim_end_matches('/').to_ascii_lowercase()
}

fn same_path(left: Option<&str>, right: Option<&str>) -> bool {
    left.zip(right)
        .is_some_and(|(left, right)| normalized_path(left) == normalized_path(right))
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

    let source_kind = identity_bound_plan
        .pointer("/source_identity/source_kind")
        .and_then(Value::as_str);
    let source_path = identity_bound_plan
        .pointer("/source_identity/canonical_path")
        .and_then(Value::as_str);
    let source_size = identity_bound_plan
        .pointer("/source_identity/size_bytes")
        .and_then(Value::as_u64);
    let trusted_package_sha = package_trust
        .get("observed_sha256")
        .and_then(Value::as_str);
    gate(
        source_kind == Some("file_sha256")
            && package_trust
                .get("verified_for_use")
                .and_then(Value::as_bool)
                == Some(true)
            && package_trust
                .get("sha256_matches")
                .and_then(Value::as_bool)
                == Some(true)
            && same_sha256(source_identity, trusted_package_sha),
        "source_package_trust_bound_to_identity",
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
            && selected_image.is_some_and(|value| !value.is_null())
            && same_path(
                source_path,
                image_metadata.get("path").and_then(Value::as_str),
            ),
        "exact_windows_image_bound_to_source",
        &mut satisfied,
        &mut blocked,
    );

    let source_architecture = image_metadata
        .pointer("/selected_image/architecture")
        .and_then(Value::as_str)
        .map(str::to_string);
    let source_edition_id = image_metadata
        .pointer("/selected_image/edition_id")
        .and_then(Value::as_str)
        .map(str::to_string);
    let selected_image_size_bytes = image_metadata
        .pointer("/selected_image/image_size_bytes")
        .and_then(Value::as_u64);
    gate(
        source_edition_id
            .as_deref()
            .is_some_and(|edition| !edition.trim().is_empty()),
        "source_windows_edition_identified",
        &mut satisfied,
        &mut blocked,
    );

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
    let target_stable_identity = target_safety
        .get("target_stable_identity_sha256")
        .and_then(Value::as_str);
    let target_size = target_safety
        .get("target_size_bytes")
        .and_then(Value::as_u64);
    gate(
        target_safety
            .get("safe_to_prepare")
            .and_then(Value::as_bool)
            == Some(true)
            && target_safety
                .get("source_target_distinct")
                .and_then(Value::as_bool)
                == Some(true)
            && is_sha256(target_identity)
            && is_sha256(target_stable_identity)
            && source_size.is_some()
            && target_safety
                .get("source_size_bytes")
                .and_then(Value::as_u64)
                == source_size
            && selected_image_size_bytes.is_some()
            && target_size
                .zip(selected_image_size_bytes)
                .is_some_and(|(target, required)| target >= required),
        "target_safety_bound_to_source_and_deployed_size",
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
            )
            && same_sha256(
                source_identity,
                rollback_bundle
                    .get("source_identity_sha256")
                    .and_then(Value::as_str),
            )
            && same_sha256(
                target_identity,
                rollback_bundle
                    .get("target_identity_sha256")
                    .and_then(Value::as_str),
            )
            && same_sha256(
                target_stable_identity,
                rollback_bundle
                    .get("target_stable_identity_sha256")
                    .and_then(Value::as_str),
            ),
        "rollback_bundle_bound_to_source_and_target",
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
        source_edition_id,
        selected_image_size_bytes,
        target_architecture,
        source_identity_sha256: source_identity.map(str::to_string),
        target_identity_sha256: target_identity.map(str::to_string),
        target_stable_identity_sha256: target_stable_identity.map(str::to_string),
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
    use serde_json::{json, Value};

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
                    "complete": true,
                    "source_kind": "file_sha256",
                    "canonical_path": "C:/recovery/install.wim",
                    "size_bytes": 4096
                },
                "destructive_actions_performed": false
            }),
            json!({
                "verified_for_use": true,
                "sha256_matches": true,
                "observed_sha256": "a".repeat(64)
            }),
            json!({
                "path": "C:/recovery/install.wim",
                "metadata_verified": true,
                "selected_index": 2,
                "selected_image": {
                    "index": 2,
                    "architecture": "x64",
                    "edition_id": "Professional",
                    "image_size_bytes": 20_000
                },
                "architecture_compatibility": {
                    "target_architecture": "x64",
                    "compatible": true
                }
            }),
            json!({
                "safe_to_prepare": true,
                "source_target_distinct": true,
                "target_identity_sha256": "b".repeat(64),
                "target_stable_identity_sha256": "d".repeat(64),
                "target_size_bytes": 64_000,
                "source_size_bytes": 4096
            }),
            json!({
                "complete": true,
                "repair_unlock_ready": true,
                "system_configuration_mutated": false,
                "bundle_sha256": "c".repeat(64),
                "source_identity_sha256": "a".repeat(64),
                "target_identity_sha256": "b".repeat(64),
                "target_stable_identity_sha256": "d".repeat(64)
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
            .contains(&"source_package_trust_bound_to_identity".to_string()));
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
            .contains(&"exact_windows_image_bound_to_source".to_string()));
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
    fn compressed_source_size_alone_cannot_pass_capacity_gate() {
        let (plan, trust, metadata, mut target, rollback) = evidence();
        target["target_size_bytes"] = json!(8_000);
        let result =
            assess_restore_readiness(&plan, &trust, &metadata, &target, &rollback);
        assert!(result
            .blocked_gates
            .contains(&"target_safety_bound_to_source_and_deployed_size".to_string()));
    }

    #[test]
    fn same_device_target_blocks_readiness() {
        let (plan, trust, metadata, mut target, rollback) = evidence();
        target["source_target_distinct"] = json!(false);
        let result =
            assess_restore_readiness(&plan, &trust, &metadata, &target, &rollback);
        assert!(result
            .blocked_gates
            .contains(&"target_safety_bound_to_source_and_deployed_size".to_string()));
    }

    #[test]
    fn mismatched_package_identity_blocks_readiness() {
        let (plan, mut trust, metadata, target, rollback) = evidence();
        trust["observed_sha256"] = json!("d".repeat(64));
        let result =
            assess_restore_readiness(&plan, &trust, &metadata, &target, &rollback);
        assert!(result
            .blocked_gates
            .contains(&"source_package_trust_bound_to_identity".to_string()));
    }

    #[test]
    fn mismatched_image_path_blocks_readiness() {
        let (plan, trust, mut metadata, target, rollback) = evidence();
        metadata["path"] = json!("C:/other/install.wim");
        let result =
            assess_restore_readiness(&plan, &trust, &metadata, &target, &rollback);
        assert!(result
            .blocked_gates
            .contains(&"exact_windows_image_bound_to_source".to_string()));
    }

    #[test]
    fn rollback_bundle_from_different_target_is_rejected() {
        let (plan, trust, metadata, target, mut rollback) = evidence();
        rollback["target_identity_sha256"] = json!("e".repeat(64));
        let result =
            assess_restore_readiness(&plan, &trust, &metadata, &target, &rollback);
        assert!(result
            .blocked_gates
            .contains(&"rollback_bundle_bound_to_source_and_target".to_string()));
    }

    #[test]
    fn mismatched_stable_target_identity_blocks_readiness() {
        let (plan, trust, metadata, target, mut rollback) = evidence();
        rollback["target_stable_identity_sha256"] = json!("e".repeat(64));
        let result =
            assess_restore_readiness(&plan, &trust, &metadata, &target, &rollback);
        assert!(result
            .blocked_gates
            .contains(&"rollback_bundle_bound_to_source_and_target".to_string()));
    }

    #[test]
    fn missing_windows_edition_blocks_readiness() {
        let (plan, trust, mut metadata, target, rollback) = evidence();
        metadata["selected_image"]["edition_id"] = Value::Null;
        let result =
            assess_restore_readiness(&plan, &trust, &metadata, &target, &rollback);
        assert!(result
            .blocked_gates
            .contains(&"source_windows_edition_identified".to_string()));
    }

    #[test]
    fn incomplete_rollback_bundle_blocks_readiness() {
        let (plan, trust, metadata, target, mut rollback) = evidence();
        rollback["complete"] = json!(false);
        let result =
            assess_restore_readiness(&plan, &trust, &metadata, &target, &rollback);
        assert!(result
            .blocked_gates
            .contains(&"rollback_bundle_bound_to_source_and_target".to_string()));
    }
}
