use anyhow::{anyhow, Context, Result};
use std::fs::OpenOptions;
use std::io::{Seek, SeekFrom, Write};
use std::path::Path;
use std::time::{SystemTime, UNIX_EPOCH};

const BYTES_PER_SECTOR: u16 = 512;
const RESERVED_SECTORS: u16 = 32;
const NUM_FATS: u8 = 2;
const ROOT_CLUSTER: u32 = 2;
const FSINFO_SECTOR: u16 = 1;
const BACKUP_BOOT_SECTOR: u16 = 6;
const MEDIA_DESCRIPTOR: u8 = 0xF8;

#[derive(Debug, Clone)]
pub struct Fat32Layout {
    pub total_sectors: u32,
    pub sectors_per_cluster: u8,
    pub sectors_per_fat: u32,
    pub root_dir_sector: u32,
}

pub fn format_fat32(
    device_path: impl AsRef<Path>,
    total_bytes: u64,
    label: Option<&str>,
) -> Result<Fat32Layout> {
    if total_bytes < (BYTES_PER_SECTOR as u64) * 1000 {
        return Err(anyhow!("device too small for FAT32"));
    }
    if total_bytes % (BYTES_PER_SECTOR as u64) != 0 {
        return Err(anyhow!("device size must be multiple of 512 bytes"));
    }

    let total_sectors = (total_bytes / (BYTES_PER_SECTOR as u64)) as u32;
    let sectors_per_cluster = select_sectors_per_cluster(total_sectors)?;
    let sectors_per_fat = compute_fat_size(total_sectors, sectors_per_cluster)?;
    let data_start = RESERVED_SECTORS as u32 + (NUM_FATS as u32 * sectors_per_fat);
    let root_dir_sector = data_start + ((ROOT_CLUSTER - 2) * sectors_per_cluster as u32);

    let mut device = OpenOptions::new()
        .read(true)
        .write(true)
        .open(device_path.as_ref())
        .with_context(|| format!("open {}", device_path.as_ref().display()))?;

    let volume_id = volume_id();
    let volume_label = label_bytes(label.unwrap_or("PHOENIX"));

    let boot_sector = build_boot_sector(
        total_sectors,
        sectors_per_cluster,
        sectors_per_fat,
        volume_id,
        &volume_label,
    );
    write_sector(&mut device, 0, &boot_sector)?;
    write_sector(&mut device, BACKUP_BOOT_SECTOR as u32, &boot_sector)?;

    let fsinfo = build_fsinfo();
    write_sector(&mut device, FSINFO_SECTOR as u32, &fsinfo)?;
    write_sector(&mut device, BACKUP_BOOT_SECTOR as u32 + 1, &fsinfo)?;

    let fat_start = RESERVED_SECTORS as u32;
    write_fat(&mut device, fat_start, sectors_per_fat, true)?;
    write_fat(
        &mut device,
        fat_start + sectors_per_fat,
        sectors_per_fat,
        false,
    )?;

    zero_cluster(&mut device, root_dir_sector, sectors_per_cluster)?;
    if !volume_label.iter().all(|b| *b == b' ') {
        write_volume_label(&mut device, root_dir_sector, &volume_label)?;
    }

    device.sync_all().ok();

    Ok(Fat32Layout {
        total_sectors,
        sectors_per_cluster,
        sectors_per_fat,
        root_dir_sector,
    })
}

fn select_sectors_per_cluster(total_sectors: u32) -> Result<u8> {
    let candidates = [1u8, 2, 4, 8, 16, 32, 64, 128];
    for spc in candidates {
        let fat = compute_fat_size(total_sectors, spc)?;
        let data_sectors = total_sectors
            .saturating_sub(RESERVED_SECTORS as u32 + NUM_FATS as u32 * fat);
        let clusters = data_sectors / spc as u32;
        if clusters >= 65525 && clusters <= 0x0FFFFFF5 {
            return Ok(spc);
        }
    }
    Err(anyhow!("unable to select sectors per cluster for FAT32"))
}

fn compute_fat_size(total_sectors: u32, spc: u8) -> Result<u32> {
    let mut fat_size = 1u32;
    loop {
        let data_sectors = total_sectors
            .saturating_sub(RESERVED_SECTORS as u32 + NUM_FATS as u32 * fat_size);
        let clusters = data_sectors / spc as u32;
        if clusters == 0 {
            return Err(anyhow!("invalid FAT32 size"));
        }
        let needed = ((clusters + 2) * 4 + (BYTES_PER_SECTOR as u32 - 1))
            / BYTES_PER_SECTOR as u32;
        if needed == fat_size {
            return Ok(fat_size);
        }
        fat_size = needed;
    }
}

