use anyhow::{anyhow, Result};
use phoenix_core::DeviceGraph;
use serde_json::Value;
use sha2::{Digest, Sha256};
use std::fs;
use std::io::Write;
use std::path::{Path, PathBuf};
use uuid::Uuid;
use zip::write::FileOptions;
use zip::ZipWriter;

pub struct ReportPaths {
    pub run_id: String,
    pub root: PathBuf,
    pub device_graph_json: PathBuf,
    pub run_json: PathBuf,
    pub logs_path: PathBuf,
    pub manifest_path: PathBuf,
    pub signature_path: Option<PathBuf>,
}

#[derive(Debug, Clone)]
pub struct ReportArtifact {
    pub name: String,
    pub bytes: Vec<u8>,
}

pub fn create_report_bundle(base: impl AsRef<Path>, graph: &DeviceGraph) -> Result<ReportPaths> {
    create_report_bundle_with_meta(base, graph, None, None)
}

pub fn create_report_bundle_with_meta(
    base: impl AsRef<Path>,
    graph: &DeviceGraph,
    extra_meta: Option<Value>,
    logs: Option<&str>,
) -> Result<ReportPaths> {
    create_report_bundle_with_meta_and_signing(base, graph, extra_meta, logs, None)
}

pub fn create_report_bundle_with_meta_and_signing(
    base: impl AsRef<Path>,
    graph: &DeviceGraph,
    extra_meta: Option<Value>,
    logs: Option<&str>,
    signing_key_hex: Option<&str>,
) -> Result<ReportPaths> {
    create_report_bundle_with_meta_signing_and_artifacts(
        base,
        graph,
        extra_meta,
        logs,
        signing_key_hex,
        &[],
    )
}

pub fn create_report_bundle_with_meta_signing_and_artifacts(
    base: impl AsRef<Path>,
    graph: &DeviceGraph,
    extra_meta: Option<Value>,
    logs: Option<&str>,
    signing_key_hex: Option<&str>,
    artifacts: &[ReportArtifact],
) -> Result<ReportPaths> {
    let run_id = Uuid::new_v4().to_string();
    let root = base.as_ref().join("reports").join(&run_id);
    fs::create_dir_all(&root)?;

    let device_graph_json = root.join("device_graph.json");
    let run_json = root.join("run.json");
    let logs_path = root.join("logs.txt");
    let manifest_path = root.join("manifest.json");
    let mut signature_path = None;

    fs::write(&device_graph_json, serde_json::to_vec_pretty(graph)?)?;

    let mut meta = serde_json::json!({
        "run_id": run_id,
        "schema_version": graph.schema_version,
        "generated_at_utc": graph.generated_at_utc,
        "host": graph.host,
        "disk_count": graph.disks.len()
    });
    if let Some(extra) = extra_meta {
        match (&mut meta, extra) {
            (Value::Object(base), Value::Object(extra)) => {
                base.extend(extra);
            }
            (Value::Object(base), other) => {
                base.insert("extra".to_string(), other);
            }
            _ => {}
        }
    }
    fs::write(&run_json, serde_json::to_vec_pretty(&meta)?)?;
    fs::write(&logs_path, logs.unwrap_or_default())?;

    let mut artifact_paths = Vec::new();
    for artifact in artifacts {
        if artifact.name.contains('/') || artifact.name.contains('\\') {
            return Err(anyhow!("artifact name must be a filename only"));
        }
        let path = root.join(&artifact.name);
        fs::write(&path, &artifact.bytes)?;
        artifact_paths.push(path);
    }

    let manifest = build_manifest(
        &run_id,
        &device_graph_json,
        &run_json,
        &logs_path,
        &artifact_paths,
    )?;
    let manifest_bytes = serde_json::to_vec_pretty(&manifest)?;
    fs::write(&manifest_path, &manifest_bytes)?;

    if let Some(key_hex) = signing_key_hex {
        let key = decode_hex(key_hex)?;
        let signature = hmac_sha256(&key, &manifest_bytes);
        let sig_path = root.join("manifest.sig");
        fs::write(&sig_path, to_hex(&signature))?;
        signature_path = Some(sig_path);
    }

    Ok(ReportPaths {
        run_id,
        root,
        device_graph_json,
        run_json,
        logs_path,
        manifest_path,
        signature_path,
    })
}

#[derive(serde::Serialize, serde::Deserialize, Debug, Clone)]
pub struct ManifestEntry {
    path: String,
    bytes: u64,
    sha256: String,
}

#[derive(serde::Serialize, serde::Deserialize, Debug, Clone)]
pub struct Manifest {
    run_id: String,
    entries: Vec<ManifestEntry>,
}

#[derive(Debug)]
pub struct ReportVerification {
    pub ok: bool,
    pub entries_checked: usize,
    pub mismatches: Vec<String>,
    pub signature_valid: Option<bool>,
}

