use serde::Serialize;
use serde_json::Value;

#[derive(Debug, Clone, Serialize, PartialEq, Eq)]
pub struct RecoveryTargetIdentityVerification {
    pub schema: &'static str,
    pub expected_snapshot_identity_sha256: String,
    pub observed_snapshot_identity_sha256: Option<String>,
    pub expected_stable_identity_sha256: String,
    pub observed_stable_identity_sha256: Option<String>,
    pub snapshot_matches: bool,
    pub stable_identity_matches: bool,
    pub matches: bool,
    pub classification: &'static str,
    pub reanalysis_required: bool,
    pub system_mutations_performed: bool,
}

#[derive(Debug, Clone, Serialize, PartialEq, Eq)]
pub struct RecoveryTargetSafety {
    pub schema: &'static str,
    pub safe_to_prepare: bool,
    pub target: Option<String>,
    pub target_identity_sha256: Option<String>,
    pub target_stable_identity_sha256: Option<String>,
    pub target_size_bytes: Option<u64>,
    pub source_size_bytes: u64,
    pub source_physical_target: Option<String>,
    pub source_physical_identity_sha256: Option<String>,
    pub source_target_distinct: Option<bool>,
    pub block_reasons: Vec<String>,
}

fn is_sha256(value: &str) -> bool {
    value.len() == 64 && value.bytes().all(|byte| byte.is_ascii_hexdigit())
}

pub fn verify_recovery_target_identity(
    evidence: &Value,
    expected_snapshot_identity_sha256: &str,
    expected_stable_identity_sha256: &str,
) -> RecoveryTargetIdentityVerification {
    let disk = evidence.get("disk").unwrap_or(&Value::Null);
    let observed_snapshot = disk
        .get("identity_sha256")
        .and_then(Value::as_str)
        .map(str::to_string);
    let observed_stable = disk
        .get("stable_identity_sha256")
        .and_then(Value::as_str)
        .map(str::to_string);

    let expected_snapshot = expected_snapshot_identity_sha256.trim().to_ascii_lowercase();
    let expected_stable = expected_stable_identity_sha256.trim().to_ascii_lowercase();

    let snapshot_matches = is_sha256(&expected_snapshot)
        && observed_snapshot.as_deref().is_some_and(|value| {
            is_sha256(value) && value.eq_ignore_ascii_case(&expected_snapshot)
        });
    let stable_identity_matches = is_sha256(&expected_stable)
        && observed_stable.as_deref().is_some_and(|value| {
            is_sha256(value) && value.eq_ignore_ascii_case(&expected_stable)
        });
    let matches = snapshot_matches && stable_identity_matches;
    let expectations_valid = is_sha256(&expected_snapshot) && is_sha256(&expected_stable);
    let classification = if !expectations_valid {
        "invalid_expectation"
    } else if matches {
        "exact_match"
    } else if stable_identity_matches {
        "same_hardware_reenumerated"
    } else {
        "hardware_substitution_or_unproven"
    };

    RecoveryTargetIdentityVerification {
        schema: "phoenix_key.recovery_target_identity_verification.v1",
        expected_snapshot_identity_sha256: expected_snapshot,
        observed_snapshot_identity_sha256: observed_snapshot,
        expected_stable_identity_sha256: expected_stable,
        observed_stable_identity_sha256: observed_stable,
        snapshot_matches,
        stable_identity_matches,
        matches,
        classification,
        reanalysis_required: !matches,
        system_mutations_performed: false,
    }
}

fn push_reason(reasons: &mut Vec<String>, reason: &str) {
    if !reasons.iter().any(|existing| existing == reason) {
        reasons.push(reason.to_string());
    }
}

