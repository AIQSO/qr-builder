# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.3.0] - 2024-12-14

### Added
- **Centralized Configuration** (`config.py`)
  - Type-safe configuration management via dataclasses
  - Environment variable loading with validation
  - Configuration validation for production deployments
  - Singleton pattern for global config access

- **File Upload Validation** (`utils.py`)
  - MIME type detection via magic bytes
  - File size limits (configurable)
  - Content validation for uploaded images
  - Context managers for temporary file cleanup

- **Security Improvements**
  - Constant-time comparison for webhook secrets (prevents timing attacks)
  - SHA256 instead of MD5 for anonymous user key generation
  - Subprocess timeout and validation in `generate_qart()`
  - Input validation for all external command parameters
  - Non-root user in Docker container

- **Documentation**
  - `ARCHITECTURE.md` - System design and module documentation
  - `INSTALL.md` - Comprehensive installation guide
  - `CHANGELOG.md` - This changelog
  - `.env.example` - Environment variable documentation

- **Docker Improvements**
  - Health check configuration
  - Non-root user for security
  - Production-ready environment defaults
  - Resource limits in docker-compose

### Changed
- **Version Consistency**
  - Aligned version to 0.3.0 across all files
  - Updated Python requirement to >=3.10

- **Dependencies**
  - Added `httpx` to main dependencies (required for auth)

- **Configuration**
  - Auth module now uses centralized config
  - Dynamic configuration loading for runtime flexibility

### Fixed
- Version mismatch between `pyproject.toml` and `__init__.py`
- Docker port inconsistency (now consistently uses 8000)
- Subprocess security in `generate_qart()` - added validation and timeout

### Security
- Replaced MD5 with SHA256 for IP-based anonymous key hashing
- Added constant-time string comparison for webhook validation
- Added parameter validation before subprocess execution
- Added file upload content validation

## [0.2.0] - 2024-12-13

### Added
- **Authentication System** (`auth.py`)
  - API key authentication
  - Tier-based access control (free, pro, business, admin)
  - Rate limiting per tier
  - Session management
  - Backend webhook integration for tier updates

- **New QR Styles**
  - `generate_qr_with_text()` - QR with text in center
  - `generate_artistic_qr()` - Image blended into QR pattern
  - `generate_qart()` - Halftone/dithered artistic style

- **API Endpoints**
  - `/qr/text` - QR with text
  - `/qr/logo` - QR with logo
  - `/qr/artistic` - Artistic QR
  - `/qr/qart` - QArt halftone
  - `/batch/artistic` - Batch artistic QR
  - `/webhooks/*` - Backend integration
  - `/usage/*` - Usage tracking
  - `/styles` - List available styles
  - `/tiers` - List tier features
  - `/me` - Current user info

- **Unified Interface**
  - `QRConfig` dataclass for configuration
  - `QRStyle` enum for style selection
  - `generate_qr_unified()` for single-function access

### Changed
- API version updated to 0.3.0
- Enhanced CORS configuration
- Added rate limit headers in responses

## [0.1.0] - 2024-12-12

### Added
- **Core Module** (`core.py`)
  - `generate_qr()` - Basic QR code generation
  - `generate_qr_only()` - Save standalone QR to file
  - `embed_qr_in_image()` - Embed QR into background image
  - `generate_qr_with_logo()` - QR with logo in center
  - `calculate_position()` - Position calculation helper
  - `validate_data()` - Data validation
  - `validate_size()` - Size validation
  - `parse_color()` - Color string parsing

- **CLI** (`cli.py`)
  - `qr` subcommand - Generate basic QR
  - `embed` subcommand - Embed QR in image
  - `logo` subcommand - QR with logo
  - `batch-embed` subcommand - Batch processing

- **REST API** (`api.py`)
  - FastAPI-based REST API
  - `/health` - Health check
  - `/qr` - Basic QR generation
  - `/embed` - Embed QR in image
  - `/batch/embed` - Batch embed
  - OpenAPI documentation at `/docs`
  - CORS support

- **Web Interface** (`server.py`)
  - Tab-based UI for all styles
  - Color picker integration
  - Live preview
  - Download functionality

- **Testing**
  - `test_core.py` - Core function tests
  - `test_api.py` - API endpoint tests

- **Documentation**
  - `README.md` - Project documentation
  - `CLAUDE.md` - Development reference
  - `docs/API.md` - API documentation
  - WordPress integration guide

- **CI/CD**
  - GitHub Actions workflow
  - Linting with ruff
  - Multi-version Python testing
  - Docker build testing

- **Docker Support**
  - Dockerfile for containerization
  - docker-compose.yml for easy deployment

### Dependencies
- qrcode[pil]>=7.4.2
- Pillow>=10.0.0
- fastapi>=0.115.0
- uvicorn[standard]>=0.30.0
- python-multipart>=0.0.9
- amzqr>=0.0.1
- pyqart>=0.1.0
- segno>=1.6.0
- qrcode-artistic>=3.0.0

---

## Migration Guide

### From 0.2.x to 0.3.0

1. **Configuration Changes**
   - Environment variables now use `QR_BUILDER_` prefix
   - Old `BACKEND_SECRET` → `QR_BUILDER_BACKEND_SECRET`
   - See `.env.example` for all variables

2. **Import Changes**
   - New imports available from `qr_builder`:
     ```python
     from qr_builder import get_config, AppConfig
     ```

3. **Docker Changes**
   - Default port is now 8000 (was 8080 for API)
   - Container runs as non-root user
   - Set `QR_BUILDER_AUTH_ENABLED=true` for production

### From 0.1.x to 0.2.x

1. **New Required Dependencies**
   - `amzqr>=0.0.1`
   - `pyqart>=0.1.0`

2. **API Changes**
   - New authentication system
   - Rate limiting headers in responses
   - New endpoints for tiers and usage

---

## Unreleased

### Planned
- Redis integration for distributed rate limiting
- Celery workers for async batch processing
- Prometheus metrics endpoint
- WebSocket support for progress updates
