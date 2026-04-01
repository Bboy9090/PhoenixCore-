use anyhow::{anyhow, Result};

pub fn free_space_bytes(_path: &str) -> Result<u64> {
    Err(anyhow!("free space query requires Windows"))
}
