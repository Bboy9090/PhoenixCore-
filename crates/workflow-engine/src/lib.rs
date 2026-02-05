use anyhow::{anyhow, Result};
use bootforge_core::{DeviceGraph, WorkflowDefinition, WORKFLOW_SCHEMA_VERSION};
use bootforge_imaging::hash_file_readonly;
use bootforge_report::{create_report_bundle, ReportPaths};
use serde_json::{json, Value};
use std::collections::HashSet;
use std::path::{Path, PathBuf};

#[derive(Debug)]
pub struct WorkflowStepReport {
    pub step_id: String,
    pub report: ReportPaths,
}

#[derive(Debug)]
pub struct WorkflowRunResult {
    pub workflow: String,
    pub step_reports: Vec<WorkflowStepReport>,
}

pub fn load_workflow_definition(path: impl AsRef<Path>) -> Result<WorkflowDefinition> {
    let path = path.as_ref();
    let data = std::fs::read_to_string(path)?;
    let workflow: WorkflowDefinition = serde_json::from_str(&data)?;
    Ok(workflow)
}

pub fn validate_workflow_definition(def: &WorkflowDefinition) -> Result<()> {
    if def.schema_version != WORKFLOW_SCHEMA_VERSION {
        return Err(anyhow!(
            "unsupported workflow schema version {}",
            def.schema_version
        ));
    }
    if def.name.trim().is_empty() {
        return Err(anyhow!("workflow name is required"));
    }
    let mut seen = HashSet::new();
    for step in &def.steps {
        if step.id.trim().is_empty() {
            return Err(anyhow!("workflow step id is required"));
        }
        if !seen.insert(step.id.as_str()) {
            return Err(anyhow!("duplicate step id {}", step.id));
        }
        if step.action.trim().is_empty() {
            return Err(anyhow!("workflow step action is required"));
        }
    }
    Ok(())
}

pub fn run_workflow_definition(
    def: &WorkflowDefinition,
    default_report_base: impl AsRef<Path>,
) -> Result<WorkflowRunResult> {
    validate_workflow_definition(def)?;
    let mut step_reports = Vec::new();
    for step in &def.steps {
        let report = match step.action.as_str() {
            "disk_hash_report" => run_disk_hash_report(step, default_report_base.as_ref())?,
            action => return Err(anyhow!("unsupported workflow action {}", action)),
        };
        step_reports.push(WorkflowStepReport {
            step_id: step.id.clone(),
            report,
        });
    }
    Ok(WorkflowRunResult {
        workflow: def.name.clone(),
        step_reports,
    })
}

fn run_disk_hash_report(step: &bootforge_core::WorkflowStep, default_report_base: &Path) -> Result<ReportPaths> {
    let source_path = param_string(&step.params, "source_path")?;
    let chunk_size = param_u64(&step.params, "chunk_size").unwrap_or(8 * 1024 * 1024);
    let report_base = param_string(&step.params, "report_base")
        .map(PathBuf::from)
        .unwrap_or_else(|_| default_report_base.to_path_buf());

    let hash_report = hash_file_readonly(&source_path, chunk_size, None)?;
    let graph = build_device_graph()?;
    let meta = json!({
        "action": step.action,
        "step_id": step.id,
        "hash_report": hash_report
    });
    create_report_bundle(report_base, &graph, Some(meta), None)
}

fn param_string(params: &Value, key: &str) -> Result<String> {
    params
        .get(key)
        .and_then(|value| value.as_str())
        .map(|value| value.to_string())
        .ok_or_else(|| anyhow!("missing or invalid param {}", key))
}

fn param_u64(params: &Value, key: &str) -> Option<u64> {
    params.get(key).and_then(|value| value.as_u64())
}

fn build_device_graph() -> Result<DeviceGraph> {
    #[cfg(windows)]
    {
        return bootforge_host_windows::build_device_graph();
    }
    #[cfg(linux)]
    {
        return bootforge_host_linux::build_device_graph();
    }
    #[cfg(not(any(windows, linux)))]
    {
        Err(anyhow!("unsupported OS for device graph"))
    }
}
