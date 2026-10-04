"""Application clock with an optional deterministic test override.

Set PROFPILOT_FIXED_NOW to an ISO-8601 datetime only in tests/local verification.
Production defaults to the system clock.
"""
from __future__ import annotations

import os
from datetime import date, datetime


def now() -> datetime:
    fixed = os.getenv("PROFPILOT_FIXED_NOW")
    if fixed:
        try:
            return datetime.fromisoformat(fixed)
        except ValueError as exc:
            raise RuntimeError(
                "PROFPILOT_FIXED_NOW must be an ISO-8601 datetime"
            ) from exc
    return datetime.now()


def today() -> date:
    return now().date()
