use crate::windows_recovery::{
    build_recovery_plan, WindowsBackupAnalysis, WindowsRecoveryPlan,
};
use std::{
    fs::{self, File},
    io::{Read, Seek, SeekFrom},
    path::{Path, PathBuf},
};

const WIM_HEADER_SIZE: u64 = 0xD0;
const VHDX_MIN_STRUCTURAL_SIZE: u64 = 1024 * 1024;
const VHD_FOOTER_SIZE: u64 = 512;

fn push_warning(analysis: &mut WindowsBackupAnalysis, warning: impl Into<String>) {
    let warning = warning.into();
    if !analysis.warnings.contains(&warning) {
        analysis.warnings.push(warning);
    }
}

fn read_exact_at(path: &Path, offset: u64, len: usize) -> Result<Vec<u8>, String> {
    let mut file = File::open(path).map_err(|error| format!("cannot open source: {error}"))?;
    file.seek(SeekFrom::Start(offset))
        .map_err(|error| format!("cannot seek source: {error}"))?;
    let mut buf = vec![0; len];
    file.read_exact(&mut buf)
        .map_err(|error| format!("cannot read source structure: {error}"))?;
    Ok(buf)
}

fn valid_wim_structure(path: &Path) -> bool {
    let Ok(meta) = path.metadata() else { return false; };
    if meta.len() < WIM_HEADER_SIZE {
        return false;
    }
    let Ok(header) = read_exact_at(path, 0, WIM_HEADER_SIZE as usize) else {
        return false;
    };
    if !header.starts_with(b"MSWIM\0\0\0") {
        return false;
    }
    let header_size = u32::from_le_bytes([header[8], header[9], header[10], header[11]]) as u64;
    header_size == WIM_HEADER_SIZE
}

fn valid_vhdx_structure(path: &Path) -> bool {
    let Ok(meta) = path.metadata() else { return false; };
    if meta.len() < VHDX_MIN_STRUCTURAL_SIZE {
        return false;
    }
    let Ok(identifier) = read_exact_at(path, 0, 8) else { return false; };
    let Ok(header1) = read_exact_at(path, 64 * 1024, 4) else { return false; };
    let Ok(header2) = read_exact_at(path, 128 * 1024, 4) else { return false; };
    identifier == b"vhdxfile" && header1 == b"head" && header2 == b"head"
}

fn vhd_checksum_valid(block: &[u8], checksum_offset: usize) -> bool {
    if checksum_offset + 4 > block.len() {
        return false;
    }
    let stored = u32::from_be_bytes([
        block[checksum_offset],
        block[checksum_offset + 1],
        block[checksum_offset + 2],
        block[checksum_offset + 3],
    ]);
    let sum = block
        .iter()
        .enumerate()
        .filter(|(index, _)| !(*index >= checksum_offset && *index < checksum_offset + 4))
        .fold(0_u32, |total, (_, byte)| total.wrapping_add(*byte as u32));
    stored == !sum
}

fn be_u32(block: &[u8], offset: usize) -> Option<u32> {
    let bytes: [u8; 4] = block.get(offset..offset + 4)?.try_into().ok()?;
    Some(u32::from_be_bytes(bytes))
}

fn be_u64(block: &[u8], offset: usize) -> Option<u64> {
    let bytes: [u8; 8] = block.get(offset..offset + 8)?.try_into().ok()?;
    Some(u64::from_be_bytes(bytes))
}

