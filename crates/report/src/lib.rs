use anyhow::{Context, Result};
use phoenix_core::DeviceGraph;
use serde::{Deserialize, Serialize};
use std::fs;
use std::path::{Path, PathBuf};
use time::format_description::well_known::Rfc3339;
use time::OffsetDateTime;
use uuid::Uuid;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RunReport {
    pub run_id: String,
    pub generated_at_utc: String,
    pub notes: Option<String>,
}

impl RunReport {
    pub fn new() -> Self {
        Self {
            run_id: Uuid::new_v4().to_string(),
            generated_at_utc: now_utc_rfc3339(),
            notes: None,
        }
    }
}

pub fn write_report(
    output_dir: &Path,
    device_graph: &DeviceGraph,
    run: &RunReport,
) -> Result<PathBuf> {
    let run_dir = output_dir.join(&run.run_id);
    fs::create_dir_all(&run_dir)
        .with_context(|| format!("create report dir {}", run_dir.display()))?;

    let graph_path = run_dir.join("device_graph.json");
    let graph_json = serde_json::to_vec_pretty(device_graph).context("serialize device graph")?;
    fs::write(&graph_path, graph_json)
        .with_context(|| format!("write {}", graph_path.display()))?;

    let run_path = run_dir.join("run.json");
    let run_json = serde_json::to_vec_pretty(run).context("serialize run report")?;
    fs::write(&run_path, run_json).with_context(|| format!("write {}", run_path.display()))?;

    Ok(run_dir)
}

fn now_utc_rfc3339() -> String {
    OffsetDateTime::now_utc()
        .format(&Rfc3339)
        .unwrap_or_else(|_| "unknown".to_string())
}
