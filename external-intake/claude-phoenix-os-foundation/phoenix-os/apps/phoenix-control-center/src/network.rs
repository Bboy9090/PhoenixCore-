// Phoenix OS — Phoenix Control Center: Network Module
// File: apps/phoenix-control-center/src/network.rs
//
// Network interface enumeration and status reporting.
// Read-only — does not modify network configuration.

use serde::{Deserialize, Serialize};
use std::process::Command;

#[derive(Debug, Serialize, Deserialize)]
pub struct NetworkInterface {
    pub name:         String,
    pub kind:         InterfaceKind,
    pub state:        InterfaceState,
    pub mac_address:  Option<String>,
    pub ipv4:         Vec<String>,
    pub ipv6:         Vec<String>,
    pub rx_bytes:     u64,
    pub tx_bytes:     u64,
    pub speed_mbps:   Option<u32>,
}

#[derive(Debug, Serialize, Deserialize)]
pub enum InterfaceKind {
    Ethernet,
    Wifi,
    Loopback,
    Virtual,
    Unknown,
}

#[derive(Debug, Serialize, Deserialize, PartialEq)]
pub enum InterfaceState {
    Up,
    Down,
    Unknown,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct NetworkStatus {
    pub interfaces:     Vec<NetworkInterface>,
    pub default_route:  Option<String>,
    pub dns_servers:    Vec<String>,
    pub internet_reachable: bool,
}

/// List all network interfaces and their status.
#[tauri::command]
pub fn get_network_interfaces() -> Result<Vec<NetworkInterface>, String> {
    let mut interfaces = Vec::new();

    let net_path = std::path::Path::new("/sys/class/net");
    let entries = std::fs::read_dir(net_path)
        .map_err(|e| format!("Cannot read /sys/class/net: {}", e))?;

    for entry in entries.flatten() {
        let iface_name = entry.file_name().to_string_lossy().to_string();
        let iface_path = entry.path();

        let kind = classify_interface(&iface_name, &iface_path);
        let state = read_iface_state(&iface_path);
        let mac_address = read_sysfs_string(&iface_path.join("address"));
        let (rx_bytes, tx_bytes) = read_iface_stats(&iface_name);
        let speed_mbps = read_sysfs_u32(&iface_path.join("speed"));

        let (ipv4, ipv6) = read_iface_addresses(&iface_name);

        interfaces.push(NetworkInterface {
            name: iface_name,
            kind,
            state,
            mac_address,
            ipv4,
            ipv6,
            rx_bytes,
            tx_bytes,
            speed_mbps,
        });
    }

    // Sort: ethernet first, then wifi, then others, loopback last
    interfaces.sort_by_key(|i| match i.kind {
        InterfaceKind::Ethernet  => 0,
        InterfaceKind::Wifi      => 1,
        InterfaceKind::Virtual   => 2,
        InterfaceKind::Unknown   => 3,
        InterfaceKind::Loopback  => 4,
    });

    Ok(interfaces)
}

/// Get overall network status including routing and internet reachability.
#[tauri::command]
pub fn get_network_status() -> Result<NetworkStatus, String> {
    let interfaces = get_network_interfaces()?;

    // Default route
    let default_route = read_default_route();

    // DNS servers from /etc/resolv.conf
    let dns_servers = read_dns_servers();

    // Quick internet reachability check (non-blocking ping)
    let internet_reachable = check_internet_reachable();

    Ok(NetworkStatus {
        interfaces,
        default_route,
        dns_servers,
        internet_reachable,
    })
}

// ---- Helpers ----

fn classify_interface(name: &str, path: &std::path::Path) -> InterfaceKind {
    if name == "lo" {
        return InterfaceKind::Loopback;
    }
    // Check if wireless: /sys/class/net/<name>/wireless exists
    if path.join("wireless").exists() || path.join("phy80211").exists() {
        return InterfaceKind::Wifi;
    }
    // Check if virtual (no device link or device is virtual)
    let dev_link = path.join("device");
    if !dev_link.exists() {
        return InterfaceKind::Virtual;
    }
    // Ethernet-like names
    if name.starts_with("eth") || name.starts_with("en") || name.starts_with("eno") {
        return InterfaceKind::Ethernet;
    }
    InterfaceKind::Unknown
}

fn read_iface_state(path: &std::path::Path) -> InterfaceState {
    match std::fs::read_to_string(path.join("operstate"))
        .map(|s| s.trim().to_string())
        .as_deref()
    {
        Ok("up")      => InterfaceState::Up,
        Ok("down")    => InterfaceState::Down,
        _             => InterfaceState::Unknown,
    }
}

fn read_sysfs_string(path: &std::path::Path) -> Option<String> {
    std::fs::read_to_string(path)
        .ok()
        .map(|s| s.trim().to_string())
        .filter(|s| !s.is_empty() && s != "00:00:00:00:00:00")
}

fn read_sysfs_u32(path: &std::path::Path) -> Option<u32> {
    std::fs::read_to_string(path)
        .ok()
        .and_then(|s| s.trim().parse().ok())
}

fn read_iface_stats(name: &str) -> (u64, u64) {
    let rx = std::fs::read_to_string(
        format!("/sys/class/net/{}/statistics/rx_bytes", name)
    )
    .ok()
    .and_then(|s| s.trim().parse().ok())
    .unwrap_or(0);

    let tx = std::fs::read_to_string(
        format!("/sys/class/net/{}/statistics/tx_bytes", name)
    )
    .ok()
    .and_then(|s| s.trim().parse().ok())
    .unwrap_or(0);

    (rx, tx)
}

fn read_iface_addresses(name: &str) -> (Vec<String>, Vec<String>) {
    let output = Command::new("ip")
        .args(["addr", "show", name])
        .output()
        .unwrap_or_default();

    let text = String::from_utf8_lossy(&output.stdout);
    let mut ipv4 = Vec::new();
    let mut ipv6 = Vec::new();

    for line in text.lines() {
        let line = line.trim();
        if line.starts_with("inet ") {
            if let Some(addr) = line.split_whitespace().nth(1) {
                ipv4.push(addr.to_string());
            }
        } else if line.starts_with("inet6 ") {
            if let Some(addr) = line.split_whitespace().nth(1) {
                // Skip link-local unless it's the only address
                if !addr.starts_with("fe80") {
                    ipv6.push(addr.to_string());
                }
            }
        }
    }

    (ipv4, ipv6)
}

fn read_default_route() -> Option<String> {
    let output = Command::new("ip")
        .args(["route", "show", "default"])
        .output()
        .ok()?;
    let text = String::from_utf8_lossy(&output.stdout);
    text.lines().next().map(|l| l.trim().to_string())
}

fn read_dns_servers() -> Vec<String> {
    std::fs::read_to_string("/etc/resolv.conf")
        .unwrap_or_default()
        .lines()
        .filter(|l| l.starts_with("nameserver"))
        .filter_map(|l| l.split_whitespace().nth(1).map(String::from))
        .collect()
}

fn check_internet_reachable() -> bool {
    // One ICMP ping to 1.1.1.1 with 1s timeout
    Command::new("ping")
        .args(["-c", "1", "-W", "1", "1.1.1.1"])
        .output()
        .map(|o| o.status.success())
        .unwrap_or(false)
}
