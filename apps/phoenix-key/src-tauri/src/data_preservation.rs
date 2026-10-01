use crate::restore_rollback_contract::verify_restore_target_rollback_contract_sha256;
use serde::Serialize;
use serde_json::Value;
use sha2::{Digest, Sha256};
use std::fs;

pub const EXPLICIT_DISCARD_ACKNOWLEDGEMENT: &str =
    "I ACCEPT DATA LOSS ON THIS TARGET";

#[derive(Debug, Clone, Serialize, PartialEq, Eq)]
pub struct TargetDataPreservationReceipt {
    pub schema: &'static str,
    pub mode: String,
    pub target_stable_identity_sha256: String,
    pub rollback_contract_sha256: String,
    pub acknowledgement: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub backup_receipt_sha256: Option<String>,
    pub resolved: bool,
    pub block_reasons: Vec<String>,
    pub required_next_evidence: Vec<String>,
    pub restore_unlock_ready: bool,
    pub system_mutations_performed: bool,
    pub receipt_sha256: String,
}

#[derive(Debug, Serialize)]
struct UnsignedTargetDataPreservationReceipt<'a> {
    schema: &'a str,
    mode: &'a str,
    target_stable_identity_sha256: &'a str,
    rollback_contract_sha256: &'a str,
    acknowledgement: &'a str,
    #[serde(skip_serializing_if = "Option::is_none")]
    backup_receipt_sha256: Option<&'a str>,
    resolved: bool,
    block_reasons: &'a [String],
    required_next_evidence: &'a [String],
    restore_unlock_ready: bool,
    system_mutations_performed: bool,
}

#[derive(Debug, Serialize)]
struct UnsignedTargetDataBackupReceipt<'a> {
    schema: &'a str,
    target_stable_identity_sha256: &'a str,
    rollback_contract_sha256: &'a str,
    backup_destination_stable_identity_sha256: &'a str,
    backup_manifest_sha256: &'a str,
    backup_verified: bool,
    files_verified: bool,
    target_bytes_written: u64,
    target_write_attempted: bool,
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
        backup_receipt_sha256: receipt.backup_receipt_sha256.as_deref(),
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

fn target_data_backup_receipt_sha256(value: &Value) -> Option<String> {
    if value.get("schema").and_then(Value::as_str)
        != Some("phoenix_key.target_data_backup_receipt.v1")
    {
        return None;
    }
    let unsigned = UnsignedTargetDataBackupReceipt {
        schema: value.get("schema")?.as_str()?,
        target_stable_identity_sha256: value
            .get("target_stable_identity_sha256")?
            .as_str()?,
        rollback_contract_sha256: value.get("rollback_contract_sha256")?.as_str()?,
        backup_destination_stable_identity_sha256: value
            .get("backup_destination_stable_identity_sha256")?
            .as_str()?,
        backup_manifest_sha256: value.get("backup_manifest_sha256")?.as_str()?,
        backup_verified: value.get("backup_verified")?.as_bool()?,
        files_verified: value.get("files_verified")?.as_bool()?,
        target_bytes_written: value.get("target_bytes_written")?.as_u64()?,
        target_write_attempted: value.get("target_write_attempted")?.as_bool()?,
        system_mutations_performed: value
            .get("system_mutations_performed")?
            .as_bool()?,
    };
    serde_json::to_vec(&unsigned)
        .ok()
        .map(|bytes| format!("{:x}", Sha256::digest(bytes)))
}

pub fn verify_target_data_backup_receipt_sha256(value: &Value) -> bool {
    let Some(expected) = value.get("receipt_sha256").and_then(Value::as_str) else {
        return false;
    };
    valid_sha256(expected)
        && target_data_backup_receipt_sha256(value)
            .is_some_and(|actual| actual.eq_ignore_ascii_case(expected))
}

