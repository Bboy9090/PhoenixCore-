# Phoenix No-Wrapper Policy

Phoenix must remain the supplier of core capabilities.

Rules:
1) UI never touches OS APIs.
2) No external tool is required at runtime for core capabilities.
3) No dependency becomes "the product."
4) If a third-party tool is used, it must sit behind an adapter interface with:
   - replacement milestone + removal plan
   - replacement issue + deadline (date or version)
5) Safety rules for destructive operations:
   - default deny for destructive writes
   - system disk blocked unless force-mode + confirmation token
6) Core capabilities are built inside Phoenix:
   - disk + volume mapping
   - imaging + hashing + verification
   - safety gates
   - evidence reports

## References
- docs/cursor-issues/epic-001-replace-third-party-tooling.md
- docs/contribution-rules.md
- docs/core-contracts.md
