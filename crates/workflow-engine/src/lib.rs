use anyhow::Result;

pub trait Workflow {
    fn name(&self) -> &'static str;
    fn run(&self) -> Result<()>;
}

pub fn run_workflow<W: Workflow>(workflow: W) -> Result<()> {
    workflow.run()
}
