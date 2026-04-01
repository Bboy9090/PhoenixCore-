pub mod windows;
pub mod macos;
pub mod linux;

use serde::{Deserialize, Serialize};

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct Drive {
  pub id: String,        // Windows: \\.\PHYSICALDRIVE1  |  macOS: /dev/disk2  |  Linux: /dev/sdb
  pub name: String,      // Friendly name
  pub size_gb: u64,      // Rounded GB
  pub vendor: Option<String>,
}

fn bytes_to_gb(b: u64) -> u64 {
  if b == 0 { return 0; }
  (b as f64 / 1_073_741_824.0).round() as u64
}

pub fn list_removable_drives() -> Result<Vec<Drive>, String> {
  #[cfg(target_os = "windows")]
  { windows::list().map_err(|e| e.to_string()) }

  #[cfg(target_os = "macos")]
  { macos::list().map_err(|e| e.to_string()) }

  #[cfg(target_os = "linux")]
  { linux::list().map_err(|e| e.to_string()) }

  #[cfg(not(any(target_os="windows", target_os="macos", target_os="linux")))]
  { Ok(vec![]) }
}