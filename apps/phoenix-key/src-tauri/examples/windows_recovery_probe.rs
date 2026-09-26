#[path = "../src/windows_recovery.rs"]
mod windows_recovery;
#[path = "../src/windows_recovery_guard.rs"]
mod windows_recovery_guard;
#[path = "../src/platform_recovery.rs"]
mod platform_recovery;
#[path = "../src/source_identity.rs"]
mod source_identity;
#[path = "../src/target_reenumeration.rs"]
mod target_reenumeration;
#[path = "../src/target_safety.rs"]
mod target_safety;
#[path = "../src/restore_rollback_contract.rs"]
mod restore_rollback_contract;
#[path = "../src/data_preservation.rs"]
mod data_preservation;
#[path = "../src/rollback_destination.rs"]
mod rollback_destination;
#[cfg(test)]
#[path = "../src/boot_repair_contract.rs"]
mod boot_repair_contract;
#[cfg(test)]
#[path = "../src/mac_bootcamp_compat.rs"]
mod mac_bootcamp_compat;
#[cfg(test)]
#[path = "../src/intel_mac_restore_gate.rs"]
mod intel_mac_restore_gate;
#[cfg(test)]
#[path = "../src/restore_readiness.rs"]
mod restore_readiness;
#[cfg(test)]
#[path = "../src/recovery_center.rs"]
mod recovery_center;
#[path = "../src/recovery_hardware_campaign.rs"]
mod recovery_hardware_campaign;

use platform_recovery::get_platform_recovery_answer;
use recovery_hardware_campaign::assess_windows_recovery_hardware_campaign;
use serde::Serialize;
use source_identity::{
    build_identity_bound_recovery_plan, capture_source_identity,
    verify_identity_bound_plan_sha256, verify_source_identity,
};
use std::{env, fs, process};
use target_reenumeration::{
    compare_recovery_target_reenumeration,
    verify_recovery_target_reenumeration_receipt_sha256,
    RecoveryTargetReenumerationReceipt,
};
use target_safety::{assess_recovery_target, verify_recovery_target_identity};
use windows_recovery::{analyze_backup_path, fixture_candidates};
use windows_recovery_guard::harden_analysis;

#[derive(Serialize)]
struct ErrorReceipt<'a> {
    schema: &'static str,
    status: &'static str,
    error: &'a str,
}

fn emit<T: Serialize>(value: &T) -> Result<(), String> {
    let json = serde_json::to_string_pretty(value)
        .map_err(|error| format!("cannot serialize recovery result: {error}"))?;
    println!("{json}");
    Ok(())
}

fn usage() -> ! {
    eprintln!(
        "usage:\n  cargo run --example windows_recovery_probe -- inspect <path>\n  cargo run --example windows_recovery_probe -- plan <path>\n  cargo run --example windows_recovery_probe -- identity <path>\n  cargo run --example windows_recovery_probe -- verify <path> <expected-sha256>\n  cargo run --example windows_recovery_probe -- target-check <evidence-json> <source-size-bytes> <source-physical-target|unknown> <source-stable-identity-sha256|unknown>\n  cargo run --example windows_recovery_probe -- target-verify <evidence-json> <expected-snapshot-sha256> <expected-stable-sha256>\n  cargo run --example windows_recovery_probe -- target-reenumeration <evidence-json> <expected-target|unknown> <expected-snapshot-sha256> <expected-stable-sha256>\n  cargo run --example windows_recovery_probe -- target-reenumeration-verify <receipt-json>\n  cargo run --example windows_recovery_probe -- plan-verify <plan-json>\n  cargo run --example windows_recovery_probe -- fixtures <directory>\n  cargo run --example windows_recovery_probe -- answer <platform> <scenario>"
    );
    process::exit(64);
}

