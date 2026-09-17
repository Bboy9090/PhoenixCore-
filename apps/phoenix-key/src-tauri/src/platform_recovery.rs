use serde::Serialize;

#[derive(Debug, Clone, Serialize, PartialEq, Eq)]
pub struct RecoveryAnswer {
    pub schema: &'static str,
    pub platform: String,
    pub scenario: String,
    pub severity: &'static str,
    pub user_summary: String,
    pub supported_actions: Vec<String>,
    pub blocked_actions: Vec<String>,
    pub evidence_to_collect: Vec<String>,
    pub destructive_warning: Option<String>,
    pub security_boundary: Vec<String>,
    pub references: Vec<String>,
}

fn normalized(value: &str) -> String {
    value.trim().to_ascii_lowercase()
}

fn base_answer(platform: &str, scenario: &str) -> RecoveryAnswer {
    RecoveryAnswer {
        schema: "phoenix_key.platform_recovery_answer.v1",
        platform: platform.to_string(),
        scenario: scenario.to_string(),
        severity: "diagnostic",
        user_summary: "Phoenix Key identified a recovery scenario and is keeping the workflow non-destructive until the supported path is confirmed.".to_string(),
        supported_actions: Vec::new(),
        blocked_actions: Vec::new(),
        evidence_to_collect: Vec::new(),
        destructive_warning: None,
        security_boundary: vec![
            "Do not bypass firmware passwords, device enrollment, Verified Boot, Secure Boot, signature checks, or ownership controls.".to_string(),
            "Prefer vendor recovery, signed boot components, documented developer/recovery modes, and evidence-backed repair.".to_string(),
        ],
        references: Vec::new(),
    }
}

