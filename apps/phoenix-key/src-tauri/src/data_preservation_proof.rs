use serde::{Deserialize, Serialize};
use serde_json::Value;
use sha2::{Digest, Sha256};

fn valid_sha256(value: &str) -> bool {
    value.len() == 64 && value.bytes().all(|byte| byte.is_ascii_hexdigit())
}

fn sha256_json<T: Serialize>(value: &T) -> String {
    let bytes = serde_json::to_vec(value).expect("proof serialization cannot fail");
    format!("{:x}", Sha256::digest(bytes))
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct TargetDataBackupCoverageProof {
    pub schema: String,
    pub target_stable_identity_sha256: String,
    pub rollback_contract_sha256: String,
    pub backup_receipt_sha256: String,
    pub backup_manifest_sha256: String,
    pub source_inventory_sha256: String,
    pub manifest_inventory_sha256: String,
    pub source_entry_count: u64,
    pub manifest_entry_count: u64,
    pub source_bytes_total: u64,
    pub manifest_bytes_total: u64,
    pub complete_coverage: bool,
    pub omitted_entry_count: u64,
    pub comparison_performed: bool,
    pub inventory_capture_mode: String,
    pub target_write_attempted: bool,
    pub system_mutations_performed: bool,
    pub receipt_sha256: String,
}

#[derive(Debug, Serialize)]
struct UnsignedCoverageProof<'a> {
    schema: &'a str,
    target_stable_identity_sha256: &'a str,
    rollback_contract_sha256: &'a str,
    backup_receipt_sha256: &'a str,
    backup_manifest_sha256: &'a str,
    source_inventory_sha256: &'a str,
    manifest_inventory_sha256: &'a str,
    source_entry_count: u64,
    manifest_entry_count: u64,
    source_bytes_total: u64,
    manifest_bytes_total: u64,
    complete_coverage: bool,
    omitted_entry_count: u64,
    comparison_performed: bool,
    inventory_capture_mode: &'a str,
    target_write_attempted: bool,
    system_mutations_performed: bool,
}

pub fn target_data_backup_coverage_proof_sha256(
    proof: &TargetDataBackupCoverageProof,
) -> String {
    sha256_json(&UnsignedCoverageProof {
        schema: &proof.schema,
        target_stable_identity_sha256: &proof.target_stable_identity_sha256,
        rollback_contract_sha256: &proof.rollback_contract_sha256,
        backup_receipt_sha256: &proof.backup_receipt_sha256,
        backup_manifest_sha256: &proof.backup_manifest_sha256,
        source_inventory_sha256: &proof.source_inventory_sha256,
        manifest_inventory_sha256: &proof.manifest_inventory_sha256,
        source_entry_count: proof.source_entry_count,
        manifest_entry_count: proof.manifest_entry_count,
        source_bytes_total: proof.source_bytes_total,
        manifest_bytes_total: proof.manifest_bytes_total,
        complete_coverage: proof.complete_coverage,
        omitted_entry_count: proof.omitted_entry_count,
        comparison_performed: proof.comparison_performed,
        inventory_capture_mode: &proof.inventory_capture_mode,
        target_write_attempted: proof.target_write_attempted,
        system_mutations_performed: proof.system_mutations_performed,
    })
}