fn valid_vhd_structure(path: &Path) -> bool {
    let Ok(meta) = path.metadata() else { return false; };
    if meta.len() < VHD_FOOTER_SIZE {
        return false;
    }
    let Ok(footer) = read_exact_at(
        path,
        meta.len() - VHD_FOOTER_SIZE,
        VHD_FOOTER_SIZE as usize,
    ) else {
        return false;
    };
    if !footer.starts_with(b"conectix") || !vhd_checksum_valid(&footer, 64) {
        return false;
    }
    if be_u32(&footer, 12) != Some(0x0001_0000) || be_u64(&footer, 48).unwrap_or(0) == 0 {
        return false;
    }

    match be_u32(&footer, 60) {
        Some(2) => true,
        Some(3 | 4) => {
            let Some(header_offset) = be_u64(&footer, 16) else {
                return false;
            };
            if header_offset == u64::MAX {
                return false;
            }
            match header_offset.checked_add(1024) {
                Some(end) if end <= meta.len() => {}
                _ => return false,
            }
            let Ok(header) = read_exact_at(path, header_offset, 1024) else {
                return false;
            };
            if !header.starts_with(b"cxsparse") || !vhd_checksum_valid(&header, 36) {
                return false;
            }
            let table_offset = be_u64(&header, 16).unwrap_or(0);
            let header_version = be_u32(&header, 24);
            let max_table_entries = be_u32(&header, 28).unwrap_or(0);
            let block_size = be_u32(&header, 32).unwrap_or(0);
            header_version == Some(0x0001_0000)
                && table_offset >= header_offset + 1024
                && table_offset < meta.len()
                && max_table_entries > 0
                && block_size >= 512
                && block_size.is_power_of_two()
        }
        _ => false,
    }
}

fn valid_iso_structure(path: &Path) -> bool {
    let Ok(meta) = path.metadata() else { return false; };
    if meta.len() < 0x8006 {
        return false;
    }
    read_exact_at(path, 0x8001, 5)
        .map(|sig| sig == b"CD001")
        .unwrap_or(false)
}

fn split_wim_files(root: &Path) -> Vec<PathBuf> {
    let sources = if root.join("sources").is_dir() {
        root.join("sources")
    } else {
        root.join("Sources")
    };
    let Ok(entries) = fs::read_dir(sources) else { return Vec::new(); };
    let mut files: Vec<PathBuf> = entries
        .filter_map(Result::ok)
        .map(|entry| entry.path())
        .filter(|path| {
            path.extension()
                .and_then(|ext| ext.to_str())
                .is_some_and(|ext| ext.eq_ignore_ascii_case("swm"))
        })
        .collect();
    files.sort();
    files
}

fn validate_directory(path: &Path, analysis: &mut WindowsBackupAnalysis) {
    if analysis.has_split_wim && !analysis.has_install_wim && !analysis.has_install_esd {
        let swm_files = split_wim_files(path);
        let structurally_valid = swm_files.len() >= 2 && swm_files.iter().all(|file| valid_wim_structure(file));
        if !structurally_valid {
            analysis.restore_candidate = false;
            analysis.kind = "split_wim_set_incomplete_or_invalid".to_string();
            analysis.confidence = "low".to_string();
            analysis.user_summary = "Split Windows image files were found, but the set is incomplete or structurally invalid.".to_string();
            analysis.recommended_action = "Select the folder containing the complete SWM set and verify every segment before planning recovery.".to_string();
            push_warning(
                analysis,
                "split WIM restore is blocked until at least two structurally valid SWM segments are present",
            );
        }
    }

    if analysis.kind == "windows_system_image_backup" {
        let valid_payloads = analysis
            .system_image_files
            .iter()
            .filter(|relative| {
                let file = path.join(relative);
                match file
                    .extension()
                    .and_then(|ext| ext.to_str())
                    .unwrap_or_default()
                    .to_ascii_lowercase()
                    .as_str()
                {
                    "vhdx" => valid_vhdx_structure(&file),
                    "vhd" => valid_vhd_structure(&file),
                    _ => false,
                }
            })
            .count();
        if valid_payloads == 0 {
            analysis.restore_candidate = false;
            analysis.kind = "windows_system_image_payload_unverified".to_string();
            analysis.confidence = "low".to_string();
            analysis.user_summary = "Windows system-image metadata was found, but its VHD/VHDX payload did not pass structural validation.".to_string();
            analysis.recommended_action = "Locate an intact VHD/VHDX payload or re-stage the backup before planning a restore.".to_string();
            push_warning(
                analysis,
                "system-image restore is blocked because no discovered VHD/VHDX payload passed structural validation",
            );
        }
    }
}

