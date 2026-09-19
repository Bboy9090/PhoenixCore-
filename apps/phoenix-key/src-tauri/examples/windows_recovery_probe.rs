#[path = "../src/windows_recovery.rs"]
mod windows_recovery;
#[path = "../src/windows_recovery_guard.rs"]
mod windows_recovery_guard;
#[path = "../src/platform_recovery.rs"]
mod platform_recovery;
#[path = "../src/source_identity.rs"]
mod source_identity;
#[path = "../src/target_safety.rs"]
mod target_safety;
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

use platform_recovery::get_platform_recovery_answer;
use serde::Serialize;
use source_identity::{build_identity_bound_recovery_plan, capture_source_identity, verify_source_identity};
use std::{env, fs, process};
use target_safety::assess_recovery_target;
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
        "usage:\n  cargo run --example windows_recovery_probe -- inspect <path>\n  cargo run --example windows_recovery_probe -- plan <path>\n  cargo run --example windows_recovery_probe -- identity <path>\n  cargo run --example windows_recovery_probe -- verify <path> <expected-sha256>\n  cargo run --example windows_recovery_probe -- target-check <evidence-json> <source-size-bytes> <source-physical-target|unknown>\n  cargo run --example windows_recovery_probe -- fixtures <directory>\n  cargo run --example windows_recovery_probe -- answer <platform> <scenario>"
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

    if command == "target-check" {
        let evidence_path = args.next().unwrap_or_else(|| usage());
        let source_size = args
            .next()
            .unwrap_or_else(|| usage())
            .parse::<u64>()
            .map_err(|_| "source-size-bytes must be an unsigned integer".to_string())?;
        let source_target = args.next().unwrap_or_else(|| usage());
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
        return emit(&assess_recovery_target(&evidence, source_size, source_target));
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
