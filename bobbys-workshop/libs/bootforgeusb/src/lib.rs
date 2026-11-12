pub mod calibration;
pub mod calibration_backup;
pub mod edl;
pub mod firehose_plan;
pub mod firmware;
pub mod firmware_catalog;
pub mod firmware_manifest;
pub mod hardware_service;
pub mod model;
pub mod mtk_brom;
pub mod planner;
pub mod preflight;
pub mod recovery;
pub mod recovery_job;
pub mod retry_policy;
pub mod telemetry;
pub mod transport;
pub mod transfer_preflight;
pub mod stream_schedule;
pub mod read_benchmark;
pub mod phoenix_sanctum;
pub mod trapdoor;
pub mod workflow_catalog;

use model::DeviceRecord;
use rusb::{Context, UsbContext};
use thiserror::Error;

#[derive(Debug, Error)]
pub enum BootForgeUsbError {
    #[error("failed to initialize USB context: {0}")]
    Context(String),
    #[error("failed to enumerate USB devices: {0}")]
    Enumeration(String),
    #[error("trapdoor operation error: {0}")]
    Trapdoor(String),
}

pub type Result<T> = std::result::Result<T, BootForgeUsbError>;

fn inspect_interfaces<T: UsbContext>(device: &rusb::Device<T>) -> (bool, bool, bool, bool) {
    let mut has_adb = false;
    let mut has_fastboot = false;
    let mut has_mtp = false;
    let mut has_acm = false;

    if let Ok(config) = device.active_config_descriptor() {
        for iface in config.interfaces() {
            for desc in iface.descriptors() {
                let c = desc.class_code();
                let sc = desc.sub_class_code();
                let p = desc.protocol_code();
                if c == 0xff && sc == 0x42 && p == 0x01 {
                    has_adb = true;
                } else if c == 0xff && sc == 0x42 && p == 0x03 {
                    has_fastboot = true;
                } else if c == 0x06 && sc == 0x01 && p == 0x01 {
                    has_mtp = true;
                } else if c == 0x02 && sc == 0x02 {
                    has_acm = true;
                }
            }
        }
    }
    (has_adb, has_fastboot, has_mtp, has_acm)
}

fn platform_hint(
    vendor_id: u16,
    product_id: u16,
    product_name: Option<&str>,
    has_android_iface: bool,
) -> &'static str {
    if vendor_id == 0x05ac {
        return if (0x1200..=0x12ff).contains(&product_id) {
            "ios"
        } else {
            "apple-host-internal"
        };
    }
    match vendor_id {
        0x04e8 => "android-samsung",
        0x05c6 => "android-qualcomm",
        0x0e8d => "android-mediatek",
        0x1782 => "android-unisoc",
        0x18d1 => "android-google",
        0x22b8 => "android-motorola",
        0x2717 => "android-xiaomi",
        0x2a70 => "android-oneplus",
        0x22d9 => "android-oppo",
        0x2b4c => "android-vivo",
        0x0fce => "android-sony",
        0x1004 | 0x0489 => "android-lg",
        0x0b05 => "android-asus",
        0x12d1 => "android-huawei",
        0x17ef => "android-lenovo",
        0x19d2 => "android-zte",
        0x1bbb => "android-tcl-revvl",
        0x3317 => "android-transsion",
        0x2970 => "android-nothing",
        0x0bb4 => "android-htc",
        0x2e04 | 0x0421 => "android-nokia",
        _ => {
            if has_android_iface {
                return "android-generic";
            }
            if let Some(name) = product_name {
                let lower = name.to_ascii_lowercase();
                if lower.contains("revvl")
                    || lower.contains("android")
                    || lower.contains("galaxy")
                    || lower.contains("pixel")
                    || lower.contains("redmi")
                    || lower.contains("poco")
                    || lower.contains("oneplus")
                    || lower.contains("xperia")
                {
                    return "android-generic";
                }
            }
            "unknown"
        }
    }
}

