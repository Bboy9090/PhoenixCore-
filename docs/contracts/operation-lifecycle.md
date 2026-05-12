# Operation Lifecycle

Phoenix Agent operations use a preview-first lifecycle.

## States

| State | Meaning |
| --- | --- |
| `requested` | A UI or client requested an operation. |
| `previewed` | Phoenix Agent created a non-destructive preview. |
| `blocked` | Safety policy blocked the operation. |
| `ready_for_execution` | Preview passed required gates, but execution is not yet started. |
| `queued` | Future executable operation is queued. |
| `running` | Future executable operation is running. |
| `succeeded` | Future executable operation completed. |
| `failed` | Operation failed. |
| `cancelled` | Operation was cancelled. |
| `not_implemented` | Contract exists but behavior is intentionally not wired. |

## Lifecycle

```text
request -> safety evaluation -> preview -> optional execute placeholder -> status -> logs/report
```

## Preview

Preview is non-destructive. It may inspect devices, estimate changes, list required gates, and produce warnings.

Preview must not write to disk, install drivers, patch bootloaders, or modify host state.

## Execute Placeholder

`POST /operations/execute` is a placeholder in PR6.

Future execution requires:

- valid `preview_id`,
- valid `safety_token`,
- matching device identity,
- non-expired preview,
- policy approval,
- audit log start,
- operation-specific tests.

## Logs And Reports

Log export and report bundle endpoints are placeholders in PR6.

Future report bundles should include:

- operation metadata,
- safety gate results,
- device identities,
- warnings and errors,
- environment summary,
- redacted logs.