pub fn verify_target_data_preservation_receipt_sha256(value: &Value) -> bool {
    if value.get("schema").and_then(Value::as_str)
        != Some("phoenix_key.target_data_preservation_receipt.v1")
    {
        return false;
    }
    let Some(expected) = value.get("receipt_sha256").and_then(Value::as_str) else {
        return false;
    };
    if !valid_sha256(expected) {
        return false;
    }

    let Some(schema) = value.get("schema").and_then(Value::as_str) else {
        return false;
    };
    let Some(mode) = value.get("mode").and_then(Value::as_str) else {
        return false;
    };
    let Some(target_stable_identity_sha256) = value
        .get("target_stable_identity_sha256")
        .and_then(Value::as_str)
    else {
        return false;
    };
    let Some(rollback_contract_sha256) =
        value.get("rollback_contract_sha256").and_then(Value::as_str)
    else {
        return false;
    };
    let Some(acknowledgement) = value.get("acknowledgement").and_then(Value::as_str) else {
        return false;
    };
    let backup_receipt_sha256 = value
        .get("backup_receipt_sha256")
        .and_then(Value::as_str);
    if backup_receipt_sha256.is_some_and(|value| !valid_sha256(value)) {
        return false;
    }
    let Some(resolved) = value.get("resolved").and_then(Value::as_bool) else {
        return false;
    };
    let Some(restore_unlock_ready) = value
        .get("restore_unlock_ready")
        .and_then(Value::as_bool)
    else {
        return false;
    };
    let Some(system_mutations_performed) = value
        .get("system_mutations_performed")
        .and_then(Value::as_bool)
    else {
        return false;
    };
    let Ok(block_reasons) = serde_json::from_value::<Vec<String>>(
        value.get("block_reasons").cloned().unwrap_or(Value::Null),
    ) else {
        return false;
    };
    let Ok(required_next_evidence) = serde_json::from_value::<Vec<String>>(
        value
            .get("required_next_evidence")
            .cloned()
            .unwrap_or(Value::Null),
    ) else {
        return false;
    };

    let unsigned = UnsignedTargetDataPreservationReceipt {
        schema,
        mode,
        target_stable_identity_sha256,
        rollback_contract_sha256,
        acknowledgement,
        backup_receipt_sha256,
        resolved,
        block_reasons: &block_reasons,
        required_next_evidence: &required_next_evidence,
        restore_unlock_ready,
        system_mutations_performed,
    };
    let bytes = match serde_json::to_vec(&unsigned) {
        Ok(bytes) => bytes,
        Err(_) => return false,
    };
    format!("{:x}", Sha256::digest(bytes)).eq_ignore_ascii_case(expected)
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
        backup_receipt_sha256: None,
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

pub fn build_target_data_preservation_receipt_with_backup(
    target_safety: &Value,
    rollback_contract: &Value,
    backup_receipt: &Value,
) -> Result<TargetDataPreservationReceipt, String> {
    let mut receipt = build_target_data_preservation_receipt(
        target_safety,
        rollback_contract,
        "preserve_existing_data",
        "",
    )?;
    if !verify_target_data_backup_receipt_sha256(backup_receipt) {
        return Err("target-data backup receipt checksum is invalid".to_string());
    }

    let backup_target = backup_receipt
        .get("target_stable_identity_sha256")
        .and_then(Value::as_str)
        .ok_or_else(|| "backup receipt target stable identity is missing".to_string())?;
    let backup_contract = backup_receipt
        .get("rollback_contract_sha256")
        .and_then(Value::as_str)
        .ok_or_else(|| "backup receipt rollback contract SHA-256 is missing".to_string())?;
    let backup_destination = backup_receipt
        .get("backup_destination_stable_identity_sha256")
        .and_then(Value::as_str)
        .ok_or_else(|| "backup destination stable identity is missing".to_string())?;
    let backup_manifest = backup_receipt
        .get("backup_manifest_sha256")
        .and_then(Value::as_str)
        .ok_or_else(|| "backup manifest SHA-256 is missing".to_string())?;
    let backup_receipt_sha = backup_receipt
        .get("receipt_sha256")
        .and_then(Value::as_str)
        .ok_or_else(|| "backup receipt SHA-256 is missing".to_string())?;

    if !valid_sha256(backup_target)
        || !valid_sha256(backup_contract)
        || !valid_sha256(backup_destination)
        || !valid_sha256(backup_manifest)
        || !valid_sha256(backup_receipt_sha)
    {
        return Err("backup evidence requires valid SHA-256 identities".to_string());
    }
    if !backup_target.eq_ignore_ascii_case(&receipt.target_stable_identity_sha256) {
        return Err("backup receipt target does not match the preservation target".to_string());
    }
    if !backup_contract.eq_ignore_ascii_case(&receipt.rollback_contract_sha256) {
        return Err("backup receipt rollback contract does not match".to_string());
    }
    if backup_destination.eq_ignore_ascii_case(&receipt.target_stable_identity_sha256) {
        return Err("backup destination must be a different physical device".to_string());
    }
    if backup_receipt.get("backup_verified").and_then(Value::as_bool) != Some(true)
        || backup_receipt.get("files_verified").and_then(Value::as_bool) != Some(true)
        || backup_receipt.get("target_bytes_written").and_then(Value::as_u64) != Some(0)
        || backup_receipt
            .get("target_write_attempted")
            .and_then(Value::as_bool)
            != Some(false)
        || backup_receipt
            .get("system_mutations_performed")
            .and_then(Value::as_bool)
            != Some(false)
    {
        return Err("backup receipt does not prove a verified read-only preservation chain".to_string());
    }

    receipt.backup_receipt_sha256 = Some(backup_receipt_sha.to_ascii_lowercase());
    receipt.resolved = true;
    receipt.block_reasons.clear();
    receipt.required_next_evidence.clear();
    receipt.receipt_sha256 = receipt_sha256(&receipt);
    Ok(receipt)
}

#[tauri::command]
pub fn load_verified_target_data_backup_receipt(
    backup_receipt_path: String,
) -> Result<Value, String> {
    let text = fs::read_to_string(&backup_receipt_path)
        .map_err(|error| format!("cannot read target-data backup receipt: {error}"))?;
    let receipt: Value = serde_json::from_str(&text)
        .map_err(|error| format!("invalid target-data backup receipt JSON: {error}"))?;
    if !verify_target_data_backup_receipt_sha256(&receipt) {
        return Err("target-data backup receipt checksum is invalid".to_string());
    }
    Ok(receipt)
}

#[tauri::command]
pub fn resolve_target_data_preservation_with_backup(
    target_safety_json: String,
    rollback_contract_json: String,
    backup_receipt_json: String,
) -> Result<TargetDataPreservationReceipt, String> {
    let target_safety: Value = serde_json::from_str(&target_safety_json)
        .map_err(|error| format!("invalid target-safety JSON: {error}"))?;
    let rollback_contract: Value = serde_json::from_str(&rollback_contract_json)
        .map_err(|error| format!("invalid rollback-contract JSON: {error}"))?;
    let backup_receipt: Value = serde_json::from_str(&backup_receipt_json)
        .map_err(|error| format!("invalid backup-receipt JSON: {error}"))?;
    build_target_data_preservation_receipt_with_backup(
        &target_safety,
        &rollback_contract,
        &backup_receipt,
    )
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
        build_target_data_preservation_receipt,
        build_target_data_preservation_receipt_with_backup,
        target_data_backup_receipt_sha256,
        verify_target_data_backup_receipt_sha256,
        verify_target_data_preservation_receipt_sha256,
        EXPLICIT_DISCARD_ACKNOWLEDGEMENT,
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

    fn backup_receipt() -> Value {
        let mut receipt = json!({
            "schema": "phoenix_key.target_data_backup_receipt.v1",
            "target_stable_identity_sha256": "c".repeat(64),
            "rollback_contract_sha256": contract()["contract_sha256"],
            "backup_destination_stable_identity_sha256": "d".repeat(64),
            "backup_manifest_sha256": "e".repeat(64),
            "backup_verified": true,
            "files_verified": true,
            "target_bytes_written": 0,
            "target_write_attempted": false,
            "system_mutations_performed": false
        });
        let digest = target_data_backup_receipt_sha256(&receipt).unwrap();
        receipt["receipt_sha256"] = json!(digest);
        receipt
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
    fn receipt_checksum_verifier_rejects_tampering() {
        let receipt = build_target_data_preservation_receipt(
            &target(),
            &contract(),
            "explicit_discard",
            EXPLICIT_DISCARD_ACKNOWLEDGEMENT,
        )
        .unwrap();
        let mut value = serde_json::to_value(receipt).unwrap();
        assert!(verify_target_data_preservation_receipt_sha256(&value));
        value["resolved"] = json!(false);
        assert!(!verify_target_data_preservation_receipt_sha256(&value));
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
    fn preserve_mode_resolves_with_verified_backup_receipt() {
        let backup = backup_receipt();
        assert!(verify_target_data_backup_receipt_sha256(&backup));
        let receipt = build_target_data_preservation_receipt_with_backup(
            &target(),
            &contract(),
            &backup,
        )
        .unwrap();
        assert!(receipt.resolved);
        assert!(receipt.block_reasons.is_empty());
        assert!(receipt.required_next_evidence.is_empty());
        assert_eq!(
            receipt.backup_receipt_sha256.as_deref(),
            backup.get("receipt_sha256").and_then(Value::as_str)
        );
        assert!(!receipt.restore_unlock_ready);
        assert!(!receipt.system_mutations_performed);
    }

    #[test]
    fn preserve_mode_rejects_backup_on_target_device() {
        let mut backup = backup_receipt();
        backup["backup_destination_stable_identity_sha256"] = json!("c".repeat(64));
        backup.as_object_mut().unwrap().remove("receipt_sha256");
        backup["receipt_sha256"] =
            json!(target_data_backup_receipt_sha256(&backup).unwrap());
        assert!(build_target_data_preservation_receipt_with_backup(
            &target(),
            &contract(),
            &backup,
        )
        .is_err());
    }

    #[test]
    fn preserve_mode_rejects_tampered_backup_receipt() {
        let mut backup = backup_receipt();
        backup["files_verified"] = json!(false);
        assert!(!verify_target_data_backup_receipt_sha256(&backup));
        assert!(build_target_data_preservation_receipt_with_backup(
            &target(),
            &contract(),
            &backup,
        )
        .is_err());
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
