use anyhow::{anyhow, Result};
use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};
use std::fs::File;
use std::io::{BufReader, Read};
use std::path::Path;

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct ChunkHash {
    pub index: u64,
    pub offset_bytes: u64,
    pub size_bytes: u64,
    pub sha256: String,
}

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct HashReport {
    pub source: String,
    pub total_size: u64,
    pub chunk_size: u64,
    pub total_sha256: String,
    pub chunks: Vec<ChunkHash>,
}

#[derive(Debug, Clone, Copy)]
pub struct HashProgress {
    pub bytes_hashed: u64,
    pub total_bytes: u64,
    pub chunk_index: u64,
    pub total_chunks: u64,
}

pub trait ProgressObserver {
    fn on_progress(&mut self, progress: HashProgress) -> bool;
}

pub fn hash_file_readonly(
    path: impl AsRef<Path>,
    chunk_size: u64,
    mut observer: Option<&mut dyn ProgressObserver>,
) -> Result<HashReport> {
    if chunk_size == 0 {
        return Err(anyhow!("chunk_size must be > 0"));
    }
    if chunk_size > usize::MAX as u64 {
        return Err(anyhow!("chunk_size too large for this platform"));
    }
    let path = path.as_ref();
    let file = File::open(path)?;
    let total_size = file.metadata()?.len();
    let total_chunks = if total_size == 0 {
        0
    } else {
        (total_size + chunk_size - 1) / chunk_size
    };

    let mut reader = BufReader::new(file);
    let mut buffer = vec![0u8; chunk_size as usize];
    let mut chunks = Vec::new();
    let mut overall = Sha256::new();
    let mut offset = 0u64;
    let mut index = 0u64;

    loop {
        let read = reader.read(&mut buffer)?;
        if read == 0 {
            break;
        }

        let mut hasher = Sha256::new();
        hasher.update(&buffer[..read]);
        let digest = hasher.finalize();

        overall.update(&buffer[..read]);
        chunks.push(ChunkHash {
            index,
            offset_bytes: offset,
            size_bytes: read as u64,
            sha256: to_hex(&digest),
        });

        offset += read as u64;
        if let Some(obs) = observer.as_deref_mut() {
            let progress = HashProgress {
                bytes_hashed: offset,
                total_bytes: total_size,
                chunk_index: index,
                total_chunks,
            };
            if !obs.on_progress(progress) {
                return Err(anyhow!("hash cancelled"));
            }
        }
        index += 1;
    }

    let total_sha256 = to_hex(&overall.finalize());
    Ok(HashReport {
        source: path.display().to_string(),
        total_size,
        chunk_size,
        total_sha256,
        chunks,
    })
}

fn to_hex(bytes: &[u8]) -> String {
    let mut out = String::with_capacity(bytes.len() * 2);
    for byte in bytes {
        out.push_str(&format!("{:02x}", byte));
    }
    out
}
