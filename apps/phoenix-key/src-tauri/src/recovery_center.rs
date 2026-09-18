use crate::source_identity::build_identity_bound_recovery_plan;
use crate::windows_recovery::{analyze_backup_path, WindowsBackupAnalysis};
use crate::windows_recovery_guard::harden_analysis;
use serde_json::Value;

fn require_source_path(source_path: String) -> Result<String, String> {
    let source_path = source_path.trim();
    if source_path.is_empty() {
        return Err(
            "Choose a Windows backup, recovery folder, ISO, WIM/ESD, or VHD/VHDX source first."
                .to_string(),
        );
    }
    Ok(source_path.to_string())
}

#[tauri::command]
pub fn analyze_windows_recovery_source(
    source_path: String,
) -> Result<WindowsBackupAnalysis, String> {
    let source_path = require_source_path(source_path)?;
    analyze_backup_path(&source_path)
        .map(|analysis| harden_analysis(&source_path, analysis))
        .map_err(|error| {
            format!(
                "Phoenix Key could not analyze that recovery source. Nothing was changed. {error}"
            )
        })
}

#[tauri::command]
pub fn plan_windows_recovery_source(source_path: String) -> Result<Value, String> {
    let source_path = require_source_path(source_path)?;
    build_identity_bound_recovery_plan(source_path).map_err(|error| {
        format!(
            "Phoenix Key could not build an identity-bound recovery plan. Nothing was changed. {error}"
        )
    })
}

#[cfg(test)]
mod tests {
    use super::{analyze_windows_recovery_source, plan_windows_recovery_source};
    use std::fs;

    fn temp_case(name: &str) -> std::path::PathBuf {
        let path = std::env::temp_dir().join(format!(
            "phoenix-key-recovery-center-{name}-{}",
            std::process::id()
        ));
        let _ = fs::remove_dir_all(&path);
        fs::create_dir_all(&path).unwrap();
        path
    }

    #[test]
    fn empty_source_is_explained_in_plain_language() {
        let error = analyze_windows_recovery_source("   ".to_string()).unwrap_err();
        assert!(error.starts_with("Choose a Windows backup"));
    }

    #[test]
    fn analysis_errors_confirm_nothing_changed() {
        let error = analyze_windows_recovery_source(
            "/this/path/does/not/exist/phoenix-key".to_string(),
        )
        .unwrap_err();
        assert!(error.contains("Nothing was changed"));
    }

    #[test]
    fn hostile_wim_is_blocked_in_product_boundary() {
        let root = temp_case("hostile-wim");
        let source = root.join("fixture.wim");
        fs::write(&source, b"MSWIM\0\0\0fixture").unwrap();
        let analysis = analyze_windows_recovery_source(source.to_string_lossy().to_string()).unwrap();
        assert!(!analysis.restore_candidate);
        assert_eq!(analysis.kind, "wim_structurally_invalid");
        fs::remove_dir_all(root).unwrap();
    }

    #[test]
    fn desktop_plan_is_identity_bound_and_read_only() {
        let root = temp_case("plan");
        let source = root.join("fixture.wim");
        fs::write(&source, b"MSWIM\0\0\0fixture").unwrap();
        let plan = plan_windows_recovery_source(source.to_string_lossy().to_string()).unwrap();
        assert_eq!(plan["dry_run"], true);
        assert_eq!(plan["destructive_actions_performed"], false);
        assert_eq!(plan["source"]["restore_candidate"], false);
        assert_eq!(
            plan["source_identity_gate"],
            "recheck_immediately_before_any_mutation"
        );
        assert_eq!(
            plan["source_identity"]["sha256"]
                .as_str()
                .map(str::len),
            Some(64)
        );
        fs::remove_dir_all(root).unwrap();
    }
}
