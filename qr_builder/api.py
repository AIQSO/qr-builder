"""
qr_builder.api
--------------

FastAPI application exposing QR Builder via HTTP.

Supported endpoints:
- /qr - Basic QR code generation
- /qr/logo - QR with logo in center
- /qr/artistic - Image blended into QR pattern
- /qr/qart - Halftone/dithered style
- /embed - QR placed on background
- /batch/embed - Batch processing

Entry points (after install):
    qr-builder-api   # convenience wrapper defined in pyproject.toml

Or manually:
    uvicorn qr_builder.api:app --reload
"""

from __future__ import annotations

import io
import logging
import zipfile
import tempfile
from pathlib import Path
from typing import List, Optional
from enum import Enum

from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from .core import (
    generate_qr,
    calculate_position,
    generate_qr_with_logo,
    generate_qr_with_text,
    generate_artistic_qr,
    generate_qart,
    QRStyle,
    ARTISTIC_PRESETS,
)

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

app = FastAPI(
    title="QR Builder API",
    description="""
Generate and embed QR codes into images via HTTP.

## Available Styles

| Style | Endpoint | Description |
|-------|----------|-------------|
| **Basic** | `/qr` | Simple QR with custom colors |
| **Logo** | `/qr/logo` | Logo embedded in QR center |
| **Text** | `/qr/text` | Text/words in QR center |
| **Artistic** | `/qr/artistic` | Image IS the QR code (colorful) |
| **QArt** | `/qr/qart` | Halftone/dithered style |
| **Embed** | `/embed` | QR placed on background image |

## Presets (Artistic mode)
- `small` - Compact, high contrast (version 5)
- `medium` - Balanced (version 10)
- `large` - High detail (version 15)
- `hd` - Maximum detail (version 20)
    """,
    version="0.2.0",
)

# CORS middleware for web integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class StyleEnum(str, Enum):
    """Available QR styles for unified endpoint."""
    basic = "basic"
    logo = "logo"
    artistic = "artistic"
    qart = "qart"
    embed = "embed"


class PresetEnum(str, Enum):
    """Artistic mode presets."""
    small = "small"
    medium = "medium"
    large = "large"
    hd = "hd"


@app.get("/health", tags=["meta"])
async def health() -> dict:
    """Health check endpoint."""
    return {"status": "ok"}


@app.get("/styles", tags=["meta"])
async def list_styles() -> dict:
    """List all available QR code styles and presets."""
    return {
        "styles": [
            {"name": "basic", "description": "Simple QR with custom colors", "requires_image": False},
            {"name": "logo", "description": "Logo embedded in QR center", "requires_image": True},
            {"name": "artistic", "description": "Image IS the QR code (colorful)", "requires_image": True},
            {"name": "qart", "description": "Halftone/dithered style", "requires_image": True},
            {"name": "embed", "description": "QR placed on background image", "requires_image": True},
        ],
        "artistic_presets": [
            {"name": "small", "version": 5, "description": "Compact, high contrast"},
            {"name": "medium", "version": 10, "description": "Balanced (default)"},
            {"name": "large", "version": 15, "description": "High detail"},
            {"name": "hd", "version": 20, "description": "Maximum detail"},
        ],
    }


# =============================================================================
# Basic QR Endpoint
# =============================================================================

@app.post("/qr", tags=["basic"])
async def create_qr(
    data: str = Form(..., description="Text or URL to encode."),
    size: int = Form(500, description="Pixel size of the QR image."),
    fill_color: str = Form("black", description="QR foreground color."),
    back_color: str = Form("white", description="QR background color."),
):
    """Generate a basic standalone QR code and return as PNG."""
    try:
        img = generate_qr(
            data=data,
            qr_size=size,
            fill_color=fill_color,
            back_color=back_color,
        )
    except Exception as exc:
        logger.exception("Failed to generate QR.")
        raise HTTPException(status_code=400, detail=str(exc))

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return StreamingResponse(buf, media_type="image/png")


# =============================================================================
# Logo QR Endpoint
# =============================================================================

