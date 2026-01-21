use anyhow::{anyhow, Context, Result};
use phoenix_core::{DeviceGraph, Disk, HostInfo, Partition};

#[cfg(windows)]
mod windows_impl {
    use super::*;
    use std::env;
    use windows::core::BSTR;
    use windows::Win32::System::Com::{
        CoCreateInstance, CoInitializeEx, CoInitializeSecurity, CoSetProxyBlanket,
        CoUninitialize, VariantClear, CLSCTX_INPROC_SERVER, COINIT_MULTITHREADED,
        EOAC_NONE, RPC_C_AUTHN_LEVEL_CALL, RPC_C_AUTHN_LEVEL_DEFAULT, RPC_C_AUTHN_WINNT,
        RPC_C_AUTHZ_NONE, RPC_C_IMP_LEVEL_IMPERSONATE, RPC_E_TOO_LATE, VARIANT, VT_BSTR,
        VT_BOOL, VT_EMPTY, VT_I4, VT_I8, VT_NULL, VT_UI4, VT_UI8,
    };
    use windows::Win32::System::Wmi::{
        CLSID_WbemLocator, IEnumWbemClassObject, IWbemClassObject, IWbemLocator,
        IWbemServices, WBEM_FLAG_FORWARD_ONLY, WBEM_FLAG_RETURN_IMMEDIATELY,
        WBEM_INFINITE,
    };

    struct ComGuard;

    impl Drop for ComGuard {
        fn drop(&mut self) {
            unsafe { CoUninitialize() };
        }
    }

    pub fn build_device_graph() -> Result<DeviceGraph> {
        let (_com, services) = init_wmi()?;
        let host = query_host_info(&services)?;
        let system_drive_root = system_drive_root();
        let disks = query_disks(&services, system_drive_root.as_deref())?;
        Ok(DeviceGraph::new(host, disks))
    }

    fn system_drive_root() -> Option<String> {
        env::var("SystemDrive").ok().map(|drive| {
            if drive.ends_with('\\') {
                drive
            } else {
                format!("{}\\", drive)
            }
        })
    }

    fn init_wmi() -> Result<(ComGuard, IWbemServices)> {
        unsafe {
            CoInitializeEx(None, COINIT_MULTITHREADED).context("initialize COM")?;

            let guard = ComGuard;
            if let Err(error) = CoInitializeSecurity(
                None,
                -1,
                None,
                None,
                RPC_C_AUTHN_LEVEL_DEFAULT,
                RPC_C_IMP_LEVEL_IMPERSONATE,
                None,
                EOAC_NONE,
                None,
            ) {
                if error.code() != RPC_E_TOO_LATE {
                    return Err(error.into());
                }
            }

            let locator: IWbemLocator =
                CoCreateInstance(&CLSID_WbemLocator, None, CLSCTX_INPROC_SERVER)
                    .context("create WMI locator")?;
            let services = locator
                .ConnectServer(
                    &BSTR::from("ROOT\\CIMV2"),
                    &BSTR::new(),
                    &BSTR::new(),
                    &BSTR::new(),
                    0,
                    &BSTR::new(),
                    None,
                )
                .context("connect to ROOT\\CIMV2")?;

            CoSetProxyBlanket(
                &services,
                RPC_C_AUTHN_WINNT,
                RPC_C_AUTHZ_NONE,
                None,
                RPC_C_AUTHN_LEVEL_CALL,
                RPC_C_IMP_LEVEL_IMPERSONATE,
                None,
                EOAC_NONE,
            )
            .context("set WMI proxy blanket")?;

            Ok((guard, services))
        }
    }

    fn query_host_info(services: &IWbemServices) -> Result<HostInfo> {
        let os_info = exec_query(services, "SELECT Caption, Version FROM Win32_OperatingSystem")?;
        let os_version = os_info
            .get(0)
            .and_then(|obj| {
                let caption = get_property_string(obj, "Caption").ok().flatten();
                let version = get_property_string(obj, "Version").ok().flatten();
                match (caption, version) {
                    (Some(caption), Some(version)) => Some(format!("{} ({})", caption, version)),
                    (Some(caption), None) => Some(caption),
                    (None, Some(version)) => Some(version),
                    _ => None,
                }
            })
            .unwrap_or_else(|| "unknown".to_string());

        let sys_info =
            exec_query(services, "SELECT Name, Manufacturer, Model FROM Win32_ComputerSystem")?;
        let machine = sys_info
            .get(0)
            .and_then(|obj| {
                let name = get_property_string(obj, "Name").ok().flatten();
                let manufacturer = get_property_string(obj, "Manufacturer").ok().flatten();
                let model = get_property_string(obj, "Model").ok().flatten();
                match (manufacturer, model, name) {
                    (Some(manufacturer), Some(model), _) => {
                        Some(format!("{} {}", manufacturer, model))
                    }
                    (Some(manufacturer), None, Some(name)) => {
                        Some(format!("{} {}", manufacturer, name))
                    }
                    (_, _, Some(name)) => Some(name),
                    _ => None,
                }
            })
            .unwrap_or_else(|| "unknown".to_string());

        Ok(HostInfo {
            os: "windows".to_string(),
            os_version,
            machine,
        })
    }

