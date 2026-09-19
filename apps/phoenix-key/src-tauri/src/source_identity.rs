use crate::windows_recovery_guard::build_guarded_recovery_plan;
use serde::Serialize;
use serde_json::Value;
use sha2::{Digest, Sha256};
use std::{
    collections::VecDeque,
    fs::{self, File},
    io::Read,
    path::Path,
    time::UNIX_EPOCH,
};

const MAX_MANIFEST_ENTRIES: usize = 1024;
const MAX_MANIFEST_DEPTH: usize = 8;

#[derive(Debug, Clone, Serialize, PartialEq, Eq)]
pub struct RecoverySourceIdentity {
    pub schema: &'static str,
    pub path: String,
    pub canonical_path: String,
    pub source_kind: &'static str,
    pub size_bytes: u64,
    pub modified_unix_seconds: Option<u64>,
    pub sha256: String,
    pub entry_count: usize,
    pub complete: bool,
    pub scan_limited: bool,
}

#[derive(Debug, Clone, Serialize, PartialEq, Eq)]
pub struct SourceIdentityVerification {
    pub schema: &'static str,
    pub expected_sha256: String,
    pub observed_sha256: String,
    pub matches: bool,
    pub reanalysis_required: bool,
}

fn metadata_is_link_or_reparse(metadata: &fs::Metadata) -> bool {
    if metadata.file_type().is_symlink() {
        return true;
    }
    #[cfg(windows)]
    {
        use std::os::windows::fs::MetadataExt;
        const FILE_ATTRIBUTE_REPARSE_POINT: u32 = 0x0400;
        metadata.file_attributes() & FILE_ATTRIBUTE_REPARSE_POINT != 0
    }
    #[cfg(not(windows))]
    {
        false
    }
}

fn modified_seconds(metadata: &fs::Metadata) -> Option<u64> {
    metadata
        .modified()
        .ok()?
        .duration_since(UNIX_EPOCH)
        .ok()
        .map(|duration| duration.as_secs())
}

fn hash_file(path: &Path) -> Result<(String, u64), String> {
    let mut file = File::open(path)
        .map_err(|error| format!("cannot open recovery source for hashing: {error}"))?;
    let mut hasher = Sha256::new();
    let mut buffer = [0u8; 1024 * 1024];
    let mut total = 0u64;
    loop {
        let count = file
            .read(&mut buffer)
            .map_err(|error| format!("cannot hash recovery source: {error}"))?;
        if count == 0 {
            break;
        }
        hasher.update(&buffer[..count]);
        total = total.saturating_add(count as u64);
    }
    Ok((format!("{:x}", hasher.finalize()), total))
}

fn canonical_string(path: &Path) -> Result<String, String> {
    fs::canonicalize(path)
        .map(|value| value.to_string_lossy().to_string())
        .map_err(|error| format!("cannot canonicalize recovery source: {error}"))
}

