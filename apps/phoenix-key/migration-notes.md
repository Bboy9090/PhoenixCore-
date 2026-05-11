# Phoenix Key Migration Notes

Current source and concept candidates:

- Product blueprint: `docs/phoenix_key_legendary_blueprint.md`.
- BootForge recovery code: `desktop/src/recovery/`.
- USB and imaging logic: `desktop/src/core/usb_builder.py`, `desktop/src/imaging/`, and `crates/imaging/`.
- Safety gates and reports: `crates/safety/`, `crates/report/`, and `desktop/src/core/safety_validator.py`.

Migration rule:

Keep Phoenix Key as a rescue/provisioning mode that shares Phoenix OS, BootForge, and Phoenix Agent foundations. Do not fork it into an unrelated recovery-only product.

Not migrated in PR 3:

- Recovery UI.
- Provisioning workflows.
- Boot media integration.