    fn query_disks(
        services: &IWbemServices,
        system_drive_root: Option<&str>,
    ) -> Result<Vec<Disk>> {
        let disks = exec_query(
            services,
            "SELECT DeviceID, Model, Size, RemovableMedia, MediaType FROM Win32_DiskDrive",
        )?;

        let mut results = Vec::new();
        for disk in disks {
            let device_id = get_property_string(&disk, "DeviceID")
                .context("read disk DeviceID")?
                .unwrap_or_else(|| "unknown".to_string());
            let model = get_property_string(&disk, "Model")
                .ok()
                .flatten()
                .unwrap_or_else(|| device_id.clone());
            let size_bytes = get_property_u64(&disk, "Size")
                .ok()
                .flatten()
                .unwrap_or(0);
            let removable_media = get_property_bool(&disk, "RemovableMedia")
                .ok()
                .flatten()
                .unwrap_or(false);
            let media_type = get_property_string(&disk, "MediaType")
                .ok()
                .flatten()
                .unwrap_or_default();

            let partitions = query_partitions_for_disk(services, &device_id)?;
            let is_system_disk = system_drive_root
                .map(|root| {
                    partitions.iter().any(|partition| {
                        partition
                            .mount_points
                            .iter()
                            .any(|mount| mount.eq_ignore_ascii_case(root))
                    })
                })
                .unwrap_or(false);

            results.push(Disk {
                id: device_id,
                friendly_name: model,
                size_bytes,
                is_system_disk,
                removable: removable_media || media_type.to_lowercase().contains("removable"),
                partitions,
            });
        }

        Ok(results)
    }

    fn query_partitions_for_disk(
        services: &IWbemServices,
        disk_device_id: &str,
    ) -> Result<Vec<Partition>> {
        let query = format!(
            "ASSOCIATORS OF {{Win32_DiskDrive.DeviceID='{}'}} WHERE AssocClass=Win32_DiskDriveToDiskPartition",
            escape_wmi_string(disk_device_id)
        );
        let partitions = exec_query(services, &query)?;

        let mut results = Vec::new();
        for partition in partitions {
            let partition_id = get_property_string(&partition, "DeviceID")
                .ok()
                .flatten()
                .unwrap_or_else(|| "unknown".to_string());
            let size_bytes = get_property_u64(&partition, "Size")
                .ok()
                .flatten()
                .unwrap_or(0);

            let logical_disks = query_logical_disks_for_partition(services, &partition_id)?;
            let mut mount_points = Vec::new();
            let mut label = None;
            let mut fs = None;
            for logical in logical_disks {
                if let Some(device_id) = get_property_string(&logical, "DeviceID").ok().flatten() {
                    mount_points.push(format!("{}\\", device_id));
                }
                if label.is_none() {
                    label = get_property_string(&logical, "VolumeName").ok().flatten();
                }
                if fs.is_none() {
                    fs = get_property_string(&logical, "FileSystem").ok().flatten();
                }
            }

            results.push(Partition {
                id: partition_id,
                label,
                fs,
                size_bytes,
                mount_points,
            });
        }

        Ok(results)
    }

    fn query_logical_disks_for_partition(
        services: &IWbemServices,
        partition_id: &str,
    ) -> Result<Vec<IWbemClassObject>> {
        let query = format!(
            "ASSOCIATORS OF {{Win32_DiskPartition.DeviceID='{}'}} WHERE AssocClass=Win32_LogicalDiskToPartition",
            escape_wmi_string(partition_id)
        );
        exec_query(services, &query)
    }

