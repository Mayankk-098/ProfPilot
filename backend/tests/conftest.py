import os

import pytest


@pytest.fixture(autouse=True)
def freeze_application_clock(monkeypatch):
    """Keep date-relative API/service tests deterministic."""
    monkeypatch.setenv("PROFPILOT_FIXED_NOW", "2026-10-01T09:00:00")
