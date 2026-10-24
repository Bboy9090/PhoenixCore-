#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use std::{fs, path::PathBuf};

const SMOKE_RECEIPT_ENV: &str = "PHOENIXCORE_DESKTOP_SMOKE_RECEIPT";

fn smoke_mode_requested() -> bool {
    std::env::args().skip(1).any(|arg| arg == "--smoke-test")
}

fn run_smoke_mode() -> Result<(), String> {
    let path = std::env::var_os(SMOKE_RECEIPT_ENV)
        .filter(|value| !value.is_empty())
        .map(PathBuf::from)
        .ok_or_else(|| format!("{SMOKE_RECEIPT_ENV} is required for --smoke-test"))?;

    if let Some(parent) = path.parent().filter(|p| !p.as_os_str().is_empty()) {
        fs::create_dir_all(parent)
            .map_err(|error| format!("cannot create smoke receipt directory: {error}"))?;
    }

    let source_commit = option_env!("PHOENIXCORE_DESKTOP_SOURCE_COMMIT").unwrap_or("unrecorded");
    let payload = format!(
        "{{\n  \"schema_version\": \"bws.phoenixcore-desktop-installed-smoke/v1\",\n  \"app_id\": \"phoenixcore-desktop\",\n  \"product_name\": \"PhoenixCore Desktop\",\n  \"version\": \"{}\",\n  \"source_commit\": \"{}\",\n  \"target_os\": \"{}\",\n  \"target_arch\": \"{}\",\n  \"process_id\": {},\n  \"mode\": \"installed-executable-smoke\",\n  \"dashboard_bundle\": \"embedded-tauri-dist\",\n  \"vite_dev_api_bridge\": \"not-claimed-in-packaged-mode\",\n  \"status\": \"pass\"\n}}\n",
        env!("CARGO_PKG_VERSION"),
        source_commit,
        std::env::consts::OS,
        std::env::consts::ARCH,
        std::process::id()
    );

    fs::write(&path, payload)
        .map_err(|error| format!("cannot write installed smoke receipt: {error}"))?;
    Ok(())
}

fn main() {
    if smoke_mode_requested() {
        match run_smoke_mode() {
            Ok(()) => return,
            Err(error) => {
                eprintln!("PHOENIXCORE_DESKTOP_SMOKE_FAIL {error}");
                std::process::exit(2);
            }
        }
    }

    tauri::Builder::default()
        .run(tauri::generate_context!())
        .expect("error while running PhoenixCore Desktop");
}
