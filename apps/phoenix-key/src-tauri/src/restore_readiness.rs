use crate::source_identity::verify_identity_bound_plan_sha256;
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
        .is_some_and(|items| {
            items
                .iter()
                .filter_map(Value::as_str)
                .any(|item| item == expected)
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
    source_identity_verification: &Value,
    package_trust: &Value,
    image_metadata: &Value,
    target_safety: &Value,
    target_identity_verification: &Value,
    rollback_bundle: &Value,
) -> RestoreReadiness {
    let mut satisfied = Vec::new();
    let mut blocked = Vec::new();

    gate(
        verify_identity_bound_plan_sha256(identity_bound_plan),
        "identity_bound_plan_integrity",
        &mut satisfied,
        &mut blocked,
    );

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

    let source_identity_current = source_identity_verification
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
        source_identity_current,
        "fresh_source_identity_revalidated",
        &mut satisfied,
        &mut blocked,
    );

    let trusted_package_sha = package_trust
        .get("observed_sha256")
        .and_then(Value::as_str);
    let source_integrity_bound = match source_kind {
        Some("file_sha256") => {
            package_trust
                .get("verified_for_use")
                .and_then(Value::as_bool)
                == Some(true)
                && package_trust
                    .get("sha256_matches")
                    .and_then(Value::as_bool)
                    == Some(true)
                && same_sha256(source_identity, trusted_package_sha)
        }
        Some("directory_manifest") => {
            source_identity_current
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
        source_integrity_bound,
        "source_integrity_bound_to_identity",
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
            && match source_kind {
                Some("file_sha256") => same_path(
                    source_path,
                    image_metadata.get("path").and_then(Value::as_str),
                ),
                Some("directory_manifest") => descendant_path(
                    source_path,
                    image_metadata.get("path").and_then(Value::as_str),
                ),
                _ => false,
            },
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
        rollback_bundle.get("complete").and_then(Value::as_bool) == Some(true)
            && rollback_bundle
                .get("restore_unlock_ready")
                .and_then(Value::as_bool)
                == Some(true)
            && string_array_contains(
                rollback_bundle,
                "restore_unlock_scope",
                "apply_system_image",
            )
            && !string_array_contains(
                rollback_bundle,
                "always_blocked_by_this_bundle",
                "apply_system_image",
            )
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

    gate(
        identity_bound_plan.get("schema").and_then(Value::as_str)
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
        "structured_dry_run_boundary_intact",
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
    source_identity_verification_json: String,
    package_trust_json: String,
    image_metadata_json: String,
    target_safety_json: String,
    target_identity_verification_json: String,
    rollback_bundle_json: String,
) -> Result<RestoreReadiness, String> {
    let parse = |label: &str, text: String| -> Result<Value, String> {
        serde_json::from_str(&text)
            .map_err(|error| format!("invalid {label} JSON: {error}"))
    };
    Ok(assess_restore_readiness(
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
        &parse("rollback bundle", rollback_bundle_json)?,
    ))
}

#[cfg(test)]
mod tests {
    use super::assess_restore_readiness;
    use crate::source_identity::identity_bound_plan_sha256;
    use serde_json::{json, Value};

    fn evidence() -> (
        serde_json::Value,
        serde_json::Value,
        serde_json::Value,
        serde_json::Value,
        serde_json::Value,
        serde_json::Value,
        serde_json::Value,
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
            json!({
                "safe_to_prepare": true,
                "source_target_distinct": true,
                "target_identity_sha256": "b".repeat(64),
                "target_stable_identity_sha256": "d".repeat(64),
                "target_size_bytes": 64_000,
                "source_size_bytes": 4096
            }),
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
            json!({
                "complete": true,
                "restore_unlock_ready": true,
                "restore_unlock_scope": ["apply_system_image"],
                "always_blocked_by_this_bundle": [],
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
        let (plan, source_verification, trust, metadata, target, verification, rollback) = evidence();
        let result =
            assess_restore_readiness(
                &plan,
                &source_verification,
                &trust,
                &metadata,
                &target,
                &verification,
                &rollback,
            );
        assert!(result.ready_for_restore_executor_design);
        assert!(!result.executable);
        assert!(result.blocked_gates.is_empty());
        assert_eq!(result.selected_image_index, Some(2));
    }

    #[test]
    fn stale_source_revalidation_blocks_readiness() {
        let (plan, mut source_verification, trust, metadata, target, verification, rollback) =
            evidence();
        source_verification["matches"] = json!(false);
        source_verification["reanalysis_required"] = json!(true);
        source_verification["observed_sha256"] = json!("e".repeat(64));
        let result = assess_restore_readiness(
            &plan,
            &source_verification,
            &trust,
            &metadata,
            &target,
            &verification,
            &rollback,
        );
        assert!(!result.ready_for_restore_executor_design);
        assert!(result
            .blocked_gates
            .contains(&"fresh_source_identity_revalidated".to_string()));
    }

    #[test]
    fn directory_manifest_source_uses_fresh_manifest_identity_not_package_signature() {
        let (
            mut plan,
            source_verification,
            _trust,
            mut metadata,
            target,
            verification,
            rollback,
        ) = evidence();
        plan["source_identity"]["source_kind"] = json!("directory_manifest");
        plan["source_identity"]["canonical_path"] =
            json!("C:/recovery/WindowsImageBackup");
        plan["source_identity"]["entry_count"] = json!(4);
        plan["source_identity"]["scan_limited"] = json!(false);
        plan["plan_sha256"] = Value::String(identity_bound_plan_sha256(&plan).unwrap());
        metadata["path"] =
            json!("C:/recovery/WindowsImageBackup/PC/Backup/system.vhdx");
        let result = assess_restore_readiness(
            &plan,
            &source_verification,
            &json!({}),
            &metadata,
            &target,
            &verification,
            &rollback,
        );
        assert!(result
            .satisfied_gates
            .contains(&"source_integrity_bound_to_identity".to_string()));
        assert!(result
            .satisfied_gates
            .contains(&"exact_windows_image_bound_to_source".to_string()));
    }

    #[test]
    fn stale_target_revalidation_blocks_readiness() {
        let (plan, source_verification, trust, metadata, target, mut verification, rollback) = evidence();
        verification["matches"] = json!(false);
        verification["snapshot_matches"] = json!(false);
        verification["reanalysis_required"] = json!(true);
        verification["observed_snapshot_identity_sha256"] = json!("e".repeat(64));
        let result = assess_restore_readiness(
            &plan,
            &source_verification,
            &trust,
            &metadata,
            &target,
            &verification,
            &rollback,
        );
        assert!(!result.ready_for_restore_executor_design);
        assert!(result
            .blocked_gates
            .contains(&"fresh_target_identity_revalidated".to_string()));
        assert!(!result.executable);
    }

    #[test]
    fn repair_only_rollback_bundle_cannot_unlock_system_image_restore() {
        let (plan, source_verification, trust, metadata, target, verification, mut rollback) = evidence();
        rollback["restore_unlock_ready"] = json!(false);
        rollback["restore_unlock_scope"] = json!([]);
        rollback["repair_unlock_ready"] = json!(true);
        rollback["repair_unlock_scope"] =
            json!(["bcd_repair", "winre_repair", "efi_file_repair"]);
        rollback["always_blocked_by_this_bundle"] = json!(["apply_system_image"]);
        let result =
            assess_restore_readiness(
                &plan,
                &source_verification,
                &trust,
                &metadata,
                &target,
                &verification,
                &rollback,
            );
        assert!(!result.ready_for_restore_executor_design);
        assert!(result
            .blocked_gates
            .contains(&"rollback_bundle_bound_to_source_and_target".to_string()));
        assert!(!result.executable);
    }

    #[test]
    fn executable_dry_run_claim_blocks_readiness() {
        let (mut plan, source_verification, trust, metadata, target, verification, rollback) = evidence();
        plan["dry_run_summary"]["executable"] = json!(true);
        plan["plan_sha256"] =
            Value::String(identity_bound_plan_sha256(&plan).unwrap());
        let result =
            assess_restore_readiness(
                &plan,
                &source_verification,
                &trust,
                &metadata,
                &target,
                &verification,
                &rollback,
            );
        assert!(!result.ready_for_restore_executor_design);
        assert!(result
            .blocked_gates
            .contains(&"structured_dry_run_boundary_intact".to_string()));
        assert!(!result.executable);
    }

    #[test]
    fn reported_mutation_in_dry_run_blocks_readiness() {
        let (mut plan, source_verification, trust, metadata, target, verification, rollback) = evidence();
        plan["dry_run_summary"]["mutation_steps_executed"] = json!(1);
        plan["plan_sha256"] =
            Value::String(identity_bound_plan_sha256(&plan).unwrap());
        let result =
            assess_restore_readiness(
                &plan,
                &source_verification,
                &trust,
                &metadata,
                &target,
                &verification,
                &rollback,
            );
        assert!(result
            .blocked_gates
            .contains(&"structured_dry_run_boundary_intact".to_string()));
    }

    #[test]
    fn tampered_identity_bound_plan_blocks_readiness() {
        let (mut plan, source_verification, trust, metadata, target, verification, rollback) = evidence();
        plan["destructive_actions_performed"] = json!(true);
        let result =
            assess_restore_readiness(
                &plan,
                &source_verification,
                &trust,
                &metadata,
                &target,
                &verification,
                &rollback,
            );
        assert!(!result.ready_for_restore_executor_design);
        assert!(result
            .blocked_gates
            .contains(&"identity_bound_plan_integrity".to_string()));
    }

    #[test]
    fn missing_package_trust_blocks_readiness() {
        let (plan, source_verification, mut trust, metadata, target, verification, rollback) = evidence();
        trust["verified_for_use"] = json!(false);
        let result =
            assess_restore_readiness(
                &plan,
                &source_verification,
                &trust,
                &metadata,
                &target,
                &verification,
                &rollback,
            );
        assert!(!result.ready_for_restore_executor_design);
        assert!(result
            .blocked_gates
            .contains(&"source_integrity_bound_to_identity".to_string()));
        assert!(!result.executable);
    }

    #[test]
    fn missing_exact_image_selection_blocks_readiness() {
        let (plan, source_verification, trust, mut metadata, target, verification, rollback) = evidence();
        metadata["selected_index"] = Value::Null;
        metadata["selected_image"] = Value::Null;
        let result =
            assess_restore_readiness(
                &plan,
                &source_verification,
                &trust,
                &metadata,
                &target,
                &verification,
                &rollback,
            );
        assert!(result
            .blocked_gates
            .contains(&"exact_windows_image_bound_to_source".to_string()));
    }

    #[test]
    fn architecture_mismatch_blocks_readiness() {
        let (plan, source_verification, trust, mut metadata, target, verification, rollback) = evidence();
        metadata["architecture_compatibility"]["compatible"] = json!(false);
        let result =
            assess_restore_readiness(
                &plan,
                &source_verification,
                &trust,
                &metadata,
                &target,
                &verification,
                &rollback,
            );
        assert!(result
            .blocked_gates
            .contains(&"source_target_architecture_compatible".to_string()));
    }

    #[test]
    fn compressed_source_size_alone_cannot_pass_capacity_gate() {
        let (plan, source_verification, trust, metadata, mut target, verification, rollback) = evidence();
        target["target_size_bytes"] = json!(8_000);
        let result =
            assess_restore_readiness(
                &plan,
                &source_verification,
                &trust,
                &metadata,
                &target,
                &verification,
                &rollback,
            );
        assert!(result
            .blocked_gates
            .contains(&"target_safety_bound_to_source_and_deployed_size".to_string()));
    }

    #[test]
    fn same_device_target_blocks_readiness() {
        let (plan, source_verification, trust, metadata, mut target, verification, rollback) = evidence();
        target["source_target_distinct"] = json!(false);
        let result =
            assess_restore_readiness(
                &plan,
                &source_verification,
                &trust,
                &metadata,
                &target,
                &verification,
                &rollback,
            );
        assert!(result
            .blocked_gates
            .contains(&"target_safety_bound_to_source_and_deployed_size".to_string()));
    }

    #[test]
    fn mismatched_package_identity_blocks_readiness() {
        let (plan, source_verification, mut trust, metadata, target, verification, rollback) = evidence();
        trust["observed_sha256"] = json!("d".repeat(64));
        let result =
            assess_restore_readiness(
                &plan,
                &source_verification,
                &trust,
                &metadata,
                &target,
                &verification,
                &rollback,
            );
        assert!(result
            .blocked_gates
            .contains(&"source_integrity_bound_to_identity".to_string()));
    }

    #[test]
    fn mismatched_image_path_blocks_readiness() {
        let (plan, source_verification, trust, mut metadata, target, verification, rollback) = evidence();
        metadata["path"] = json!("C:/other/install.wim");
        let result =
            assess_restore_readiness(
                &plan,
                &source_verification,
                &trust,
                &metadata,
                &target,
                &verification,
                &rollback,
            );
        assert!(result
            .blocked_gates
            .contains(&"exact_windows_image_bound_to_source".to_string()));
    }

    #[test]
    fn rollback_bundle_from_different_target_is_rejected() {
        let (plan, source_verification, trust, metadata, target, verification, mut rollback) = evidence();
        rollback["target_identity_sha256"] = json!("e".repeat(64));
        let result =
            assess_restore_readiness(
                &plan,
                &source_verification,
                &trust,
                &metadata,
                &target,
                &verification,
                &rollback,
            );
        assert!(result
            .blocked_gates
            .contains(&"rollback_bundle_bound_to_source_and_target".to_string()));
    }

    #[test]
    fn mismatched_stable_target_identity_blocks_readiness() {
        let (plan, source_verification, trust, metadata, target, verification, mut rollback) = evidence();
        rollback["target_stable_identity_sha256"] = json!("e".repeat(64));
        let result =
            assess_restore_readiness(
                &plan,
                &source_verification,
                &trust,
                &metadata,
                &target,
                &verification,
                &rollback,
            );
        assert!(result
            .blocked_gates
            .contains(&"rollback_bundle_bound_to_source_and_target".to_string()));
    }

    #[test]
    fn missing_windows_edition_blocks_readiness() {
        let (plan, source_verification, trust, mut metadata, target, verification, rollback) = evidence();
        metadata["selected_image"]["edition_id"] = Value::Null;
        let result =
            assess_restore_readiness(
                &plan,
                &source_verification,
                &trust,
                &metadata,
                &target,
                &verification,
                &rollback,
            );
        assert!(result
            .blocked_gates
            .contains(&"source_windows_edition_identified".to_string()));
    }

    #[test]
    fn incomplete_rollback_bundle_blocks_readiness() {
        let (plan, source_verification, trust, metadata, target, verification, mut rollback) = evidence();
        rollback["complete"] = json!(false);
        let result =
            assess_restore_readiness(
                &plan,
                &source_verification,
                &trust,
                &metadata,
                &target,
                &verification,
                &rollback,
            );
        assert!(result
            .blocked_gates
            .contains(&"rollback_bundle_bound_to_source_and_target".to_string()));
    }
}
