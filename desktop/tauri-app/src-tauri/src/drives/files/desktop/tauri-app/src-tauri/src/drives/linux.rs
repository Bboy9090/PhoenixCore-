use super::Drive;
use serde::Deserialize;
use std::process::Command;

#[derive(Debug, Deserialize)]
struct Lsblk {
  blockdevices: Vec<BlockDev>
}

#[derive(Debug, Deserialize)]
struct BlockDev {
  name: String,
  model: Option<String>,
  size: Option<String>,
  rm: Option<u8>,
  tran: Option<String>,
  #[serde(rename="type")]
  dtype: String,
  mountpoint: Option<String>,
  pkname: Option<String>,
}

fn cmd_out(cmd: &str, args: &[&str]) -> Result<String, String> {
  let out = Command::new(cmd).args(args).output().map_err(|e| e.to_string())?;
  if !out.status.success() {
    return Err(String::from_utf8_lossy(&out.stderr).to_string());
  }
  Ok(String::from_utf8_lossy(&out.stdout).to_string())
}

fn root_parent_disk() -> Option<String> {
  // findmnt -no SOURCE /  -> /dev/nvme0n1p2 or /dev/sda2
  // then lsblk -no PKNAME <source> -> nvme0n1 or sda
  let src = cmd_out("findmnt", &["-no", "SOURCE", "/"]).ok()?;
  let src = src.trim();
  if !src.starts_with("/dev/") { return None; }
  let pk = cmd_out("lsblk", &["-no", "PKNAME", src]).ok()?;
  let pk = pk.trim();
  if pk.is_empty() { None } else { Some(pk.to_string()) }
}

fn parse_size_gb(size_str: &str) -> u64 {
  // simple parse for lsblk sizes like "28.7G" or "931.5G"
  let s = size_str.trim();
  if let Some(num) = s.strip_suffix("G") {
    return num.parse::<f64>().ok().map(|v| v.round() as u64).unwrap_or(0);
  }
  if let Some(num) = s.strip_suffix("T") {
    return num.parse::<f64>().ok().map(|v| (v * 1024.0).round() as u64).unwrap_or(0);
  }
  0
}

pub fn list() -> Result<Vec<Drive>, String> {
  let root_pk = root_parent_disk();

  let json = cmd_out("lsblk", &["-J", "-o", "NAME,MODEL,SIZE,RM,TRAN,TYPE,MOUNTPOINT,PKNAME"])?;
  let parsed: Lsblk = serde_json::from_str(&json).map_err(|e| format!("JSON parse error: {e}"))?;

  let mut out = vec![];

  for b in parsed.blockdevices.into_iter() {
    if b.dtype != "disk" { continue; }
    let name = b.name.clone();

    // Exclude the parent disk that holds /
    if let Some(pk) = &root_pk {
      if &name == pk { continue; }
    }

    let rm = b.rm.unwrap_or(0);
    let tran_usb = b.tran.as_deref().unwrap_or("").eq_ignore_ascii_case("usb");

    // Strict: removable flag OR usb transport
    if !(rm == 1 || tran_usb) { continue; }

    // Extra strict: ignore virtuals by name patterns
    if name.starts_with("loop") || name.starts_with("ram") { continue; }

    let size_gb = b.size.as_deref().map(parse_size_gb).unwrap_or(0);
    out.push(Drive {
      id: format!("/dev/{}", name),
      name: b.model.clone().unwrap_or_else(|| format!("Disk {}", name)),
      size_gb,
      vendor: b.tran.clone()
    });
  }

  Ok(out)
}