pub fn verify_target_data_backup_coverage_proof(
    value: &Value,
    expected_target_stable_identity_sha256: Option<&str>,
    expected_rollback_contract_sha256: Option<&str>,
    expected_backup_receipt_sha256: Option<&str>,
    expected_backup_manifest_sha256: Option<&str>,
) -> bool {
    let Ok(proof) = serde_json::from_value::<TargetDataBackupCoverageProof>(value.clone()) else {
        return false;
    };
    proof.schema == "phoenix_key.target_data_backup_coverage_proof.v1"
        && valid_sha256(&proof.target_stable_identity_sha256)
        && valid_sha256(&proof.rollback_contract_sha256)
        && valid_sha256(&proof.backup_receipt_sha256)
        && valid_sha256(&proof.backup_manifest_sha256)
        && valid_sha256(&proof.source_inventory_sha256)
        && valid_sha256(&proof.manifest_inventory_sha256)
        && valid_sha256(&proof.receipt_sha256)
        && target_data_backup_coverage_proof_sha256(&proof)
            .eq_ignore_ascii_case(&proof.receipt_sha256)
        && expected_target_stable_identity_sha256
            .is_some_and(|expected| expected.eq_ignore_ascii_case(&proof.target_stable_identity_sha256))
        && expected_rollback_contract_sha256
            .is_some_and(|expected| expected.eq_ignore_ascii_case(&proof.rollback_contract_sha256))
        && expected_backup_receipt_sha256
            .is_some_and(|expected| expected.eq_ignore_ascii_case(&proof.backup_receipt_sha256))
        && expected_backup_manifest_sha256
            .is_some_and(|expected| expected.eq_ignore_ascii_case(&proof.backup_manifest_sha256))
        && proof.complete_coverage
        && proof.comparison_performed
        && proof.omitted_entry_count == 0
        && proof.source_entry_count > 0
        && proof.source_entry_count == proof.manifest_entry_count
        && proof.source_bytes_total == proof.manifest_bytes_total
        && proof.source_inventory_sha256.eq_ignore_ascii_case(&proof.manifest_inventory_sha256)
        && proof.inventory_capture_mode == "fresh_pre_backup_source_inventory"
        && !proof.target_write_attempted
        && !proof.system_mutations_performed
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct BackupDestinationIdentityVerification {
    pub schema: String,
    pub target_stable_identity_sha256: String,
    pub expected_destination_stable_identity_sha256: String,
    pub observed_destination_stable_identity_sha256: String,
    pub identity_source: String,
    pub unique_match: bool,
    pub ambiguous: bool,
    pub matches_expected_destination: bool,
    pub separate_from_target: bool,
    pub system_mutations_performed: bool,
    pub receipt_sha256: String,
}

#[derive(Debug, Serialize)]
struct UnsignedDestinationIdentityVerification<'a> {
    schema: &'a str,
    target_stable_identity_sha256: &'a str,
    expected_destination_stable_identity_sha256: &'a str,
    observed_destination_stable_identity_sha256: &'a str,
    identity_source: &'a str,
    unique_match: bool,
    ambiguous: bool,
    matches_expected_destination: bool,
    separate_from_target: bool,
    system_mutations_performed: bool,
}

pub fn backup_destination_identity_verification_sha256(
    proof: &BackupDestinationIdentityVerification,
) -> String {
    sha256_json(&UnsignedDestinationIdentityVerification {
        schema: &proof.schema,
        target_stable_identity_sha256: &proof.target_stable_identity_sha256,
        expected_destination_stable_identity_sha256:
            &proof.expected_destination_stable_identity_sha256,
        observed_destination_stable_identity_sha256:
            &proof.observed_destination_stable_identity_sha256,
        identity_source: &proof.identity_source,
        unique_match: proof.unique_match,
        ambiguous: proof.ambiguous,
        matches_expected_destination: proof.matches_expected_destination,
        separate_from_target: proof.separate_from_target,
        system_mutations_performed: proof.system_mutations_performed,
    })
}

pub fn verify_backup_destination_identity_verification(
    value: &Value,
    expected_target_stable_identity_sha256: Option<&str>,
    expected_destination_stable_identity_sha256: Option<&str>,
) -> bool {
    let Ok(proof) =
        serde_json::from_value::<BackupDestinationIdentityVerification>(value.clone())
    else {
        return false;
    };
    proof.schema == "phoenix_key.backup_destination_identity_verification.v1"
        && valid_sha256(&proof.target_stable_identity_sha256)
        && valid_sha256(&proof.expected_destination_stable_identity_sha256)
        && valid_sha256(&proof.observed_destination_stable_identity_sha256)
        && valid_sha256(&proof.receipt_sha256)
        && backup_destination_identity_verification_sha256(&proof)
            .eq_ignore_ascii_case(&proof.receipt_sha256)
        && expected_target_stable_identity_sha256
            .is_some_and(|expected| expected.eq_ignore_ascii_case(&proof.target_stable_identity_sha256))
        && expected_destination_stable_identity_sha256.is_some_and(|expected| {
            expected.eq_ignore_ascii_case(&proof.expected_destination_stable_identity_sha256)
                && expected.eq_ignore_ascii_case(&proof.observed_destination_stable_identity_sha256)
        })
        && proof.identity_source == "fresh_hardware_scan"
        && proof.unique_match
        && !proof.ambiguous
        && proof.matches_expected_destination
        && proof.separate_from_target
        && !proof
            .target_stable_identity_sha256
            .eq_ignore_ascii_case(&proof.observed_destination_stable_identity_sha256)
        && !proof.system_mutations_performed
}