fn mode_hint(
    vendor_id: u16,
    product_id: u16,
    class: u8,
    subclass: u8,
    protocol: u8,
) -> &'static str {
    if vendor_id == 0x05ac {
        return match product_id {
            0x1227 => "ios-dfu",
            0x1281 => "ios-recovery",
            0x1200..=0x12ff => "ios-normal",
            _ => "apple-host",
        };
    }
    if vendor_id == 0x04e8 && product_id == 0x6601 {
        return "samsung-download";
    }
    if vendor_id == 0x04e8 && product_id == 0x685d {
        return "samsung-usb";
    }
    if vendor_id == 0x05c6 && product_id == 0x9008 {
        return "qualcomm-edl";
    }
    if vendor_id == 0x0e8d && product_id == 0x0003 {
        return "mediatek-brom";
    }
    if vendor_id == 0x0e8d && matches!(product_id, 0x2000 | 0x2001) {
        return "mediatek-preloader";
    }
    if vendor_id == 0x1782 && product_id == 0x4d00 {
        return "unisoc-diag";
    }
    if class == 0x06 && subclass == 0x01 && protocol == 0x01 {
        return "ptp";
    }
    "usb"
}

fn read_strings<T: UsbContext>(
    device: &rusb::Device<T>,
) -> (Option<String>, Option<String>, Option<String>) {
    let descriptor = match device.device_descriptor() {
        Ok(d) => d,
        Err(_) => return (None, None, None),
    };
    let handle = match device.open() {
        Ok(h) => h,
        Err(_) => return (None, None, None),
    };
    let manufacturer = handle
        .read_manufacturer_string_ascii(&descriptor)
        .ok()
        .map(|v| v.trim_matches(char::from(0)).trim().to_string())
        .filter(|v| !v.is_empty());
    let product = handle
        .read_product_string_ascii(&descriptor)
        .ok()
        .map(|v| v.trim_matches(char::from(0)).trim().to_string())
        .filter(|v| !v.is_empty());
    let serial = handle
        .read_serial_number_string_ascii(&descriptor)
        .ok()
        .map(|v| v.trim_matches(char::from(0)).trim().to_string())
        .filter(|v| !v.is_empty());
    (manufacturer, product, serial)
}

pub fn scan() -> Result<Vec<DeviceRecord>> {
    let context = Context::new().map_err(|e| BootForgeUsbError::Context(e.to_string()))?;
    let devices = context
        .devices()
        .map_err(|e| BootForgeUsbError::Enumeration(e.to_string()))?;

    let mut records = Vec::new();
    for device in devices.iter() {
        let descriptor = match device.device_descriptor() {
            Ok(d) => d,
            Err(_) => continue,
        };
        let (manufacturer, product_name, serial_number) = read_strings(&device);
        let (has_adb, has_fastboot, has_mtp, has_acm) = inspect_interfaces(&device);
        let vendor_id = descriptor.vendor_id();
        let product_id = descriptor.product_id();
        let plat_hint = platform_hint(
            vendor_id,
            product_id,
            product_name.as_deref(),
            has_adb || has_fastboot || has_mtp,
        );
        let base_mode = mode_hint(
            vendor_id,
            product_id,
            descriptor.class_code(),
            descriptor.sub_class_code(),
            descriptor.protocol_code(),
        );
        let resolved_mode = if base_mode != "usb" {
            base_mode
        } else if has_fastboot {
            "fastboot"
        } else if has_adb {
            "adb"
        } else if has_mtp {
            "mtp-ptp"
        } else if has_acm {
            "serial-acm"
        } else {
            "usb"
        };

        let device_uid = serial_number
            .as_ref()
            .map(|serial| format!("usb:{:04x}:{:04x}:{}", vendor_id, product_id, serial))
            .unwrap_or_else(|| {
                format!(
                    "usb:{:04x}:{:04x}:bus{}:addr{}",
                    vendor_id,
                    product_id,
                    device.bus_number(),
                    device.address()
                )
            });

        records.push(DeviceRecord {
            device_uid,
            vendor_id,
            product_id,
            manufacturer,
            product_name,
            serial_number,
            class: descriptor.class_code(),
            subclass: descriptor.sub_class_code(),
            protocol: descriptor.protocol_code(),
            bus_number: device.bus_number(),
            device_address: device.address(),
            speed: format!("{:?}", device.speed()).to_ascii_lowercase(),
            platform_hint: plat_hint.to_string(),
            mode: resolved_mode.to_string(),
            transport: "usb".to_string(),
            evidence_source: "rusb-descriptor".to_string(),
        });
    }
    Ok(records)
}

