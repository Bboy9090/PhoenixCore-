#[path = "../src/windows_recovery.rs"]
mod windows_recovery;
#[path = "../src/windows_recovery_guard.rs"]
mod windows_recovery_guard;
#[cfg(test)]
#[path = "../src/recovery_center.rs"]
mod recovery_center;

use serde::Serialize;
use std::{env, process};
use windows_recovery::{analyze_backup_path, fixture_candidates};
use windows_recovery_guard::{build_guarded_recovery_plan, harden_analysis};

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
        "usage:\n  cargo run --example windows_recovery_probe -- inspect <path>\n  cargo run --example windows_recovery_probe -- plan <path>\n  cargo run --example windows_recovery_probe -- fixtures <directory>"
    );
    process::exit(64);
}

fn run() -> Result<(), String> {
    let mut args = env::args().skip(1);
    let command = args.next().unwrap_or_else(|| usage());
    let path = args.next().unwrap_or_else(|| usage());
    if args.next().is_some() {
        usage();
    }

    match command.as_str() {
        "inspect" => {
            let analysis = analyze_backup_path(&path)?;
            emit(&harden_analysis(&path, analysis))
        }
        "plan" => emit(&build_guarded_recovery_plan(path)?),
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
