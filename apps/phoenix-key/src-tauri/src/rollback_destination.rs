use serde::Serialize;
use serde_json::{Map, Value};
use sha2::{Digest, Sha256};

#[derive(Debug, Clone, Serialize, PartialEq, Eq)]
pub struct RollbackDestinationVerification {
    pub schema: &'static str,
    pub target: Option<String>,
    pub target_snapshot_identity_sha256: Option<String>,
    pub target_stable_identity_sha256: Option<String>,
    pub expected_target_stable_identity_sha256: String,
    pub destination_path: String,
    pub destination_physical_target: Option<String>,
    pub destination_stable_identity_sha256: Option<String>,
    pub target_identity_matches_expected: bool,
    pub separate_physical_device: bool,
    pub ready_for_hardware_rollback_capture: bool,
    pub block_reasons: Vec<String>,
    pub system_mutations_performed: bool,
    pub receipt_sha256: String,
}

fn valid_sha256(value: &str) -> bool {
    value.len() == 64 && value.bytes().all(|byte| byte.is_ascii_hexdigit())
}

fn canonicalize_json(value: &Value) -> Value {
    match value {
        Value::Object(object) => {
            let mut keys: Vec<&String> = object.keys().collect();
            keys.sort();
            let mut canonical = Map::new();
            for key in keys {
                if key == "receipt_sha256" {
                    continue;
                }
                canonical.insert(key.clone(), canonicalize_json(&object[key]));
            }
            Value::Object(canonical)
        }
        Value::Array(items) => Value::Array(items.iter().map(canonicalize_json).collect()),
        _ => value.clone(),
    }
}

fn receipt_sha256(value: &Value) -> String {
    let bytes = serde_json::to_vec(&canonicalize_json(value))
        .expect("rollback destination receipt serialization cannot fail");
    format!("{:x}", Sha256::digest(bytes))
}

pub fn verify_rollback_destination_verification_sha256(value: &Value) -> bool {
    value.get("schema").and_then(Value::as_str)
        == Some("phoenix_key.rollback_destination_verification.v1")
        && value
            .get("receipt_sha256")
            .and_then(Value::as_str)
            .is_some_and(|expected| {
                valid_sha256(expected) && receipt_sha256(value).eq_ignore_ascii_case(expected)
            })
}

fn push_reason(reasons: &mut Vec<String>, reason: &str) {
    if !reasons.iter().any(|existing| existing == reason) {
        reasons.push(reason.to_string());
    }
}

pub fn assess_rollback_destination(
    target_evidence: &Value,
    destination_resolution: &Value,
    destination_path: &str,
    expected_target_stable_identity_sha256: &str,
) -> RollbackDestinationVerification {
    let disk = target_evidence.get("disk").unwrap_or(&Value::Null);
    let target = disk
        .get("target")
        .and_then(Value::as_str)
        .map(str::to_string);
    let target_snapshot_identity = disk
        .get("identity_sha256")
        .and_then(Value::as_str)
        .map(str::to_string);
    let target_stable_identity = disk
        .get("stable_identity_sha256")
        .and_then(Value::as_str)
        .map(str::to_string);
    let destination_physical_target = destination_resolution
        .pointer("/source/physical_target")
        .and_then(Value::as_str)
        .map(str::to_string);
    let destination_stable_identity = destination_resolution
        .pointer("/source/stable_identity_sha256")
        .and_then(Value::as_str)
        .map(str::to_string);
    let expected = expected_target_stable_identity_sha256
        .trim()
        .to_ascii_lowercase();

    let mut block_reasons = Vec::new();

    if !valid_sha256(&expected) {
        push_reason(
            &mut block_reasons,
            "expected-target-stable-identity-missing-or-invalid",
        );
    }
    if !target_snapshot_identity
        .as_deref()
        .is_some_and(valid_sha256)
    {
        push_reason(
            &mut block_reasons,
            "target-snapshot-identity-missing-or-invalid",
        );
    }
    if !target_stable_identity
        .as_deref()
        .is_some_and(valid_sha256)
    {
        push_reason(
            &mut block_reasons,
            "target-stable-identity-missing-or-invalid",
        );
    }
    if !destination_stable_identity
        .as_deref()
        .is_some_and(valid_sha256)
    {
        push_reason(
            &mut block_reasons,
            "rollback-destination-stable-identity-missing-or-invalid",
        );
    }
    if destination_physical_target
        .as_deref()
        .is_none_or(|value| value.trim().is_empty())
    {
        push_reason(
            &mut block_reasons,
            "rollback-destination-physical-device-unproven",
        );
    }

    let target_identity_matches_expected = target_stable_identity
        .as_deref()
        .is_some_and(|observed| {
            valid_sha256(observed)
                && valid_sha256(&expected)
                && observed.eq_ignore_ascii_case(&expected)
        });
    if !target_identity_matches_expected {
        push_reason(
            &mut block_reasons,
            "restore-target-stable-identity-changed",
        );
    }

    let separate_physical_device = match (
        target_stable_identity.as_deref(),
        destination_stable_identity.as_deref(),
    ) {
        (Some(target_identity), Some(destination_identity))
            if valid_sha256(target_identity) && valid_sha256(destination_identity) =>
        {
            !target_identity.eq_ignore_ascii_case(destination_identity)
        }
        _ => false,
    };
    if !separate_physical_device {
        push_reason(
            &mut block_reasons,
            "rollback-destination-is-restore-target-device",
        );
    }

    if destination_path.trim().is_empty() {
        push_reason(&mut block_reasons, "rollback-destination-path-missing");
    }

    let mut receipt = RollbackDestinationVerification {
        schema: "phoenix_key.rollback_destination_verification.v1",
        target,
        target_snapshot_identity_sha256: target_snapshot_identity,
        target_stable_identity_sha256: target_stable_identity,
        expected_target_stable_identity_sha256: expected,
        destination_path: destination_path.trim().to_string(),
        destination_physical_target,
        destination_stable_identity_sha256: destination_stable_identity,
        target_identity_matches_expected,
        separate_physical_device,
        ready_for_hardware_rollback_capture: block_reasons.is_empty(),
        block_reasons,
        system_mutations_performed: false,
        receipt_sha256: String::new(),
    };
    receipt.receipt_sha256 = receipt_sha256(
        &serde_json::to_value(&receipt)
            .expect("rollback destination receipt serialization cannot fail"),
    );
    receipt
}

