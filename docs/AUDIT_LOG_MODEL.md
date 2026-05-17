# Phoenix OS Audit Log Model

This document defines the structured log schema, cryptographic signing parameters, and governance specifications for the secure **Phoenix OS** privilege log stream.

---

## 🔒 Log File Definition

All privileged actions must append an audit record to the secure local log:
* **Log Location:** `/var/log/phoenix/governance.log`
* **Access Scope:** Write-only by elevated system helpers; read-only by audited administrators.

---

## 📋 Audit Record Schema

Each line in `governance.log` must represent a single, space-delimited string structured exactly as follows:

`[TIMESTAMP] [OP_ID] [ACTOR_USER] [PRIV_LEVEL] [ACTION_ID] [RESULT_CLASS] [PREVIEW_HASH]`

### Schema Field Specifications:

1. **`TIMESTAMP`:** ISO-8601 UTC date string format: `YYYY-MM-DDTHH:MM:SSZ`.
2. **`OP_ID`:** Unique 8-character alphanumeric string generated securely at execution start (`OP-XXXXXXX`).
3. **`ACTOR_USER`:** The user name triggering the UI process (e.g. `phoenixdebian`).
4. **`PRIV_LEVEL`:** Active privilege tier utilized during execution (`ROOT` or `USER`).
5. **`ACTION_ID`:** The unique canonical Polkit action identifier (`org.aurelia.phoenix.core.read_smart`).
6. **`RESULT_CLASS`:** Action termination outcome classification (`SUCCESS`, `BLOCKED`, or `FAILED`).
7. **`PREVIEW_HASH`:** A SHA256 signature hashing the scanned plan parameters to guarantee that the executed action perfectly matches the preview parameters.

---

## 📝 Example Log Output Trace

```text
[2026-05-17T13:20:10Z] [OP-K9X2J7N4] [phoenixdebian] [ROOT] [org.aurelia.phoenix.core.read_smart] [SUCCESS] [SHA256-e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855]
[2026-05-17T13:22:45Z] [OP-R4V9M3Z1] [phoenixdebian] [USER] [org.aurelia.phoenix.core.disk_mutate] [BLOCKED] [SHA256-8f43c3f81e35d631e5f8f43c3f81e35d631e5f8f43c3f81e35d631e5f8f43c3f]
```
