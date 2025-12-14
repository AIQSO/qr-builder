"""
qr_builder.utils
----------------

Utility functions for QR Builder.
"""

from __future__ import annotations

import contextlib
import logging
import tempfile
from collections.abc import Generator
from pathlib import Path

from fastapi import HTTPException, UploadFile

from .config import get_config

logger = logging.getLogger(__name__)

# Valid image MIME types
VALID_IMAGE_TYPES = {
    "image/png",
    "image/jpeg",
    "image/jpg",
    "image/gif",
    "image/webp",
    "image/bmp",
}

# Magic bytes for image file detection
IMAGE_MAGIC_BYTES = {
    b'\x89PNG\r\n\x1a\n': 'image/png',
    b'\xff\xd8\xff': 'image/jpeg',
    b'GIF87a': 'image/gif',
    b'GIF89a': 'image/gif',
    b'RIFF': 'image/webp',  # WebP (partial check)
    b'BM': 'image/bmp',
}


def detect_image_type(data: bytes) -> str | None:
    """Detect image type from magic bytes."""
    for magic, mime_type in IMAGE_MAGIC_BYTES.items():
        if data.startswith(magic):
            return mime_type
    # WebP has RIFF header but needs additional check
    if data.startswith(b'RIFF') and len(data) > 12 and data[8:12] == b'WEBP':
        return 'image/webp'
    return None


async def validate_upload_file(
    file: UploadFile,
    max_size_mb: int | None = None,
    allowed_types: set | None = None,
) -> bytes:
    """
    Validate and read an uploaded file.

    Args:
        file: The uploaded file to validate.
        max_size_mb: Maximum file size in MB (uses config default if None).
        allowed_types: Set of allowed MIME types (uses VALID_IMAGE_TYPES if None).

    Returns:
        The file contents as bytes.

    Raises:
        HTTPException: If validation fails.
    """
    config = get_config()

    if max_size_mb is None:
        max_size_mb = config.security.max_upload_size_mb

    if allowed_types is None:
        allowed_types = VALID_IMAGE_TYPES

    max_size_bytes = max_size_mb * 1024 * 1024

    # Read file content
    try:
        content = await file.read()
    except Exception as e:
        logger.warning(f"Failed to read uploaded file: {e}")
        raise HTTPException(
            status_code=400,
            detail="Failed to read uploaded file"
        ) from e

    # Check file size
    if len(content) > max_size_bytes:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Maximum size is {max_size_mb}MB"
        )

    if len(content) == 0:
        raise HTTPException(
            status_code=400,
            detail="Uploaded file is empty"
        )

    # Detect actual content type from magic bytes
    detected_type = detect_image_type(content)

    # Check declared content type
    declared_type = file.content_type or ""

    # Validate content type
    if detected_type is None:
        # Fall back to declared type if we can't detect
        if declared_type not in allowed_types:
            raise HTTPException(
                status_code=415,
                detail=f"Invalid file type. Allowed types: {', '.join(allowed_types)}"
            )
    else:
        # Verify detected type matches or is valid
        if detected_type not in allowed_types:
            raise HTTPException(
                status_code=415,
                detail=f"Invalid image type detected. Allowed types: {', '.join(allowed_types)}"
            )

    logger.debug(
        f"Validated upload: {file.filename}, "
        f"size={len(content)} bytes, "
        f"declared={declared_type}, "
        f"detected={detected_type}"
    )

    return content


@contextlib.contextmanager
def temp_file_context(
    content: bytes,
    suffix: str = ".png",
) -> Generator[Path, None, None]:
    """
    Context manager for creating a temporary file with content.

    Ensures the file is cleaned up even if an exception occurs.

    Args:
        content: Bytes to write to the temp file.
        suffix: File extension to use.

    Yields:
        Path to the temporary file.
    """
    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            tmp.write(content)
            tmp_path = Path(tmp.name)
        yield tmp_path
    finally:
        if tmp_path and tmp_path.exists():
            try:
                tmp_path.unlink()
            except OSError as e:
                logger.warning(f"Failed to delete temp file {tmp_path}: {e}")


@contextlib.contextmanager
def temp_output_context(suffix: str = ".png") -> Generator[Path, None, None]:
    """
    Context manager for a temporary output file path.

    Creates a temp file path and ensures cleanup.

    Args:
        suffix: File extension to use.

    Yields:
        Path where output can be written.
    """
    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            tmp_path = Path(tmp.name)
        yield tmp_path
    finally:
        if tmp_path and tmp_path.exists():
            try:
                tmp_path.unlink()
            except OSError as e:
                logger.warning(f"Failed to delete temp file {tmp_path}: {e}")


def read_and_cleanup(path: Path) -> bytes:
    """Read file content and delete the file."""
    try:
        with open(path, "rb") as f:
            return f.read()
    finally:
        try:
            path.unlink(missing_ok=True)
        except OSError as e:
            logger.warning(f"Failed to delete file {path}: {e}")
