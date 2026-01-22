use anyhow::Result;
use phoenix_core::DeviceGraph;
use serde_json::Value;
use std::fs;
use std::path::{Path, PathBuf};
use uuid::Uuid;

pub struct ReportPaths {
    pub run_id: String,
    pub root: PathBuf,
    pub device_graph_json: PathBuf,
    pub run_json: PathBuf,
    pub logs_path: PathBuf,
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
    let run_id = Uuid::new_v4().to_string();
    let root = base.as_ref().join("reports").join(&run_id);
    fs::create_dir_all(&root)?;

    let device_graph_json = root.join("device_graph.json");
    let run_json = root.join("run.json");
    let logs_path = root.join("logs.txt");

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

    Ok(ReportPaths {
        run_id,
        root,
        device_graph_json,
        run_json,
        logs_path,
    })
}
