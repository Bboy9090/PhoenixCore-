use crate::recovery_evidence_bundle::build_recovery_evidence_bundle_v2;
use crate::recovery_session::build_recovery_session_state;
use serde::Serialize;
use serde_json::{Map, Value};
use sha2::{Digest, Sha256};

#[derive(Debug, Clone, Serialize)]
pub struct RecoveryDiagnosticsExportV1 {
    pub schema: &'static str,
    pub evidence_bundle: Value,
    pub session_state: Value,
    pub sanitized_evidence: Value,
    pub redacted_fields: Vec<String>,
    pub destructive_authorization_included: bool,
    pub restore_executable: bool,
    pub system_mutations_performed: bool,
    pub export_sha256: String,
}

fn canonicalize_json(value: &Value) -> Value {
    match value {
        Value::Object(object) => {
            let mut keys: Vec<&String> = object.keys().collect();
            keys.sort();
            let mut canonical = Map::new();
            for key in keys {
                canonical.insert(key.clone(), canonicalize_json(&object[key]));
            }
            Value::Object(canonical)
        }
        Value::Array(items) => {
            Value::Array(items.iter().map(canonicalize_json).collect::<Vec<_>>())
        }
        _ => value.clone(),
    }
}

fn value_sha256(value: &Value) -> String {
    let bytes = serde_json::to_vec(&canonicalize_json(value))
        .expect("diagnostics JSON serialization cannot fail");
    format!("{:x}", Sha256::digest(bytes))
}

fn should_redact(key: &str) -> bool {
    matches!(
        key,
        "path"
            | "canonical_path"
            | "source_path"
            | "staged_path"
            | "partial_path"
            | "output_directory"
            | "destination_path"
            | "receipt_path"
            | "session_path"
            | "bundle_directory"
            | "serial_number"
            | "unique_id"
            | "stdout"
            | "stderr"
            | "arguments"
            | "acknowledgement"
            | "provider_file_id"
    )
}

fn sanitize_value(
    value: &Value,
    pointer: &str,
    redacted_fields: &mut Vec<String>,
) -> Value {
    match value {
        Value::Object(object) => {
            let mut sanitized = Map::new();
            for (key, child) in object {
                let child_pointer = format!("{pointer}/{key}");
                if should_redact(key) {
                    sanitized.insert(key.clone(), Value::String("[redacted]".to_string()));
                    redacted_fields.push(child_pointer);
                } else {
                    sanitized.insert(
                        key.clone(),
                        sanitize_value(child, &child_pointer, redacted_fields),
                    );
                }
            }
            Value::Object(sanitized)
        }
        Value::Array(items) => Value::Array(
            items
                .iter()
                .enumerate()
                .map(|(index, child)| {
                    sanitize_value(child, &format!("{pointer}/{index}"), redacted_fields)
                })
                .collect(),
        ),
        _ => value.clone(),
    }
}

fn export_sha256(export: &RecoveryDiagnosticsExportV1) -> String {
    let mut value =
        serde_json::to_value(export).expect("diagnostics export serialization cannot fail");
    if let Some(object) = value.as_object_mut() {
        object.remove("export_sha256");
    }
    value_sha256(&value)
}

pub fn build_recovery_diagnostics_export(
    evidence: &Value,
) -> Result<RecoveryDiagnosticsExportV1, String> {
    let bundle = build_recovery_evidence_bundle_v2(evidence);
    let bundle_value = serde_json::to_value(bundle)
        .map_err(|error| format!("cannot serialize recovery evidence bundle: {error}"))?;
    let reenumeration = evidence
        .get("target_reenumeration_receipt")
        .filter(|value| !value.is_null());
    let session = build_recovery_session_state(&bundle_value, reenumeration)?;
    let session_value = serde_json::to_value(session)
        .map_err(|error| format!("cannot serialize recovery session state: {error}"))?;

    let mut redacted_fields = Vec::new();
    let sanitized_evidence = sanitize_value(evidence, "", &mut redacted_fields);
    redacted_fields.sort();
    redacted_fields.dedup();

    let mut export = RecoveryDiagnosticsExportV1 {
        schema: "phoenix_key.recovery_diagnostics_export.v1",
        evidence_bundle: bundle_value,
        session_state: session_value,
        sanitized_evidence,
        redacted_fields,
        destructive_authorization_included: false,
        restore_executable: false,
        system_mutations_performed: false,
        export_sha256: String::new(),
    };
    export.export_sha256 = export_sha256(&export);
    Ok(export)
}

#[tauri::command]
pub fn build_windows_recovery_diagnostics_export(
    evidence_json: String,
) -> Result<RecoveryDiagnosticsExportV1, String> {
    let evidence: Value = serde_json::from_str(&evidence_json)
        .map_err(|error| format!("invalid recovery evidence JSON: {error}"))?;
    build_recovery_diagnostics_export(&evidence)
}

#[cfg(test)]
mod tests {
    use super::{build_recovery_diagnostics_export, export_sha256};
    use serde_json::json;

    #[test]
    fn export_redacts_paths_hardware_ids_and_acknowledgement() {
        let evidence = json!({
            "identity_bound_plan": {
                "source_identity": {
                    "canonical_path": "C:/Users/Alice/private/install.wim",
                    "sha256": "a".repeat(64)
                }
            },
            "target_safety": {
                "serial_number": "SECRET-SERIAL",
                "unique_id": "SECRET-UNIQUE",
                "target_stable_identity_sha256": "b".repeat(64)
            },
            "data_preservation_receipt": {
                "acknowledgement": "I ACCEPT DATA LOSS ON THIS TARGET"
            }
        });

        let export = build_recovery_diagnostics_export(&evidence).unwrap();
        assert_eq!(
            export.sanitized_evidence["identity_bound_plan"]["source_identity"]
                ["canonical_path"],
            "[redacted]"
        );
        assert_eq!(
            export.sanitized_evidence["target_safety"]["serial_number"],
            "[redacted]"
        );
        assert_eq!(
            export.sanitized_evidence["target_safety"]["unique_id"],
            "[redacted]"
        );
        assert_eq!(
            export.sanitized_evidence["data_preservation_receipt"]
                ["acknowledgement"],
            "[redacted]"
        );
        assert_eq!(
            export.sanitized_evidence["identity_bound_plan"]["source_identity"]["sha256"],
            "a".repeat(64)
        );
        assert!(!export.destructive_authorization_included);
        assert!(!export.restore_executable);
        assert!(!export.system_mutations_performed);
        assert_eq!(export.export_sha256.len(), 64);
        assert_eq!(export.export_sha256, export_sha256(&export));
    }

    #[test]
    fn command_output_and_provider_ids_are_redacted() {
        let evidence = json!({
            "boot": {
                "stdout": "C:/Users/Alice",
                "stderr": "sensitive",
                "arguments": ["/enum", "all"]
            },
            "drive": {
                "provider_file_id": "provider-secret"
            }
        });
        let export = build_recovery_diagnostics_export(&evidence).unwrap();
        assert_eq!(export.sanitized_evidence["boot"]["stdout"], "[redacted]");
        assert_eq!(export.sanitized_evidence["boot"]["stderr"], "[redacted]");
        assert_eq!(export.sanitized_evidence["boot"]["arguments"], "[redacted]");
        assert_eq!(
            export.sanitized_evidence["drive"]["provider_file_id"],
            "[redacted]"
        );
    }
}
