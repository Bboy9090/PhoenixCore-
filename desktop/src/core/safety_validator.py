"""
BootForge safety API — re-exports the canonical implementation.

The single source of truth lives in **packages/phoenix_safety** (`phoenix_safety.safety_validator`).
Install with: `pip install -e packages/phoenix_safety` (included from repo root `requirements.txt`).
"""

from phoenix_safety.safety_validator import *  # noqa: F403
