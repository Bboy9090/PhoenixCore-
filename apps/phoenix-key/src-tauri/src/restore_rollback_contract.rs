use crate::source_identity::verify_identity_bound_plan_sha256;
use serde::Serialize;
use serde_json::Value;
use sha2::{Digest, Sha256};

#[derive(Debug, Clone, Serialize, PartialEq, Eq)]
pub struct RestoreTargetRollbackContract {
    pub schema: &'static str,
    pub source_identity_sha256: String,
    pub target_identity_sha256: String,
    pub target_stable_identity_sha256: String,
    pub target_size_bytes: u64,
    pub required_artifacts: Vec<&'static str>,
    pub artifact_destination_requirement: &'static str,
    pub fresh_target_revalidation_required: bool,
    pub restore_unlock_ready: bool,
    pub restore_unlock_scope: Vec<&'static str>,
    pub always_blocked_by_this_contract: Vec<&'static str>,
    pub system_mutations_performed: bool,
    pub contract_sha256: String,
}

fn valid_sha256(value: &str) -> bool {
    value.len() == 64 && value.bytes().all(|byte| byte.is_ascii_hexdigit())
}

fn hash_contract_without_digest(
    contract: &RestoreTargetRollbackContract,
) -> Result<String, String> {
    let mut value = serde_json::to_value(contract)
        .map_err(|error| format!("cannot serialize restore rollback contract: {error}"))?;
    value
        .as_object_mut()
        .ok_or_else(|| "restore rollback contract did not serialize as an object".to_string())?
        .remove("contract_sha256");
    let bytes = serde_json::to_vec(&value)
        .map_err(|error| format!("cannot canonicalize restore rollback contract: {error}"))?;
    let mut hasher = Sha256::new();
    hasher.update(bytes);
    Ok(format!("{:x}", hasher.finalize()))
}

pub fn build_restore_target_rollback_contract(
    identity_bound_plan: &Value,
    target_safety: &Value,
) -> Result<RestoreTargetRollbackContract, String> {
    if !verify_identity_bound_plan_sha256(identity_bound_plan) {
        return Err("identity-bound recovery plan checksum is invalid".to_string());
    }

    if target_safety
        .get("safe_to_prepare")
        .and_then(Value::as_bool)
        != Some(true)
    {
        return Err("target safety evidence is not approved for preparation".to_string());
    }
    if target_safety
        .get("source_target_distinct")
        .and_then(Value::as_bool)
        != Some(true)
    {
        return Err("source and target physical devices are not proven distinct".to_string());
    }

    let source_identity = identity_bound_plan
        .pointer("/source_identity/sha256")
        .and_then(Value::as_str)
        .ok_or_else(|| "recovery plan is missing source identity".to_string())?;
    let target_identity = target_safety
        .get("target_identity_sha256")
        .and_then(Value::as_str)
        .ok_or_else(|| "target safety evidence is missing snapshot identity".to_string())?;
    let target_stable_identity = target_safety
        .get("target_stable_identity_sha256")
        .and_then(Value::as_str)
        .ok_or_else(|| "target safety evidence is missing stable hardware identity".to_string())?;
    let target_size_bytes = target_safety
        .get("target_size_bytes")
        .and_then(Value::as_u64)
        .ok_or_else(|| "target safety evidence is missing target capacity".to_string())?;

    if !valid_sha256(source_identity)
        || !valid_sha256(target_identity)
        || !valid_sha256(target_stable_identity)
    {
        return Err("restore rollback contract requires valid SHA-256 identities".to_string());
    }
    if target_size_bytes == 0 {
        return Err("restore rollback contract requires a nonzero target capacity".to_string());
    }

    let mut contract = RestoreTargetRollbackContract {
        schema: "phoenix_key.restore_target_rollback_contract.v1",
        source_identity_sha256: source_identity.to_ascii_lowercase(),
        target_identity_sha256: target_identity.to_ascii_lowercase(),
        target_stable_identity_sha256: target_stable_identity.to_ascii_lowercase(),
        target_size_bytes,
        required_artifacts: vec![
            "target_partition_table_backup",
            "target_partition_manifest",
            "target_boot_metadata_backup_if_present",
            "target_data_preservation_receipt_or_explicit_discard_decision",
            "artifact_checksums",
        ],
        artifact_destination_requirement: "separate-physical-device-from-restore-target",
        fresh_target_revalidation_required: true,
        restore_unlock_ready: false,
        restore_unlock_scope: Vec::new(),
        always_blocked_by_this_contract: vec!["apply_system_image"],
        system_mutations_performed: false,
        contract_sha256: String::new(),
    };
    contract.contract_sha256 = hash_contract_without_digest(&contract)?;
    Ok(contract)
}

#[tauri::command]
pub fn plan_restore_target_rollback_contract(
    identity_bound_plan_json: String,
    target_safety_json: String,
) -> Result<RestoreTargetRollbackContract, String> {
    let identity_bound_plan: Value = serde_json::from_str(&identity_bound_plan_json)
        .map_err(|error| format!("invalid identity-bound plan JSON: {error}"))?;
    let target_safety: Value = serde_json::from_str(&target_safety_json)
        .map_err(|error| format!("invalid target-safety JSON: {error}"))?;
    build_restore_target_rollback_contract(&identity_bound_plan, &target_safety)
}

#[cfg(test)]
mod tests {
    use super::build_restore_target_rollback_contract;
    use crate::source_identity::identity_bound_plan_sha256;
    use serde_json::{json, Value};

    fn plan() -> Value {
        let mut plan = json!({
            "schema": "phoenix_key.windows_recovery_plan.v4",
            "source_identity": {
                "sha256": "a".repeat(64),
                "complete": true,
                "source_kind": "file_sha256",
                "canonical_path": "C:/recovery/install.wim",
                "size_bytes": 4096
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

    fn target() -> Value {
        json!({
            "safe_to_prepare": true,
            "source_target_distinct": true,
            "target_identity_sha256": "b".repeat(64),
            "target_stable_identity_sha256": "d".repeat(64),
            "target_size_bytes": 64_000
        })
    }

    #[test]
    fn contract_binds_source_and_both_target_identities() {
        let contract = build_restore_target_rollback_contract(&plan(), &target()).unwrap();
        assert_eq!(contract.source_identity_sha256, "a".repeat(64));
        assert_eq!(contract.target_identity_sha256, "b".repeat(64));
        assert_eq!(contract.target_stable_identity_sha256, "d".repeat(64));
        assert_eq!(contract.contract_sha256.len(), 64);
        assert!(contract.fresh_target_revalidation_required);
    }

    #[test]
    fn planning_contract_never_unlocks_restore_execution() {
        let contract = build_restore_target_rollback_contract(&plan(), &target()).unwrap();
        assert!(!contract.restore_unlock_ready);
        assert!(contract.restore_unlock_scope.is_empty());
        assert!(contract
            .always_blocked_by_this_contract
            .contains(&"apply_system_image"));
        assert!(!contract.system_mutations_performed);
    }

    #[test]
    fn unsafe_target_is_rejected() {
        let mut target = target();
        target["safe_to_prepare"] = json!(false);
        assert!(build_restore_target_rollback_contract(&plan(), &target).is_err());
    }

    #[test]
    fn tampered_plan_is_rejected() {
        let mut plan = plan();
        plan["source_identity"]["size_bytes"] = json!(8192);
        assert!(build_restore_target_rollback_contract(&plan, &target()).is_err());
    }
}
