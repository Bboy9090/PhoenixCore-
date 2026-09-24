use crate::restore_rollback_contract::verify_restore_target_rollback_contract_sha256;
use serde::Serialize;
use serde_json::Value;
use sha2::{Digest, Sha256};

pub const EXPLICIT_DISCARD_ACKNOWLEDGEMENT: &str =
    "I ACCEPT DATA LOSS ON THIS TARGET";

#[derive(Debug, Clone, Serialize, PartialEq, Eq)]
pub struct TargetDataPreservationReceipt {
    pub schema: &'static str,
    pub mode: String,
    pub target_stable_identity_sha256: String,
    pub rollback_contract_sha256: String,
    pub acknowledgement: String,
    pub resolved: bool,
    pub block_reasons: Vec<String>,
    pub required_next_evidence: Vec<String>,
    pub restore_unlock_ready: bool,
    pub system_mutations_performed: bool,
    pub receipt_sha256: String,
}

#[derive(Debug, Serialize)]
struct UnsignedTargetDataPreservationReceipt<'a> {
    schema: &'static str,
    mode: &'a str,
    target_stable_identity_sha256: &'a str,
    rollback_contract_sha256: &'a str,
    acknowledgement: &'a str,
    resolved: bool,
    block_reasons: &'a [String],
    required_next_evidence: &'a [String],
    restore_unlock_ready: bool,
    system_mutations_performed: bool,
}

fn valid_sha256(value: &str) -> bool {
    value.len() == 64 && value.bytes().all(|byte| byte.is_ascii_hexdigit())
}

fn receipt_sha256(receipt: &TargetDataPreservationReceipt) -> String {
    let unsigned = UnsignedTargetDataPreservationReceipt {
        schema: receipt.schema,
        mode: &receipt.mode,
        target_stable_identity_sha256: &receipt.target_stable_identity_sha256,
        rollback_contract_sha256: &receipt.rollback_contract_sha256,
        acknowledgement: &receipt.acknowledgement,
        resolved: receipt.resolved,
        block_reasons: &receipt.block_reasons,
        required_next_evidence: &receipt.required_next_evidence,
        restore_unlock_ready: receipt.restore_unlock_ready,
        system_mutations_performed: receipt.system_mutations_performed,
    };
    let bytes =
        serde_json::to_vec(&unsigned).expect("data-preservation receipt serialization cannot fail");
    format!("{:x}", Sha256::digest(bytes))
}

pub fn build_target_data_preservation_receipt(
    target_safety: &Value,
    rollback_contract: &Value,
    mode: &str,
    acknowledgement: &str,
) -> Result<TargetDataPreservationReceipt, String> {
    if target_safety
        .get("safe_to_prepare")
        .and_then(Value::as_bool)
        != Some(true)
    {
        return Err("target safety evidence is not approved for preparation".to_string());
    }
    if !verify_restore_target_rollback_contract_sha256(rollback_contract) {
        return Err("rollback contract checksum is invalid".to_string());
    }

    let target_stable_identity = target_safety
        .get("target_stable_identity_sha256")
        .and_then(Value::as_str)
        .ok_or_else(|| "target stable identity is missing".to_string())?
        .to_ascii_lowercase();
    let contract_target_stable_identity = rollback_contract
        .get("target_stable_identity_sha256")
        .and_then(Value::as_str)
        .ok_or_else(|| "rollback contract target stable identity is missing".to_string())?
        .to_ascii_lowercase();
    let contract_sha256 = rollback_contract
        .get("contract_sha256")
        .and_then(Value::as_str)
        .ok_or_else(|| "rollback contract SHA-256 is missing".to_string())?
        .to_ascii_lowercase();

    if !valid_sha256(&target_stable_identity)
        || !valid_sha256(&contract_target_stable_identity)
        || !valid_sha256(&contract_sha256)
    {
        return Err("data-preservation gate requires valid SHA-256 identities".to_string());
    }
    if target_stable_identity != contract_target_stable_identity {
        return Err("target stable identity does not match rollback contract".to_string());
    }

    let mode = mode.trim();
    let acknowledgement = acknowledgement.trim();
    let mut block_reasons = Vec::new();
    let mut required_next_evidence = Vec::new();

    let resolved = match mode {
        "explicit_discard" => {
            if acknowledgement != EXPLICIT_DISCARD_ACKNOWLEDGEMENT {
                block_reasons.push("explicit_discard_acknowledgement_missing_or_inexact".to_string());
                false
            } else {
                true
            }
        }
        "preserve_existing_data" => {
            block_reasons.push("target_data_backup_receipt_not_yet_present".to_string());
            required_next_evidence.push("target_data_backup_receipt".to_string());
            false
        }
        _ => {
            block_reasons.push("unsupported_data_preservation_mode".to_string());
            false
        }
    };

    let mut receipt = TargetDataPreservationReceipt {
        schema: "phoenix_key.target_data_preservation_receipt.v1",
        mode: mode.to_string(),
        target_stable_identity_sha256: target_stable_identity,
        rollback_contract_sha256: contract_sha256,
        acknowledgement: acknowledgement.to_string(),
        resolved,
        block_reasons,
        required_next_evidence,
        restore_unlock_ready: false,
        system_mutations_performed: false,
        receipt_sha256: String::new(),
    };
    receipt.receipt_sha256 = receipt_sha256(&receipt);
    Ok(receipt)
}

