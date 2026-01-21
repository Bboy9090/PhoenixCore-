use anyhow::{anyhow, Result};

fn main() -> Result<()> {
    let mut args = std::env::args().skip(1);
    let Some(command) = args.next() else {
        print_usage();
        return Ok(());
    };

    match command.as_str() {
        "device-graph" => {
            #[cfg(windows)]
            {
                let graph = phoenix_host_windows::build_device_graph()?;
                println!("{}", serde_json::to_string_pretty(&graph)?);
                return Ok(());
            }

            #[cfg(not(windows))]
            {
                return Err(anyhow!("device-graph is Windows-only"));
            }
        }
        "-h" | "--help" | "help" => {
            print_usage();
        }
        other => {
            eprintln!("Unknown command: {}", other);
            print_usage();
        }
    }

    Ok(())
}

fn print_usage() {
    eprintln!("phoenix-cli device-graph");
}
