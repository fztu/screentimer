import hashlib
import json
import os
from pathlib import Path
import pytest
from screentimer.config import AppConfig, ConfigStore, hash_password


def test_hash_password_returns_sha256_hex():
    result = hash_password("secret")
    expected = hashlib.sha256("secret".encode()).hexdigest()
    assert result == expected


def test_hash_password_empty_string():
    result = hash_password("")
    assert result == hashlib.sha256(b"").hexdigest()


def test_appconfig_defaults():
    cfg = AppConfig(lock_interval_mins=30, auto_unlock_mins=5, password_hash="abc")
    assert cfg.lock_interval_mins == 30
    assert cfg.auto_unlock_mins == 5
    assert cfg.password_hash == "abc"


def test_appconfig_check_password_correct():
    h = hash_password("mypassword")
    cfg = AppConfig(lock_interval_mins=10, auto_unlock_mins=2, password_hash=h)
    assert cfg.check_password("mypassword") is True


def test_appconfig_check_password_wrong():
    h = hash_password("mypassword")
    cfg = AppConfig(lock_interval_mins=10, auto_unlock_mins=2, password_hash=h)
    assert cfg.check_password("wrong") is False


def test_configstore_save_and_load(tmp_path):
    store = ConfigStore(config_dir=tmp_path)
    cfg = AppConfig(lock_interval_mins=20, auto_unlock_mins=3, password_hash=hash_password("pw"))
    store.save(cfg)

    loaded = store.load()
    assert loaded is not None
    assert loaded.lock_interval_mins == 20
    assert loaded.auto_unlock_mins == 3
    assert loaded.password_hash == hash_password("pw")


def test_configstore_load_returns_none_when_missing(tmp_path):
    store = ConfigStore(config_dir=tmp_path)
    assert store.load() is None


def test_configstore_creates_directory(tmp_path):
    nested = tmp_path / "a" / "b"
    store = ConfigStore(config_dir=nested)
    cfg = AppConfig(lock_interval_mins=5, auto_unlock_mins=1, password_hash="x")
    store.save(cfg)
    assert (nested / "config.json").exists()