#[tauri::command]
pub fn create_target_data_preservation_decision(
    target_safety_json: String,
    rollback_contract_json: String,
    mode: String,
    acknowledgement: String,
) -> Result<TargetDataPreservationReceipt, String> {
    let target_safety: Value = serde_json::from_str(&target_safety_json)
        .map_err(|error| format!("invalid target-safety JSON: {error}"))?;
    let rollback_contract: Value = serde_json::from_str(&rollback_contract_json)
        .map_err(|error| format!("invalid rollback-contract JSON: {error}"))?;
    build_target_data_preservation_receipt(
        &target_safety,
        &rollback_contract,
        &mode,
        &acknowledgement,
    )
}

#[cfg(test)]
mod tests {
    use super::{
        build_target_data_preservation_receipt, EXPLICIT_DISCARD_ACKNOWLEDGEMENT,
    };
    use crate::restore_rollback_contract::build_restore_target_rollback_contract;
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
            "target_stable_identity_sha256": "c".repeat(64),
            "target_size_bytes": 64_000
        })
    }

    fn contract() -> Value {
        serde_json::to_value(
            build_restore_target_rollback_contract(&plan(), &target()).unwrap(),
        )
        .unwrap()
    }

    #[test]
    fn explicit_discard_requires_exact_acknowledgement() {
        let blocked = build_target_data_preservation_receipt(
            &target(),
            &contract(),
            "explicit_discard",
            "I accept",
        )
        .unwrap();
        assert!(!blocked.resolved);
        assert!(!blocked.restore_unlock_ready);

        let resolved = build_target_data_preservation_receipt(
            &target(),
            &contract(),
            "explicit_discard",
            EXPLICIT_DISCARD_ACKNOWLEDGEMENT,
        )
        .unwrap();
        assert!(resolved.resolved);
        assert_eq!(resolved.receipt_sha256.len(), 64);
        assert!(!resolved.restore_unlock_ready);
        assert!(!resolved.system_mutations_performed);
    }

    #[test]
    fn preserve_mode_never_claims_success_without_backup_receipt() {
        let receipt = build_target_data_preservation_receipt(
            &target(),
            &contract(),
            "preserve_existing_data",
            "",
        )
        .unwrap();
        assert!(!receipt.resolved);
        assert!(receipt
            .required_next_evidence
            .contains(&"target_data_backup_receipt".to_string()));
        assert!(!receipt.restore_unlock_ready);
    }

    #[test]
    fn stable_target_mismatch_is_rejected() {
        let mut target = target();
        target["target_stable_identity_sha256"] = json!("d".repeat(64));
        assert!(build_target_data_preservation_receipt(
            &target,
            &contract(),
            "explicit_discard",
            EXPLICIT_DISCARD_ACKNOWLEDGEMENT,
        )
        .is_err());
    }
}
