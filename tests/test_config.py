import os
import json
import pytest
from claimer import load_profiles

def test_load_profiles_success(tmp_path):
    # Create a temporary valid configuration file
    config_file = tmp_path / "profiles.json"
    dummy_profiles = [
        {"name": "Player One", "uid": "123456789012"},
        {"name": "Player Two", "uid": "987654321098"}
    ]
    with open(config_file, "w") as f:
        json.dump(dummy_profiles, f)
        
    loaded = load_profiles(str(config_file))
    assert len(loaded) == 2
    assert loaded[0]["name"] == "Player One"
    assert loaded[0]["uid"] == "123456789012"
    assert loaded[1]["name"] == "Player Two"
    assert loaded[1]["uid"] == "987654321098"

def test_load_profiles_missing():
    # Attempt to load a file that does not exist
    loaded = load_profiles("config/non_existent_profiles.json")
    assert isinstance(loaded, list)
    assert len(loaded) == 0

def test_load_profiles_malformed(tmp_path):
    # Create a temporary malformed configuration file
    config_file = tmp_path / "profiles.json"
    with open(config_file, "w") as f:
        f.write("[ malformed json")
        
    loaded = load_profiles(str(config_file))
    assert isinstance(loaded, list)
    assert len(loaded) == 0

def test_load_profiles_from_env_success(monkeypatch):
    dummy_profiles = [
        {"name": "Env Player", "uid": "111222333444"}
    ]
    monkeypatch.setenv("CODM_PROFILES", json.dumps(dummy_profiles))
    loaded = load_profiles("non_existent_file.json")
    assert len(loaded) == 1
    assert loaded[0]["name"] == "Env Player"
    assert loaded[0]["uid"] == "111222333444"

def test_load_profiles_from_env_malformed(monkeypatch):
    monkeypatch.setenv("CODM_PROFILES", "[ malformed json")
    loaded = load_profiles("non_existent_file.json")
    assert isinstance(loaded, list)
    assert len(loaded) == 0
