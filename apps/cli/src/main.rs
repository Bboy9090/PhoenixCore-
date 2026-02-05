use anyhow::{anyhow, Result};
use bootforge_imaging::hash_file_readonly;
use bootforge_report::create_report_bundle;
use bootforge_workflow_engine::{load_workflow_definition, run_workflow_definition};

fn main() -> Result<()> {
    let args: Vec<String> = std::env::args().collect();
    if args.len() < 2 {
        print_help();
        return Ok(());
    }

    match args[1].as_str() {
        "device-graph" => {
            let pretty = args.iter().any(|arg| arg == "--pretty");
            let graph = build_device_graph()?;
            if pretty {
                println!("{}", serde_json::to_string_pretty(&graph)?);
            } else {
                println!("{}", serde_json::to_string(&graph)?);
            }
            Ok(())
        }
        "hash-file" => {
            let path = arg_value(&args, "--path")
                .ok_or_else(|| anyhow!("--path is required"))?;
            let chunk_size = arg_value(&args, "--chunk-size")
                .and_then(|value| value.parse::<u64>().ok())
                .unwrap_or(8 * 1024 * 1024);
            let report = hash_file_readonly(path, chunk_size, None)?;
            println!("{}", serde_json::to_string_pretty(&report)?);
            Ok(())
        }
        "report" => {
            let base = arg_value(&args, "--base").unwrap_or_else(|| ".".to_string());
            let graph = build_device_graph()?;
            let report = create_report_bundle(base, &graph, None, None)?;
            println!("report_root: {}", report.root.display());
            println!("device_graph: {}", report.device_graph_json.display());
            println!("run_json: {}", report.run_json.display());
            println!("logs: {}", report.logs_path.display());
            Ok(())
        }
        "workflow-run" => {
            let file = arg_value(&args, "--file")
                .ok_or_else(|| anyhow!("--file is required"))?;
            let report_base = arg_value(&args, "--report-base").unwrap_or_else(|| ".".to_string());
            let workflow = load_workflow_definition(&file)?;
            let result = run_workflow_definition(&workflow, report_base)?;
            println!("workflow: {}", result.workflow);
            for report in result.step_reports {
                println!("step: {} -> {}", report.step_id, report.report.root.display());
            }
            Ok(())
        }
        _ => {
            print_help();
            Ok(())
        }
    }
}

fn arg_value(args: &[String], flag: &str) -> Option<String> {
    args.iter()
        .position(|arg| arg == flag)
        .and_then(|idx| args.get(idx + 1))
        .cloned()
}

fn build_device_graph() -> Result<bootforge_core::DeviceGraph> {
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

fn print_help() {
    eprintln!("BootForge CLI (Rust)");
    eprintln!("  device-graph [--pretty]");
    eprintln!("  hash-file --path <file> [--chunk-size <bytes>]");
    eprintln!("  report [--base <dir>]");
    eprintln!("  workflow-run --file <workflow.json> [--report-base <dir>]");
}
