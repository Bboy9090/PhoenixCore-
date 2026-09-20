use crate::restore_rollback_contract::verify_restore_target_rollback_contract_sha256;
use crate::source_identity::verify_identity_bound_plan_sha256;
use serde::Serialize;
use serde_json::Value;

#[derive(Debug, Clone, Serialize, PartialEq, Eq)]
pub struct RestoreHardwarePreflight {
    pub schema: &'static str,
    pub ready_to_capture_hardware_rollback_evidence: bool,
    pub executable: bool,
    pub satisfied_gates: Vec<String>,
    pub blocked_gates: Vec<String>,
    pub required_hardware_evidence: Vec<String>,
    pub source_identity_sha256: Option<String>,
    pub image_path: Option<String>,
    pub target_identity_sha256: Option<String>,
    pub target_stable_identity_sha256: Option<String>,
    pub rollback_contract_sha256: Option<String>,
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

fn descendant_path(root: Option<&str>, child: Option<&str>) -> bool {
    root.zip(child).is_some_and(|(root, child)| {
        let root = normalized_path(root);
        let child = normalized_path(child);
        if root.is_empty()
            || child.is_empty()
            || child.contains("/../")
            || child.ends_with("/..")
            || child.starts_with("../")
        {
            return false;
        }
        child
            .strip_prefix(&(root + "/"))
            .is_some_and(|relative| !relative.is_empty())
    })
}

fn string_array_contains(value: &Value, key: &str, expected: &str) -> bool {
    value
        .get(key)
        .and_then(Value::as_array)
        .is_some_and(|items| items.iter().filter_map(Value::as_str).any(|item| item == expected))
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

pub fn assess_restore_hardware_preflight(
    identity_bound_plan: &Value,
    source_identity_verification: &Value,
    package_trust: &Value,
    image_metadata: &Value,
    target_safety: &Value,
    target_identity_verification: &Value,
    rollback_contract: &Value,
) -> RestoreHardwarePreflight {
    let mut satisfied = Vec::new();
    let mut blocked = Vec::new();

    let source_identity = identity_bound_plan
        .pointer("/source_identity/sha256")
        .and_then(Value::as_str);
    let source_kind = identity_bound_plan
        .pointer("/source_identity/source_kind")
        .and_then(Value::as_str);
    let source_path = identity_bound_plan
        .pointer("/source_identity/canonical_path")
        .and_then(Value::as_str);
    let source_size = identity_bound_plan
        .pointer("/source_identity/size_bytes")
        .and_then(Value::as_u64);

    gate(
        verify_identity_bound_plan_sha256(identity_bound_plan)
            && identity_bound_plan.get("schema").and_then(Value::as_str)
                == Some("phoenix_key.windows_recovery_plan.v4")
            && identity_bound_plan
                .pointer("/execution_boundary/planner_only")
                .and_then(Value::as_bool)
                == Some(true)
            && identity_bound_plan
                .pointer("/execution_boundary/restore_executor_available")
                .and_then(Value::as_bool)
                == Some(false)
            && identity_bound_plan
                .pointer("/execution_boundary/system_mutations_performed")
                .and_then(Value::as_bool)
                == Some(false)
            && identity_bound_plan
                .pointer("/dry_run_summary/executable")
                .and_then(Value::as_bool)
                == Some(false)
            && identity_bound_plan
                .pointer("/dry_run_summary/mutation_steps_executed")
                .and_then(Value::as_u64)
                == Some(0),
        "identity_bound_non_executable_plan",
        &mut satisfied,
        &mut blocked,
    );

    let source_current = source_identity_verification
        .get("matches")
        .and_then(Value::as_bool)
        == Some(true)
        && source_identity_verification
            .get("reanalysis_required")
            .and_then(Value::as_bool)
            == Some(false)
        && same_sha256(
            source_identity,
            source_identity_verification
                .get("expected_sha256")
                .and_then(Value::as_str),
        )
        && same_sha256(
            source_identity,
            source_identity_verification
                .get("observed_sha256")
                .and_then(Value::as_str),
        );
    gate(
        source_current,
        "fresh_source_identity_revalidated",
        &mut satisfied,
        &mut blocked,
    );

    let source_integrity = match source_kind {
        Some("file_sha256") => {
            package_trust
                .get("verified_for_use")
                .and_then(Value::as_bool)
                == Some(true)
                && package_trust
                    .get("sha256_matches")
                    .and_then(Value::as_bool)
                    == Some(true)
                && same_sha256(
                    source_identity,
                    package_trust.get("observed_sha256").and_then(Value::as_str),
                )
        }
        Some("directory_manifest") => {
            source_current
                && identity_bound_plan
                    .pointer("/source_identity/scan_limited")
                    .and_then(Value::as_bool)
                    == Some(false)
                && identity_bound_plan
                    .pointer("/source_identity/entry_count")
                    .and_then(Value::as_u64)
                    .is_some_and(|count| count > 0)
        }
        _ => false,
    };
    gate(
        source_integrity,
        "source_integrity_bound_to_identity",
        &mut satisfied,
        &mut blocked,
    );

    let image_path = image_metadata.get("path").and_then(Value::as_str);
    let selected_image_size = image_metadata
        .pointer("/selected_image/image_size_bytes")
        .and_then(Value::as_u64);
    let image_bound = image_metadata
        .get("metadata_verified")
        .and_then(Value::as_bool)
        == Some(true)
        && image_metadata.get("selected_index").and_then(Value::as_u64).is_some()
        && image_metadata
            .get("selected_image")
            .is_some_and(|value| !value.is_null())
        && image_metadata
            .pointer("/selected_image/edition_id")
            .and_then(Value::as_str)
            .is_some_and(|edition| !edition.trim().is_empty())
        && image_metadata
            .pointer("/architecture_compatibility/compatible")
            .and_then(Value::as_bool)
            == Some(true)
        && match source_kind {
            Some("file_sha256") => same_path(source_path, image_path),
            Some("directory_manifest") => descendant_path(source_path, image_path),
            _ => false,
        };
    gate(
        image_bound,
        "exact_windows_image_metadata_bound_to_source",
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
            && target_size
                .zip(selected_image_size)
                .is_some_and(|(target, required)| target >= required),
        "target_safety_bound_to_source_and_image",
        &mut satisfied,
        &mut blocked,
    );

    gate(
        target_identity_verification
            .get("matches")
            .and_then(Value::as_bool)
            == Some(true)
            && target_identity_verification
                .get("snapshot_matches")
                .and_then(Value::as_bool)
                == Some(true)
            && target_identity_verification
                .get("stable_identity_matches")
                .and_then(Value::as_bool)
                == Some(true)
            && target_identity_verification
                .get("reanalysis_required")
                .and_then(Value::as_bool)
                == Some(false)
            && target_identity_verification
                .get("system_mutations_performed")
                .and_then(Value::as_bool)
                == Some(false)
            && same_sha256(
                target_identity,
                target_identity_verification
                    .get("expected_snapshot_identity_sha256")
                    .and_then(Value::as_str),
            )
            && same_sha256(
                target_identity,
                target_identity_verification
                    .get("observed_snapshot_identity_sha256")
                    .and_then(Value::as_str),
            )
            && same_sha256(
                target_stable_identity,
                target_identity_verification
                    .get("expected_stable_identity_sha256")
                    .and_then(Value::as_str),
            )
            && same_sha256(
                target_stable_identity,
                target_identity_verification
                    .get("observed_stable_identity_sha256")
                    .and_then(Value::as_str),
            ),
        "fresh_target_identity_revalidated",
        &mut satisfied,
        &mut blocked,
    );

    gate(
        verify_restore_target_rollback_contract_sha256(rollback_contract)
            && rollback_contract.get("schema").and_then(Value::as_str)
                == Some("phoenix_key.restore_target_rollback_contract.v1")
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
            )
            && rollback_contract.get("target_size_bytes").and_then(Value::as_u64)
                == target_size
            && rollback_contract
                .get("fresh_target_revalidation_required")
                .and_then(Value::as_bool)
                == Some(true)
            && rollback_contract
                .get("restore_unlock_ready")
                .and_then(Value::as_bool)
                == Some(false)
            && string_array_contains(
                rollback_contract,
                "always_blocked_by_this_contract",
                "apply_system_image",
            )
            && rollback_contract
                .get("system_mutations_performed")
                .and_then(Value::as_bool)
                == Some(false),
        "rollback_contract_integrity_and_lock",
        &mut satisfied,
        &mut blocked,
    );

    let required_hardware_evidence = rollback_contract
        .get("required_artifacts")
        .and_then(Value::as_array)
        .map(|items| {
            items
                .iter()
                .filter_map(Value::as_str)
                .map(str::to_string)
                .collect::<Vec<_>>()
        })
        .unwrap_or_default();

    gate(
        !required_hardware_evidence.is_empty()
            && rollback_contract
                .get("artifact_destination_requirement")
                .and_then(Value::as_str)
                == Some("separate-physical-device-from-restore-target"),
        "hardware_rollback_requirements_explicit",
        &mut satisfied,
        &mut blocked,
    );

    RestoreHardwarePreflight {
        schema: "phoenix_key.restore_hardware_preflight.v1",
        ready_to_capture_hardware_rollback_evidence: blocked.is_empty(),
        executable: false,
        satisfied_gates: satisfied,
        blocked_gates: blocked,
        required_hardware_evidence,
        source_identity_sha256: source_identity.map(str::to_string),
        image_path: image_path.map(str::to_string),
        target_identity_sha256: target_identity.map(str::to_string),
        target_stable_identity_sha256: target_stable_identity.map(str::to_string),
        rollback_contract_sha256: rollback_contract
            .get("contract_sha256")
            .and_then(Value::as_str)
            .map(str::to_string),
        system_mutations_performed: false,
    }
}

#[tauri::command]
pub fn assess_windows_restore_hardware_preflight(
    identity_bound_plan_json: String,
    source_identity_verification_json: String,
    package_trust_json: String,
    image_metadata_json: String,
    target_safety_json: String,
    target_identity_verification_json: String,
    rollback_contract_json: String,
) -> Result<RestoreHardwarePreflight, String> {
    let parse = |label: &str, text: String| -> Result<Value, String> {
        serde_json::from_str(&text)
            .map_err(|error| format!("invalid {label} JSON: {error}"))
    };

    Ok(assess_restore_hardware_preflight(
        &parse("identity-bound plan", identity_bound_plan_json)?,
        &parse(
            "source identity verification",
            source_identity_verification_json,
        )?,
        &parse("package trust", package_trust_json)?,
        &parse("image metadata", image_metadata_json)?,
        &parse("target safety", target_safety_json)?,
        &parse(
            "target identity verification",
            target_identity_verification_json,
        )?,
        &parse("rollback contract", rollback_contract_json)?,
    ))
}

#[cfg(test)]
mod tests {
    use super::assess_restore_hardware_preflight;
    use crate::restore_rollback_contract::{
        build_restore_target_rollback_contract,
        restore_target_rollback_contract_sha256,
    };
    use crate::source_identity::identity_bound_plan_sha256;
    use serde_json::{json, Value};