pub fn assess_recovery_target(
    evidence: &Value,
    source_size_bytes: u64,
    source_physical_target: Option<&str>,
    source_physical_identity_sha256: Option<&str>,
) -> RecoveryTargetSafety {
    let disk = evidence.get("disk").unwrap_or(&Value::Null);
    let target = disk.get("target").and_then(Value::as_str).map(str::to_string);
    let identity = disk
        .get("identity_sha256")
        .and_then(Value::as_str)
        .map(str::to_string);
    let stable_identity = disk
        .get("stable_identity_sha256")
        .and_then(Value::as_str)
        .map(str::to_string);
    let source_stable_identity = source_physical_identity_sha256.map(str::to_string);
    let target_size = disk.get("size_bytes").and_then(Value::as_u64);
    let mut block_reasons = Vec::new();

    if disk.get("write_candidate").and_then(Value::as_bool) != Some(true) {
        if let Some(reasons) = disk.get("write_block_reasons").and_then(Value::as_array) {
            for reason in reasons.iter().filter_map(Value::as_str) {
                push_reason(&mut block_reasons, reason);
            }
        }
        if block_reasons.is_empty() {
            push_reason(&mut block_reasons, "target-not-proven-safe-write-candidate");
        }
    }

    if disk.get("is_boot").and_then(Value::as_bool) == Some(true) {
        push_reason(&mut block_reasons, "target-is-boot-disk");
    }
    if disk.get("is_system").and_then(Value::as_bool) == Some(true) {
        push_reason(&mut block_reasons, "target-is-system-disk");
    }

    match identity.as_deref() {
        Some(value) if value.len() == 64 && value.bytes().all(|byte| byte.is_ascii_hexdigit()) => {}
        _ => push_reason(&mut block_reasons, "target-snapshot-identity-missing-or-invalid"),
    }

    match stable_identity.as_deref() {
        Some(value) if value.len() == 64 && value.bytes().all(|byte| byte.is_ascii_hexdigit()) => {}
        _ => push_reason(&mut block_reasons, "stable-target-identity-missing-or-invalid"),
    }

    match source_stable_identity.as_deref() {
        Some(value) if value.len() == 64 && value.bytes().all(|byte| byte.is_ascii_hexdigit()) => {}
        _ => push_reason(&mut block_reasons, "stable-source-identity-missing-or-invalid"),
    }

    match target_size {
        Some(size) if size >= source_size_bytes && source_size_bytes > 0 => {}
        Some(_) => push_reason(&mut block_reasons, "target-capacity-smaller-than-source"),
        None => push_reason(&mut block_reasons, "target-capacity-missing"),
    }

    let source_target_distinct = match (source_physical_target, target.as_deref()) {
        (Some(source), Some(target)) => {
            let path_distinct = !source.eq_ignore_ascii_case(target);
            let stable_identity_distinct = match (
                source_stable_identity.as_deref(),
                stable_identity.as_deref(),
            ) {
                (Some(source_identity), Some(target_identity))
                    if source_identity.len() == 64
                        && target_identity.len() == 64
                        && source_identity.bytes().all(|byte| byte.is_ascii_hexdigit())
                        && target_identity.bytes().all(|byte| byte.is_ascii_hexdigit()) =>
                {
                    !source_identity.eq_ignore_ascii_case(target_identity)
                }
                _ => false,
            };
            let distinct = path_distinct && stable_identity_distinct;
            if !distinct {
                push_reason(&mut block_reasons, "source-and-target-same-physical-device");
            }
            Some(distinct)
        }
        (Some(_), None) => {
            push_reason(&mut block_reasons, "target-path-missing");
            None
        }
        (None, _) => {
            push_reason(&mut block_reasons, "source-physical-device-not-proven");
            None
        }
    };

    RecoveryTargetSafety {
        schema: "phoenix_key.recovery_target_safety.v1",
        safe_to_prepare: block_reasons.is_empty(),
        target,
        target_identity_sha256: identity,
        target_stable_identity_sha256: stable_identity,
        target_size_bytes: target_size,
        source_size_bytes,
        source_physical_target: source_physical_target.map(str::to_string),
        source_physical_identity_sha256: source_stable_identity,
        source_target_distinct,
        block_reasons,
    }
}



#[cfg(test)]
mod tests {
    use super::{assess_recovery_target, verify_recovery_target_identity};
    use serde_json::{json, Value};

    fn safe_evidence() -> Value {
        json!({
            "disk": {
                "target": "\\\\.\\PHYSICALDRIVE7",
                "identity_sha256": "a".repeat(64),
                "stable_identity_sha256": "b".repeat(64),
                "size_bytes": 64_000u64,
                "is_boot": false,
                "is_system": false,
                "write_candidate": true,
                "write_block_reasons": []
            }
        })
    }

    #[test]
    fn target_identity_verification_requires_snapshot_and_stable_match() {
        let evidence = safe_evidence();
        let result = verify_recovery_target_identity(
            &evidence,
            &"a".repeat(64),
            &"b".repeat(64),
        );
        assert!(result.matches);
        assert_eq!(result.classification, "exact_match");
        assert!(!result.reanalysis_required);
        assert!(!result.system_mutations_performed);
    }

