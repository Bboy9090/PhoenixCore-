use anyhow::Result;

fn main() -> Result<()> {
    #[cfg(windows)]
    {
        let graph = bootforge_host_windows::build_device_graph()?;
        println!("{}", serde_json::to_string_pretty(&graph)?);
        return Ok(());
    }

    #[cfg(not(windows))]
    {
        eprintln!("This CLI build is Windows-first for now.");
        Ok(())
    }
}