pub fn answer_recovery_question(
    platform: String,
    scenario: String,
    managed_device: Option<bool>,
    hp_sure_start: Option<bool>,
) -> Result<RecoveryAnswer, String> {
    let platform_key = normalized(&platform);
    let scenario_key = normalized(&scenario);
    if platform_key.is_empty() || scenario_key.is_empty() {
        return Err("platform and scenario are required".to_string());
    }

    let mut answer = base_answer(&platform, &scenario);

    if platform_key.contains("hp") && (scenario_key.contains("bios") || scenario_key.contains("firmware")) {
        answer.severity = "firmware-recovery";
        answer.evidence_to_collect = vec![
            "Exact HP product/model number and motherboard/System Board ID".to_string(),
            "Power/charge LED state and Caps Lock/Num Lock blink or beep pattern".to_string(),
            "Whether HP Sure Start is present/enabled".to_string(),
            "Current BIOS version if readable and whether a BIOS update failed".to_string(),
        ];
        answer.references.push("HP Notebook PCs - Recovering the BIOS (Basic Input Output System)".to_string());

        if scenario_key.contains("password") || scenario_key.contains("lock") || scenario_key.contains("admin") {
            answer.user_summary = "This looks like a firmware access-control problem, not BIOS corruption. Phoenix Key will not attempt to defeat the firmware password or ownership control.".to_string();
            answer.supported_actions = vec![
                "Confirm ownership and exact HP model/serial information".to_string(),
                "Use HP-authorized password/service recovery or the organization IT administrator for managed hardware".to_string(),
                "Preserve current firmware and disk state while collecting diagnostic evidence".to_string(),
            ];
            answer.blocked_actions = vec![
                "BIOS password bypass or master-password generation".to_string(),
                "SPI flash modification intended to remove security ownership data".to_string(),
                "TPM/Secure Boot ownership reset performed solely to defeat access controls".to_string(),
            ];
            return Ok(answer);
        }

        match hp_sure_start {
            Some(true) => {
                answer.user_summary = "HP Sure Start systems use protected automatic firmware recovery and do not use the same manual BIOS recovery paths as non-Sure-Start systems.".to_string();
                answer.supported_actions = vec![
                    "Allow HP Sure Start automatic recovery and capture any on-screen or blink-code evidence".to_string(),
                    "Use HP-documented CMOS reset or HP service diagnostics if automatic repair does not recover boot".to_string(),
                    "Escalate to HP service when firmware recovery remains unsuccessful".to_string(),
                ];
                answer.blocked_actions = vec![
                    "Force a non-Sure-Start manual BIOS recovery method onto a Sure Start machine".to_string(),
                    "Flash an unverified BIOS image".to_string(),
                ];
            }
            _ => {
                answer.user_summary = "This matches an HP BIOS-corruption recovery case. Phoenix Key should verify the exact model and then route to HP-supported automatic/manual or USB BIOS recovery rather than guessing a firmware image.".to_string();
                answer.supported_actions = vec![
                    "Match the exact HP model/System Board ID to an official HP BIOS package".to_string(),
                    "Use HP automatic BIOS recovery when available".to_string(),
                    "Use HP-documented manual or USB BIOS recovery only after exact-package verification".to_string(),
                    "Capture the recovered BIOS version and post-recovery boot result".to_string(),
                ];
                answer.blocked_actions = vec![
                    "Cross-flash a BIOS from a different model or board ID".to_string(),
                    "Disable firmware verification to accept an unknown image".to_string(),
                ];
            }
        }
        return Ok(answer);
    }

    if platform_key.contains("chrome") || platform_key.contains("chromebook") {
        answer.evidence_to_collect = vec![
            "Exact Chromebook manufacturer/model or board name".to_string(),
            "Displayed recovery/error message".to_string(),
            "Whether the device is enterprise/school managed".to_string(),
            "Whether Recovery Mode, Developer Mode, or normal Verified Boot is currently active".to_string(),
        ];
        answer.references.extend([
            "Google Chromebook Help - Recover your Chromebook".to_string(),
            "ChromiumOS - Verified Boot".to_string(),
            "ChromiumOS - Firmware Boot and Recovery".to_string(),
        ]);

        if managed_device.unwrap_or(false)
            || scenario_key.contains("enroll")
            || scenario_key.contains("managed")
            || scenario_key.contains("enterprise")
        {
            answer.severity = "ownership-policy";
            answer.user_summary = "This Chromebook is managed or enrollment-controlled. Recovery can reinstall ChromeOS, but Phoenix Key will not remove enterprise enrollment or administrator ownership policy.".to_string();
            answer.supported_actions = vec![
                "Use official ChromeOS recovery to repair the operating system".to_string(),
                "Contact the organization administrator to change enrollment or ownership policy".to_string(),
                "Back up permitted user data before any recovery that erases local storage".to_string(),
            ];
            answer.blocked_actions = vec![
                "Enterprise enrollment bypass".to_string(),
                "Forced re-enrollment defeat".to_string(),
                "Verified Boot or firmware modification whose purpose is to evade management".to_string(),
            ];
            answer.destructive_warning = Some("ChromeOS recovery can erase local data on the Chromebook.".to_string());
            return Ok(answer);
        }

        if scenario_key.contains("missing")
            || scenario_key.contains("damaged")
            || scenario_key.contains("recover")
            || scenario_key.contains("boot loop")
        {
            answer.severity = "os-recovery";
            answer.user_summary = "This matches a ChromeOS recovery case. The supported route is to restore ChromeOS through the device's recovery path; newer devices may support internet recovery, while other devices use official recovery media.".to_string();
            answer.supported_actions = vec![
                "Try less-invasive restart/reset diagnostics before full recovery when the device still boots".to_string(),
                "Use official ChromeOS Recovery Mode and a model-matched recovery image or supported internet recovery".to_string(),
                "Verify the device returns to a normal Verified Boot state after recovery".to_string(),
            ];
            answer.blocked_actions = vec![
                "Use a recovery image for a different Chromebook board/model".to_string(),
                "Patch recovery media to defeat Verified Boot or enrollment".to_string(),
            ];
            answer.destructive_warning = Some("ChromeOS recovery normally erases local storage; back up accessible data first.".to_string());
            return Ok(answer);
        }

        if scenario_key.contains("shim")
            || scenario_key.contains("verified boot")
            || scenario_key.contains("custom firmware")
            || scenario_key.contains("developer")
        {
            answer.severity = "verified-boot";
            answer.user_summary = "This is a Verified Boot/developer-path question. Phoenix Key can explain and validate supported owner/developer modes, but it will not supply shims or patched firmware intended to bypass Verified Boot or device-management controls.".to_string();
            answer.supported_actions = vec![
                "Use documented Developer Mode/debugging features only on a device you own and control".to_string(),
                "Use recovery to restore normal Verified Boot when returning the device to a trusted state".to_string(),
                "Validate recovery media and board compatibility before writing it".to_string(),
            ];
            answer.blocked_actions = vec![
                "Verified Boot bypass shim or signature-bypass payload".to_string(),
                "Firmware patching intended to suppress ownership/enrollment checks".to_string(),
            ];
            return Ok(answer);
        }
    }

    if platform_key.contains("uefi")
        || platform_key.contains("secure boot")
        || scenario_key.contains("shim")
        || scenario_key.contains("secure boot")
        || scenario_key.contains("signature")
    {
        answer.severity = "boot-trust";
        answer.user_summary = "This looks like a UEFI Secure Boot or signed-shim/bootloader trust failure. Phoenix Key should diagnose the signature/key chain and repair it with trusted signed components instead of bypassing verification.".to_string();
        answer.supported_actions = vec![
            "Inspect firmware boot mode, Secure Boot state, enrolled keys, boot entries, and the failing boot component".to_string(),
            "Restore a vendor- or distribution-signed shim/bootloader appropriate for the installed OS".to_string(),
            "Repair EFI boot entries and signed boot files while preserving the existing key hierarchy".to_string(),
            "Only change Secure Boot policy through an explicit owner-authorized firmware workflow".to_string(),
        ];
        answer.blocked_actions = vec![
            "Signature-check bypass or patched shim designed to execute untrusted code".to_string(),
            "Silently disabling Secure Boot as a generic repair step".to_string(),
            "Replacing platform keys without an ownership-backed recovery plan".to_string(),
        ];
        answer.evidence_to_collect = vec![
            "UEFI vs legacy boot mode".to_string(),
            "Secure Boot enabled/disabled state".to_string(),
            "EFI System Partition inventory and boot entries".to_string(),
            "Exact shim/bootloader file and signature status".to_string(),
        ];
        answer.references.push("Microsoft/UEFI Secure Boot documentation and the installed OS vendor's signed bootloader documentation".to_string());
        return Ok(answer);
    }

    answer.user_summary = "Phoenix Key does not yet have a platform-specific rule for this scenario, so it will stay in diagnostic mode and avoid destructive or security-bypass actions.".to_string();
    answer.supported_actions = vec![
        "Collect exact manufacturer/model, firmware version, boot error, and recovery-state evidence".to_string(),
        "Identify the official vendor recovery procedure and verify every recovery image before use".to_string(),
        "Prefer read-only diagnosis and reversible boot repair before destructive recovery".to_string(),
    ];
    answer.blocked_actions = vec![
        "Unknown firmware flashing".to_string(),
        "Credential, enrollment, Verified Boot, or Secure Boot bypass".to_string(),
    ];
    Ok(answer)
}