fn directory_identity(path: &Path) -> Result<RecoverySourceIdentity, String> {
    let canonical_path = canonical_string(path)?;
    let mut queue = VecDeque::from([(path.to_path_buf(), 0usize)]);
    let mut entries: Vec<(String, u64, Option<u64>, String)> = Vec::new();
    let mut total_size = 0u64;
    let mut scan_limited = false;

    while let Some((directory, depth)) = queue.pop_front() {
        if depth > MAX_MANIFEST_DEPTH || entries.len() >= MAX_MANIFEST_ENTRIES {
            scan_limited = true;
            break;
        }
        let read_dir = fs::read_dir(&directory)
            .map_err(|error| format!("cannot read recovery source directory: {error}"))?;
        for entry in read_dir {
            let entry = entry.map_err(|error| format!("cannot read recovery source entry: {error}"))?;
            let child = entry.path();
            let metadata = fs::symlink_metadata(&child)
                .map_err(|error| format!("cannot inspect recovery source entry: {error}"))?;
            if metadata_is_link_or_reparse(&metadata) {
                return Err("recovery source identity refuses symbolic-link entries".to_string());
            }
            if metadata.is_dir() {
                if depth < MAX_MANIFEST_DEPTH {
                    queue.push_back((child, depth + 1));
                } else {
                    scan_limited = true;
                }
                continue;
            }
            if !metadata.is_file() {
                return Err(
                    "recovery source identity refuses non-regular filesystem entries".to_string(),
                );
            }
            if entries.len() >= MAX_MANIFEST_ENTRIES {
                scan_limited = true;
                break;
            }
            let relative = child
                .strip_prefix(path)
                .unwrap_or(&child)
                .to_string_lossy()
                .replace('\\', "/");
            let (digest, size) = hash_file(&child)?;
            total_size = total_size.saturating_add(size);
            entries.push((relative, size, modified_seconds(&metadata), digest));
        }
    }

    entries.sort_by(|left, right| left.0.cmp(&right.0));
    let mut manifest = Sha256::new();
    for (relative, size, modified, digest) in &entries {
        manifest.update(relative.as_bytes());
        manifest.update([0]);
        manifest.update(size.to_le_bytes());
        manifest.update(modified.unwrap_or_default().to_le_bytes());
        manifest.update(digest.as_bytes());
        manifest.update([0xff]);
    }

    let root_meta = fs::metadata(path)
        .map_err(|error| format!("cannot inspect recovery source directory: {error}"))?;
    Ok(RecoverySourceIdentity {
        schema: "phoenix_key.recovery_source_identity.v1",
        path: path.to_string_lossy().to_string(),
        canonical_path,
        source_kind: "directory_manifest",
        size_bytes: total_size,
        modified_unix_seconds: modified_seconds(&root_meta),
        sha256: format!("{:x}", manifest.finalize()),
        entry_count: entries.len(),
        complete: !scan_limited,
        scan_limited,
    })
}

pub fn capture_source_identity(path: impl AsRef<Path>) -> Result<RecoverySourceIdentity, String> {
    let path = path.as_ref();
    let metadata = fs::symlink_metadata(path)
        .map_err(|error| format!("cannot inspect recovery source identity: {error}"))?;
    if metadata_is_link_or_reparse(&metadata) {
        return Err("recovery source identity refuses symbolic-link sources".to_string());
    }
    if metadata.is_file() {
        let canonical_path = canonical_string(path)?;
        let (sha256, size_bytes) = hash_file(path)?;
        return Ok(RecoverySourceIdentity {
            schema: "phoenix_key.recovery_source_identity.v1",
            path: path.to_string_lossy().to_string(),
            canonical_path,
            source_kind: "file_sha256",
            size_bytes,
            modified_unix_seconds: modified_seconds(&metadata),
            sha256,
            entry_count: 1,
            complete: true,
            scan_limited: false,
        });
    }
    if metadata.is_dir() {
        return directory_identity(path);
    }
    Err("recovery source identity supports only regular files and directories".to_string())
}

pub fn build_identity_bound_recovery_plan(path: impl AsRef<Path>) -> Result<Value, String> {
    let path = path.as_ref();
    let identity_before = capture_source_identity(path)?;
    if !identity_before.complete {
        return Err(
            "recovery source identity manifest exceeded its bounded scan and is not complete"
                .to_string(),
        );
    }
    let plan = build_guarded_recovery_plan(path)?;
    let identity_after = capture_source_identity(path)?;
    if identity_before != identity_after {
        return Err(
            "recovery source changed while the plan was being built; re-analysis is required"
                .to_string(),
        );
    }
    let mut value = serde_json::to_value(plan)
        .map_err(|error| format!("cannot serialize recovery plan: {error}"))?;
    let object = value
        .as_object_mut()
        .ok_or_else(|| "recovery plan did not serialize as an object".to_string())?;
    object.insert(
        "source_identity".to_string(),
        serde_json::to_value(identity_after)
            .map_err(|error| format!("cannot serialize recovery source identity: {error}"))?,
    );
    object.insert(
        "source_identity_gate".to_string(),
        Value::String("recheck_immediately_before_any_mutation".to_string()),
    );
    Ok(value)
}

