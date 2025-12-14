"""Tests for qr_builder.utils module."""

import os
import pytest
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

# Set test environment before imports
os.environ.setdefault("QR_BUILDER_ENV", "development")
os.environ.setdefault("QR_BUILDER_AUTH_ENABLED", "false")

from qr_builder.utils import (
    detect_image_type,
    validate_upload_file,
    temp_file_context,
    temp_output_context,
    read_and_cleanup,
    VALID_IMAGE_TYPES,
)


class TestDetectImageType:
    """Tests for image type detection."""

    def test_detect_png(self):
        """Test PNG detection."""
        # PNG magic bytes
        png_bytes = b'\x89PNG\r\n\x1a\n' + b'\x00' * 100
        assert detect_image_type(png_bytes) == 'image/png'

    def test_detect_jpeg(self):
        """Test JPEG detection."""
        # JPEG magic bytes
        jpeg_bytes = b'\xff\xd8\xff' + b'\x00' * 100
        assert detect_image_type(jpeg_bytes) == 'image/jpeg'

    def test_detect_gif87a(self):
        """Test GIF87a detection."""
        gif_bytes = b'GIF87a' + b'\x00' * 100
        assert detect_image_type(gif_bytes) == 'image/gif'

    def test_detect_gif89a(self):
        """Test GIF89a detection."""
        gif_bytes = b'GIF89a' + b'\x00' * 100
        assert detect_image_type(gif_bytes) == 'image/gif'

    def test_detect_webp(self):
        """Test WebP detection."""
        # WebP has RIFF header with WEBP at offset 8
        webp_bytes = b'RIFF\x00\x00\x00\x00WEBP' + b'\x00' * 100
        assert detect_image_type(webp_bytes) == 'image/webp'

    def test_detect_bmp(self):
        """Test BMP detection."""
        bmp_bytes = b'BM' + b'\x00' * 100
        assert detect_image_type(bmp_bytes) == 'image/bmp'

    def test_detect_unknown(self):
        """Test unknown format returns None."""
        unknown_bytes = b'unknown format data'
        assert detect_image_type(unknown_bytes) is None


class TestValidateUploadFile:
    """Tests for file upload validation."""

    @pytest.fixture
    def mock_upload_file(self):
        """Create a mock UploadFile."""
        def _create(content: bytes, content_type: str = "image/png", filename: str = "test.png"):
            mock = MagicMock()
            mock.read = AsyncMock(return_value=content)
            mock.content_type = content_type
            mock.filename = filename
            return mock
        return _create

    @pytest.mark.asyncio
    async def test_valid_png(self, mock_upload_file):
        """Test valid PNG file passes validation."""
        # Create a minimal valid PNG
        png_bytes = b'\x89PNG\r\n\x1a\n' + b'\x00' * 100
        file = mock_upload_file(png_bytes, "image/png")

        content = await validate_upload_file(file)
        assert content == png_bytes

    @pytest.mark.asyncio
    async def test_file_too_large(self, mock_upload_file):
        """Test file size limit is enforced."""
        # Create a file larger than 1MB limit
        large_bytes = b'\x89PNG\r\n\x1a\n' + b'\x00' * (2 * 1024 * 1024)
        file = mock_upload_file(large_bytes, "image/png")

        with pytest.raises(Exception) as exc_info:
            await validate_upload_file(file, max_size_mb=1)
        assert "too large" in str(exc_info.value.detail).lower()

    @pytest.mark.asyncio
    async def test_empty_file(self, mock_upload_file):
        """Test empty file is rejected."""
        file = mock_upload_file(b"", "image/png")

        with pytest.raises(Exception) as exc_info:
            await validate_upload_file(file)
        assert "empty" in str(exc_info.value.detail).lower()

    @pytest.mark.asyncio
    async def test_invalid_mime_type(self, mock_upload_file):
        """Test invalid MIME type is rejected."""
        # Not an image - just text data
        file = mock_upload_file(b"not an image", "text/plain")

        with pytest.raises(Exception) as exc_info:
            await validate_upload_file(file)
        assert "Invalid" in str(exc_info.value.detail)


class TestTempFileContext:
    """Tests for temporary file context managers."""

    def test_temp_file_context_creates_file(self):
        """Test temp file is created with content."""
        content = b"test content"

        with temp_file_context(content, suffix=".txt") as path:
            assert path.exists()
            assert path.read_bytes() == content
            assert path.suffix == ".txt"

        # File should be cleaned up
        assert not path.exists()

    def test_temp_file_context_cleanup_on_error(self):
        """Test temp file is cleaned up even on error."""
        content = b"test content"
        captured_path = None

        try:
            with temp_file_context(content) as path:
                captured_path = path
                raise ValueError("Test error")
        except ValueError:
            pass

        # File should still be cleaned up
        assert captured_path is not None
        assert not captured_path.exists()

    def test_temp_output_context(self):
        """Test temp output file context."""
        with temp_output_context(suffix=".png") as path:
            # Write something to the file
            path.write_bytes(b"test output")
            assert path.exists()

        # File should be cleaned up
        assert not path.exists()


class TestReadAndCleanup:
    """Tests for read_and_cleanup function."""

    def test_read_and_cleanup(self):
        """Test file is read and deleted."""
        # Create a temp file
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as f:
            f.write(b"test content")
            path = Path(f.name)

        # Read and cleanup
        content = read_and_cleanup(path)

        assert content == b"test content"
        assert not path.exists()

    def test_read_and_cleanup_nonexistent(self):
        """Test reading nonexistent file raises error."""
        path = Path("/nonexistent/file.txt")

        with pytest.raises(FileNotFoundError):
            read_and_cleanup(path)