@app.post("/qr/logo", tags=["logo"])
async def create_qr_with_logo(
    logo: UploadFile = File(..., description="Logo image to embed in center."),
    data: str = Form(..., description="Text or URL to encode."),
    size: int = Form(500, description="Pixel size of the QR image."),
    logo_scale: float = Form(0.25, description="Logo size as fraction of QR (0.1-0.4)."),
    fill_color: str = Form("black", description="QR foreground color."),
    back_color: str = Form("white", description="QR background color."),
):
    """Generate a QR code with logo embedded in the center."""
    try:
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
            tmp.write(await logo.read())
            tmp_path = Path(tmp.name)

        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as out:
            out_path = Path(out.name)

        generate_qr_with_logo(
            data=data,
            logo_path=tmp_path,
            output_path=out_path,
            size=size,
            logo_scale=logo_scale,
            fill_color=fill_color,
            back_color=back_color,
        )

        # Read result and clean up
        with open(out_path, "rb") as f:
            result = f.read()
        tmp_path.unlink(missing_ok=True)
        out_path.unlink(missing_ok=True)

    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as exc:
        logger.exception("Failed to generate QR with logo.")
        raise HTTPException(status_code=500, detail=str(exc))

    return StreamingResponse(io.BytesIO(result), media_type="image/png")


# =============================================================================
# Text QR Endpoint
# =============================================================================

@app.post("/qr/text", tags=["text"])
async def create_qr_with_text_endpoint(
    text: str = Form(..., description="Text/words to display in center."),
    data: str = Form(..., description="Text or URL to encode."),
    size: int = Form(500, description="Pixel size of the QR image."),
    text_scale: float = Form(0.3, description="Text area size as fraction of QR (0.1-0.4)."),
    fill_color: str = Form("black", description="QR foreground color."),
    back_color: str = Form("white", description="QR background color."),
    font_color: str = Form("black", description="Text color."),
    font_size: int = Form(None, description="Font size in pixels (auto if not set)."),
):
    """Generate a QR code with text/words embedded in the center."""
    try:
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as out:
            out_path = Path(out.name)

        generate_qr_with_text(
            data=data,
            text=text,
            output_path=out_path,
            size=size,
            text_scale=text_scale,
            fill_color=fill_color,
            back_color=back_color,
            font_color=font_color,
            font_size=font_size,
        )

        with open(out_path, "rb") as f:
            result = f.read()
        out_path.unlink(missing_ok=True)

    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as exc:
        logger.exception("Failed to generate QR with text.")
        raise HTTPException(status_code=500, detail=str(exc))

    return StreamingResponse(io.BytesIO(result), media_type="image/png")


# =============================================================================
# Artistic QR Endpoint
# =============================================================================

@app.post("/qr/artistic", tags=["artistic"])
async def create_artistic_qr(
    image: UploadFile = File(..., description="Image to blend into QR pattern."),
    data: str = Form(..., description="Text or URL to encode."),
    preset: Optional[PresetEnum] = Form(None, description="Quality preset (small/medium/large/hd)."),
    version: int = Form(10, description="QR version 1-40 (higher = more detail)."),
    contrast: float = Form(1.0, description="Image contrast (try 1.2-1.5)."),
    brightness: float = Form(1.0, description="Image brightness (try 1.1-1.2)."),
    colorized: bool = Form(True, description="Keep colors (False for B&W)."),
):
    """
    Generate an artistic QR code where the image IS the QR code.

    The image is blended into the QR pattern itself, creating a visually
    striking QR code that remains scannable.

    **Recommended presets:**
    - `small` - Compact, good for small displays
    - `medium` - Balanced (default)
    - `large` - High detail, good for print
    - `hd` - Maximum detail, large format
    """
    try:
        # Apply preset
        if preset:
            p = ARTISTIC_PRESETS[preset.value]
            version = p["version"]
            contrast = p["contrast"]
            brightness = p["brightness"]

        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
            tmp.write(await image.read())
            tmp_path = Path(tmp.name)

        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as out:
            out_path = Path(out.name)

        generate_artistic_qr(
            data=data,
            image_path=tmp_path,
            output_path=out_path,
            colorized=colorized,
            contrast=contrast,
            brightness=brightness,
            version=version,
        )

        # Read result and clean up
        with open(out_path, "rb") as f:
            result = f.read()
        tmp_path.unlink(missing_ok=True)
        out_path.unlink(missing_ok=True)

    except Exception as exc:
        logger.exception("Failed to generate artistic QR.")
        raise HTTPException(status_code=500, detail=str(exc))

    return StreamingResponse(io.BytesIO(result), media_type="image/png")


