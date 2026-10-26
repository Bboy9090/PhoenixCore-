# ARCWYRE external qualification infrastructure

These definitions add independent build lanes; they do not authorize disk writes.

- `aws/buildspec-windows-release.yml` is the primary native Windows compile and
  test lane. Its artifact is evidence input, not hardware proof.
- `google/cloudbuild-independent.yaml` independently reruns portable Python,
  dashboard, and locked Rust checks.
- `scripts/release/evaluate_arcwyre_release_gate.py` rejects promotion until all
  receipts required by the requested level exist, match the exact source commit,
  pass their gate, and retain an intact canonical SHA-256.

Cloud executors must never receive a general command that selects or erases a
physical disk. Physical USB provisioning requires a separately designated lab
target, local elevation, exact target identity review, a one-time authorization,
readback, and a named-machine boot receipt.
