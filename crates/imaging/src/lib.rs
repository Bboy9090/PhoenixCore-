use anyhow::{Context, Result};
use indicatif::{ProgressBar, ProgressStyle};
use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};
use std::io::{Read, Seek, SeekFrom, Write};

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
            return Self {
                total_size: 0,
                chunk_size,
                total_chunks: 0,
            };
        }
        let total_chunks = ((total_size as f64) / (chunk_size as f64)).ceil() as usize;
        Self {
            total_size,
            chunk_size,
            total_chunks,
        }
    }
}

#[derive(Debug, Clone, Copy)]
pub struct PlannedChunk {
    pub index: u64,
    pub offset: u64,
    pub size: u64,
}

#[derive(Debug, Clone)]
pub struct ImageWriteResult {
    pub bytes_written: u64,
    pub sha256: String,
    pub verify_ok: Option<bool>,
}

pub fn make_chunk_plan(total_size: u64, chunk_size: u64) -> Vec<PlannedChunk> {
    if total_size == 0 || chunk_size == 0 {
        return Vec::new();
    }

    let mut chunks = Vec::new();
    let mut offset = 0u64;
    let mut index = 0u64;
    while offset < total_size {
        let size = chunk_size.min(total_size - offset);
        chunks.push(PlannedChunk {
            index,
            offset,
            size,
        });
        offset = offset.saturating_add(size);
        index = index.saturating_add(1);
    }
    chunks
}

pub fn hash_device_readonly(
    device_path: &str,
    total_size: u64,
    chunk_size: u64,
    max_chunks: Option<u64>,
) -> Result<Vec<(u64, String)>> {
    if chunk_size == 0 {
        anyhow::bail!("chunk_size must be greater than zero");
    }
    let chunk_size = usize::try_from(chunk_size).context("chunk_size too large")?;
    let plan = ChunkPlan::new(total_size, chunk_size);
    let max_chunks = max_chunks.map(|value| value as usize);
    let hashes = hash_disk_chunks(device_path, &plan, max_chunks)?;
    Ok(hashes
        .into_iter()
        .map(|hash| (hash.index as u64, hash.hash))
        .collect())
}

pub fn hash_disk_readonly_physicaldrive(
    disk_id: &str,
    total_size: u64,
    chunk_size: u64,
    max_chunks: Option<u64>,
) -> Result<Vec<(u64, String)>> {
    let disk_path = windows_physical_drive_path(disk_id);
    hash_device_readonly(&disk_path, total_size, chunk_size, max_chunks)
}

pub fn write_image_to_device(
    source_image: impl AsRef<std::path::Path>,
    target_device: impl AsRef<std::path::Path>,
    chunk_size: u64,
    verify: bool,
) -> Result<ImageWriteResult> {
    if chunk_size == 0 {
        anyhow::bail!("chunk_size must be greater than zero");
    }

    let mut source = std::fs::File::open(source_image.as_ref())
        .with_context(|| format!("open source image {}", source_image.as_ref().display()))?;
    let mut target = std::fs::OpenOptions::new()
        .write(true)
        .open(target_device.as_ref())
        .with_context(|| format!("open target device {}", target_device.as_ref().display()))?;

    let mut hasher = Sha256::new();
    let mut buffer = vec![0u8; usize::try_from(chunk_size).context("chunk_size too large")?];
    let mut bytes_written = 0u64;

    loop {
        let read = source.read(&mut buffer)?;
        if read == 0 {
            break;
        }
        target.write_all(&buffer[..read])?;
        hasher.update(&buffer[..read]);
        bytes_written = bytes_written.saturating_add(read as u64);
    }
    target.flush()?;

    let sha256 = format!("{:x}", hasher.finalize());
    let verify_ok = if verify {
        Some(verify_device_prefix(
            source_image.as_ref(),
            target_device.as_ref(),
            bytes_written,
            chunk_size,
            &sha256,
        )?)
    } else {
        None
    };

    Ok(ImageWriteResult {
        bytes_written,
        sha256,
        verify_ok,
    })
}

fn verify_device_prefix(
    source_image: &std::path::Path,
    target_device: &std::path::Path,
    bytes_to_verify: u64,
    chunk_size: u64,
    expected_sha256: &str,
) -> Result<bool> {
    let source_sha = hash_file_prefix(source_image, bytes_to_verify, chunk_size)?;
    let target_sha = hash_file_prefix(target_device, bytes_to_verify, chunk_size)?;
    Ok(source_sha == expected_sha256 && source_sha == target_sha)
}

fn hash_file_prefix(path: &std::path::Path, bytes_to_hash: u64, chunk_size: u64) -> Result<String> {
    let mut file = std::fs::File::open(path).with_context(|| format!("open {}", path.display()))?;
    let mut remaining = bytes_to_hash;
    let mut buffer = vec![0u8; usize::try_from(chunk_size).context("chunk_size too large")?];
    let mut hasher = Sha256::new();

    while remaining > 0 {
        let limit = remaining.min(buffer.len() as u64) as usize;
        let read = file.read(&mut buffer[..limit])?;
        if read == 0 {
            break;
        }
        hasher.update(&buffer[..read]);
        remaining -= read as u64;
    }

    Ok(format!("{:x}", hasher.finalize()))
}

fn windows_physical_drive_path(disk_id: &str) -> String {
    if disk_id.starts_with(r"\\.\") {
        disk_id.to_string()
    } else if disk_id.to_ascii_lowercase().starts_with("physicaldrive") {
        format!(r"\\.\{}", disk_id)
    } else {
        format!(r"\\.\PhysicalDrive{}", disk_id)
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
            .with_context(|| {
                format!(
                    "Read error at chunk {} (offset {}). Check permissions.",
                    i, offset
                )
            })?;

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
        .with_context(|| {
            format!(
                "Access Denied: Could not open {}. Ensure you are running as Administrator.",
                path
            )
        })
}

#[cfg(not(windows))]
fn open_disk_read_only(path: &str) -> Result<std::fs::File> {
    // Stub or POSIX implementation
    std::fs::OpenOptions::new()
        .read(true)
        .open(path)
        .with_context(|| {
            format!(
                "Failed to open {}. Check permissions (sudo might be required).",
                path
            )
        })
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
