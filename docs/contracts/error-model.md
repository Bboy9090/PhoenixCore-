# Error Model

Phoenix Agent uses a stable error envelope for every non-2xx response.

## Error Envelope

```json
{
  "error": {
    "code": "safety.preview_required",
    "message": "Operation requires a fresh preview before execution.",
    "severity": "error",
    "details": {},
    "correlation_id": "pa_01H00000000000000000000000"
  }
}
```

## Severities

- `info`
- `warning`
- `error`
- `critical`

## Common Codes

| Code | Meaning |
| --- | --- |
| `agent.not_ready` | Phoenix Agent is not ready. |
| `device.not_found` | Device was not found during re-resolution. |
| `device.identity_mismatch` | Client-supplied identity does not match current scan. |
| `device.system_disk_protected` | Device appears to be a system disk. |
| `safety.preview_required` | Operation needs preview first. |
| `safety.preview_expired` | Preview is too old for execution. |
| `safety.gate_failed` | A safety gate failed. |
| `operation.not_implemented` | Endpoint exists as a placeholder only. |
| `operation.not_found` | Operation ID is unknown. |
| `contract.invalid_request` | Request failed validation. |

## HTTP Status Rules

- `400` for invalid request shape.
- `403` for policy or safety denial.
- `404` for unknown devices or operations.
- `409` for identity mismatch or stale preview.
- `422` for valid shape but unsafe operation.
- `501` for PR6 placeholders not implemented.
- `503` for Agent not ready.

## Correlation IDs

All errors and operation responses should include a correlation ID for later report bundles.