fn validate_file(path: &Path, analysis: &mut WindowsBackupAnalysis) {
    let valid = match analysis.kind.as_str() {
        "wim" | "esd" => valid_wim_structure(path),
        "vhdx" => valid_vhdx_structure(path),
        "vhd" => valid_vhd_structure(path),
        "iso" => valid_iso_structure(path),
        _ => true,
    };
    if !valid {
        let original_kind = analysis.kind.clone();
        analysis.restore_candidate = false;
        analysis.kind = format!("{original_kind}_structurally_invalid");
        analysis.confidence = "low".to_string();
        analysis.user_summary = format!(
            "The file resembles a {original_kind} source, but its required structure is missing or truncated."
        );
        analysis.recommended_action = "Use an intact source file and re-run analysis before planning recovery.".to_string();
        push_warning(
            analysis,
            format!("{original_kind} signature matched but structural validation failed"),
        );
    }
}

pub fn harden_analysis(path: impl AsRef<Path>, mut analysis: WindowsBackupAnalysis) -> WindowsBackupAnalysis {
    let path = path.as_ref();
    if path.is_file() {
        validate_file(path, &mut analysis);
    } else if path.is_dir() {
        validate_directory(path, &mut analysis);
    }
    analysis
}

pub fn build_guarded_recovery_plan(path: impl AsRef<Path>) -> Result<WindowsRecoveryPlan, String> {
    let path = path.as_ref();
    let mut plan = build_recovery_plan(path)?;
    plan.source = harden_analysis(path, plan.source);
    if !plan.source.restore_candidate {
        plan.allowed_operations.retain(|operation| {
            !matches!(
                operation.as_str(),
                "plan_recovery_media" | "plan_system_image_restore" | "plan_bootcamp_restore"
            )
        });
        if !plan
            .blocked_operations
            .contains(&"restore_source_not_verified".to_string())
        {
            plan.blocked_operations
                .push("restore_source_not_verified".to_string());
        }
        plan.next_steps
            .push("Re-analyze an intact, structurally valid source before any restore plan can proceed.".to_string());
    }
    Ok(plan)
}

#[cfg(test)]
mod tests {
    use super::{build_guarded_recovery_plan, harden_analysis, valid_vhd_structure};
    use crate::windows_recovery::analyze_backup_path;
    use std::fs;

    fn temp_case(name: &str) -> std::path::PathBuf {
        let path = std::env::temp_dir().join(format!(
            "phoenix-key-recovery-guard-{name}-{}",
            std::process::id()
        ));
        let _ = fs::remove_dir_all(&path);
        fs::create_dir_all(&path).unwrap();
        path
    }

    #[test]
    fn blocks_truncated_wim_even_when_signature_matches() {
        let root = temp_case("truncated-wim");
        let source = root.join("fake.wim");
        fs::write(&source, b"MSWIM\0\0\0fixture").unwrap();
        let analysis = analyze_backup_path(&source).unwrap();
        assert!(analysis.restore_candidate);
        let hardened = harden_analysis(&source, analysis);
        assert!(!hardened.restore_candidate);
        assert_eq!(hardened.kind, "wim_structurally_invalid");
        fs::remove_dir_all(root).unwrap();
    }

    #[test]
    fn blocks_single_segment_split_wim_directory() {
        let root = temp_case("single-swm");
        fs::create_dir_all(root.join("sources")).unwrap();
        fs::write(root.join("sources/install.swm"), b"MSWIM\0\0\0fixture").unwrap();
        let analysis = analyze_backup_path(&root).unwrap();
        assert!(analysis.has_split_wim);
        let hardened = harden_analysis(&root, analysis);
        assert!(!hardened.restore_candidate);
        assert_eq!(hardened.kind, "split_wim_set_incomplete_or_invalid");
        fs::remove_dir_all(root).unwrap();
    }

    #[test]
    fn blocks_fake_vhdx_inside_windows_image_backup() {
        let parent = temp_case("fake-system-image");
        let root = parent.join("WindowsImageBackup");
        let backup = root.join("PC").join("Backup 2026-09-17 010101");
        fs::create_dir_all(root.join("PC/Catalog")).unwrap();
        fs::create_dir_all(&backup).unwrap();
        fs::write(root.join("PC/MediaId.bin"), b"fixture").unwrap();
        fs::write(backup.join("BackupSpecs.xml"), b"fixture").unwrap();
        fs::write(backup.join("system.vhdx"), b"vhdxfilefixture").unwrap();
        let analysis = analyze_backup_path(&root).unwrap();
        assert!(analysis.restore_candidate);
        let hardened = harden_analysis(&root, analysis);
        assert!(!hardened.restore_candidate);
        assert_eq!(hardened.kind, "windows_system_image_payload_unverified");
        fs::remove_dir_all(parent).unwrap();
    }