    fn exec_query(services: &IWbemServices, query: &str) -> Result<Vec<IWbemClassObject>> {
        let enumerator: IEnumWbemClassObject = unsafe {
            services.ExecQuery(
                &BSTR::from("WQL"),
                &BSTR::from(query),
                (WBEM_FLAG_FORWARD_ONLY | WBEM_FLAG_RETURN_IMMEDIATELY) as i32,
                None,
            )
        }
        .with_context(|| format!("exec WMI query: {}", query))?;

        let mut results = Vec::new();
        loop {
            let mut object = None;
            let mut returned = 0;
            unsafe {
                enumerator
                    .Next(WBEM_INFINITE as i32, 1, &mut object, &mut returned)
                    .context("iterate WMI query")?;
            }
            if returned == 0 {
                break;
            }
            if let Some(object) = object {
                results.push(object);
            }
        }

        Ok(results)
    }

    fn get_property_string(obj: &IWbemClassObject, name: &str) -> Result<Option<String>> {
        unsafe {
            let mut value = VARIANT::default();
            obj.Get(
                &BSTR::from(name),
                0,
                &mut value,
                std::ptr::null_mut(),
                std::ptr::null_mut(),
            )
            .with_context(|| format!("read WMI property {}", name))?;

            let result = variant_to_string(&value);
            VariantClear(&mut value).ok();
            Ok(result)
        }
    }

    fn get_property_u64(obj: &IWbemClassObject, name: &str) -> Result<Option<u64>> {
        unsafe {
            let mut value = VARIANT::default();
            obj.Get(
                &BSTR::from(name),
                0,
                &mut value,
                std::ptr::null_mut(),
                std::ptr::null_mut(),
            )
            .with_context(|| format!("read WMI property {}", name))?;

            let result = variant_to_u64(&value);
            VariantClear(&mut value).ok();
            Ok(result)
        }
    }

    fn get_property_bool(obj: &IWbemClassObject, name: &str) -> Result<Option<bool>> {
        unsafe {
            let mut value = VARIANT::default();
            obj.Get(
                &BSTR::from(name),
                0,
                &mut value,
                std::ptr::null_mut(),
                std::ptr::null_mut(),
            )
            .with_context(|| format!("read WMI property {}", name))?;

            let result = variant_to_bool(&value);
            VariantClear(&mut value).ok();
            Ok(result)
        }
    }

    fn escape_wmi_string(value: &str) -> String {
        value.replace('\\', "\\\\").replace('\'', "''")
    }

    unsafe fn variant_to_string(variant: &VARIANT) -> Option<String> {
        match variant.Anonymous.Anonymous.vt {
            VT_BSTR => {
                let value = variant.Anonymous.Anonymous.Anonymous.bstrVal;
                value.to_string().ok()
            }
            VT_NULL | VT_EMPTY => None,
            VT_I4 => Some(variant.Anonymous.Anonymous.Anonymous.lVal.to_string()),
            VT_I8 => Some(variant.Anonymous.Anonymous.Anonymous.llVal.to_string()),
            VT_UI4 => Some(variant.Anonymous.Anonymous.Anonymous.ulVal.to_string()),
            VT_UI8 => Some(variant.Anonymous.Anonymous.Anonymous.ullVal.to_string()),
            VT_BOOL => Some(if variant.Anonymous.Anonymous.Anonymous.boolVal.0 != 0 {
                "true"
            } else {
                "false"
            }
            .to_string()),
            _ => None,
        }
    }

    unsafe fn variant_to_u64(variant: &VARIANT) -> Option<u64> {
        match variant.Anonymous.Anonymous.vt {
            VT_UI8 => Some(variant.Anonymous.Anonymous.Anonymous.ullVal as u64),
            VT_I8 => Some(variant.Anonymous.Anonymous.Anonymous.llVal as u64),
            VT_UI4 => Some(variant.Anonymous.Anonymous.Anonymous.ulVal as u64),
            VT_I4 => Some(variant.Anonymous.Anonymous.Anonymous.lVal as u64),
            VT_BSTR => variant_to_string(variant).and_then(|value| value.parse().ok()),
            _ => None,
        }
    }

    unsafe fn variant_to_bool(variant: &VARIANT) -> Option<bool> {
        match variant.Anonymous.Anonymous.vt {
            VT_BOOL => Some(variant.Anonymous.Anonymous.Anonymous.boolVal.0 != 0),
            VT_BSTR => variant_to_string(variant)
                .map(|value| value.eq_ignore_ascii_case("true") || value == "1"),
            _ => None,
        }
    }
}

#[cfg(windows)]
pub fn build_device_graph() -> Result<DeviceGraph> {
    windows_impl::build_device_graph()
}

#[cfg(not(windows))]
pub fn build_device_graph() -> Result<DeviceGraph> {
    Err(anyhow!("phoenix-host-windows requires Windows"))
}