use sha2::{Sha256, Digest};
use std::io::{Read, Seek, SeekFrom};
use indicatif::{ProgressBar, ProgressStyle};
use anyhow::{Result, Context};
use serde::{Serialize, Deserialize};

#[derive(Debug, Serialize, Deserialize)]
pub struct ChunkHash {
    pub index: usize,
    pub offset: u64,
    pub size: usize,
    pub hash: String,
}

pub struct ChunkPlan {
    pub total_size: u64,
    pub chunk_size: usize,
    pub total_chunks: usize,
}

impl ChunkPlan {
    pub fn new(total_size: u64, chunk_size: usize) -> Self {
        if total_size == 0 {
             return Self { total_size: 0, chunk_size, total_chunks: 0 };
        }
        let total_chunks = ((total_size as f64) / (chunk_size as f64)).ceil() as usize;
        Self {
            total_size,
            chunk_size,
            total_chunks,
        }
    }
}

pub fn hash_disk_chunks(
    disk_path: &str,
    plan: &ChunkPlan,
    max_chunks: Option<usize>,
) -> Result<Vec<ChunkHash>> {
    let mut file = open_disk_read_only(disk_path)?;
    let mut hashes = Vec::new();
    
    let chunks_to_process = match max_chunks {
        Some(m) => m.min(plan.total_chunks),
        None => plan.total_chunks,
    };

    let pb = ProgressBar::new(chunks_to_process as u64);
    pb.set_style(ProgressStyle::default_bar()
        .template("{spinner:.green} [{elapsed_precise}] [{bar:40.cyan/blue}] {pos}/{len} chunks ({eta})")?
        .progress_chars("#>-"));

    let mut buffer = vec![0u8; plan.chunk_size];

    for i in 0..chunks_to_process {
        let offset = (i as u64) * (plan.chunk_size as u64);
        file.seek(SeekFrom::Start(offset))
            .with_context(|| format!("Failed to seek to offset {}", offset))?;
        
        let bytes_to_read = if i == plan.total_chunks - 1 {
            (plan.total_size - offset) as usize
        } else {
            plan.chunk_size
        };

        file.read_exact(&mut buffer[..bytes_to_read])
            .with_context(|| format!("Read error at chunk {} (offset {}). Check permissions.", i, offset))?;

        let mut hasher = Sha256::new();
        hasher.update(&buffer[..bytes_to_read]);
        let hash = format!("{:x}", hasher.finalize());

        hashes.push(ChunkHash {
            index: i,
            offset,
            size: bytes_to_read,
            hash,
        });

        pb.inc(1);
    }

    pb.finish_with_message("Hashing complete");
    Ok(hashes)
}

#[cfg(windows)]
fn open_disk_read_only(path: &str) -> Result<std::fs::File> {
    use std::os::windows::fs::OpenOptionsExt;
    use windows::Win32::Storage::FileSystem::{FILE_SHARE_READ, FILE_SHARE_WRITE};
    
    // On Windows, PhysicalDrive access requires administrative privileges.
    std::fs::OpenOptions::new()
        .read(true)
        .share_mode(FILE_SHARE_READ.0 | FILE_SHARE_WRITE.0)
        .open(path)
        .with_context(|| format!("Access Denied: Could not open {}. Ensure you are running as Administrator.", path))
}

#[cfg(not(windows))]
fn open_disk_read_only(path: &str) -> Result<std::fs::File> {
    // Stub or POSIX implementation
    std::fs::OpenOptions::new()
        .read(true)
        .open(path)
        .with_context(|| format!("Failed to open {}. Check permissions (sudo might be required).", path))
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_chunk_planner() {
        let plan = ChunkPlan::new(100, 30);
        assert_eq!(plan.total_chunks, 4);
        
        let plan2 = ChunkPlan::new(1024, 1024);
        assert_eq!(plan2.total_chunks, 1);

        let plan3 = ChunkPlan::new(0, 1024);
        assert_eq!(plan3.total_chunks, 0);
    }
}
