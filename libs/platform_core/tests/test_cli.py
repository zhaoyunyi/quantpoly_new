"""CLI 接口测试。"""
import json
import subprocess
import sys

import pytest


PYTHON = sys.executable or "python3.11"
CLI_MODULE = "platform_core.cli"


class TestCLI:
    """Test平台核心CLI接口。"""

    def test_config_command_dotenv_default(self, tmp_path, monkeypatch):
        """未显式指定 --env-file 时应读取 model_config 默认 .env。"""
        env_file = tmp_path / ".env"
        env_file.write_text("ENVIRONMENT=production\nSECRET_KEY=from-dotenv\n", encoding="utf-8")
        monkeypatch.chdir(tmp_path)

        result = subprocess.run(
            [PYTHON, "-m", CLI_MODULE, "config"],
            capture_output=True,
            text=True,
            env={
                "PATH": "",
            },
        )

        data = json.loads(result.stdout)
        assert data["success"] is True
        assert data["data"]["environment"] == "production"

    def test_validate_command_dotenv_default(self, tmp_path):
        """validate 在未传 --env-file 时也应读取 .env 并执行校验。"""
        env_file = tmp_path / ".env"
        env_file.write_text("ENVIRONMENT=production\nSECRET_KEY=\n", encoding="utf-8")

        result = subprocess.run(
            [PYTHON, "-m", CLI_MODULE, "validate"],
            capture_output=True,
            text=True,
            cwd=tmp_path,
            env={
                "PATH": "",
            },
        )

        data = json.loads(result.stdout)
        assert data["success"] is False
        assert data["error"]["code"] == "CONFIG_VALIDATION_ERROR"

    def test_config_command_outputs_json(self, monkeypatch):
        monkeypatch.setenv("ENVIRONMENT", "local")
        monkeypatch.setenv("SECRET_KEY", "")
        result = subprocess.run(
            [PYTHON, "-m", CLI_MODULE, "config"],
            capture_output=True,
            text=True,
        )
        data = json.loads(result.stdout)
        assert data["success"] is True
        assert data["data"]["environment"] == "local"

    def test_validate_command_local_ok(self, monkeypatch):
        monkeypatch.setenv("ENVIRONMENT", "local")
        monkeypatch.setenv("SECRET_KEY", "")
        result = subprocess.run(
            [PYTHON, "-m", CLI_MODULE, "validate"],
            capture_output=True,
            text=True,
        )
        data = json.loads(result.stdout)
        assert data["success"] is True

    def test_validate_command_production_fail(self):
        result = subprocess.run(
            [PYTHON, "-m", CLI_MODULE, "validate"],
            capture_output=True,
            text=True,
            env={
                "ENVIRONMENT": "production",
                "SECRET_KEY": "",
                "PATH": "",
            },
        )
        data = json.loads(result.stdout)
        assert data["success"] is False
        assert data["error"]["code"] == "CONFIG_VALIDATION_ERROR"

    def test_mask_command_with_arg(self):
        result = subprocess.run(
            [PYTHON, "-m", CLI_MODULE, "mask", "password=secret123"],
            capture_output=True,
            text=True,
        )
        data = json.loads(result.stdout)
        assert data["success"] is True
        assert "secret123" not in data["data"]["masked"]

    def test_mask_command_from_stdin(self):
        result = subprocess.run(
            [PYTHON, "-m", CLI_MODULE, "mask"],
            capture_output=True,
            text=True,
            input="api_key=sk-abcdef123456",
        )
        data = json.loads(result.stdout)
        assert data["success"] is True
        assert "sk-abcdef123456" not in data["data"]["masked"]

    def test_mask_command_empty_string_arg(self):
        """显式传入空字符串参数时不应读取 stdin 阻塞。"""
        result = subprocess.run(
            [PYTHON, "-m", CLI_MODULE, "mask", ""],
            capture_output=True,
            text=True,
            input="token=should-not-read-stdin",
        )

        data = json.loads(result.stdout)
        assert data["success"] is True
        assert data["data"]["masked"] == ""

    def test_no_command_exits_nonzero(self):
        result = subprocess.run(
            [PYTHON, "-m", CLI_MODULE],
            capture_output=True,
            text=True,
        )
        assert result.returncode != 0