# =============================================================================
# QArt Endpoint
# =============================================================================

@app.post("/qr/qart", tags=["qart"])
async def create_qart(
    image: UploadFile = File(..., description="Image to transform into QR."),
    data: str = Form(..., description="Text or URL to encode."),
    version: int = Form(10, description="QR version 1-40."),
    point_size: int = Form(8, description="Point size in pixels."),
    dither: bool = Form(True, description="Use dithering for smoother gradients."),
    fast: bool = Form(False, description="Fast mode (data bits only)."),
    color_r: int = Form(0, description="Red component (0-255)."),
    color_g: int = Form(0, description="Green component (0-255)."),
    color_b: int = Form(0, description="Blue component (0-255)."),
):
    """
    Generate a QArt-style halftone/dithered QR code.

    Creates a black & white (or single color) artistic QR using dithering
    techniques. Good for minimalist designs.
    """
    try:
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
            tmp.write(await image.read())
            tmp_path = Path(tmp.name)

        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as out:
            out_path = Path(out.name)

        fill_color = None
        if color_r != 0 or color_g != 0 or color_b != 0:
            fill_color = (color_r, color_g, color_b)

        generate_qart(
            data=data,
            image_path=tmp_path,
            output_path=out_path,
            version=version,
            point_size=point_size,
            dither=dither,
            only_data=fast,
            fill_color=fill_color,
        )

        # Read result and clean up
        with open(out_path, "rb") as f:
            result = f.read()
        tmp_path.unlink(missing_ok=True)
        out_path.unlink(missing_ok=True)

    except Exception as exc:
        logger.exception("Failed to generate QArt.")
        raise HTTPException(status_code=500, detail=str(exc))

    return StreamingResponse(io.BytesIO(result), media_type="image/png")


# =============================================================================
# Embed Endpoint
# =============================================================================

@app.post("/embed", tags=["embed"])
async def embed_qr(
    background: UploadFile = File(..., description="Background image file."),
    data: str = Form(..., description="Text or URL to encode."),
    scale: float = Form(0.3, description="Fraction of background width to use for QR."),
    position: str = Form("center", description="Position: center, top-left, top-right, bottom-left, bottom-right."),
    margin: int = Form(20, description="Margin from edge in pixels."),
    fill_color: str = Form("black", description="QR foreground color."),
    back_color: str = Form("white", description="QR background color."),
):
    """Embed a QR into an uploaded background image and return the result as PNG."""
    try:
        raw = await background.read()
        tmp_buf = io.BytesIO(raw)

        from PIL import Image

        bg = Image.open(tmp_buf).convert("RGBA")
        bg_w, bg_h = bg.size

        if not (0 < scale <= 1):
            raise ValueError("scale must be between 0 and 1.")

        qr_size = int(bg_w * scale)
        qr_img = generate_qr(
            data=data,
            qr_size=qr_size,
            fill_color=fill_color,
            back_color=back_color,
        )

        x, y = calculate_position(bg_w, bg_h, qr_size, position, margin)
        bg.paste(qr_img, (x, y), qr_img)

        out_buf = io.BytesIO()
        bg.save(out_buf, format="PNG")
        out_buf.seek(0)

    except ValueError as ve:
        logger.warning("Bad request for /embed: %s", ve)
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception:
        logger.exception("Failed to embed QR.")
        raise HTTPException(status_code=500, detail="Internal server error")

    return StreamingResponse(out_buf, media_type="image/png")


# =============================================================================
# Batch Endpoints
# =============================================================================

