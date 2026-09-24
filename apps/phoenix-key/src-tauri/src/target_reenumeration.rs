use serde::{Deserialize, Serialize};
use serde_json::Value;
use sha2::{Digest, Sha256};

#[derive(Debug, Clone, Deserialize, Serialize, PartialEq, Eq)]
pub struct RecoveryTargetReenumerationReceipt {
    pub schema: String,
    pub expected_target: Option<String>,
    pub observed_target: Option<String>,
    pub expected_snapshot_identity_sha256: String,
    pub observed_snapshot_identity_sha256: Option<String>,
    pub expected_stable_identity_sha256: String,
    pub observed_stable_identity_sha256: Option<String>,
    pub same_stable_hardware: bool,
    pub snapshot_changed: bool,
    pub target_path_changed: bool,
    pub stale_authorization_rejected: bool,
    pub reanalysis_required: bool,
    pub substitution_detected: bool,
    pub classification: String,
    pub system_mutations_performed: bool,
    pub receipt_sha256: String,
}

#[derive(Debug, Serialize)]
struct UnsignedRecoveryTargetReenumerationReceipt<'a> {
    schema: &'a str,
    expected_target: &'a Option<String>,
    observed_target: &'a Option<String>,
    expected_snapshot_identity_sha256: &'a str,
    observed_snapshot_identity_sha256: &'a Option<String>,
    expected_stable_identity_sha256: &'a str,
    observed_stable_identity_sha256: &'a Option<String>,
    same_stable_hardware: bool,
    snapshot_changed: bool,
    target_path_changed: bool,
    stale_authorization_rejected: bool,
    reanalysis_required: bool,
    substitution_detected: bool,
    classification: &'a str,
    system_mutations_performed: bool,
}

fn is_sha256(value: &str) -> bool {
    value.len() == 64 && value.bytes().all(|byte| byte.is_ascii_hexdigit())
}

fn sha256_hex<T: Serialize>(value: &T) -> String {
    let bytes = serde_json::to_vec(value).expect("reenumeration receipt serialization cannot fail");
    format!("{:x}", Sha256::digest(bytes))
}

fn unsigned_receipt(
    receipt: &RecoveryTargetReenumerationReceipt,
) -> UnsignedRecoveryTargetReenumerationReceipt<'_> {
    UnsignedRecoveryTargetReenumerationReceipt {
        schema: &receipt.schema,
        expected_target: &receipt.expected_target,
        observed_target: &receipt.observed_target,
        expected_snapshot_identity_sha256: &receipt.expected_snapshot_identity_sha256,
        observed_snapshot_identity_sha256: &receipt.observed_snapshot_identity_sha256,
        expected_stable_identity_sha256: &receipt.expected_stable_identity_sha256,
        observed_stable_identity_sha256: &receipt.observed_stable_identity_sha256,
        same_stable_hardware: receipt.same_stable_hardware,
        snapshot_changed: receipt.snapshot_changed,
        target_path_changed: receipt.target_path_changed,
        stale_authorization_rejected: receipt.stale_authorization_rejected,
        reanalysis_required: receipt.reanalysis_required,
        substitution_detected: receipt.substitution_detected,
        classification: &receipt.classification,
        system_mutations_performed: receipt.system_mutations_performed,
    }
}

pub fn verify_recovery_target_reenumeration_receipt_sha256(
    receipt: &RecoveryTargetReenumerationReceipt,
) -> bool {
    is_sha256(&receipt.receipt_sha256)
        && sha256_hex(&unsigned_receipt(receipt)).eq_ignore_ascii_case(&receipt.receipt_sha256)
}

pub fn compare_recovery_target_reenumeration(
    evidence: &Value,
    expected_target: Option<&str>,
    expected_snapshot_identity_sha256: &str,
    expected_stable_identity_sha256: &str,
) -> RecoveryTargetReenumerationReceipt {
    let disk = evidence.get("disk").unwrap_or(&Value::Null);
    let observed_target = disk
        .get("target")
        .and_then(Value::as_str)
        .map(str::to_string);
    let observed_snapshot = disk
        .get("identity_sha256")
        .and_then(Value::as_str)
        .map(str::to_string);
    let observed_stable = disk
        .get("stable_identity_sha256")
        .and_then(Value::as_str)
        .map(str::to_string);

    let expected_target = expected_target
        .map(str::trim)
        .filter(|value| !value.is_empty())
        .map(str::to_string);
    let expected_snapshot = expected_snapshot_identity_sha256
        .trim()
        .to_ascii_lowercase();
    let expected_stable = expected_stable_identity_sha256
        .trim()
        .to_ascii_lowercase();

    let expectations_valid = is_sha256(&expected_snapshot) && is_sha256(&expected_stable);
    let observed_snapshot_valid = observed_snapshot.as_deref().is_some_and(is_sha256);
    let observed_stable_valid = observed_stable.as_deref().is_some_and(is_sha256);

    let same_stable_hardware = expectations_valid
        && observed_stable.as_deref().is_some_and(|value| {
            is_sha256(value) && value.eq_ignore_ascii_case(&expected_stable)
        });
    let snapshot_changed = expectations_valid
        && observed_snapshot_valid
        && observed_snapshot
            .as_deref()
            .is_some_and(|value| !value.eq_ignore_ascii_case(&expected_snapshot));
    let target_path_changed = expected_target
        .as_deref()
        .zip(observed_target.as_deref())
        .is_some_and(|(expected, observed)| !expected.eq_ignore_ascii_case(observed));

    let substitution_detected =
        expectations_valid && observed_stable_valid && !same_stable_hardware;
    let stale_authorization_rejected =
        same_stable_hardware && (snapshot_changed || target_path_changed);
    let reanalysis_required = !expectations_valid
        || !observed_snapshot_valid
        || !observed_stable_valid
        || snapshot_changed
        || target_path_changed
        || substitution_detected;

    let classification = if !expectations_valid {
        "invalid_expectation"
    } else if !observed_snapshot_valid || !observed_stable_valid {
        "observed_identity_unproven"
    } else if substitution_detected {
        "hardware_substitution_detected"
    } else if stale_authorization_rejected {
        "same_hardware_reenumerated"
    } else {
        "exact_snapshot_match"
    };

    let mut receipt = RecoveryTargetReenumerationReceipt {
        schema: "phoenix_key.recovery_target_reenumeration_receipt.v1".to_string(),
        expected_target,
        observed_target,
        expected_snapshot_identity_sha256: expected_snapshot,
        observed_snapshot_identity_sha256: observed_snapshot,
        expected_stable_identity_sha256: expected_stable,
        observed_stable_identity_sha256: observed_stable,
        same_stable_hardware,
        snapshot_changed,
        target_path_changed,
        stale_authorization_rejected,
        reanalysis_required,
        substitution_detected,
        classification: classification.to_string(),
        system_mutations_performed: false,
        receipt_sha256: String::new(),
    };

    receipt.receipt_sha256 = sha256_hex(&unsigned_receipt(&receipt));
    receipt
}

