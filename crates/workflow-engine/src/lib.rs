use serde::{Deserialize, Serialize};
use time::format_description::well_known::Rfc3339;
use time::OffsetDateTime;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Workflow {
    pub id: String,
    pub name: String,
    pub steps: Vec<WorkflowStep>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct WorkflowStep {
    pub id: String,
    pub name: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct WorkflowRun {
    pub workflow_id: String,
    pub started_at_utc: String,
    pub status: RunStatus,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum RunStatus {
    Planned,
    Completed,
}

impl Workflow {
    pub fn plan_run(&self) -> WorkflowRun {
        WorkflowRun {
            workflow_id: self.id.clone(),
            started_at_utc: now_utc_rfc3339(),
            status: RunStatus::Planned,
        }
    }
}

fn now_utc_rfc3339() -> String {
    OffsetDateTime::now_utc()
        .format(&Rfc3339)
        .unwrap_or_else(|_| "unknown".to_string())
}
