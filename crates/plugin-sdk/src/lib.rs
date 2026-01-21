#[derive(Debug, Clone, Copy)]
pub struct PluginInfo {
    pub id: &'static str,
    pub version: &'static str,
    pub description: &'static str,
}

pub trait PhoenixPlugin {
    fn info(&self) -> PluginInfo;
}
