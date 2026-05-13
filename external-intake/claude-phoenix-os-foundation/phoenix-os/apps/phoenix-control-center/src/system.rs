// Phoenix OS — Phoenix Control Center: System Module
// File: apps/phoenix-control-center/src/system.rs
//
// Re-exports and system-level helpers used across the backend.
// Extended system commands (services, boot entries) live here.

use serde::{Deserialize, Serialize};
use std::process::Command;

#[derive(Debug, Serialize, Deserialize)]
pub struct SystemdService {
    pub name:        String,
    pub description: String,
    pub state:       ServiceState,
    pub enabled:     bool,
}

#[derive(Debug, Serialize, Deserialize, PartialEq)]
pub enum ServiceState {
    Active,
    Inactive,
    Failed,
    Unknown,
}

/// List systemd services relevant to Phoenix OS workflows.
/// Returns only a curated set — not all 200+ units.
#[tauri::command]
pub fn list_relevant_services() -> Result<Vec<SystemdService>, String> {
    // Services that matter for repair and recovery workflows
    let relevant = [
        "NetworkManager",
        "bluetooth",
        "cups",
        "fwupd",
        "smartd",
        "udisks2",
        "ufw",
        "ssh",
        "avahi-daemon",
    ];

    let mut services = Vec::new();

    for name in &relevant {
        let state = query_service_state(name);
        let enabled = query_service_enabled(name);

        // Get description from systemctl show
        let description = Command::new("systemctl")
            .args(["show", name, "--property=Description", "--value"])
            .output()
            .ok()
            .map(|o| String::from_utf8_lossy(&o.stdout).trim().to_string())
            .unwrap_or_else(|| name.to_string());

        services.push(SystemdService {
            name: name.to_string(),
            description,
            state,
            enabled,
        });
    }

    Ok(services)
}

fn query_service_state(name: &str) -> ServiceState {
    let output = Command::new("systemctl")
        .args(["is-active", name])
        .output()
        .unwrap_or_default();

    match String::from_utf8_lossy(&output.stdout).trim() {
        "active"   => ServiceState::Active,
        "inactive" => ServiceState::Inactive,
        "failed"   => ServiceState::Failed,
        _          => ServiceState::Unknown,
    }
}

fn query_service_enabled(name: &str) -> bool {
    Command::new("systemctl")
        .args(["is-enabled", name])
        .output()
        .map(|o| String::from_utf8_lossy(&o.stdout).trim() == "enabled")
        .unwrap_or(false)
}