fn run() -> Result<(), String> {
    let mut args = env::args().skip(1);
    let command = args.next().unwrap_or_else(|| usage());

    if command == "answer" {
        let platform = args.next().unwrap_or_else(|| usage());
        let scenario = args.next().unwrap_or_else(|| usage());
        if args.next().is_some() {
            usage();
        }
        return emit(&get_platform_recovery_answer(platform, scenario, None, None)?);
    }

    if command == "verify" {
        let path = args.next().unwrap_or_else(|| usage());
        let expected = args.next().unwrap_or_else(|| usage());
        if args.next().is_some() {
            usage();
        }
        return emit(&verify_source_identity(path, &expected)?);
    }

    if command == "plan-verify" {
        let plan_path = args.next().unwrap_or_else(|| usage());
        if args.next().is_some() {
            usage();
        }
        let plan_bytes =
            fs::read(&plan_path).map_err(|error| format!("cannot read recovery plan JSON: {error}"))?;
        let plan: serde_json::Value = serde_json::from_slice(&plan_bytes)
            .map_err(|error| format!("recovery plan is not valid JSON: {error}"))?;
        return emit(&serde_json::json!({
            "schema": "phoenix_key.identity_bound_plan_verification.v1",
            "integrity_verified": verify_identity_bound_plan_sha256(&plan),
            "system_mutations_performed": false
        }));
    }

    if command == "target-verify" {
        let evidence_path = args.next().unwrap_or_else(|| usage());
        let expected_snapshot = args.next().unwrap_or_else(|| usage());
        let expected_stable = args.next().unwrap_or_else(|| usage());
        if args.next().is_some() {
            usage();
        }
        let evidence_bytes = fs::read(&evidence_path)
            .map_err(|error| format!("cannot read target evidence JSON: {error}"))?;
        let evidence: serde_json::Value = serde_json::from_slice(&evidence_bytes)
            .map_err(|error| format!("target evidence is not valid JSON: {error}"))?;
        return emit(&verify_recovery_target_identity(
            &evidence,
            &expected_snapshot,
            &expected_stable,
        ));
    }

    if command == "target-reenumeration" {
        let evidence_path = args.next().unwrap_or_else(|| usage());
        let expected_target = args.next().unwrap_or_else(|| usage());
        let expected_snapshot = args.next().unwrap_or_else(|| usage());
        let expected_stable = args.next().unwrap_or_else(|| usage());
        if args.next().is_some() {
            usage();
        }
        let evidence_bytes = fs::read(&evidence_path)
            .map_err(|error| format!("cannot read target evidence JSON: {error}"))?;
        let evidence: serde_json::Value = serde_json::from_slice(&evidence_bytes)
            .map_err(|error| format!("target evidence is not valid JSON: {error}"))?;
        let expected_target = if expected_target.eq_ignore_ascii_case("unknown") {
            None
        } else {
            Some(expected_target.as_str())
        };
        return emit(&compare_recovery_target_reenumeration(
            &evidence,
            expected_target,
            &expected_snapshot,
            &expected_stable,
        ));
    }

    if command == "target-reenumeration-verify" {
        let receipt_path = args.next().unwrap_or_else(|| usage());
        if args.next().is_some() {
            usage();
        }
        let receipt_bytes = fs::read(&receipt_path)
            .map_err(|error| format!("cannot read target re-enumeration receipt JSON: {error}"))?;
        let receipt: RecoveryTargetReenumerationReceipt =
            serde_json::from_slice(&receipt_bytes).map_err(|error| {
                format!("target re-enumeration receipt is not valid JSON: {error}")
            })?;
        return emit(&serde_json::json!({
            "schema": "phoenix_key.recovery_target_reenumeration_receipt_verification.v1",
            "checksum_verified": verify_recovery_target_reenumeration_receipt_sha256(&receipt),
            "system_mutations_performed": false
        }));
    }

    if command == "hardware-campaign-report" {
        let evidence_path = args.next().unwrap_or_else(|| usage());
        if args.next().is_some() {
            usage();
        }
        let evidence_bytes = fs::read(&evidence_path)
            .map_err(|error| format!("cannot read hardware campaign evidence JSON: {error}"))?;
        let evidence_json = String::from_utf8(evidence_bytes)
            .map_err(|error| format!("hardware campaign evidence is not UTF-8 JSON: {error}"))?;
        return emit(&assess_windows_recovery_hardware_campaign(evidence_json)?);
    }

    if command == "target-check" {
        let evidence_path = args.next().unwrap_or_else(|| usage());
        let source_size = args
            .next()
            .unwrap_or_else(|| usage())
            .parse::<u64>()
            .map_err(|_| "source-size-bytes must be an unsigned integer".to_string())?;
        let source_target = args.next().unwrap_or_else(|| usage());
        let source_stable_identity = args.next().unwrap_or_else(|| usage());
        if args.next().is_some() {
            usage();
        }
        let evidence_bytes = fs::read(&evidence_path)
            .map_err(|error| format!("cannot read target evidence JSON: {error}"))?;
        let evidence: serde_json::Value = serde_json::from_slice(&evidence_bytes)
            .map_err(|error| format!("target evidence is not valid JSON: {error}"))?;
        let source_target = if source_target.eq_ignore_ascii_case("unknown") {
            None
        } else {
            Some(source_target.as_str())
        };
        let source_stable_identity =
            if source_stable_identity.eq_ignore_ascii_case("unknown") {
                None
            } else {
                Some(source_stable_identity.as_str())
            };
        return emit(&assess_recovery_target(
            &evidence,
            source_size,
            source_target,
            source_stable_identity,
        ));
    }

    let path = args.next().unwrap_or_else(|| usage());
    if args.next().is_some() {
        usage();
    }

    match command.as_str() {
        "inspect" => {
            let analysis = analyze_backup_path(&path)?;
            emit(&harden_analysis(&path, analysis))
        }
        "plan" => emit(&build_identity_bound_recovery_plan(path)?),
        "identity" => emit(&capture_source_identity(path)?),
        "fixtures" => {
            let candidates = fixture_candidates(path)?;
            let rendered: Vec<String> = candidates
                .into_iter()
                .map(|candidate| candidate.to_string_lossy().to_string())
                .collect();
            emit(&rendered)
        }
        _ => usage(),
    }
}

fn main() {
    if let Err(error) = run() {
        let _ = emit(&ErrorReceipt {
            schema: "phoenix_key.windows_recovery_error.v1",
            status: "error",
            error: &error,
        });
        process::exit(1);
    }
}