    #[test]
    fn target_identity_verification_rejects_reenumerated_snapshot() {
        let evidence = safe_evidence();
        let result = verify_recovery_target_identity(
            &evidence,
            &"c".repeat(64),
            &"b".repeat(64),
        );
        assert!(!result.matches);
        assert!(!result.snapshot_matches);
        assert!(result.stable_identity_matches);
        assert_eq!(result.classification, "same_hardware_reenumerated");
        assert!(result.reanalysis_required);
    }

    #[test]
    fn target_identity_verification_rejects_stable_hardware_mismatch() {
        let evidence = safe_evidence();
        let result = verify_recovery_target_identity(
            &evidence,
            &"a".repeat(64),
            &"c".repeat(64),
        );
        assert!(!result.matches);
        assert!(result.snapshot_matches);
        assert!(!result.stable_identity_matches);
        assert_eq!(
            result.classification,
            "hardware_substitution_or_unproven"
        );
        assert!(result.reanalysis_required);
    }

    #[test]
    fn invalid_expected_identity_is_classified_and_blocked() {
        let evidence = safe_evidence();
        let result =
            verify_recovery_target_identity(&evidence, "bad", &"b".repeat(64));
        assert!(!result.matches);
        assert_eq!(result.classification, "invalid_expectation");
        assert!(result.reanalysis_required);
    }

    #[test]
    fn allows_distinct_sized_external_candidate_contract() {
        let result = assess_recovery_target(
            &safe_evidence(),
            32_000,
            Some("\\\\.\\PHYSICALDRIVE8"),
            Some(&"c".repeat(64)),
        );
        assert!(result.safe_to_prepare);
        assert_eq!(result.source_target_distinct, Some(true));
    }

    #[test]
    fn blocks_source_target_collision() {
        let result = assess_recovery_target(
            &safe_evidence(),
            32_000,
            Some("\\\\.\\physicaldrive7"),
            Some(&"c".repeat(64)),
        );
        assert!(!result.safe_to_prepare);
        assert!(result
            .block_reasons
            .contains(&"source-and-target-same-physical-device".to_string()));
    }

    #[test]
    fn stable_identity_collision_blocks_reenumerated_same_device() {
        let result = assess_recovery_target(
            &safe_evidence(),
            32_000,
            Some("\\\\.\\PHYSICALDRIVE9"),
            Some(&"b".repeat(64)),
        );
        assert!(!result.safe_to_prepare);
        assert_eq!(result.source_target_distinct, Some(false));
        assert!(result
            .block_reasons
            .contains(&"source-and-target-same-physical-device".to_string()));
    }

    #[test]
    fn blocks_insufficient_capacity() {
        let result = assess_recovery_target(
            &safe_evidence(),
            128_000,
            Some("\\\\.\\PHYSICALDRIVE8"),
            Some(&"c".repeat(64)),
        );
        assert!(!result.safe_to_prepare);
        assert!(result
            .block_reasons
            .contains(&"target-capacity-smaller-than-source".to_string()));
    }

    #[test]
    fn blocks_unproven_source_device() {
        let result = assess_recovery_target(
            &safe_evidence(),
            32_000,
            None,
            Some(&"c".repeat(64)),
        );
        assert!(!result.safe_to_prepare);
        assert!(result
            .block_reasons
            .contains(&"source-physical-device-not-proven".to_string()));
    }

    #[test]
    fn preserves_existing_system_disk_block() {
        let evidence = json!({
            "disk": {
                "target": "\\\\.\\PHYSICALDRIVE0",
                "identity_sha256": "b".repeat(64),
                "size_bytes": 64_000u64,
                "is_boot": true,
                "is_system": true,
                "write_candidate": false,
                "write_block_reasons": ["target-is-system-disk", "target-is-boot-disk"]
            }
        });
        let result = assess_recovery_target(
            &evidence,
            32_000,
            Some("\\\\.\\PHYSICALDRIVE8"),
            Some(&"c".repeat(64)),
        );
        assert!(!result.safe_to_prepare);
        assert!(result.block_reasons.contains(&"target-is-system-disk".to_string()));
        assert!(result.block_reasons.contains(&"target-is-boot-disk".to_string()));
    }
}
