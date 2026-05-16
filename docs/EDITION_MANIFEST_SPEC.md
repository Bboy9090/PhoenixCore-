# EDITION MANIFEST SPECIFICATION

Edition manifests are YAML files located in `editions/*/edition.yaml`. They define how the BWOS platform is synthesized into a specific product.

## 1. Required Fields

| Field | Type | Description |
|-------|------|-------------|
| `id` | String | Unique slug for the edition (e.g., `thunder-god`). |
| `display_name` | String | User-facing name of the edition. |
| `parent` | String | Must be `Bobby’s Worldwide OS`. |
| `edition_type` | String | One of: `premium`, `professional`, `industrial`, `legacy`. |
| `tagline` | String | Short marketing slogan. |
| `inherits_core_safety_rules` | Boolean | Must be `true`. |

## 2. Theme and Palette
The `theme` block defines the HSL or Hex colors used by the UI. The `palette.path` points to a `colors.css` file containing CSS variables.

## 3. Safety Enforcement
The `safety` block is mandatory and must follow these defaults:

```yaml
safety:
  allow_destructive_disk_ops_by_default: false
  require_dry_run_for_recovery_ops: true
  inherit_agent_permissions: true
  inherit_audit_rules: true
```

Editions cannot override `allow_destructive_disk_ops_by_default` to `true` without platform-level security clearance.

## 4. Package Profiles
`packages.profile` points to `package-profile.txt`, a newline-delimited list of packages to include in the final image. `bwos-core` is always required.
