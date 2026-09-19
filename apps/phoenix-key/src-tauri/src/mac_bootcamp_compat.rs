use serde::Serialize;
use std::process::Command;

#[derive(Debug, Clone, Serialize, PartialEq, Eq)]
pub struct MacBootCampCompatibility {
    pub schema: &'static str,
    pub architecture: String,
    pub model_identifier: Option<String>,
    pub route: &'static str,
    pub traditional_bootcamp_supported: bool,
    pub source_architecture_compatible: bool,
    pub model_identity_complete: bool,
    pub driver_package_verified: bool,
    pub repair_or_restore_executable: bool,
    pub required_evidence: Vec<String>,
    pub blocked_operations: Vec<String>,
    pub user_summary: String,
}

fn normalized_architecture(value: &str) -> String {
    match value.trim().to_ascii_lowercase().as_str() {
        "amd64" | "x64" | "x86_64" => "x86_64".to_string(),
        "arm64" | "aarch64" => "arm64".to_string(),
        other => other.to_string(),
    }
}

pub fn assess_mac_bootcamp_compatibility(
    architecture: &str,
    model_identifier: Option<&str>,
    source_architecture: Option<&str>,
) -> MacBootCampCompatibility {
    let architecture = normalized_architecture(architecture);
    let model_identifier = model_identifier
        .map(str::trim)
        .filter(|value| !value.is_empty())
        .map(str::to_string);
    let source_architecture = source_architecture.map(normalized_architecture);
    let model_identity_complete = model_identifier.is_some();

    if architecture == "arm64" {
        return MacBootCampCompatibility {
            schema: "phoenix_key.mac_bootcamp_compatibility.v1",
            architecture,
            model_identifier,
            route: "apple_silicon_windows_vm_or_external_recovery",
            traditional_bootcamp_supported: false,
            source_architecture_compatible: source_architecture
                .as_deref()
                .is_none_or(|value| value == "arm64"),
            model_identity_complete,
            driver_package_verified: false,
            repair_or_restore_executable: false,
            required_evidence: vec![
                "Apple Silicon model identifier".to_string(),
                "Windows ARM recovery or VM target architecture".to_string(),
                "verified recovery source identity".to_string(),
            ],
            blocked_operations: vec![
                "traditional_bootcamp_partition_or_restore".to_string(),
                "intel_bootcamp_driver_injection".to_string(),
            ],
            user_summary: "Apple Silicon does not enter the traditional Intel Boot Camp path. Route Windows recovery through an ARM-compatible VM, external recovery workflow, or other supported virtualization path.".to_string(),
        };
    }

    if architecture == "x86_64" {
        let source_architecture_compatible = source_architecture
            .as_deref()
            .is_none_or(|value| value == "x86_64");
        let mut blocked_operations = vec![
            "automatic_bootcamp_partition_mutation".to_string(),
            "unverified_bootcamp_driver_injection".to_string(),
        ];
        if !source_architecture_compatible {
            blocked_operations.push("restore_architecture_mismatch".to_string());
        }
        if !model_identity_complete {
            blocked_operations.push("bootcamp_restore_without_exact_mac_model".to_string());
        }
        return MacBootCampCompatibility {
            schema: "phoenix_key.mac_bootcamp_compatibility.v1",
            architecture,
            model_identifier,
            route: "intel_bootcamp_recovery_assessment",
            traditional_bootcamp_supported: true,
            source_architecture_compatible,
            model_identity_complete,
            driver_package_verified: false,
            repair_or_restore_executable: false,
            required_evidence: vec![
                "exact Mac model identifier".to_string(),
                "verified x86_64 Windows recovery source".to_string(),
                "current partition/APFS topology snapshot".to_string(),
                "Apple Boot Camp Windows support software downloaded for this Mac through Boot Camp Assistant".to_string(),
                "driver package manifest and hashes".to_string(),
                "rollback bundle".to_string(),
            ],
            blocked_operations,
            user_summary: "This is an Intel Mac and may use the traditional Boot Camp recovery route, but Phoenix Key will not partition, restore, or inject drivers until the exact model and Apple support-software package are verified.".to_string(),
        };
    }

    MacBootCampCompatibility {
        schema: "phoenix_key.mac_bootcamp_compatibility.v1",
        architecture,
        model_identifier,
        route: "unsupported_or_unknown_mac_architecture",
        traditional_bootcamp_supported: false,
        source_architecture_compatible: false,
        model_identity_complete,
        driver_package_verified: false,
        repair_or_restore_executable: false,
        required_evidence: vec![
            "recognized Mac CPU architecture".to_string(),
            "exact Mac model identifier".to_string(),
        ],
        blocked_operations: vec![
            "traditional_bootcamp_partition_or_restore".to_string(),
            "driver_injection".to_string(),
        ],
        user_summary: "The Mac architecture is not recognized well enough to choose a Boot Camp recovery path, so recovery remains diagnostic.".to_string(),
    }
}

fn query_sysctl(name: &str) -> Option<String> {
    let output = Command::new("sysctl").args(["-n", name]).output().ok()?;
    if !output.status.success() {
        return None;
    }
    let value = String::from_utf8_lossy(&output.stdout).trim().to_string();
    (!value.is_empty()).then_some(value)
}

#[tauri::command]
pub fn inspect_mac_bootcamp_host(
    source_architecture: Option<String>,
) -> Result<MacBootCampCompatibility, String> {
    if std::env::consts::OS != "macos" {
        return Err("Mac Boot Camp host inspection requires macOS.".to_string());
    }
    let architecture = std::env::consts::ARCH;
    let model_identifier = query_sysctl("hw.model");
    Ok(assess_mac_bootcamp_compatibility(
        architecture,
        model_identifier.as_deref(),
        source_architecture.as_deref(),
    ))
}

#[cfg(test)]
mod tests {
    use super::assess_mac_bootcamp_compatibility;

    #[test]
    fn apple_silicon_never_enters_traditional_bootcamp() {
        let result =
            assess_mac_bootcamp_compatibility("aarch64", Some("MacBookPro18,3"), Some("arm64"));
        assert!(!result.traditional_bootcamp_supported);
        assert_eq!(
            result.route,
            "apple_silicon_windows_vm_or_external_recovery"
        );
        assert!(result
            .blocked_operations
            .contains(&"traditional_bootcamp_partition_or_restore".to_string()));
        assert!(!result.repair_or_restore_executable);
    }

    #[test]
    fn intel_mac_requires_exact_model_and_driver_evidence() {
        let result =
            assess_mac_bootcamp_compatibility("x86_64", Some("MacBookPro16,1"), Some("x86_64"));
        assert!(result.traditional_bootcamp_supported);
        assert!(result.source_architecture_compatible);
        assert!(result.model_identity_complete);
        assert!(!result.driver_package_verified);
        assert!(!result.repair_or_restore_executable);
    }

    #[test]
    fn intel_arm_source_is_blocked_as_architecture_mismatch() {
        let result =
            assess_mac_bootcamp_compatibility("x86_64", Some("MacBookPro16,1"), Some("arm64"));
        assert!(!result.source_architecture_compatible);
        assert!(result
            .blocked_operations
            .contains(&"restore_architecture_mismatch".to_string()));
    }

    #[test]
    fn missing_model_keeps_intel_restore_locked() {
        let result = assess_mac_bootcamp_compatibility("x86_64", None, Some("x86_64"));
        assert!(!result.model_identity_complete);
        assert!(result
            .blocked_operations
            .contains(&"bootcamp_restore_without_exact_mac_model".to_string()));
        assert!(!result.repair_or_restore_executable);
    }
}
