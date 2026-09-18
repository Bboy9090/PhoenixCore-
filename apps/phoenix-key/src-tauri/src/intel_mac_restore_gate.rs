use serde::Serialize;
use serde_json::Value;

#[derive(Debug, Clone, Serialize, PartialEq, Eq)]
pub struct IntelMacRestoreGate {
    pub schema: &'static str,
    pub ready_for_intel_mac_restore_executor_design: bool,
    pub executable: bool,
    pub mac_model_identifier: Option<String>,
    pub driver_manifest_sha256: Option<String>,
    pub satisfied_gates: Vec<String>,
    pub blocked_gates: Vec<String>,
    pub system_mutations_performed: bool,
}

fn is_sha256(value: Option<&str>) -> bool {
    value.is_some_and(|value| {
        value.len() == 64 && value.bytes().all(|byte| byte.is_ascii_hexdigit())
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

pub fn assess_intel_mac_restore_gate(
    restore_readiness: &Value,
    mac_compatibility: &Value,
    driver_package: &Value,
) -> IntelMacRestoreGate {
    let mut satisfied = Vec::new();
    let mut blocked = Vec::new();

    gate(
        restore_readiness
            .get("ready_for_restore_executor_design")
            .and_then(Value::as_bool)
            == Some(true)
            && restore_readiness.get("executable").and_then(Value::as_bool) == Some(false)
            && restore_readiness
                .get("system_mutations_performed")
                .and_then(Value::as_bool)
                == Some(false),
        "generic_restore_evidence_ready",
        &mut satisfied,
        &mut blocked,
    );

    let model = mac_compatibility
        .get("model_identifier")
        .and_then(Value::as_str)
        .filter(|value| !value.trim().is_empty());
    gate(
        mac_compatibility
            .get("route")
            .and_then(Value::as_str)
            == Some("intel_bootcamp_recovery_assessment")
            && mac_compatibility
                .get("traditional_bootcamp_supported")
                .and_then(Value::as_bool)
                == Some(true)
            && mac_compatibility
                .get("source_architecture_compatible")
                .and_then(Value::as_bool)
                == Some(true)
            && mac_compatibility
                .get("model_identity_complete")
                .and_then(Value::as_bool)
                == Some(true)
            && model.is_some(),
        "intel_mac_model_and_architecture_verified",
        &mut satisfied,
        &mut blocked,
    );

    let driver_model = driver_package
        .get("mac_model_identifier")
        .and_then(Value::as_str);
    let manifest_sha = driver_package
        .get("manifest_sha256")
        .and_then(Value::as_str);
    gate(
        driver_package
            .get("verified_for_model")
            .and_then(Value::as_bool)
            == Some(true)
            && driver_package
                .get("exact_model_support_evidence")
                .and_then(Value::as_bool)
                == Some(true)
            && is_sha256(manifest_sha)
            && model
                .zip(driver_model)
                .is_some_and(|(model, driver_model)| model.eq_ignore_ascii_case(driver_model)),
        "bootcamp_driver_package_bound_to_exact_model",
        &mut satisfied,
        &mut blocked,
    );

    gate(
        mac_compatibility
            .get("repair_or_restore_executable")
            .and_then(Value::as_bool)
            == Some(false),
        "mac_planning_remained_non_executable",
        &mut satisfied,
        &mut blocked,
    );

    IntelMacRestoreGate {
        schema: "phoenix_key.intel_mac_restore_gate.v1",
        ready_for_intel_mac_restore_executor_design: blocked.is_empty(),
        executable: false,
        mac_model_identifier: model.map(str::to_string),
        driver_manifest_sha256: manifest_sha.map(str::to_string),
        satisfied_gates: satisfied,
        blocked_gates: blocked,
        system_mutations_performed: false,
    }
}

#[tauri::command]
pub fn assess_intel_mac_restore_readiness(
    restore_readiness_json: String,
    mac_compatibility_json: String,
    driver_package_json: String,
) -> Result<IntelMacRestoreGate, String> {
    let parse = |label: &str, text: String| -> Result<Value, String> {
        serde_json::from_str(&text).map_err(|error| format!("invalid {label} JSON: {error}"))
    };
    Ok(assess_intel_mac_restore_gate(
        &parse("restore readiness", restore_readiness_json)?,
        &parse("Mac compatibility", mac_compatibility_json)?,
        &parse("Boot Camp driver package", driver_package_json)?,
    ))
}

#[cfg(test)]
mod tests {
    use super::assess_intel_mac_restore_gate;
    use serde_json::json;

    fn evidence() -> (serde_json::Value, serde_json::Value, serde_json::Value) {
        (
            json!({
                "ready_for_restore_executor_design": true,
                "executable": false,
                "system_mutations_performed": false
            }),
            json!({
                "route": "intel_bootcamp_recovery_assessment",
                "architecture": "x86_64",
                "model_identifier": "MacBookPro16,1",
                "traditional_bootcamp_supported": true,
                "source_architecture_compatible": true,
                "model_identity_complete": true,
                "repair_or_restore_executable": false
            }),
            json!({
                "mac_model_identifier": "MacBookPro16,1",
                "manifest_sha256": "a".repeat(64),
                "verified_for_model": true,
                "exact_model_support_evidence": true
            }),
        )
    }

    #[test]
    fn exact_model_package_can_reach_design_readiness_only() {
        let (restore, mac, drivers) = evidence();
        let result = assess_intel_mac_restore_gate(&restore, &mac, &drivers);
        assert!(result.ready_for_intel_mac_restore_executor_design);
        assert!(!result.executable);
        assert!(result.system_mutations_performed == false);
    }

    #[test]
    fn different_model_driver_package_is_blocked() {
        let (restore, mac, mut drivers) = evidence();
        drivers["mac_model_identifier"] = json!("MacBookPro15,1");
        let result = assess_intel_mac_restore_gate(&restore, &mac, &drivers);
        assert!(!result.ready_for_intel_mac_restore_executor_design);
        assert!(result
            .blocked_gates
            .contains(&"bootcamp_driver_package_bound_to_exact_model".to_string()));
    }

    #[test]
    fn apple_silicon_route_cannot_pass_intel_gate() {
        let (restore, mut mac, drivers) = evidence();
        mac["route"] = json!("apple_silicon_windows_vm_or_external_recovery");
        mac["traditional_bootcamp_supported"] = json!(false);
        let result = assess_intel_mac_restore_gate(&restore, &mac, &drivers);
        assert!(!result.ready_for_intel_mac_restore_executor_design);
        assert!(result
            .blocked_gates
            .contains(&"intel_mac_model_and_architecture_verified".to_string()));
    }

    #[test]
    fn generic_restore_evidence_must_be_ready_first() {
        let (mut restore, mac, drivers) = evidence();
        restore["ready_for_restore_executor_design"] = json!(false);
        let result = assess_intel_mac_restore_gate(&restore, &mac, &drivers);
        assert!(!result.ready_for_intel_mac_restore_executor_design);
        assert!(result
            .blocked_gates
            .contains(&"generic_restore_evidence_ready".to_string()));
    }
}