pub fn verify_source_identity(
    path: impl AsRef<Path>,
    expected_sha256: &str,
) -> Result<SourceIdentityVerification, String> {
    let observed = capture_source_identity(path)?;
    let matches = observed.complete && observed.sha256.eq_ignore_ascii_case(expected_sha256.trim());
    Ok(SourceIdentityVerification {
        schema: "phoenix_key.recovery_source_identity_verification.v1",
        expected_sha256: expected_sha256.trim().to_ascii_lowercase(),
        observed_sha256: observed.sha256,
        matches,
        reanalysis_required: !matches,
    })
}

#[cfg(test)]
mod tests {
    use super::{build_identity_bound_recovery_plan, capture_source_identity, verify_source_identity};
    use std::{fs, path::PathBuf};

    fn temp_case(name: &str) -> PathBuf {
        let path = std::env::temp_dir().join(format!(
            "phoenix-key-source-identity-{name}-{}",
            std::process::id()
        ));
        let _ = fs::remove_dir_all(&path);
        fs::create_dir_all(&path).unwrap();
        path
    }

    #[cfg(unix)]
    #[test]
    fn directory_identity_rejects_nested_symlink_entries() {
        use std::os::unix::fs::symlink;

        let root = temp_case("nested-symlink");
        let outside = temp_case("nested-symlink-outside");
        fs::write(outside.join("payload.bin"), b"outside").unwrap();
        symlink(&outside, root.join("escape")).unwrap();

        let error = capture_source_identity(&root).unwrap_err();
        assert!(error.contains("symbolic-link") || error.contains("reparse"));
        fs::remove_dir_all(root).unwrap();
        fs::remove_dir_all(outside).unwrap();
    }

    #[test]
    fn file_identity_changes_when_source_changes() {
        let root = temp_case("file-change");
        let source = root.join("source.bin");
        fs::write(&source, b"alpha").unwrap();
        let before = capture_source_identity(&source).unwrap();
        fs::write(&source, b"beta").unwrap();
        let after = capture_source_identity(&source).unwrap();
        assert_ne!(before.sha256, after.sha256);
        fs::remove_dir_all(root).unwrap();
    }

    #[test]
    fn directory_manifest_changes_when_member_changes() {
        let root = temp_case("dir-change");
        fs::write(root.join("one.txt"), b"one").unwrap();
        fs::write(root.join("two.txt"), b"two").unwrap();
        let before = capture_source_identity(&root).unwrap();
        fs::write(root.join("two.txt"), b"changed").unwrap();
        let after = capture_source_identity(&root).unwrap();
        assert_ne!(before.sha256, after.sha256);
        fs::remove_dir_all(root).unwrap();
    }

    #[test]
    fn stale_expected_digest_requires_reanalysis() {
        let root = temp_case("stale");
        let source = root.join("source.bin");
        fs::write(&source, b"first").unwrap();
        let identity = capture_source_identity(&source).unwrap();
        fs::write(&source, b"second").unwrap();
        let verification = verify_source_identity(&source, &identity.sha256).unwrap();
        assert!(!verification.matches);
        assert!(verification.reanalysis_required);
        fs::remove_dir_all(root).unwrap();
    }

    #[test]
    fn guarded_plan_contains_source_identity() {
        let root = temp_case("plan");
        let source = root.join("fake.wim");
        fs::write(&source, b"MSWIM\0\0\0fixture").unwrap();
        let plan = build_identity_bound_recovery_plan(&source).unwrap();
        assert_eq!(plan["source_identity"]["source_kind"], "file_sha256");
        assert_eq!(
            plan["source_identity_gate"],
            "recheck_immediately_before_any_mutation"
        );
        fs::remove_dir_all(root).unwrap();
    }
}