#[cfg(test)]
mod tests {
    use super::{
        backup_destination_identity_verification_sha256,
        target_data_backup_coverage_proof_sha256,
        verify_backup_destination_identity_verification,
        verify_target_data_backup_coverage_proof,
        BackupDestinationIdentityVerification, TargetDataBackupCoverageProof,
    };
    use serde_json::json;

    fn coverage() -> TargetDataBackupCoverageProof {
        let mut proof = TargetDataBackupCoverageProof {
            schema: "phoenix_key.target_data_backup_coverage_proof.v1".to_string(),
            target_stable_identity_sha256: "a".repeat(64),
            rollback_contract_sha256: "b".repeat(64),
            backup_receipt_sha256: "c".repeat(64),
            backup_manifest_sha256: "d".repeat(64),
            source_inventory_sha256: "e".repeat(64),
            manifest_inventory_sha256: "e".repeat(64),
            source_entry_count: 3,
            manifest_entry_count: 3,
            source_bytes_total: 8192,
            manifest_bytes_total: 8192,
            complete_coverage: true,
            omitted_entry_count: 0,
            comparison_performed: true,
            inventory_capture_mode: "fresh_pre_backup_source_inventory".to_string(),
            target_write_attempted: false,
            system_mutations_performed: false,
            receipt_sha256: String::new(),
        };
        proof.receipt_sha256 = target_data_backup_coverage_proof_sha256(&proof);
        proof
    }

    fn destination() -> BackupDestinationIdentityVerification {
        let mut proof = BackupDestinationIdentityVerification {
            schema: "phoenix_key.backup_destination_identity_verification.v1".to_string(),
            target_stable_identity_sha256: "a".repeat(64),
            expected_destination_stable_identity_sha256: "f".repeat(64),
            observed_destination_stable_identity_sha256: "f".repeat(64),
            identity_source: "fresh_hardware_scan".to_string(),
            unique_match: true,
            ambiguous: false,
            matches_expected_destination: true,
            separate_from_target: true,
            system_mutations_performed: false,
            receipt_sha256: String::new(),
        };
        proof.receipt_sha256 = backup_destination_identity_verification_sha256(&proof);
        proof
    }

    #[test]
    fn coverage_requires_exact_complete_inventory_match() {
        let proof = coverage();
        let value = serde_json::to_value(&proof).unwrap();
        assert!(verify_target_data_backup_coverage_proof(
            &value,
            Some(&"a".repeat(64)),
            Some(&"b".repeat(64)),
            Some(&"c".repeat(64)),
            Some(&"d".repeat(64)),
        ));

        let mut partial = value.clone();
        partial["omitted_entry_count"] = json!(1);
        assert!(!verify_target_data_backup_coverage_proof(
            &partial,
            Some(&"a".repeat(64)),
            Some(&"b".repeat(64)),
            Some(&"c".repeat(64)),
            Some(&"d".repeat(64)),
        ));
    }

    #[test]
    fn destination_requires_fresh_unique_hardware_identity_match() {
        let proof = destination();
        let value = serde_json::to_value(&proof).unwrap();
        assert!(verify_backup_destination_identity_verification(
            &value,
            Some(&"a".repeat(64)),
            Some(&"f".repeat(64)),
        ));

        let mut self_asserted = value.clone();
        self_asserted["identity_source"] = json!("backup_receipt");
        assert!(!verify_backup_destination_identity_verification(
            &self_asserted,
            Some(&"a".repeat(64)),
            Some(&"f".repeat(64)),
        ));
    }
}