#[tauri::command]
pub fn get_platform_recovery_answer(
    platform: String,
    scenario: String,
    managed_device: Option<bool>,
    hp_sure_start: Option<bool>,
) -> Result<RecoveryAnswer, String> {
    answer_recovery_question(platform, scenario, managed_device, hp_sure_start)
}

#[cfg(test)]
mod tests {
    use super::answer_recovery_question;

    #[test]
    fn hp_sure_start_does_not_offer_manual_bypass_path() {
        let answer = answer_recovery_question(
            "HP laptop".to_string(),
            "BIOS corruption black screen".to_string(),
            Some(false),
            Some(true),
        )
        .unwrap();
        assert!(answer.supported_actions.iter().any(|item| item.contains("Sure Start")));
        assert!(answer.blocked_actions.iter().any(|item| item.contains("non-Sure-Start")));
    }

    #[test]
    fn hp_password_scenario_blocks_bypass() {
        let answer = answer_recovery_question(
            "HP".to_string(),
            "BIOS admin password locked".to_string(),
            None,
            None,
        )
        .unwrap();
        assert!(answer.blocked_actions.iter().any(|item| item.contains("password bypass")));
    }

    #[test]
    fn managed_chromebook_blocks_enrollment_bypass() {
        let answer = answer_recovery_question(
            "Chromebook".to_string(),
            "enterprise enrollment".to_string(),
            Some(true),
            None,
        )
        .unwrap();
        assert!(answer.blocked_actions.iter().any(|item| item.contains("enrollment bypass")));
        assert!(answer.supported_actions.iter().any(|item| item.contains("official ChromeOS recovery")));
    }

    #[test]
    fn chromeos_missing_or_damaged_routes_to_recovery() {
        let answer = answer_recovery_question(
            "ChromeOS".to_string(),
            "ChromeOS is missing or damaged".to_string(),
            Some(false),
            None,
        )
        .unwrap();
        assert_eq!(answer.severity, "os-recovery");
        assert!(answer.destructive_warning.is_some());
    }

    #[test]
    fn shim_question_keeps_secure_boot_trust_boundary() {
        let answer = answer_recovery_question(
            "UEFI Secure Boot".to_string(),
            "shim signature failure".to_string(),
            None,
            None,
        )
        .unwrap();
        assert!(answer.blocked_actions.iter().any(|item| item.contains("Signature-check bypass")));
        assert!(answer.supported_actions.iter().any(|item| item.contains("signed shim")));
    }
}
