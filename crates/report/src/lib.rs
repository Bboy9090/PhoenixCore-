use anyhow::Result;
use phoenix_core::DeviceGraph;
use std::fs;
use std::path::{Path, PathBuf};
use uuid::Uuid;

pub struct ReportPaths {
    pub run_id: String,
    pub root: PathBuf,
    pub device_graph_json: PathBuf,
    pub run_json: PathBuf,
}

pub fn create_report_bundle(base: impl AsRef<Path>, graph: &DeviceGraph) -> Result<ReportPaths> {
    let run_id = Uuid::new_v4().to_string();
    let root = base.as_ref().join("reports").join(&run_id);
    fs::create_dir_all(&root)?;

    let device_graph_json = root.join("device_graph.json");
    let run_json = root.join("run.json");

    fs::write(&device_graph_json, serde_json::to_vec_pretty(graph)?)?;

    let meta = serde_json::json!({
        "run_id": run_id,
        "schema_version": graph.schema_version,
        "generated_at_utc": graph.generated_at_utc,
        "host": graph.host,
        "disk_count": graph.disks.len()
    });
    fs::write(&run_json, serde_json::to_vec_pretty(&meta)?)?;

    Ok(ReportPaths {
        run_id,
        root,
        device_graph_json,
        run_json,
    })
}
