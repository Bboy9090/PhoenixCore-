use super::{Drive};
use serde::Deserialize;
use std::process::Command;

#[derive(Debug, Deserialize)]
struct DiskRow {
  Number: u32,
  FriendlyName: Option<String>,
  Size: u64,
  BusType: Option<String>,
  IsBoot: bool,
  IsSystem: bool,
  IsRemovable: bool
}

pub fn list() -> Result<Vec<Drive>, String> {
  // Strict filter:
  // - Exclude boot/system disks always
  // - Include removable OR USB bus
  // - Return \\.\PHYSICALDRIVE{Number} as target id
  let ps = r#"
    $ErrorActionPreference="Stop";
    $disks = Get-Disk |
      Select-Object Number,FriendlyName,Size,BusType,IsBoot,IsSystem,IsRemovable;
    $disks | ConvertTo-Json -Depth 3
  "#;

  let out = Command::new("powershell")
    .args(["-NoProfile", "-Command", ps])
    .output()
    .map_err(|e| format!("PowerShell failed: {e}"))?;

  if !out.status.success() {
    return Err(String::from_utf8_lossy(&out.stderr).to_string());
  }

  let raw = String::from_utf8_lossy(&out.stdout).to_string();
  let mut rows: Vec<DiskRow> = if raw.trim_start().starts_with('[') {
    serde_json::from_str(&raw).map_err(|e| format!("JSON parse error: {e}"))?
  } else if raw.trim().is_empty() {
    vec![]
  } else {
    vec![serde_json::from_str(&raw).map_err(|e| format!("JSON parse error: {e}"))?]
  };

  // Filter in Rust (belt + suspenders)
  rows.retain(|d| {
    if d.IsBoot || d.IsSystem { return false; }
    let bus_usb = d.BusType.as_deref().unwrap_or("").eq_ignore_ascii_case("USB");
    d.IsRemovable || bus_usb
  });

  let drives = rows.into_iter().map(|d| {
    let name = d.FriendlyName.clone().unwrap_or_else(|| format!("Disk {}", d.Number));
    Drive {
      id: format!(r"\\.\PHYSICALDRIVE{}", d.Number),
      name,
      size_gb: super::bytes_to_gb(d.Size),
      vendor: d.BusType.clone()
    }
  }).collect();

  Ok(drives)
}