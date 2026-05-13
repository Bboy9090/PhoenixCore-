# Phoenix Device Identity Model

Accurate hardware identification is critical for the safety doctrine.

## Identity Attributes
A verified `device_identity` must include:
- `vendor`: Hardware manufacturer (e.g., Apple, Dell).
- `model`: Specific model identifier (e.g., MacBookPro16,1).
- `serial`: Unique serial number (if available via interrogation).
- `transport`: Connection type (SATA, NVMe, USB, Network).
- `classification`: `removable` | `system` | `external`.
- `safety_classification`: (protected | writable | restricted).

## Interrogation Requirements
Identity should not be assumed from OS reports alone. The Agent should use native tools (via Rust system crates) to verify:
1. Physical port mapping.
2. Partition table GUIDs.
3. Firmware-level identifiers.
