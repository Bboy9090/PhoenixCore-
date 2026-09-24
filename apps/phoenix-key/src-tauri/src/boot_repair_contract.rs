use serde::Serialize;
use serde_json::Value;

const BOOT_STATE_SCHEMA: &str = "phoenix_key.windows_boot_state.v1";

#[derive(Debug, Clone, Serialize, PartialEq, Eq)]
pub struct BootRepairContract {
    pub schema: &'static str,
    pub route: &'static str,
    pub repair_candidate: bool,
    pub evidence_summary: Vec<String>,
    pub proposed_operations: Vec<String>,
    pub blocked_operations: Vec<String>,
    pub required_backups: Vec<String>,
    pub required_rechecks: Vec<String>,
    pub executable: bool,
    pub system_mutations_performed: bool,
}

fn command_succeeded(root: &Value, key: &str) -> bool {
    root.get(key)
        .and_then(|value| value.get("returncode"))
        .and_then(Value::as_i64)
        == Some(0)
}

pub fn build_boot_repair_contract(
    boot_state: &Value,
    source_restore_candidate: bool,
) -> Result<BootRepairContract, String> {
    if boot_state.get("schema").and_then(Value::as_str) != Some(BOOT_STATE_SCHEMA) {
        return Err("unsupported Windows boot-state snapshot schema".to_string());
    }

    let has_esp = boot_state
        .get("efi_system_partitions")
        .and_then(Value::as_array)
        .is_some_and(|partitions| !partitions.is_empty());
    let bcd_ok = command_succeeded(boot_state, "bcd");
    let winre_ok = command_succeeded(boot_state, "winre");

    let mut evidence_summary = vec![
        format!("efi_system_partition_present={has_esp}"),
        format!("bcd_enumeration_succeeded={bcd_ok}"),
        format!("winre_query_succeeded={winre_ok}"),
        format!("restore_source_available={source_restore_candidate}"),
    ];

    let (route, repair_candidate, proposed_operations) = if has_esp && !bcd_ok {
        (
            "boot_chain_repair_assessment",
            true,
            vec![
                "restore_or_rebuild_bcd_from_verified_windows_installation".to_string(),
                "verify_signed_windows_boot_manager_after_repair".to_string(),
            ],
        )
    } else if has_esp && bcd_ok && !winre_ok {
        (
            "winre_repair_assessment",
            true,
            vec![
                "repair_winre_registration_from_verified_recovery_image".to_string(),
                "verify_winre_registration_after_repair".to_string(),
            ],
        )
    } else if !has_esp && source_restore_candidate {
        (
            "partition_or_full_restore_assessment",
            true,
            vec![
                "assess_efi_system_partition_reconstruction".to_string(),
                "assess_full_system_restore_against_partition_manifest".to_string(),
            ],
        )
    } else if !has_esp {
        (
            "partition_recovery_blocked_without_verified_source",
            false,
            Vec::new(),
        )
    } else {
        (
            "diagnostic_no_boot_state_fault_proven",
            false,
            Vec::new(),
        )
    };

    if !repair_candidate {
        evidence_summary.push(
            "No boot mutation is justified by the current evidence; remain diagnostic.".to_string(),
        );
    }

    Ok(BootRepairContract {
        schema: "phoenix_key.boot_repair_contract.v1",
        route,
        repair_candidate,
        evidence_summary,
        proposed_operations,
        blocked_operations: vec![
            "write_efi_files".to_string(),
            "modify_bcd_store".to_string(),
            "modify_winre_configuration".to_string(),
            "repartition_disk".to_string(),
            "apply_system_image".to_string(),
        ],
        required_backups: vec![
            "partition_table_backup".to_string(),
            "efi_system_partition_file_backup".to_string(),
            "bcd_store_export".to_string(),
            "winre_configuration_and_image_identity".to_string(),
        ],
        required_rechecks: vec![
            "source_identity".to_string(),
            "target_snapshot_identity".to_string(),
            "target_stable_hardware_identity".to_string(),
            "source_target_distinct_physical_device".to_string(),
            "rollback_manifest_integrity".to_string(),
            "secure_boot_and_boot_mode_compatibility".to_string(),
        ],
        executable: false,
        system_mutations_performed: false,
    })
}

#[tauri::command]
pub fn plan_windows_boot_repair(
    boot_state_json: String,
    source_restore_candidate: bool,
) -> Result<BootRepairContract, String> {
    let boot_state: Value = serde_json::from_str(&boot_state_json)
        .map_err(|error| format!("invalid Windows boot-state JSON: {error}"))?;
    build_boot_repair_contract(&boot_state, source_restore_candidate)
}

#[cfg(test)]
mod tests {
    use super::build_boot_repair_contract;
    use serde_json::json;

    fn snapshot(has_esp: bool, bcd_code: i64, winre_code: i64) -> serde_json::Value {
        json!({
            "schema": "phoenix_key.windows_boot_state.v1",
            "efi_system_partitions": if has_esp {
                vec![json!({"disk_number": 0, "partition_number": 1})]
            } else {
                Vec::new()
            },
            "bcd": {"returncode": bcd_code},
            "winre": {"returncode": winre_code}
        })
    }

    #[test]
    fn bcd_failure_routes_to_boot_chain_repair_but_stays_locked() {
        let contract = build_boot_repair_contract(&snapshot(true, 1, 0), true).unwrap();
        assert_eq!(contract.route, "boot_chain_repair_assessment");
        assert!(contract.repair_candidate);
        assert!(!contract.executable);
        assert!(contract
            .blocked_operations
            .contains(&"modify_bcd_store".to_string()));
    }

    #[test]
    fn repair_contract_requires_snapshot_and_stable_target_rechecks() {
        let contract = build_boot_repair_contract(&snapshot(true, 1, 0), true).unwrap();
        assert!(contract
            .required_rechecks
            .contains(&"target_snapshot_identity".to_string()));
        assert!(contract
            .required_rechecks
            .contains(&"target_stable_hardware_identity".to_string()));
    }

    #[test]
    fn winre_failure_routes_to_winre_repair() {
        let contract = build_boot_repair_contract(&snapshot(true, 0, 1), true).unwrap();
        assert_eq!(contract.route, "winre_repair_assessment");
        assert!(contract.repair_candidate);
        assert!(!contract.executable);
    }

    #[test]
    fn missing_esp_with_verified_source_routes_to_restore_assessment() {
        let contract = build_boot_repair_contract(&snapshot(false, 1, 1), true).unwrap();
        assert_eq!(contract.route, "partition_or_full_restore_assessment");
        assert!(contract.repair_candidate);
        assert!(!contract.executable);
    }

    #[test]
    fn missing_esp_without_source_fails_closed() {
        let contract = build_boot_repair_contract(&snapshot(false, 1, 1), false).unwrap();
        assert_eq!(
            contract.route,
            "partition_recovery_blocked_without_verified_source"
        );
        assert!(!contract.repair_candidate);
    }

    #[test]
    fn healthy_snapshot_does_not_invent_a_repair() {
        let contract = build_boot_repair_contract(&snapshot(true, 0, 0), true).unwrap();
        assert_eq!(contract.route, "diagnostic_no_boot_state_fault_proven");
        assert!(!contract.repair_candidate);
        assert!(contract.proposed_operations.is_empty());
    }
}
