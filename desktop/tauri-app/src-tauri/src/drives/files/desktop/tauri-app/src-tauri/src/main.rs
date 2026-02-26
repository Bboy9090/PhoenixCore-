#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

mod forge;
mod license;
mod paths;
mod drives; // newly added module

use license::{License, verify_signature, tier_allows};
use serde_json::json;
use std::fs;
use std::path::PathBuf;
use std::process::Command;

#[tauri::command]
fn load_license(path: String) -> Result<License, String> {
  let raw = fs::read_to_string(path).map_err(|e| e.to_string())?;
  let lic: License = serde_json::from_str(&raw).map_err(|e| e.to_string())?;
  if !verify_signature(&lic) {
    return Err("License signature invalid".into());
  }
  Ok(lic)
}

#[tauri::command]
fn can_use_feature(license_json: String, feature: String) -> Result<bool, String> {
  let lic: License = serde_json::from_str(&license_json).map_err(|e| e.to_string())?;
  Ok(tier_allows(&lic, &feature))
}

#[tauri::command]
fn get_catalog() -> Result<serde_json::Value, String> {
  let root = paths::repo_root();
  let p = root.join("runtime").join("manifests").join("phoenix-catalog.json");
  let raw = fs::read_to_string(&p).map_err(|e| format!("Cannot read catalog {}: {}", p.display(), e))?;
  let v: serde_json::Value = serde_json::from_str(&raw).map_err(|e| e.to_string())?;
  Ok(v)
}

#[tauri::command]
fn list_drives() -> Result<serde_json::Value, String> {
  let drives_list = drives::list_removable_drives().map_err(|e| e.to_string())?;
  Ok(json!({ "drives": drives_list }))
}

fn appdata_path(app_handle: &tauri::AppHandle, name: &str) -> Result<PathBuf, String> {
  let dir = app_handle
    .path()
    .app_data_dir()
    .map_err(|e| e.to_string())?;
  Ok(dir.join(name))
}

#[tauri::command]
fn forge_usb(app_handle: tauri::AppHandle, build_plan_name: String, target_device: String) -> Result<String, String> {
  let root = paths::repo_root();
  let plan_path = appdata_path(&app_handle, &build_plan_name)?;

  if !plan_path.exists() {
    return Err(format!("Build plan not found in AppData: {}", plan_path.display()));
  }

  forge::run_forge(root, plan_path, target_device)
}

fn main() {
  tauri::Builder::default()
    .invoke_handler(tauri::generate_handler![
      load_license,
      can_use_feature,
      get_catalog,
      list_drives,
      forge_usb
    ])
    .run(tauri::generate_context!())
    .expect("error running tauri application");
}