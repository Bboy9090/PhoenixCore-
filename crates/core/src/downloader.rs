use serde::{Deserialize, Serialize};
use anyhow::{Result, Context};
use std::path::PathBuf;
use std::fs;
use sha2::{Sha256, Digest};

#[derive(Debug, Serialize, Deserialize)]
pub struct Payload {
    pub name: String,
    pub version: String,
    pub url: String,
    pub expected_hash: String,
}

pub struct PayloadDownloader {
    base_path: PathBuf,
}

impl PayloadDownloader {
    pub fn new(base_path: PathBuf) -> Self {
        Self { base_path }
    }

    pub fn verify_payload(&self, payload: &Payload) -> Result<bool> {
        let path = self.base_path.join(&payload.name);
        if !path.exists() {
            return Ok(false);
        }

        let mut file = fs::File::open(&path)?;
        let mut hasher = Sha256::new();
        std::io::copy(&mut file, &mut hasher)?;
        let hash = format!("{:x}", hasher.finalize());

        Ok(hash == payload.expected_hash)
    }

    pub fn sync_all(&self, payloads: Vec<Payload>) -> Result<()> {
        println!("[DOWNLOADER] 📥 Synchronizing Industrial Binaries...");
        fs::create_dir_all(&self.base_path)?;

        for p in payloads {
            let is_valid = self.verify_payload(&p).unwrap_or(false);
            if is_valid {
                println!("[DOWNLOADER] ✅ {} (v{}) verified.", p.name, p.version);
            } else {
                println!("[DOWNLOADER] ⚠️  {} missing or corrupt. (Download required)", p.name);
                // Real download logic would go here
            }
        }

        Ok(())
    }
}