#[cfg(test)]
mod tests {
    use super::{
        assess_rollback_destination, verify_rollback_destination_verification_sha256,
    };
    use serde_json::json;

    fn target() -> serde_json::Value {
        json!({
            "disk": {
                "target": "\\\\.\\PHYSICALDRIVE7",
                "identity_sha256": "a".repeat(64),
                "stable_identity_sha256": "b".repeat(64)
            }
        })
    }

    fn destination() -> serde_json::Value {
        json!({
            "source": {
                "physical_target": "\\\\.\\PHYSICALDRIVE9",
                "stable_identity_sha256": "c".repeat(64)
            }
        })
    }

    #[test]
    fn destination_receipt_checksum_detects_tampering() {
        let result = assess_rollback_destination(
            &target(),
            &destination(),
            "E:/PhoenixKeyRollback",
            &"b".repeat(64),
        );
        let mut value = serde_json::to_value(result).unwrap();
        assert!(verify_rollback_destination_verification_sha256(&value));
        value["separate_physical_device"] = json!(false);
        assert!(!verify_rollback_destination_verification_sha256(&value));
    }

    #[test]
    fn distinct_destination_device_can_reach_capture_boundary() {
        let result = assess_rollback_destination(
            &target(),
            &destination(),
            "E:/PhoenixKeyRollback",
            &"b".repeat(64),
        );
        assert!(result.target_identity_matches_expected);
        assert!(result.separate_physical_device);
        assert!(result.ready_for_hardware_rollback_capture);
        assert!(result.block_reasons.is_empty());
        assert!(!result.system_mutations_performed);
    }

    #[test]
    fn same_physical_device_is_blocked_even_under_another_path() {
        let mut destination = destination();
        destination["source"]["stable_identity_sha256"] = json!("b".repeat(64));
        let result = assess_rollback_destination(
            &target(),
            &destination,
            "F:/Rollback",
            &"b".repeat(64),
        );
        assert!(!result.separate_physical_device);
        assert!(!result.ready_for_hardware_rollback_capture);
        assert!(result
            .block_reasons
            .contains(&"rollback-destination-is-restore-target-device".to_string()));
    }

    #[test]
    fn changed_target_hardware_invalidates_destination_verification() {
        let result = assess_rollback_destination(
            &target(),
            &destination(),
            "E:/PhoenixKeyRollback",
            &"d".repeat(64),
        );
        assert!(!result.target_identity_matches_expected);
        assert!(!result.ready_for_hardware_rollback_capture);
        assert!(result
            .block_reasons
            .contains(&"restore-target-stable-identity-changed".to_string()));
    }

    #[test]
    fn missing_destination_identity_is_blocked() {
        let destination = json!({
            "source": {
                "physical_target": "\\\\.\\PHYSICALDRIVE9",
                "stable_identity_sha256": null
            }
        });
        let result = assess_rollback_destination(
            &target(),
            &destination,
            "E:/PhoenixKeyRollback",
            &"b".repeat(64),
        );
        assert!(!result.ready_for_hardware_rollback_capture);
        assert!(result
            .block_reasons
            .contains(&"rollback-destination-stable-identity-missing-or-invalid".to_string()));
    }
}
