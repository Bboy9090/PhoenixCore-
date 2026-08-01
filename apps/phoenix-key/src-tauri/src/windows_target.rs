use serde::Serialize;

const PHYSICAL_DRIVE_MARKER: &str = "PHYSICALDRIVE";

#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
pub struct TargetResolution {
    pub requested_path: String,
    pub canonical_path: String,
    pub resolution_source: &'static str,
    pub target_kind: &'static str,
    pub canonicalized: bool,
}

impl TargetResolution {
    pub fn is_windows_physical_drive(&self) -> bool {
        self.target_kind == "windows_physical_drive"
    }
}

pub fn resolve_target(value: &str) -> Result<TargetResolution, String> {
    let requested_path = value.trim().replace('/', "\\");
    if requested_path.is_empty() {
        return Err("target_drive_empty".to_string());
    }

    let upper = requested_path.to_ascii_uppercase();
    let Some(marker_index) = upper.find(PHYSICAL_DRIVE_MARKER) else {
        return Ok(TargetResolution {
            canonical_path: requested_path.clone(),
            requested_path,
            resolution_source: "phoenix_key_bridge_passthrough",
            target_kind: "filesystem_or_volume_path",
            canonicalized: false,
        });
    };

    let prefix = &upper[..marker_index];
    let suffix = &upper[marker_index + PHYSICAL_DRIVE_MARKER.len()..];
    let prefix_without_slashes: String = prefix
        .chars()
        .filter(|character| *character != '\\')
        .collect();

    if !(prefix_without_slashes.is_empty() || prefix_without_slashes == ".") {
        return Err("invalid_windows_physicaldrive_prefix".to_string());
    }

    if suffix.is_empty() || !suffix.chars().all(|character| character.is_ascii_digit()) {
        return Err("invalid_windows_physicaldrive_suffix".to_string());
    }

    let disk_number = suffix
        .parse::<u32>()
        .map_err(|_| "invalid_windows_physicaldrive_number".to_string())?;
    let canonical_path = format!(r"\\.\PHYSICALDRIVE{disk_number}");
    let canonicalized = requested_path != canonical_path;

    Ok(TargetResolution {
        requested_path,
        canonical_path,
        resolution_source: "phoenix_key_bridge",
        target_kind: "windows_physical_drive",
        canonicalized,
    })
}

#[cfg(test)]
mod tests {
    use super::resolve_target;

    #[test]
    fn canonicalizes_standard_windows_physical_drive() {
        let resolution = resolve_target(r"\\.\PHYSICALDRIVE1").unwrap();
        assert_eq!(resolution.canonical_path, r"\\.\PHYSICALDRIVE1");
        assert!(!resolution.canonicalized);
        assert!(resolution.is_windows_physical_drive());
    }

    #[test]
    fn canonicalizes_plain_physical_drive() {
        let resolution = resolve_target("PHYSICALDRIVE1").unwrap();
        assert_eq!(resolution.canonical_path, r"\\.\PHYSICALDRIVE1");
        assert!(resolution.canonicalized);
    }

    #[test]
    fn canonicalizes_lowercase_physical_drive() {
        let resolution = resolve_target("physicaldrive1").unwrap();
        assert_eq!(resolution.canonical_path, r"\\.\PHYSICALDRIVE1");
        assert!(resolution.canonicalized);
    }

    #[test]
    fn canonicalizes_over_escaped_physical_drive() {
        let resolution = resolve_target(r"\\\\.\\PHYSICALDRIVE1").unwrap();
        assert_eq!(resolution.canonical_path, r"\\.\PHYSICALDRIVE1");
        assert!(resolution.canonicalized);
    }

    #[test]
    fn canonicalizes_forward_slash_physical_drive() {
        let resolution = resolve_target("//./physicaldrive1").unwrap();
        assert_eq!(resolution.canonical_path, r"\\.\PHYSICALDRIVE1");
        assert!(resolution.canonicalized);
    }

    #[test]
    fn removes_leading_zeroes_from_disk_number() {
        let resolution = resolve_target("PHYSICALDRIVE001").unwrap();
        assert_eq!(resolution.canonical_path, r"\\.\PHYSICALDRIVE1");
    }

    #[test]
    fn leaves_non_physical_drive_target_unchanged() {
        let resolution = resolve_target("E:\\").unwrap();
        assert_eq!(resolution.canonical_path, "E:\\");
        assert!(!resolution.canonicalized);
        assert!(!resolution.is_windows_physical_drive());
    }

    #[test]
    fn rejects_embedded_physical_drive_marker() {
        let error = resolve_target(r"C:\temp\PHYSICALDRIVE1").unwrap_err();
        assert_eq!(error, "invalid_windows_physicaldrive_prefix");
    }

    #[test]
    fn rejects_trailing_physical_drive_junk() {
        let error = resolve_target("PHYSICALDRIVE1.tmp").unwrap_err();
        assert_eq!(error, "invalid_windows_physicaldrive_suffix");
    }

    #[test]
    fn rejects_empty_target() {
        let error = resolve_target("   ").unwrap_err();
        assert_eq!(error, "target_drive_empty");
    }
}
