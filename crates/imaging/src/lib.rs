use anyhow::{anyhow, Result};
use sha2::{Digest, Sha256};
use std::fmt::Write as _;

#[derive(Debug, Clone)]
pub struct ChunkPlan {
    pub chunk_size_bytes: u64,
    pub chunks: Vec<Chunk>,
}

#[derive(Debug, Clone)]
pub struct Chunk {
    pub index: u64,
    pub offset: u64,
    pub size: u64,
}

#[derive(Debug, Clone, Copy)]
pub struct HashProgress {
    pub chunk_index: u64,
    pub total_chunks: u64,
    pub bytes_hashed: u64,
    pub total_bytes: u64,
}

pub trait ProgressObserver {
    fn on_progress(&mut self, progress: HashProgress) -> bool;
}

pub fn make_chunk_plan(total_size: u64, chunk_size_bytes: u64) -> ChunkPlan {
    let mut chunks = Vec::new();
    if chunk_size_bytes == 0 {
        return ChunkPlan {
            chunk_size_bytes,
            chunks,
        };
    }

    let mut offset = 0u64;
    let mut index = 0u64;
    while offset < total_size {
        let remaining = total_size - offset;
        let size = remaining.min(chunk_size_bytes);
        chunks.push(Chunk { index, offset, size });
        offset += size;
        index += 1;
    }

    ChunkPlan {
        chunk_size_bytes,
        chunks,
    }
}

#[cfg(windows)]
fn wide(s: &str) -> Vec<u16> {
    use std::os::windows::prelude::*;
    std::ffi::OsStr::new(s)
        .encode_wide()
        .chain(std::iter::once(0))
        .collect()
}

#[cfg(windows)]
pub fn hash_disk_readonly_physicaldrive(
    disk_id: &str,
    total_size: u64,
    chunk_size: u64,
    max_chunks: Option<u64>,
) -> Result<Vec<(u64, String)>> {
    let mut observer = NoopObserver;
    hash_disk_readonly_physicaldrive_with_progress(
        disk_id,
        total_size,
        chunk_size,
        max_chunks,
        &mut observer,
    )
}

#[cfg(windows)]
pub fn hash_disk_readonly_physicaldrive_with_progress(
    disk_id: &str,
    total_size: u64,
    chunk_size: u64,
    max_chunks: Option<u64>,
    observer: &mut dyn ProgressObserver,
) -> Result<Vec<(u64, String)>> {
    use windows::core::PCWSTR;
    use windows::Win32::Foundation::{CloseHandle, INVALID_HANDLE_VALUE};
    use windows::Win32::Storage::FileSystem::{
        CreateFileW, ReadFile, SetFilePointerEx, FILE_ATTRIBUTE_NORMAL, FILE_BEGIN,
        FILE_GENERIC_READ, FILE_SHARE_READ, FILE_SHARE_WRITE, OPEN_EXISTING,
    };

    if chunk_size == 0 {
        return Err(anyhow!("chunk_size must be greater than zero"));
    }
    if chunk_size > usize::MAX as u64 {
        return Err(anyhow!("chunk_size too large for buffer allocation"));
    }

    let path = format!(r"\\.\{}", disk_id);
    let w = wide(&path);

    unsafe {
        let handle = CreateFileW(
            PCWSTR(w.as_ptr()),
            FILE_GENERIC_READ,
            FILE_SHARE_READ | FILE_SHARE_WRITE,
            None,
            OPEN_EXISTING,
            FILE_ATTRIBUTE_NORMAL,
            None,
        );
        if handle == INVALID_HANDLE_VALUE {
            return Err(anyhow!("CreateFileW failed for {}", path));
        }

        let plan = make_chunk_plan(total_size, chunk_size);
        let limit = max_chunks.unwrap_or(u64::MAX) as usize;
        let mut results = Vec::new();
        let mut buffer = vec![0u8; chunk_size as usize];
        let total_chunks = plan.chunks.len() as u64;
        let mut bytes_hashed = 0u64;

        for chunk in plan.chunks.iter().take(limit) {
            let mut new_pos = 0i64;
            let ok_seek = SetFilePointerEx(
                handle,
                chunk.offset as i64,
                Some(&mut new_pos),
                FILE_BEGIN,
            )
            .as_bool();
            if !ok_seek {
                CloseHandle(handle);
                return Err(anyhow!("SetFilePointerEx failed at offset {}", chunk.offset));
            }

            if chunk.size > u32::MAX as u64 {
                CloseHandle(handle);
                return Err(anyhow!("chunk size too large for ReadFile"));
            }

            let to_read = chunk.size as u32;
            let mut read = 0u32;
            let ok_read = ReadFile(
                handle,
                Some(&mut buffer[..to_read as usize]),
                Some(&mut read),
                None,
            )
            .as_bool();
            if !ok_read || read == 0 {
                CloseHandle(handle);
                return Err(anyhow!("ReadFile failed at chunk {}", chunk.index));
            }

            let mut hasher = Sha256::new();
            hasher.update(&buffer[..read as usize]);
            let hash = hasher.finalize();
            results.push((chunk.index, to_hex(&hash)));

            bytes_hashed = bytes_hashed.saturating_add(read as u64);
            let progress = HashProgress {
                chunk_index: chunk.index,
                total_chunks,
                bytes_hashed,
                total_bytes: total_size,
            };
            if !observer.on_progress(progress) {
                CloseHandle(handle);
                return Err(anyhow!("hash operation cancelled"));
            }
        }

        CloseHandle(handle);
        Ok(results)
    }
}

