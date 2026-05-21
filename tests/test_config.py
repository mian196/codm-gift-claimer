import os
import json
import pytest
from claimer import load_profiles

def test_load_profiles_from_env_success(monkeypatch):
    dummy_profiles = [
        {"name": "Env Player", "uid": "111222333444"}
    ]
    monkeypatch.setenv("CODM_PROFILES", json.dumps(dummy_profiles))
    loaded = load_profiles()
    assert len(loaded) == 1
    assert loaded[0]["name"] == "Env Player"
    assert loaded[0]["uid"] == "111222333444"

def test_load_profiles_from_env_malformed(monkeypatch):
    monkeypatch.setenv("CODM_PROFILES", "[ malformed json")
    loaded = load_profiles()
    assert isinstance(loaded, list)
    assert len(loaded) == 0

def test_load_profiles_from_env_missing(monkeypatch):
    monkeypatch.delenv("CODM_PROFILES", raising=False)
    loaded = load_profiles()
    assert isinstance(loaded, list)
    assert len(loaded) == 0
