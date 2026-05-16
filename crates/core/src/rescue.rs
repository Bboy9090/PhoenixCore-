use anyhow::{Context, Result};
use serde::{Deserialize, Serialize};
use std::process::Command;

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct DeviceState {
    pub udid: String,
    pub mode: DeviceMode,
    pub product_type: String,
    pub product_version: String,
}

#[derive(Debug, Serialize, Deserialize, Clone, PartialEq)]
pub enum DeviceMode {
    Normal,
    Recovery,
    Dfu,
    Unknown,
}

pub struct RescueService;

impl RescueService {
    pub fn detect_devices() -> Result<Vec<DeviceState>> {
        let mut devices = Vec::new();
        if let Ok(output) = Command::new("idevice_id").arg("-l").output() {
            let udids = String::from_utf8_lossy(&output.stdout);
            for udid in udids.lines() {
                if !udid.is_empty() {
                    if let Ok(info) = Self::get_device_info(udid) {
                        devices.push(info);
                    }
                }
            }
        }
        if let Ok(output) = Command::new("irecovery").arg("-l").output() {
            let list = String::from_utf8_lossy(&output.stdout);
            for line in list.lines() {
                if line.contains("CPID") {
                    devices.push(DeviceState {
                        udid: "RECOVERY_DEVICE".to_string(),
                        mode: DeviceMode::Recovery,
                        product_type: "Unknown".to_string(),
                        product_version: "Unknown".to_string(),
                    });
                }
            }
        }
        Ok(devices)
    }

    fn get_device_info(udid: &str) -> Result<DeviceState> {
        let output = Command::new("ideviceinfo")
            .arg("-u")
            .arg(udid)
            .arg("-s")
            .output()
            .with_context(|| "Failed to execute ideviceinfo")?;
        let info_str = String::from_utf8_lossy(&output.stdout);
        let mut product_type = "Unknown".to_string();
        let mut product_version = "Unknown".to_string();
        for line in info_str.lines() {
            if line.starts_with("ProductType:") {
                product_type = line.split(':').nth(1).unwrap_or("").trim().to_string();
            } else if line.starts_with("ProductVersion:") {
                product_version = line.split(':').nth(1).unwrap_or("").trim().to_string();
            }
        }
        Ok(DeviceState {
            udid: udid.to_string(),
            mode: DeviceMode::Normal,
            product_type,
            product_version,
        })
    }

    pub fn exit_recovery() -> Result<()> {
        let status = Command::new("irecovery").arg("-n").status()?;
        if status.success() {
            Ok(())
        } else {
            Err(anyhow::anyhow!("irecovery failed"))
        }
    }
}
