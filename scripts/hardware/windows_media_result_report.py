"""Render conservative reports from internal assessments; grants no authority."""

from __future__ import annotations

from typing import Any

SCHEMAS = {
    "staging": "arcwyre.windows_install_staging.v1",
    "preparation": "arcwyre.windows_install_preparation.v1",
    "compatibility": "arcwyre.windows_media_boot_compatibility.v1",
    "rehearsal": "arcwyre.restore_rehearsal_assessment.v1",
    "resume": "arcwyre.windows_media_resume_assessment.v1",
}


def build_result_report(
    *,
    staging: Any = None,
    preparation: Any = None,
    compatibility: Any = None,
    rehearsal: Any = None,
    resume: Any = None,
    failure: Any = None,
) -> dict[str, Any]:
    """Report supplied results without upgrading them to trusted boot evidence."""
    failures: list[str] = []
    sections = {}
    for name, value in (
        ("staging", staging),
        ("preparation", preparation),
        ("compatibility", compatibility),
        ("rehearsal", rehearsal),
        ("resume", resume),
    ):
        if value is None:
            continue
        if not isinstance(value, dict) or value.get("schema") != SCHEMAS[name]:
            failures.append(f"{name}: malformed or unsupported result")
            continue
        if any(value.get(field) is True for field in (
            "boot_proven", "boot_verified", "write_authorized",
            "restore_executor_authorized", "physical_writes_authorized",
        )):
            failures.append(f"{name}: unsupported authorization or boot claim")
            continue
        valid = True
        for field in ("block_reasons", "unresolved_reasons"):
            reasons = value.get(field, [])
            if not isinstance(reasons, list) or not all(
                isinstance(reason, str) and reason.strip() for reason in reasons
            ):
                failures.append(f"{name}: malformed {field}")
                valid = False
            else:
                failures.extend(f"{name}: {reason}" for reason in reasons)
        if valid:
            sections[name] = value

    output_path = None
    reported_bytes = None
    staged = sections.get("staging", {})
    if staged:
        count = staged.get("verified_bytes")
        path = staged.get("staging_directory")
        if (
            type(count) is not int or count < 0
            or not isinstance(path, str) or not path.strip()
            or staged.get("staging_verified") is not True
            or staged.get("raw_disk_operations_performed") is not False
        ):
            failures.append("staging: incomplete file-verification result")
        else:
            reported_bytes = count
            output_path = path

    resumed = sections.get("resume", {})
    prepared = sections.get("preparation", {})
    preparation_bytes = None
    if prepared:
        count = prepared.get("verified_bytes")
        path = prepared.get("staging_directory")
        if (
            type(count) is not int or count < 0
            or not isinstance(path, str) or not path.strip()
            or prepared.get("staging_verified") is not True
            or prepared.get("raw_disk_operations_performed") is not False
            or prepared.get("original_source_modified") is not False
        ):
            failures.append("preparation: incomplete file-verification result")
        else:
            preparation_bytes = count
            output_path = path
        failures.append("preparation: independent image integrity and boot remain unverified")
    if resumed:
        done = resumed.get("verified_completed_bytes")
        total = resumed.get("source_total_bytes")
        if type(done) is not int or type(total) is not int or not 0 <= done <= total:
            failures.append("resume: invalid byte counts")

    if failure is not None:
        if not isinstance(failure, dict) or not isinstance(failure.get("message"), str):
            failures.append("operation: malformed failure result")
        else:
            failures.append(f"operation: {failure['message']}")
            partial = failure.get("partial_directory")
            if isinstance(partial, str) and partial.strip():
                output_path = partial

    if not sections and failure is None:
        failures.append("operation: no valid assessment supplied")
    next_step = (
        "Resolve the reported failures; preserve partial output for inspection."
        if failures else
        "Review the media preparation plan; a real boot test is still required."
    )
    lines = ["Windows media operation report"]
    if reported_bytes is not None:
        lines.append(f"Reported staging file readback: {reported_bytes} bytes.")
    else:
        lines.append("No valid staging file-readback result supplied.")
    if output_path:
        lines.append(f"Output for inspection: {output_path}")
    if preparation_bytes is not None:
        lines.append(f"Reported prepared file readback: {preparation_bytes} bytes.")
    lines.extend(f"Unresolved: {reason}" for reason in failures)
    lines.extend([
        "Boot verification: not proven. Data rescue: not verified.",
        f"Next step: {next_step}",
    ])
    return {
        "schema": "arcwyre.windows_media_result_report.v1",
        "reported_staging_verified_bytes": reported_bytes,
        "reported_preparation_verified_bytes": preparation_bytes,
        "evidence_scope": "supplied_assessments_not_independently_verified",
        "output_path": output_path,
        "output_requires_review": output_path is not None,
        "unresolved_reasons": failures,
        "boot_proven": False,
        "data_rescue_verified": False,
        "write_authorized": False,
        "next_step": next_step,
        "text": "\n".join(lines),
    }