fn build_boot_sector(
    total_sectors: u32,
    sectors_per_cluster: u8,
    sectors_per_fat: u32,
    volume_id: u32,
    volume_label: &[u8; 11],
) -> [u8; 512] {
    let mut sector = [0u8; 512];
    sector[0] = 0xEB;
    sector[1] = 0x58;
    sector[2] = 0x90;
    sector[3..11].copy_from_slice(b"PHOENIX ");
    write_u16(&mut sector, 0x0B, BYTES_PER_SECTOR);
    sector[0x0D] = sectors_per_cluster;
    write_u16(&mut sector, 0x0E, RESERVED_SECTORS);
    sector[0x10] = NUM_FATS;
    write_u16(&mut sector, 0x11, 0);
    if total_sectors < 65536 {
        write_u16(&mut sector, 0x13, total_sectors as u16);
    } else {
        write_u16(&mut sector, 0x13, 0);
    }
    sector[0x15] = MEDIA_DESCRIPTOR;
    write_u16(&mut sector, 0x16, 0);
    write_u16(&mut sector, 0x18, 63);
    write_u16(&mut sector, 0x1A, 255);
    write_u32(&mut sector, 0x1C, 0);
    write_u32(&mut sector, 0x20, total_sectors);
    write_u32(&mut sector, 0x24, sectors_per_fat);
    write_u16(&mut sector, 0x28, 0);
    write_u16(&mut sector, 0x2A, 0);
    write_u32(&mut sector, 0x2C, ROOT_CLUSTER);
    write_u16(&mut sector, 0x30, FSINFO_SECTOR);
    write_u16(&mut sector, 0x32, BACKUP_BOOT_SECTOR);
    sector[0x36] = 0x80;
    sector[0x38] = 0x29;
    write_u32(&mut sector, 0x39, volume_id);
    sector[0x3D..0x48].copy_from_slice(volume_label);
    sector[0x47..0x4F].copy_from_slice(b"FAT32   ");
    sector[510] = 0x55;
    sector[511] = 0xAA;
    sector
}

fn build_fsinfo() -> [u8; 512] {
    let mut sector = [0u8; 512];
    sector[0..4].copy_from_slice(&[0x52, 0x52, 0x61, 0x41]);
    sector[0x1E4..0x1E8].copy_from_slice(&[0x72, 0x72, 0x41, 0x61]);
    write_u32(&mut sector, 0x1E8, 0xFFFFFFFF);
    write_u32(&mut sector, 0x1EC, 0xFFFFFFFF);
    sector[510] = 0x55;
    sector[511] = 0xAA;
    sector
}

fn write_fat(
    device: &mut std::fs::File,
    start_sector: u32,
    sectors_per_fat: u32,
    primary: bool,
) -> Result<()> {
    let mut first_sector = vec![0u8; BYTES_PER_SECTOR as usize];
    write_u32_slice(&mut first_sector, 0, 0x0FFFFFF8);
    write_u32_slice(&mut first_sector, 1, 0x0FFFFFFF);
    write_u32_slice(&mut first_sector, 2, 0x0FFFFFFF);
    write_sector(device, start_sector, &first_sector)?;

    let zero_sector = vec![0u8; BYTES_PER_SECTOR as usize];
    for sector in 1..sectors_per_fat {
        write_sector(device, start_sector + sector, &zero_sector)?;
    }

    if primary {
        Ok(())
    } else {
        Ok(())
    }
}

fn zero_cluster(device: &mut std::fs::File, start_sector: u32, spc: u8) -> Result<()> {
    let zero_sector = vec![0u8; BYTES_PER_SECTOR as usize];
    for offset in 0..spc as u32 {
        write_sector(device, start_sector + offset, &zero_sector)?;
    }
    Ok(())
}

fn write_volume_label(
    device: &mut std::fs::File,
    root_sector: u32,
    label: &[u8; 11],
) -> Result<()> {
    let mut entry = [0u8; 32];
    entry[0..11].copy_from_slice(label);
    entry[11] = 0x08;
    write_sector(device, root_sector, &entry)?;
    Ok(())
}

fn write_sector(device: &mut std::fs::File, sector: u32, data: &[u8]) -> Result<()> {
    device.seek(SeekFrom::Start(sector as u64 * BYTES_PER_SECTOR as u64))?;
    device.write_all(data)?;
    Ok(())
}

fn write_u16(buffer: &mut [u8], offset: usize, value: u16) {
    buffer[offset..offset + 2].copy_from_slice(&value.to_le_bytes());
}

fn write_u32(buffer: &mut [u8], offset: usize, value: u32) {
    buffer[offset..offset + 4].copy_from_slice(&value.to_le_bytes());
}

fn write_u32_slice(buffer: &mut [u8], index: usize, value: u32) {
    let offset = index * 4;
    buffer[offset..offset + 4].copy_from_slice(&value.to_le_bytes());
}

fn label_bytes(label: &str) -> [u8; 11] {
    let mut out = [b' '; 11];
    let upper = label.to_ascii_uppercase();
    let bytes = upper.as_bytes();
    for (idx, byte) in bytes.iter().take(11).enumerate() {
        out[idx] = *byte;
    }
    out
}

fn volume_id() -> u32 {
    SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .map(|d| d.as_secs() as u32)
        .unwrap_or(0x12345678)
}
