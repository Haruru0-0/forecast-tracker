import pytest

from ftracker import sources


@pytest.fixture(autouse=True)
def no_sleep(monkeypatch):
    monkeypatch.setattr(sources, "_sleep", lambda s: None)