#[cfg(test)]
mod tests {
    use super::{
        compare_recovery_target_reenumeration,
        verify_recovery_target_reenumeration_receipt_sha256,
    };
    use serde_json::json;

    fn evidence(target: &str, snapshot: &str, stable: &str) -> serde_json::Value {
        json!({
            "disk": {
                "target": target,
                "identity_sha256": snapshot,
                "stable_identity_sha256": stable
            }
        })
    }

    #[test]
    fn exact_snapshot_match_requires_no_reanalysis() {
        let receipt = compare_recovery_target_reenumeration(
            &evidence(
                "\\\\.\\PHYSICALDRIVE7",
                &"a".repeat(64),
                &"b".repeat(64),
            ),
            Some("\\\\.\\PHYSICALDRIVE7"),
            &"a".repeat(64),
            &"b".repeat(64),
        );
        assert!(receipt.same_stable_hardware);
        assert!(!receipt.snapshot_changed);
        assert!(!receipt.target_path_changed);
        assert!(!receipt.stale_authorization_rejected);
        assert!(!receipt.reanalysis_required);
        assert!(!receipt.substitution_detected);
        assert_eq!(receipt.classification, "exact_snapshot_match");
        assert_eq!(receipt.receipt_sha256.len(), 64);
        assert!(verify_recovery_target_reenumeration_receipt_sha256(&receipt));
    }

    #[test]
    fn tampered_receipt_checksum_is_rejected() {
        let mut receipt = compare_recovery_target_reenumeration(
            &evidence(
                "\\\\.\\PHYSICALDRIVE7",
                &"a".repeat(64),
                &"b".repeat(64),
            ),
            Some("\\\\.\\PHYSICALDRIVE7"),
            &"a".repeat(64),
            &"b".repeat(64),
        );
        receipt.observed_target = Some("\\\\.\\PHYSICALDRIVE8".to_string());
        assert!(!verify_recovery_target_reenumeration_receipt_sha256(&receipt));
    }

    #[test]
    fn same_hardware_after_disk_renumbering_rejects_stale_authorization() {
        let receipt = compare_recovery_target_reenumeration(
            &evidence(
                "\\\\.\\PHYSICALDRIVE9",
                &"c".repeat(64),
                &"b".repeat(64),
            ),
            Some("\\\\.\\PHYSICALDRIVE7"),
            &"a".repeat(64),
            &"b".repeat(64),
        );
        assert!(receipt.same_stable_hardware);
        assert!(receipt.snapshot_changed);
        assert!(receipt.target_path_changed);
        assert!(receipt.stale_authorization_rejected);
        assert!(receipt.reanalysis_required);
        assert!(!receipt.substitution_detected);
        assert_eq!(receipt.classification, "same_hardware_reenumerated");
    }

    #[test]
    fn different_stable_hardware_is_substitution() {
        let receipt = compare_recovery_target_reenumeration(
            &evidence(
                "\\\\.\\PHYSICALDRIVE7",
                &"a".repeat(64),
                &"d".repeat(64),
            ),
            Some("\\\\.\\PHYSICALDRIVE7"),
            &"a".repeat(64),
            &"b".repeat(64),
        );
        assert!(!receipt.same_stable_hardware);
        assert!(receipt.substitution_detected);
        assert!(receipt.reanalysis_required);
        assert_eq!(receipt.classification, "hardware_substitution_detected");
    }

    #[test]
    fn missing_stable_identity_is_unproven_not_same_hardware() {
        let evidence = json!({
            "disk": {
                "target": "\\\\.\\PHYSICALDRIVE7",
                "identity_sha256": "a".repeat(64),
                "stable_identity_sha256": null
            }
        });
        let receipt = compare_recovery_target_reenumeration(
            &evidence,
            Some("\\\\.\\PHYSICALDRIVE7"),
            &"a".repeat(64),
            &"b".repeat(64),
        );
        assert!(!receipt.same_stable_hardware);
        assert!(!receipt.substitution_detected);
        assert!(receipt.reanalysis_required);
        assert_eq!(receipt.classification, "observed_identity_unproven");
    }
}