#[cfg(test)]
mod mode_tests {
    use super::mode_hint;

    #[test]
    fn samsung_685d_descriptor_is_not_download_mode() {
        assert_eq!(mode_hint(0x04e8, 0x685d, 0x02, 0x02, 0x00), "samsung-usb");
    }

    #[test]
    fn samsung_6601_descriptor_is_download_mode() {
        assert_eq!(mode_hint(0x04e8, 0x6601, 0x00, 0x00, 0x00), "samsung-download");
    }
}

#[cfg(feature = "python")]
mod python_api {
    use super::*;
    use pyo3::{exceptions::PyRuntimeError, prelude::*};
    use std::collections::HashMap;

    #[pyclass]
    pub struct RawUsbController {
        device_id: String,
    }

    #[pymethods]
    impl RawUsbController {
        #[new]
        pub fn new(device_id: String) -> Self {
            Self { device_id }
        }

        pub fn bulk_write(&self, _data: Vec<u8>) -> PyResult<usize> {
            Err(PyRuntimeError::new_err(format!(
                "raw USB write is disabled for {} until endpoint discovery and hardware qualification are implemented",
                self.device_id
            )))
        }

        pub fn bulk_read(&self, _length: usize) -> PyResult<Vec<u8>> {
            Err(PyRuntimeError::new_err(format!(
                "raw USB read is disabled for {} until endpoint discovery and hardware qualification are implemented",
                self.device_id
            )))
        }

        pub fn control_transfer(
            &self,
            _rt: u8,
            _r: u8,
            _v: u16,
            _i: u16,
            _data: Vec<u8>,
        ) -> PyResult<bool> {
            Err(PyRuntimeError::new_err(format!(
                "raw USB control transfers are disabled for {} in BobFWTools",
                self.device_id
            )))
        }
    }

    #[pyclass]
    pub struct UsbMonitor;

    #[pymethods]
    impl UsbMonitor {
        #[new]
        pub fn new(_mock_mode: bool) -> Self {
            Self
        }

        pub fn poll_active_devices(&self) -> PyResult<Vec<HashMap<String, String>>> {
            let records = scan().map_err(|e| PyRuntimeError::new_err(e.to_string()))?;
            Ok(records
                .into_iter()
                .map(|d| {
                    let mut m = HashMap::new();
                    m.insert(
                        "name".into(),
                        d.product_name.unwrap_or_else(|| {
                            format!("USB {:04X}:{:04X}", d.vendor_id, d.product_id)
                        }),
                    );
                    m.insert("protocol".into(), d.mode);
                    m.insert(
                        "serial".into(),
                        d.serial_number
                            .unwrap_or_else(|| format!("{:04X}:{:04X}", d.vendor_id, d.product_id)),
                    );
                    m.insert("category".into(), d.platform_hint);
                    m
                })
                .collect())
        }
    }

    #[pymodule]
    fn bootforge_usb(_py: Python<'_>, m: &Bound<'_, PyModule>) -> PyResult<()> {
        m.add_class::<RawUsbController>()?;
        m.add_class::<UsbMonitor>()?;
        Ok(())
    }
}