@app.post("/batch/embed", tags=["batch"])
async def batch_embed_qr(
    backgrounds: List[UploadFile] = File(..., description="Multiple background images."),
    data: str = Form(..., description="Text or URL to encode."),
    scale: float = Form(0.3, description="Fraction of background width to use for QR."),
    position: str = Form("center"),
    margin: int = Form(20),
    fill_color: str = Form("black"),
    back_color: str = Form("white"),
):
    """
    Embed the same QR into multiple uploaded background images and return a ZIP.

    Filenames inside the ZIP will be the original filename with `_qr` appended.
    """
    try:
        zip_buf = io.BytesIO()
        with zipfile.ZipFile(zip_buf, "w", zipfile.ZIP_DEFLATED) as zf:
            from PIL import Image
            for file in backgrounds:
                raw = await file.read()
                tmp_buf = io.BytesIO(raw)
                bg = Image.open(tmp_buf).convert("RGBA")
                bg_w, bg_h = bg.size

                if not (0 < scale <= 1):
                    raise ValueError("scale must be between 0 and 1.")

                qr_size = int(bg_w * scale)
                qr_img = generate_qr(
                    data=data,
                    qr_size=qr_size,
                    fill_color=fill_color,
                    back_color=back_color,
                )

                x, y = calculate_position(bg_w, bg_h, qr_size, position, margin)
                bg.paste(qr_img, (x, y), qr_img)

                out_img_buf = io.BytesIO()
                bg.save(out_img_buf, format="PNG")
                out_img_buf.seek(0)

                name = file.filename or "image.png"
                if "." in name:
                    base, _ = name.rsplit(".", 1)
                    out_name = f"{base}_qr.png"
                else:
                    out_name = f"{name}_qr.png"

                zf.writestr(out_name, out_img_buf.getvalue())

        zip_buf.seek(0)

    except ValueError as ve:
        logger.warning("Bad request for /batch/embed: %s", ve)
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception:
        logger.exception("Failed to batch embed QR.")
        raise HTTPException(status_code=500, detail="Internal server error")

    return StreamingResponse(
        zip_buf,
        media_type="application/zip",
        headers={"Content-Disposition": "attachment; filename=batch_qr.zip"},
    )


@app.post("/batch/artistic", tags=["batch"])
async def batch_artistic_qr(
    images: List[UploadFile] = File(..., description="Multiple images to transform."),
    data: str = Form(..., description="Text or URL to encode."),
    preset: Optional[PresetEnum] = Form(PresetEnum.large, description="Quality preset."),
):
    """
    Generate artistic QR codes from multiple images and return a ZIP.
    """
    try:
        p = ARTISTIC_PRESETS[preset.value]
        version = p["version"]
        contrast = p["contrast"]
        brightness = p["brightness"]

        zip_buf = io.BytesIO()
        with zipfile.ZipFile(zip_buf, "w", zipfile.ZIP_DEFLATED) as zf:
            for file in images:
                # Save uploaded file temporarily
                with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
                    tmp.write(await file.read())
                    tmp_path = Path(tmp.name)

                with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as out:
                    out_path = Path(out.name)

                generate_artistic_qr(
                    data=data,
                    image_path=tmp_path,
                    output_path=out_path,
                    colorized=True,
                    contrast=contrast,
                    brightness=brightness,
                    version=version,
                )

                # Read result
                with open(out_path, "rb") as f:
                    result = f.read()

                # Clean up
                tmp_path.unlink(missing_ok=True)
                out_path.unlink(missing_ok=True)

                name = file.filename or "image.png"
                if "." in name:
                    base, _ = name.rsplit(".", 1)
                    out_name = f"{base}_artistic.png"
                else:
                    out_name = f"{name}_artistic.png"

                zf.writestr(out_name, result)

        zip_buf.seek(0)

    except Exception:
        logger.exception("Failed to batch generate artistic QR.")
        raise HTTPException(status_code=500, detail="Internal server error")

    return StreamingResponse(
        zip_buf,
        media_type="application/zip",
        headers={"Content-Disposition": "attachment; filename=batch_artistic_qr.zip"},
    )


def run() -> None:
    """Convenience entrypoint for `qr-builder-api` script."""
    import os
    import uvicorn

    host = os.getenv("QR_BUILDER_HOST", "0.0.0.0")
    port = int(os.getenv("QR_BUILDER_PORT", "8000"))
    reload = os.getenv("QR_BUILDER_RELOAD", "true").lower() == "true"

    uvicorn.run(
        "qr_builder.api:app",
        host=host,
        port=port,
        reload=reload,
    )
