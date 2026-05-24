# PR39D Home Boot Repeatability + Clean Shutdown Validation

Status: **repeatability not proven; clean shutdown not verified**

## Canonical Evidence

- Artifact: `bwos-home.iso`
- SHA256: `8f5e094ca9164d8b117a07ea2371816c8afdd0e4ad8d7e6a47d00195b93f5f32`
- Canonical classification: `BOOT_PASS_DESKTOP`
- Canonical evidence path: `iso/outputs/vm-boot-evidence/home/20260523T150945Z/`

## Repeatability Attempts

| Attempt | Timestamp | Result Stage | Desktop | Clean Shutdown | Shutdown Method | Notes |
|---|---|---|---|---|---|---|
| canonical | 20260523T150945Z | BOOT_PASS_DESKTOP | True | False | not verified | PR39C canonical desktop-confirmed boot; strongest evidence retained as canonical. |
| A | 20260523T172910Z | BOOT_FAIL_DISPLAY | False | False | forced kill | Repeatability attempt reached graphical/login boundary but no desktop confirmation. |
| B | 20260523T174109Z | BOOT_FAIL_DISPLAY | False | False | forced kill | Repeatability attempt again reached graphical/login boundary only. |


## Outcome

- Desktop repeatable: `false`
- Clean shutdown verified: `false`
- Repeatability risk: `true`
- Canonical boot status was not downgraded.
- Weaker reruns are stored as separate evidence attempts and did not overwrite the stronger desktop-confirmed row.

## Validation Notes

- Attempt A reached the graphical/login boundary and was terminated by the host after observation.
- Attempt B reached the graphical/login boundary and was terminated by the host after observation.
- ACPI/QMP shutdown did not produce a verified clean exit, so the shutdown path remains unproven.
