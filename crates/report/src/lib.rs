use anyhow::Result;
use bootforge_core::{now_utc_rfc3339, DeviceGraph, DEVICE_GRAPH_SCHEMA_VERSION};
use serde::Serialize;
use serde_json::Value;
use std::path::{Path, PathBuf};
use uuid::Uuid;

#[derive(Debug, Serialize)]
pub struct ReportPaths {
    pub run_id: String,
    pub root: PathBuf,
    pub device_graph_json: PathBuf,
    pub run_json: PathBuf,
    pub logs_path: PathBuf,
}

#[derive(Debug, Serialize)]
struct RunMetadata {
    run_id: String,
    created_at_utc: String,
    device_graph_schema_version: String,
    meta: Option<Value>,
}

pub fn create_report_bundle(
    base: impl AsRef<Path>,
    device_graph: &DeviceGraph,
    meta: Option<Value>,
    logs: Option<&str>,
) -> Result<ReportPaths> {
    let run_id = Uuid::new_v4().to_string();
    let base = base.as_ref();
    let root = base.join("reports").join(&run_id);
    std::fs::create_dir_all(&root)?;

    let device_graph_json = root.join("device_graph.json");
    let run_json = root.join("run.json");
    let logs_path = root.join("logs.txt");

    let graph_json = serde_json::to_string_pretty(device_graph)?;
    std::fs::write(&device_graph_json, graph_json)?;

    let run_meta = RunMetadata {
        run_id: run_id.clone(),
        created_at_utc: now_utc_rfc3339(),
        device_graph_schema_version: DEVICE_GRAPH_SCHEMA_VERSION.to_string(),
        meta,
    };
    let run_json_data = serde_json::to_string_pretty(&run_meta)?;
    std::fs::write(&run_json, run_json_data)?;

    let log_data = logs.unwrap_or("");
    std::fs::write(&logs_path, log_data)?;

    Ok(ReportPaths {
        run_id,
        root,
        device_graph_json,
        run_json,
        logs_path,
    })
}