fn build_manifest(
    run_id: &str,
    device_graph: &Path,
    run_json: &Path,
    logs: &Path,
    artifacts: &[PathBuf],
) -> Result<Manifest> {
    let mut entries = Vec::new();
    for path in [device_graph, run_json, logs] {
        let data = fs::read(path)?;
        let hash = Sha256::digest(&data);
        entries.push(ManifestEntry {
            path: path.file_name().unwrap_or_default().to_string_lossy().to_string(),
            bytes: data.len() as u64,
            sha256: to_hex(&hash),
        });
    }
    for path in artifacts {
        let data = fs::read(path)?;
        let hash = Sha256::digest(&data);
        entries.push(ManifestEntry {
            path: path.file_name().unwrap_or_default().to_string_lossy().to_string(),
            bytes: data.len() as u64,
            sha256: to_hex(&hash),
        });
    }
    Ok(Manifest {
        run_id: run_id.to_string(),
        entries,
    })
}

fn decode_hex(value: &str) -> Result<Vec<u8>> {
    let value = value.trim();
    if value.len() % 2 != 0 {
        return Err(anyhow!("signing key hex must be even length"));
    }
    let raw = value.as_bytes();
    let mut bytes = Vec::with_capacity(raw.len() / 2);
    for idx in (0..raw.len()).step_by(2) {
        let hex = std::str::from_utf8(&raw[idx..idx + 2]).map_err(|_| anyhow!("invalid hex"))?;
        let byte = u8::from_str_radix(hex, 16).map_err(|_| anyhow!("invalid hex"))?;
        bytes.push(byte);
    }
    Ok(bytes)
}

fn hmac_sha256(key: &[u8], message: &[u8]) -> [u8; 32] {
    let mut key_block = [0u8; 64];
    if key.len() > key_block.len() {
        let hash = Sha256::digest(key);
        key_block[..hash.len()].copy_from_slice(&hash);
    } else {
        key_block[..key.len()].copy_from_slice(key);
    }

    let mut o_key = [0u8; 64];
    let mut i_key = [0u8; 64];
    for i in 0..64 {
        o_key[i] = key_block[i] ^ 0x5c;
        i_key[i] = key_block[i] ^ 0x36;
    }

    let mut inner = Sha256::new();
    inner.update(&i_key);
    inner.update(message);
    let inner_hash = inner.finalize();

    let mut outer = Sha256::new();
    outer.update(&o_key);
    outer.update(inner_hash);
    let digest = outer.finalize();

    let mut out = [0u8; 32];
    out.copy_from_slice(&digest);
    out
}

fn to_hex(bytes: &[u8]) -> String {
    let mut out = String::with_capacity(bytes.len() * 2);
    for byte in bytes {
        out.push_str(&format!("{:02x}", byte));
    }
    out
}

pub fn verify_report_bundle(
    report_root: impl AsRef<Path>,
    signing_key_hex: Option<&str>,
) -> Result<ReportVerification> {
    let root = report_root.as_ref();
    let manifest_path = root.join("manifest.json");
    if !manifest_path.exists() {
        return Err(anyhow!("manifest.json not found"));
    }

    let manifest_bytes = fs::read(&manifest_path)?;
    let manifest: Manifest = serde_json::from_slice(&manifest_bytes)?;

    let mut mismatches = Vec::new();
    let mut entries_checked = 0usize;
    for entry in &manifest.entries {
        let path = root.join(&entry.path);
        if !path.exists() {
            mismatches.push(format!("missing {}", entry.path));
            continue;
        }
        let data = fs::read(&path)?;
        let hash = Sha256::digest(&data);
        let sha = to_hex(&hash);
        if sha != entry.sha256 {
            mismatches.push(format!("hash mismatch {}", entry.path));
        }
        if data.len() as u64 != entry.bytes {
            mismatches.push(format!("size mismatch {}", entry.path));
        }
        entries_checked += 1;
    }

    let sig_path = root.join("manifest.sig");
    let signature_valid = if sig_path.exists() {
        let key_hex = signing_key_hex.ok_or_else(|| anyhow!("signing key required"))?;
        let key = decode_hex(key_hex)?;
        let expected = hmac_sha256(&key, &manifest_bytes);
        let actual = fs::read_to_string(&sig_path)?;
        Some(actual.trim().eq_ignore_ascii_case(&to_hex(&expected)))
    } else {
        None
    };

    let ok = mismatches.is_empty() && signature_valid.unwrap_or(true);
    Ok(ReportVerification {
        ok,
        entries_checked,
        mismatches,
        signature_valid,
    })
}

pub fn export_report_zip(
    report_root: impl AsRef<Path>,
    output_path: impl AsRef<Path>,
) -> Result<PathBuf> {
    let root = report_root.as_ref();
    let output_path = output_path.as_ref().to_path_buf();
    let file = fs::File::create(&output_path)?;
    let mut zip = ZipWriter::new(file);
    let options = FileOptions::default();
    add_dir_to_zip(root, root, &mut zip, options)?;
    zip.finish()?;
    Ok(output_path)
}

fn add_dir_to_zip(
    base: &Path,
    current: &Path,
    zip: &mut ZipWriter<fs::File>,
    options: FileOptions,
) -> Result<()> {
    for entry in fs::read_dir(current)? {
        let entry = entry?;
        let path = entry.path();
        let meta = entry.metadata()?;
        if meta.is_dir() {
            add_dir_to_zip(base, &path, zip, options)?;
        } else if meta.is_file() {
            let rel = path
                .strip_prefix(base)
                .unwrap_or(&path)
                .to_string_lossy()
                .replace('\\', "/");
            zip.start_file(rel, options)?;
            let data = fs::read(&path)?;
            zip.write_all(&data)?;
        }
    }
    Ok(())
}
