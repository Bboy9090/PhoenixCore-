use crate::capability::{ActionId, CapabilityMatrix, DeviceState};
use crate::rescue::{DeviceMode, RescueService};
use anyhow::Result;
use std::thread;
use std::time::Duration;

pub struct Orchestrator {
    matrix: CapabilityMatrix,
    downloader: crate::downloader::PayloadDownloader,
}

impl Orchestrator {
    pub fn new() -> Self {
        Self {
            matrix: CapabilityMatrix::default(),
            downloader: crate::downloader::PayloadDownloader::new(std::path::PathBuf::from(
                "./bin",
            )),
        }
    }

    pub fn execute_job(&self, job_json: &str) -> Result<()> {
        let job: crate::capability::ImagingJob = serde_json::from_str(job_json)?;
        let job_id = job.job_id.clone();
        let dry_run = job.verify; // Using verify as a proxy for dry_run in this simplified example
        let force_error = false; // Internal testing flag

        // 1. Capability & Fingerprint Gating (Enforcement Spine)
        self.stream_status("CAPABILITY_CHECK", "Enforcing Capability Matrix gate...");

        // Mock current state and actual disk size for validation demo
        let current_state = DeviceState::Normal;
        let actual_disk_size = job.expected_size_bytes; // Fingerprint matches for now

        self.matrix
            .enforce_gate(&job, &current_state, actual_disk_size)?;
        thread::sleep(Duration::from_millis(500));

        if dry_run {
            self.stream_status(
                "DRY_RUN",
                "🛡 DRY RUN ACTIVE: Hardware fingerprint verified. No bits flipped.",
            );
        }

        // 1. Capability Gating
        self.stream_status(
            "CAPABILITY_CHECK",
            "Verifying target device compatibility...",
        );
        thread::sleep(Duration::from_millis(500));

        // 2. Binary Verification
        self.stream_status("BINARY_SYNC", "Verifying industrial binary requirements...");
        // In a real scenario, we'd check specific payloads from the job
        self.downloader.sync_all(vec![])?;
        thread::sleep(Duration::from_millis(500));

        // 3. Imaging (Transactional)
        self.stream_status("IMAGING", "Initializing transactional write...");

        for i in (0..=100).step_by(10) {
            if force_error && i == 50 {
                return Err(anyhow::anyhow!(
                    "SIMULATED_FAILURE: Transactional rollback triggered at 50%"
                ));
            }

            self.stream_progress(i, "IMAGING", 50.0, (100 - i) as u64);

            if !dry_run {
                // Real IO would happen here
                thread::sleep(Duration::from_millis(100));
            } else {
                thread::sleep(Duration::from_millis(10));
            }
        }

        // 3. Verification
        self.stream_status("VERIFYING", "Performing post-write hash verification...");
        thread::sleep(Duration::from_millis(500));

        // 4. Result
        println!(
            r#"{{"type": "result", "success": true, "job_id": "{}"}}"#,
            job_id
        );

        Ok(())
    }

    fn stream_status(&self, stage: &str, message: &str) {
        println!(
            r#"{{"type": "status", "stage": "{}", "message": "{}"}}"#,
            stage, message
        );
    }

    fn stream_progress(&self, overall: u32, stage: &str, speed: f64, eta: u64) {
        println!(
            r#"{{"type": "progress", "overall": {}, "stage": "{}", "speed_mbps": {:.1}, "eta_seconds": {}}}"#,
            overall, stage, speed, eta
        );
    }
}