    fn write_dynamic_vhd(path: &std::path::Path, corrupt_footer: bool, corrupt_header: bool) {
        let mut image = vec![0_u8; 4096];
        let mut header = vec![0_u8; 1024];
        header[0..8].copy_from_slice(b"cxsparse");
        header[8..16].copy_from_slice(&u64::MAX.to_be_bytes());
        header[16..24].copy_from_slice(&1536_u64.to_be_bytes());
        header[24..28].copy_from_slice(&0x0001_0000_u32.to_be_bytes());
        header[28..32].copy_from_slice(&1_u32.to_be_bytes());
        header[32..36].copy_from_slice(&(2_u32 * 1024 * 1024).to_be_bytes());
        let header_sum = header
            .iter()
            .enumerate()
            .filter(|(index, _)| !(*index >= 36 && *index < 40))
            .fold(0_u32, |total, (_, byte)| total.wrapping_add(*byte as u32));
        header[36..40].copy_from_slice(&(!header_sum).to_be_bytes());
        if corrupt_header {
            header[40] ^= 0x01;
        }
        image[512..1536].copy_from_slice(&header);

        let mut footer = vec![0_u8; 512];
        footer[0..8].copy_from_slice(b"conectix");
        footer[8..12].copy_from_slice(&2_u32.to_be_bytes());
        footer[12..16].copy_from_slice(&0x0001_0000_u32.to_be_bytes());
        footer[16..24].copy_from_slice(&512_u64.to_be_bytes());
        footer[40..48].copy_from_slice(&(2_u64 * 1024 * 1024).to_be_bytes());
        footer[48..56].copy_from_slice(&(2_u64 * 1024 * 1024).to_be_bytes());
        footer[60..64].copy_from_slice(&3_u32.to_be_bytes());
        let footer_sum = footer
            .iter()
            .enumerate()
            .filter(|(index, _)| !(*index >= 64 && *index < 68))
            .fold(0_u32, |total, (_, byte)| total.wrapping_add(*byte as u32));
        footer[64..68].copy_from_slice(&(!footer_sum).to_be_bytes());
        if corrupt_footer {
            footer[68] ^= 0x01;
        }
        image[3584..4096].copy_from_slice(&footer);
        fs::write(path, image).unwrap();
    }

    #[test]
    fn validates_dynamic_vhd_footer_and_sparse_header_checksums() {
        let root = temp_case("valid-dynamic-vhd");
        let source = root.join("valid.vhd");
        write_dynamic_vhd(&source, false, false);
        assert!(valid_vhd_structure(&source));
        fs::remove_dir_all(root).unwrap();
    }

    #[test]
    fn blocks_vhd_with_corrupt_footer_checksum() {
        let root = temp_case("bad-vhd-footer");
        let source = root.join("bad-footer.vhd");
        write_dynamic_vhd(&source, true, false);
        assert!(!valid_vhd_structure(&source));
        fs::remove_dir_all(root).unwrap();
    }

    #[test]
    fn blocks_vhd_with_corrupt_dynamic_header_checksum() {
        let root = temp_case("bad-vhd-header");
        let source = root.join("bad-header.vhd");
        write_dynamic_vhd(&source, false, true);
        assert!(!valid_vhd_structure(&source));
        fs::remove_dir_all(root).unwrap();
    }

    #[test]
    fn guarded_plan_removes_restore_routes_for_bad_source() {
        let root = temp_case("guarded-plan");
        let source = root.join("fake.wim");
        fs::write(&source, b"MSWIM\0\0\0fixture").unwrap();
        let plan = build_guarded_recovery_plan(&source).unwrap();
        assert!(!plan.source.restore_candidate);
        assert!(!plan.allowed_operations.contains(&"plan_recovery_media".to_string()));
        assert!(plan.blocked_operations.contains(&"restore_source_not_verified".to_string()));
        fs::remove_dir_all(root).unwrap();
    }
}
