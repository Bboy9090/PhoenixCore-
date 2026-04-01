use super::Drive;
use serde_json::Value;
use std::process::Command;

pub fn list() -> Result<Vec<Drive>, String> {
  // diskutil -> plist, plutil converts to JSON for easy parsing
  let plist_out = Command::new("diskutil")
    .args(["list", "-plist"])
    .output()
    .map_err(|e| format!("diskutil failed: {e}"))?;

  if !plist_out.status.success() {
    return Err(String::from_utf8_lossy(&plist_out.stderr).to_string());
  }

  let plutil_out = Command::new("plutil")
    .args(["-convert", "json", "-o", "-", "-"])
    .stdin(std::process::Stdio::piped())
    .stdout(std::process::Stdio::piped())
    .spawn()
    .and_then(|mut child| {
      use std::io::Write;
      if let Some(stdin) = child.stdin.as_mut() {
        stdin.write_all(&plist_out.stdout)?;
      }
      child.wait_with_output()
    })
    .map_err(|e| format!("plutil convert failed: {e}"))?;

  if !plutil_out.status.success() {
    return Err(String::from_utf8_lossy(&plutil_out.stderr).to_string());
  }

  let v: Value = serde_json::from_slice(&plutil_out.stdout)
    .map_err(|e| format!("JSON parse error: {e}"))?;

  // diskutil list -plist provides AllDisks and metadata per disk.
  let disks = v.get("AllDisks").and_then(|x| x.as_array()).cloned().unwrap_or_default();

  let mut out: Vec<Drive> = vec![];

  for d in disks {
    let disk = match d.as_str() { Some(s) => s.to_string(), None => continue };

    let info_out = Command::new("diskutil")
      .args(["info", "-plist", &disk])
      .output()
      .map_err(|e| format!("diskutil info failed: {e}"))?;

    if !info_out.status.success() {
      continue;
    }

    let info_json = Command::new("plutil")
      .args(["-convert", "json", "-o", "-", "-"])
      .stdin(std::process::Stdio::piped())
      .stdout(std::process::Stdio::piped())
      .spawn()
      .and_then(|mut child| {
        use std::io::Write;
        if let Some(stdin) = child.stdin.as_mut() {
          stdin.write_all(&info_out.stdout)?;
        }
        child.wait_with_output()
      })
      .map_err(|e| format!("plutil info convert failed: {e}"))?;

    if !info_json.status.success() {
      continue;
    }

    let info: Value = serde_json::from_slice(&info_json.stdout).unwrap_or(Value::Null);

    let is_external = info.get("Internal").and_then(|x| x.as_bool()).map(|b| !b).unwrap_or(false);
    let is_whole = info.get("WholeDisk").and_then(|x| x.as_bool()).unwrap_or(false);

    // Strict: only external whole disks
    if !(is_external && is_whole) { continue; }

    let size = info.get("TotalSize").and_then(|x| x.as_u64()).unwrap_or(0);
    let name = info.get("MediaName").and_then(|x| x.as_str()).unwrap_or("External Disk").to_string();
    let protocol = info.get("BusProtocol").and_then(|x| x.as_str()).map(|s| s.to_string());

    out.push(Drive {
      id: format!("/dev/{}", disk),
      name,
      size_gb: super::bytes_to_gb(size),
      vendor: protocol
    });
  }

  Ok(out)
}