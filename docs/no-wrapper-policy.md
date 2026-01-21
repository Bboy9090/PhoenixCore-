# Phoenix No-Wrapper Policy

Phoenix must remain the supplier of core capabilities.

Rules:
1) UI never touches OS APIs.
2) No dependency that becomes "the product."
3) If a third-party tool is used, it must sit behind an adapter interface with:
   - clear replacement plan
   - removal date/milestone
4) Core capabilities are built inside Phoenix:
   - device graph + disk/partition mapping
   - imaging + hashing + verification
   - safety gates
   - evidence reports