#[cfg(not(windows))]
pub fn hash_disk_readonly_physicaldrive(
    _disk_id: &str,
    _total_size: u64,
    _chunk_size: u64,
    _max_chunks: Option<u64>,
) -> Result<Vec<(u64, String)>> {
    Err(anyhow!("Windows-only in M0"))
}

#[cfg(not(windows))]
pub fn hash_disk_readonly_physicaldrive_with_progress(
    _disk_id: &str,
    _total_size: u64,
    _chunk_size: u64,
    _max_chunks: Option<u64>,
    _observer: &mut dyn ProgressObserver,
) -> Result<Vec<(u64, String)>> {
    Err(anyhow!("Windows-only in M0"))
}

#[cfg(unix)]
pub fn hash_device_readonly(
    device_path: &str,
    total_size: u64,
    chunk_size: u64,
    max_chunks: Option<u64>,
) -> Result<Vec<(u64, String)>> {
    use std::fs::File;
    use std::io::{Read, Seek, SeekFrom};

    if chunk_size == 0 {
        return Err(anyhow!("chunk_size must be greater than zero"));
    }
    let mut file = File::open(device_path)
        .map_err(|err| anyhow!("open {} failed: {}", device_path, err))?;
    let plan = make_chunk_plan(total_size, chunk_size);
    let limit = max_chunks.unwrap_or(u64::MAX) as usize;
    let mut results = Vec::new();
    let mut buffer = vec![0u8; chunk_size as usize];

    for chunk in plan.chunks.iter().take(limit) {
        file.seek(SeekFrom::Start(chunk.offset))?;
        let mut remaining = chunk.size as usize;
        let mut hasher = Sha256::new();
        while remaining > 0 {
            let read_len = remaining.min(buffer.len());
            let read = file.read(&mut buffer[..read_len])?;
            if read == 0 {
                return Err(anyhow!("unexpected EOF while hashing device"));
            }
            hasher.update(&buffer[..read]);
            remaining -= read;
        }
        let hash = hasher.finalize();
        results.push((chunk.index, to_hex(&hash)));
    }

    Ok(results)
}

#[cfg(not(unix))]
pub fn hash_device_readonly(
    _device_path: &str,
    _total_size: u64,
    _chunk_size: u64,
    _max_chunks: Option<u64>,
) -> Result<Vec<(u64, String)>> {
    Err(anyhow!("device hashing requires Unix-like OS"))
}

struct NoopObserver;

impl ProgressObserver for NoopObserver {
    fn on_progress(&mut self, _progress: HashProgress) -> bool {
        true
    }
}

fn to_hex(bytes: &[u8]) -> String {
    let mut out = String::with_capacity(bytes.len() * 2);
    for byte in bytes {
        let _ = write!(&mut out, "{:02x}", byte);
    }
    out
}
