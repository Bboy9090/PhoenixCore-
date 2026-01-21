use anyhow::{anyhow, Context, Result};
use sha2::{Digest, Sha256};
use std::fs::File;
use std::io::{Read, Seek, SeekFrom};
use std::path::Path;

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct ChunkRange {
    pub offset: u64,
    pub length: u64,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ChunkHash {
    pub offset: u64,
    pub length: u64,
    pub sha256: [u8; 32],
}

pub fn plan_chunks(total_bytes: u64, chunk_size: u64) -> Vec<ChunkRange> {
    if total_bytes == 0 || chunk_size == 0 {
        return Vec::new();
    }

    let mut ranges = Vec::new();
    let mut offset = 0;
    while offset < total_bytes {
        let remaining = total_bytes - offset;
        let length = remaining.min(chunk_size);
        ranges.push(ChunkRange { offset, length });
        offset += length;
    }
    ranges
}

pub fn hash_reader_chunks<R: Read + Seek>(
    reader: &mut R,
    plan: &[ChunkRange],
) -> Result<Vec<ChunkHash>> {
    let mut results = Vec::with_capacity(plan.len());
    let mut buffer = vec![0u8; 1024 * 1024];

    for chunk in plan {
        reader
            .seek(SeekFrom::Start(chunk.offset))
            .with_context(|| format!("seek to offset {}", chunk.offset))?;

        let mut remaining = chunk.length;
        let mut hasher = Sha256::new();
        while remaining > 0 {
            let read_len = (remaining as usize).min(buffer.len());
            let read_count = reader
                .read(&mut buffer[..read_len])
                .with_context(|| format!("read {} bytes", read_len))?;

            if read_count == 0 {
                return Err(anyhow!(
                    "unexpected EOF after {} bytes for chunk at {}",
                    chunk.length - remaining,
                    chunk.offset
                ));
            }

            hasher.update(&buffer[..read_count]);
            remaining -= read_count as u64;
        }

        let digest = hasher.finalize();
        let mut sha256 = [0u8; 32];
        sha256.copy_from_slice(&digest);
        results.push(ChunkHash {
            offset: chunk.offset,
            length: chunk.length,
            sha256,
        });
    }

    Ok(results)
}

pub fn hash_file_chunks(path: &Path, chunk_size: u64) -> Result<Vec<ChunkHash>> {
    if chunk_size == 0 {
        return Err(anyhow!("chunk_size must be greater than zero"));
    }

    let mut file = File::open(path).with_context(|| format!("open {}", path.display()))?;
    let total = file.metadata().context("read file metadata")?.len();
    let plan = plan_chunks(total, chunk_size);
    hash_reader_chunks(&mut file, &plan)
}