    fn evidence() -> (
        Value,
        Value,
        Value,
        Value,
        Value,
        Value,
        Value,
    ) {
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

        let target = json!({
            "safe_to_prepare": true,
            "source_target_distinct": true,
            "target_identity_sha256": "b".repeat(64),
            "target_stable_identity_sha256": "d".repeat(64),
            "target_size_bytes": 64_000,
            "source_size_bytes": 4096
        });
        let rollback = serde_json::to_value(
            build_restore_target_rollback_contract(&plan, &target).unwrap(),
        )
        .unwrap();
        assert_eq!(
            rollback["contract_sha256"].as_str().unwrap(),
            restore_target_rollback_contract_sha256(&rollback).unwrap()
        );

        (
            plan,
            json!({
                "matches": true,
                "reanalysis_required": false,
                "expected_sha256": "a".repeat(64),
                "observed_sha256": "a".repeat(64)
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
            target,
            json!({
                "matches": true,
                "snapshot_matches": true,
                "stable_identity_matches": true,
                "reanalysis_required": false,
                "system_mutations_performed": false,
                "expected_snapshot_identity_sha256": "b".repeat(64),
                "observed_snapshot_identity_sha256": "b".repeat(64),
                "expected_stable_identity_sha256": "d".repeat(64),
                "observed_stable_identity_sha256": "d".repeat(64)
            }),
            rollback,
        )
    }

    #[test]
    fn software_preflight_can_reach_hardware_capture_boundary_without_execution() {
        let (plan, source, trust, metadata, target, verification, rollback) = evidence();
        let result = assess_restore_hardware_preflight(
            &plan,
            &source,
            &trust,
            &metadata,
            &target,
            &verification,
            &rollback,
        );
        assert!(result.ready_to_capture_hardware_rollback_evidence);
        assert!(!result.executable);
        assert!(result.blocked_gates.is_empty());
        assert!(!result.required_hardware_evidence.is_empty());
        assert!(!result.system_mutations_performed);
    }

    #[test]
    fn stale_target_blocks_hardware_capture_boundary() {
        let (plan, source, trust, metadata, target, mut verification, rollback) = evidence();
        verification["matches"] = json!(false);
        verification["snapshot_matches"] = json!(false);
        verification["reanalysis_required"] = json!(true);
        let result = assess_restore_hardware_preflight(
            &plan,
            &source,
            &trust,
            &metadata,
            &target,
            &verification,
            &rollback,
        );
        assert!(!result.ready_to_capture_hardware_rollback_evidence);
        assert!(result
            .blocked_gates
            .contains(&"fresh_target_identity_revalidated".to_string()));
        assert!(!result.executable);
    }

    #[test]
    fn tampered_rollback_contract_blocks_preflight() {
        let (plan, source, trust, metadata, target, verification, mut rollback) = evidence();
        rollback["target_size_bytes"] = json!(128_000);
        let result = assess_restore_hardware_preflight(
            &plan,
            &source,
            &trust,
            &metadata,
            &target,
            &verification,
            &rollback,
        );
        assert!(!result.ready_to_capture_hardware_rollback_evidence);
        assert!(result
            .blocked_gates
            .contains(&"rollback_contract_integrity_and_lock".to_string()));
        assert!(!result.executable);
    }

    #[test]
    fn preflight_rejects_any_executable_plan_claim() {
        let (mut plan, source, trust, metadata, target, verification, rollback) = evidence();
        plan["dry_run_summary"]["executable"] = json!(true);
        plan["plan_sha256"] = Value::String(identity_bound_plan_sha256(&plan).unwrap());
        let result = assess_restore_hardware_preflight(
            &plan,
            &source,
            &trust,
            &metadata,
            &target,
            &verification,
            &rollback,
        );
        assert!(!result.ready_to_capture_hardware_rollback_evidence);
        assert!(result
            .blocked_gates
            .contains(&"identity_bound_non_executable_plan".to_string()));
        assert!(!result.executable);
    }
}
