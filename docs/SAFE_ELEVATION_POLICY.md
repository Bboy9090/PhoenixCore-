# Phoenix OS Safe Elevation Policy

This policy governs privilege escalation boundaries, administrative scopes, and audit logging parameters inside the **Phoenix OS / BWOS** runtime environment.

---

## 🚫 Deny-By-Default Mandate

Phoenix OS enforces a absolute **Deny-by-Default** security posture. No graphical UI utility, system helper, or third-party service may execute code with root privileges unless it passes through standard audited elevation boundaries.

1. **No Blanket Root Access:**
   * Applications are strictly prohibited from spawning a general administrative shell (`sudo bash` or root konsole).
   * Polkit overrides allowing blank root execution are illegal.
2. **Operation-Scoped Elevation:**
   * Elevation must only be requested for a singular, discrete, pre-approved action (e.g., retrieving low-level SMART sector flags).
   * The privileged executable must be a compiled, statically scoped helper utility (e.g., the `phoenix-core` Rust binary) designed to handle that specific operation.
3. **Explicit User Approval:**
   * Escalation must spawn a visible, standard graphical Polkit prompt (`pkexec` / system prompt) requiring the operator to enter active administrative credentials.
   * "Silent" or background elevation is strictly prohibited.

---

## 📋 Scoped pkexec / Polkit Integration

Every privileged action must register a corresponding PolicyKit configuration (`.policy`) under `/usr/share/polkit-1/actions/`.

### Canonical Policy Spec Structure:
```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE policyconfig PUBLIC "-//freedesktop//DTD PolicyKit Policy Configuration 1.0//EN"
 "http://www.freedesktop.org/standards/PolicyKit/1/policyconfig.dtd">
<policyconfig>
  <vendor>Bobby's Worldwide OS (Aurelia)</vendor>
  <vendor_url>https://aurelia-os.org</vendor_url>

  <action id="org.aurelia.phoenix.core.read_smart">
    <description>Read raw storage SMART telemetry diagnostics</description>
    <message>Authentication is required to view low-level storage telemetry</message>
    <defaults>
      <allow_any>no</allow_any>
      <allow_inactive>no</allow_inactive>
      <allow_active>auth_admin_keep</allow_active>
    </defaults>
    <annotate key="org.freedesktop.policykit.exec.path">/usr/libexec/phoenix/phoenix-smart-helper</annotate>
  </action>
</policyconfig>
```

---

## 📝 Mandatory Audit Logging Requirements

Every escalated operation must generate a secure, cryptographic audit signature in the system log before executing:
* **Log Location:** `/var/log/phoenix/governance.log` (write-only append stream).
* **Escalation Record Schema:**
  `[TIMESTAMP] [OP_ID] [ACTOR_USER] [PRIV_LEVEL] [ACTION_ID] [RESULT_CLASS] [PREVIEW_HASH]`
* **Audit Integrity:** Purging this log must require physical terminal access under a separate, highly isolated Polkit action.
