from __future__ import annotations

import os
from pathlib import Path

from trustedge_wg import env as env_module
from trustedge_wg.constants import ENV_API_TOKEN, ENV_API_URL


def test_load_dotenv_file_parses_comments_and_quotes(tmp_path: Path) -> None:
    dotenv = tmp_path / ".env"
    dotenv.write_text(
        "# comment\n"
        "export TRUSTEDGE_API_URL='https://api.test.local'\n"
        'TRUSTEDGE_API_TOKEN="secret-token"\n',
        encoding="utf-8",
    )
    env_module._load_dotenv_file(dotenv)
    assert os.environ[ENV_API_URL] == "https://api.test.local"
    assert os.environ[ENV_API_TOKEN] == "secret-token"


def test_load_dotenv_file_does_not_override_existing_env(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv(ENV_API_URL, "https://existing.example.com")
    dotenv = tmp_path / ".env"
    dotenv.write_text("TRUSTEDGE_API_URL=https://from-file.example.com\n", encoding="utf-8")
    env_module._load_dotenv_file(dotenv, override=False)
    assert os.environ[ENV_API_URL] == "https://existing.example.com"


def test_load_dotenv_file_override_replaces_existing_env(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv(ENV_API_URL, "https://existing.example.com")
    dotenv = tmp_path / ".env"
    dotenv.write_text("TRUSTEDGE_API_URL=https://from-file.example.com\n", encoding="utf-8")
    env_module._load_dotenv_file(dotenv, override=True)
    assert os.environ[ENV_API_URL] == "https://from-file.example.com"


def test_api_url_and_token_empty_when_unset() -> None:
    assert env_module.api_url() == ""
    assert env_module.api_token() == ""


def test_api_url_and_token_read_from_environment(monkeypatch) -> None:
    monkeypatch.setenv(ENV_API_URL, "https://api.example.com")
    monkeypatch.setenv(ENV_API_TOKEN, "tok")
    assert env_module.api_url() == "https://api.example.com"
    assert env_module.api_token() == "tok"
