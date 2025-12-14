"""Tests for qr_builder.config module."""

import os
import pytest
from unittest.mock import patch

# Reset config before importing
os.environ.setdefault("QR_BUILDER_ENV", "development")
os.environ.setdefault("QR_BUILDER_AUTH_ENABLED", "false")

from qr_builder.config import (
    AppConfig,
    ServerConfig,
    SecurityConfig,
    QRConfig,
    get_config,
    reset_config,
    _parse_bool,
    _parse_list,
)


class TestParseHelpers:
    """Tests for parsing helper functions."""

    def test_parse_bool_true_values(self):
        for val in ["true", "True", "TRUE", "1", "yes", "on"]:
            assert _parse_bool(val) is True

    def test_parse_bool_false_values(self):
        for val in ["false", "False", "FALSE", "0", "no", "off", ""]:
            assert _parse_bool(val) is False

    def test_parse_list_basic(self):
        result = _parse_list("a,b,c")
        assert result == ["a", "b", "c"]

    def test_parse_list_with_spaces(self):
        result = _parse_list("a, b , c")
        assert result == ["a", "b", "c"]

    def test_parse_list_empty(self):
        result = _parse_list("")
        assert result == []

    def test_parse_list_with_empty_items(self):
        result = _parse_list("a,,b")
        assert result == ["a", "b"]


class TestServerConfig:
    """Tests for ServerConfig."""

    def test_default_values(self):
        config = ServerConfig()
        assert config.host == "0.0.0.0"
        assert config.port == 8000
        assert config.reload is False
        assert config.workers == 1
        assert config.log_level == "info"


class TestSecurityConfig:
    """Tests for SecurityConfig."""

    def test_default_values(self):
        config = SecurityConfig()
        # Secret should be auto-generated
        assert len(config.backend_secret) > 20
        assert config.auth_enabled is True
        assert config.max_upload_size_mb == 10


class TestQRConfig:
    """Tests for QRConfig."""

    def test_default_values(self):
        config = QRConfig()
        assert config.max_data_length == 4296
        assert config.max_qr_size == 4000
        assert config.min_qr_size == 21
        assert config.default_size == 500
        assert config.max_batch_size == 100


class TestAppConfig:
    """Tests for AppConfig."""

    def test_from_env_development(self):
        """Test loading development configuration."""
        reset_config()
        env = {
            "QR_BUILDER_ENV": "development",
            "QR_BUILDER_AUTH_ENABLED": "false",
            "QR_BUILDER_PORT": "9000",
        }
        with patch.dict(os.environ, env, clear=False):
            reset_config()
            config = AppConfig.from_env()

            assert config.environment == "development"
            assert config.server.port == 9000
            assert config.security.auth_enabled is False

    def test_from_env_production_requires_secret(self):
        """Test that production requires backend secret."""
        reset_config()
        env = {
            "QR_BUILDER_ENV": "production",
            "QR_BUILDER_AUTH_ENABLED": "true",
            "QR_BUILDER_BACKEND_SECRET": "",  # Empty secret
        }
        with patch.dict(os.environ, env, clear=False):
            reset_config()
            with pytest.raises(ValueError, match="BACKEND_SECRET must be set"):
                AppConfig.from_env()

    def test_validate_valid_config(self):
        """Test validation passes for valid config."""
        config = AppConfig(
            server=ServerConfig(port=8000),
            security=SecurityConfig(backend_secret="test-secret"),
            qr=QRConfig(),
            environment="development",
        )
        issues = config.validate()
        assert len(issues) == 0

    def test_validate_invalid_port(self):
        """Test validation catches invalid port."""
        config = AppConfig(
            server=ServerConfig(port=99999),
            security=SecurityConfig(backend_secret="test"),
            qr=QRConfig(),
            environment="development",
        )
        issues = config.validate()
        assert any("Invalid port" in issue for issue in issues)

    def test_validate_invalid_qr_size(self):
        """Test validation catches invalid QR size range."""
        config = AppConfig(
            server=ServerConfig(),
            security=SecurityConfig(backend_secret="test"),
            qr=QRConfig(min_qr_size=100, max_qr_size=50),
            environment="development",
        )
        issues = config.validate()
        assert any("min_qr_size" in issue for issue in issues)

    def test_validate_production_wildcard_cors(self):
        """Test validation catches wildcard CORS in production."""
        config = AppConfig(
            server=ServerConfig(),
            security=SecurityConfig(
                backend_secret="valid-secret",
                allowed_origins=["*"],
            ),
            qr=QRConfig(),
            environment="production",
        )
        issues = config.validate()
        assert any("Wildcard CORS" in issue for issue in issues)


class TestGetConfig:
    """Tests for get_config singleton."""

    def test_get_config_returns_same_instance(self):
        """Test that get_config returns singleton."""
        reset_config()
        os.environ["QR_BUILDER_ENV"] = "development"
        os.environ["QR_BUILDER_AUTH_ENABLED"] = "false"

        config1 = get_config()
        config2 = get_config()
        assert config1 is config2

    def test_reset_config(self):
        """Test that reset_config clears singleton."""
        reset_config()
        os.environ["QR_BUILDER_ENV"] = "development"
        os.environ["QR_BUILDER_AUTH_ENABLED"] = "false"

        config1 = get_config()
        reset_config()

        os.environ["QR_BUILDER_PORT"] = "9999"
        config2 = get_config()

        assert config2.server.port == 9999
        # Clean up
        os.environ["QR_BUILDER_PORT"] = "8000"
        reset_config()
