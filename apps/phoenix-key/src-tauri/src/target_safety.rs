use serde::Serialize;
use serde_json::Value;

#[derive(Debug, Clone, Serialize, PartialEq, Eq)]
pub struct RecoveryTargetSafety {
    pub schema: &'static str,
    pub safe_to_prepare: bool,
    pub target: Option<String>,
    pub target_identity_sha256: Option<String>,
    pub target_size_bytes: Option<u64>,
    pub source_size_bytes: u64,
    pub source_physical_target: Option<String>,
    pub source_target_distinct: Option<bool>,
    pub block_reasons: Vec<String>,
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
) -> RecoveryTargetSafety {
    let disk = evidence.get("disk").unwrap_or(&Value::Null);
    let target = disk.get("target").and_then(Value::as_str).map(str::to_string);
    let identity = disk
        .get("identity_sha256")
        .and_then(Value::as_str)
        .map(str::to_string);
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
        _ => push_reason(&mut block_reasons, "stable-target-identity-missing-or-invalid"),
    }

    match target_size {
        Some(size) if size >= source_size_bytes && source_size_bytes > 0 => {}
        Some(_) => push_reason(&mut block_reasons, "target-capacity-smaller-than-source"),
        None => push_reason(&mut block_reasons, "target-capacity-missing"),
    }

    let source_target_distinct = match (source_physical_target, target.as_deref()) {
        (Some(source), Some(target)) => {
            let distinct = !source.eq_ignore_ascii_case(target);
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
        target_size_bytes: target_size,
        source_size_bytes,
        source_physical_target: source_physical_target.map(str::to_string),
        source_target_distinct,
        block_reasons,
    }
}

#[cfg(test)]
mod tests {
    use super::assess_recovery_target;
    use serde_json::json;

    fn safe_evidence() -> Value {
        json!({
            "disk": {
                "target": "\\\\.\\PHYSICALDRIVE7",
                "identity_sha256": "a".repeat(64),
                "size_bytes": 64_000u64,
                "is_boot": false,
                "is_system": false,
                "write_candidate": true,
                "write_block_reasons": []
            }
        })
    }

    #[test]
    fn allows_distinct_sized_external_candidate_contract() {
        let result = assess_recovery_target(
            &safe_evidence(),
            32_000,
            Some("\\\\.\\PHYSICALDRIVE8"),
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
        );
        assert!(!result.safe_to_prepare);
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
        );
        assert!(!result.safe_to_prepare);
        assert!(result
            .block_reasons
            .contains(&"target-capacity-smaller-than-source".to_string()));
    }

    #[test]
    fn blocks_unproven_source_device() {
        let result = assess_recovery_target(&safe_evidence(), 32_000, None);
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
        );
        assert!(!result.safe_to_prepare);
        assert!(result.block_reasons.contains(&"target-is-system-disk".to_string()));
        assert!(result.block_reasons.contains(&"target-is-boot-disk".to_string()));
    }
}
