"""
qr_builder.core
----------------

Core functionality for generating QR codes and embedding them into images.

Supported styles:
- basic: Simple QR code with custom colors
- logo: QR code with logo embedded in center
- artistic: Image blended into QR pattern (colorful)
- qart: Halftone/dithered style (single color)
- embed: QR code placed on top of background image
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

import qrcode
from PIL import Image

logger = logging.getLogger(__name__)

# Constants for validation
MAX_DATA_LENGTH = 4296  # Maximum characters for QR code
MAX_QR_SIZE = 4000  # Maximum QR image size in pixels
MIN_QR_SIZE = 21  # Minimum QR image size in pixels
VALID_POSITIONS = ("center", "top-left", "top-right", "bottom-left", "bottom-right")


class QRStyle(str, Enum):
    """Available QR code generation styles."""
    BASIC = "basic"           # Simple QR with custom colors
    LOGO = "logo"             # Logo embedded in center
    ARTISTIC = "artistic"     # Image IS the QR (colorful)
    QART = "qart"             # Halftone/dithered style
    EMBED = "embed"           # QR placed on background


# Presets for artistic mode
ARTISTIC_PRESETS = {
    "small": {"version": 5, "contrast": 1.5, "brightness": 1.2},
    "medium": {"version": 10, "contrast": 1.3, "brightness": 1.1},
    "large": {"version": 15, "contrast": 1.3, "brightness": 1.0},
    "hd": {"version": 20, "contrast": 1.2, "brightness": 1.0},
}


@dataclass
class QRConfig:
    """Configuration for QR code generation."""
    data: str
    style: QRStyle = QRStyle.BASIC
    output_path: str | None = None

    # Basic options
    size: int = 500
    fill_color: str = "black"
    back_color: str = "white"

    # Image-based options (for artistic, qart, logo, embed)
    image_path: str | None = None

    # Logo options
    logo_scale: float = 0.25

    # Artistic options
    colorized: bool = True
    contrast: float = 1.0
    brightness: float = 1.0
    version: int = 10
    preset: str | None = None  # small, medium, large, hd

    # QArt options
    point_size: int = 8
    dither: bool = True
    only_data: bool = False

    # Embed options
    position: str = "center"
    margin: int = 20
    qr_scale: float = 0.3


def generate_qr_unified(config: QRConfig) -> Path:
    """
    Unified QR code generator that supports all styles.

    Args:
        config: QRConfig object with all generation parameters.

    Returns:
        Path to the generated QR code image.
    """
    if config.style == QRStyle.BASIC:
        return generate_qr_only(
            data=config.data,
            output_path=config.output_path,
            size=config.size,
            fill_color=config.fill_color,
            back_color=config.back_color,
        )
    elif config.style == QRStyle.LOGO:
        return generate_qr_with_logo(
            data=config.data,
            logo_path=config.image_path,
            output_path=config.output_path,
            size=config.size,
            logo_scale=config.logo_scale,
            fill_color=config.fill_color,
            back_color=config.back_color,
        )
    elif config.style == QRStyle.ARTISTIC:
        # Apply preset if specified
        if config.preset and config.preset in ARTISTIC_PRESETS:
            p = ARTISTIC_PRESETS[config.preset]
            version = p["version"]
            contrast = p["contrast"]
            brightness = p["brightness"]
        else:
            version = config.version
            contrast = config.contrast
            brightness = config.brightness

        return generate_artistic_qr(
            data=config.data,
            image_path=config.image_path,
            output_path=config.output_path,
            colorized=config.colorized,
            contrast=contrast,
            brightness=brightness,
            version=version,
        )
    elif config.style == QRStyle.QART:
        fill_color = None
        if config.fill_color != "black":
            # Parse color string to RGB tuple
            fill_color = parse_color(config.fill_color)
        return generate_qart(
            data=config.data,
            image_path=config.image_path,
            output_path=config.output_path,
            version=config.version,
            point_size=config.point_size,
            dither=config.dither,
            only_data=config.only_data,
            fill_color=fill_color,
        )
    elif config.style == QRStyle.EMBED:
        return embed_qr_in_image(
            background_image_path=config.image_path,
            data=config.data,
            output_path=config.output_path,
            qr_scale=config.qr_scale,
            position=config.position,
            margin=config.margin,
            fill_color=config.fill_color,
            back_color=config.back_color,
        )
    else:
        raise ValueError(f"Unknown style: {config.style}")


def parse_color(color: str) -> tuple:
    """Parse color string to RGB tuple."""
    if color.startswith("#"):
        # Hex color
        color = color.lstrip("#")
        return tuple(int(color[i:i+2], 16) for i in (0, 2, 4))
    # Named colors - basic mapping
    color_map = {
        "black": (0, 0, 0),
        "white": (255, 255, 255),
        "red": (255, 0, 0),
        "green": (0, 255, 0),
        "blue": (0, 0, 255),
        "navy": (26, 58, 92),
        "orange": (224, 112, 48),
    }
    return color_map.get(color.lower(), (0, 0, 0))


def validate_data(data: str) -> None:
    """Validate QR code data input."""
    if not data or not data.strip():
        raise ValueError("Data cannot be empty.")
    if len(data) > MAX_DATA_LENGTH:
        raise ValueError(f"Data exceeds maximum length of {MAX_DATA_LENGTH} characters.")


def validate_size(size: int) -> None:
    """Validate QR code size."""
    if not MIN_QR_SIZE <= size <= MAX_QR_SIZE:
        raise ValueError(f"Size must be between {MIN_QR_SIZE} and {MAX_QR_SIZE} pixels.")


def generate_qr(
    data: str,
    qr_size: int = 500,
    border: int = 4,
    fill_color: str = "black",
    back_color: str = "white",
) -> Image.Image:
    """
    Generate a QR code as a Pillow Image.

    Args:
        data: Text/URL encoded inside the QR.
        qr_size: Final pixel dimensions of QR (square).
        border: Thickness of the QR border.
        fill_color: Foreground color.
        back_color: Background color.

    Returns:
        Pillow Image (RGBA).

    Raises:
        ValueError: If data is empty or exceeds maximum length.
    """
    validate_data(data)
    validate_size(qr_size)
    logger.debug("Generating QR with data=%s", data)

    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=border,
    )
    qr.add_data(data)
    qr.make(fit=True)

    img = qr.make_image(
        fill_color=fill_color,
        back_color=back_color,
    ).convert("RGBA")

    img = img.resize((qr_size, qr_size), Image.LANCZOS)
    return img


def calculate_position(
    bg_w: int,
    bg_h: int,
    qr_size: int,
    position: str,
    margin: int,
) -> tuple[int, int]:
    """
    Calculate top-left position for a QR on a background.
    """
    position = position.lower()

    if position == "center":
        return (bg_w - qr_size) // 2, (bg_h - qr_size) // 2

    if position == "bottom-right":
        return bg_w - qr_size - margin, bg_h - qr_size - margin

    if position == "bottom-left":
        return margin, bg_h - qr_size - margin

    if position == "top-right":
        return bg_w - qr_size - margin, margin

    if position == "top-left":
        return margin, margin

    raise ValueError(
        f"Unsupported position '{position}'. "
        "Use one of: center, top-left, top-right, bottom-left, bottom-right."
    )


def embed_qr_in_image(
    background_image_path: str | Path,
    data: str,
    output_path: str | Path,
    qr_scale: float = 0.3,
    position: str = "center",
    margin: int = 20,
    fill_color: str = "black",
    back_color: str = "white",
) -> Path:
    """
    Embed a generated QR code inside an existing image.

    Args:
        background_image_path: Path to the background image.
        data: Text/URL encoded into the QR code.
        output_path: File path to save final merged image.
        qr_scale: Fraction of background width used as QR size (0<qr_scale<=1).
        position: Placement (center, top-left, top-right, bottom-left, bottom-right).
        margin: Edge spacing in px.
        fill_color: QR foreground color.
        back_color: QR background color.

    Returns:
        Path: Saved output path.
    """
    logger.info("Embedding QR into image: %s", background_image_path)

    bg_path = Path(background_image_path)
    if not bg_path.exists():
        raise FileNotFoundError(f"Background image not found: {bg_path}")

    bg = Image.open(bg_path).convert("RGBA")
    bg_w, bg_h = bg.size

    if not (0 < qr_scale <= 1):
        raise ValueError("qr_scale must be between 0 and 1.")

    qr_size = int(bg_w * qr_scale)
    qr_img = generate_qr(
        data,
        qr_size=qr_size,
        fill_color=fill_color,
        back_color=back_color,
    )

    x, y = calculate_position(bg_w, bg_h, qr_size, position, margin)
    bg.paste(qr_img, (x, y), qr_img)

    output_path = Path(output_path)
    bg.save(output_path)

    logger.info("Saved merged image to %s", output_path)
    return output_path


def generate_qr_only(
    data: str,
    output_path: str | Path,
    size: int = 500,
    fill_color: str = "black",
    back_color: str = "white",
) -> Path:
    """
    Save a standalone QR code.

    Args:
        data: Content of QR.
        output_path: File path for saving.
        size: Pixel size.
        fill_color: Foreground color.
        back_color: Background color.

    Returns:
        Path: Saved output file.
    """
    logger.debug("Generating standalone QR for data=%s", data)
    img = generate_qr(
        data,
        qr_size=size,
        fill_color=fill_color,
        back_color=back_color,
    )
    output_path = Path(output_path)
    img.save(output_path)
    logger.info("Saved QR-only image: %s", output_path)
    return output_path


def generate_artistic_qr(
    data: str,
    image_path: str | Path,
    output_path: str | Path,
    colorized: bool = True,
    contrast: float = 1.0,
    brightness: float = 1.0,
    version: int = 10,
) -> Path:
    """
    Generate an artistic QR code where the image IS the QR code.

    The image is blended into the QR code pattern itself, creating a
    visually striking QR code that displays the image while remaining scannable.

    Args:
        data: Text/URL to encode in the QR code.
        image_path: Path to the image to merge into the QR pattern.
        output_path: File path to save the final image.
        colorized: If True, keeps original colors. If False, black & white.
        contrast: Image contrast adjustment (default 1.0, try 1.2-1.5 for pop).
        brightness: Image brightness adjustment (default 1.0, try 1.1-1.2).
        version: QR code version 1-40 (higher = larger/more detail, default 10).
                 Recommended: 5 (small), 10 (medium), 15 (large/detailed).

    Returns:
        Path: Saved output file.

    Raises:
        FileNotFoundError: If image file doesn't exist.
    """
    from amzqr import amzqr

    image_path = Path(image_path)
    output_path = Path(output_path)

    if not image_path.exists():
        raise FileNotFoundError(f"Image not found: {image_path}")

    logger.info("Generating artistic QR from image: %s", image_path)

    # amzqr requires separate dir and filename
    save_dir = str(output_path.parent) if output_path.parent != Path(".") else "."
    save_name = output_path.name

    amzqr.run(
        data,
        version=version,
        level="H",  # High error correction for better scannability
        picture=str(image_path),
        colorized=colorized,
        contrast=contrast,
        brightness=brightness,
        save_name=save_name,
        save_dir=save_dir,
    )

    logger.info("Saved artistic QR: %s", output_path)
    return output_path


def generate_qart(
    data: str,
    image_path: str | Path,
    output_path: str | Path,
    version: int = 10,
    point_size: int = 8,
    dither: bool = True,
    only_data: bool = False,
    fill_color: tuple | None = None,
) -> Path:
    """
    Generate a QArt-style QR code using halftone/dithering techniques.

    QArt encodes the image directly into the QR data bits, creating a
    black & white artistic representation. Different from artistic mode
    which overlays color.

    Args:
        data: Text/URL to encode in the QR code.
        image_path: Path to the image to transform.
        output_path: File path to save the final image.
        version: QR code version 1-40 (default 10).
        point_size: Size of each QR module in pixels (default 8).
        dither: Use dithering for smoother gradients (default True).
        only_data: Only use data bits for faster generation (default False).
        fill_color: RGB tuple for QR color, e.g., (26, 58, 92) for navy.

    Returns:
        Path: Saved output file.

    Raises:
        FileNotFoundError: If image file doesn't exist.
        ValueError: If parameters are invalid.
        RuntimeError: If pyqart command fails.
    """
    import shutil
    import subprocess

    image_path = Path(image_path)
    output_path = Path(output_path)

    if not image_path.exists():
        raise FileNotFoundError(f"Image not found: {image_path}")

    # Validate parameters to prevent injection
    if not 1 <= version <= 40:
        raise ValueError(f"Version must be between 1 and 40, got {version}")
    if not 1 <= point_size <= 100:
        raise ValueError(f"Point size must be between 1 and 100, got {point_size}")
    if fill_color is not None:
        if len(fill_color) != 3:
            raise ValueError("fill_color must be an RGB tuple of 3 integers")
        for i, c in enumerate(fill_color):
            if not 0 <= c <= 255:
                raise ValueError(f"Color component {i} must be between 0 and 255, got {c}")

    # Validate data doesn't contain shell metacharacters (defense in depth)
    validate_data(data)

    # Check if pyqart is available
    pyqart_path = shutil.which("pyqart")
    if pyqart_path is None:
        raise RuntimeError(
            "pyqart command not found. Install it with: pip install pyqart"
        )

    logger.info("Generating QArt from image: %s", image_path)

    # Build command with validated parameters
    cmd = [
        pyqart_path,
        "-v", str(int(version)),
        "-p", str(int(point_size)),
        "-o", str(output_path.resolve()),
    ]

    if dither:
        cmd.append("-d")
    if only_data:
        cmd.append("-y")
    if fill_color:
        cmd.extend([
            "-c",
            str(int(fill_color[0])),
            str(int(fill_color[1])),
            str(int(fill_color[2]))
        ])

    cmd.extend([data, str(image_path.resolve())])

    try:
        result = subprocess.run(
            cmd,
            check=True,
            capture_output=True,
            timeout=60,  # 60 second timeout
        )
        logger.debug("pyqart output: %s", result.stdout.decode())
    except subprocess.TimeoutExpired as e:
        raise RuntimeError("QArt generation timed out after 60 seconds") from e
    except subprocess.CalledProcessError as e:
        error_msg = e.stderr.decode() if e.stderr else str(e)
        logger.error("pyqart failed: %s", error_msg)
        raise RuntimeError(f"QArt generation failed: {error_msg}") from e

    if not output_path.exists():
        raise RuntimeError("QArt generation completed but output file not created")

    logger.info("Saved QArt: %s", output_path)
    return output_path


def generate_qr_with_text(
    data: str,
    text: str,
    output_path: str | Path,
    size: int = 500,
    text_scale: float = 0.3,
    fill_color: str = "black",
    back_color: str = "white",
    font_color: str = "black",
    font_size: int = None,
) -> Path:
    """
    Generate a QR code with text/words embedded in the center.

    Args:
        data: Text/URL to encode in the QR code.
        text: Text/words to display in the center of the QR.
        output_path: File path to save the final image.
        size: Final QR code size in pixels.
        text_scale: Text area size as fraction of QR size (0.1-0.4).
        fill_color: QR code foreground color.
        back_color: QR code background color.
        font_color: Color of the text.
        font_size: Font size in pixels (auto-calculated if None).

    Returns:
        Path: Saved output file.
    """
    from PIL import ImageDraw, ImageFont

    if not (0.1 <= text_scale <= 0.4):
        raise ValueError("text_scale should be between 0.1 and 0.4 for reliable scanning.")

    logger.info("Generating QR with text: %s", text)

    # Generate QR code
    qr_img = generate_qr(
        data,
        qr_size=size,
        fill_color=fill_color,
        back_color=back_color,
    )

    # Calculate text area
    text_area_size = int(size * text_scale)
    box_padding = 10
    box_size = text_area_size + box_padding * 2
    box_pos = ((size - box_size) // 2, (size - box_size) // 2)

    # Draw white rectangle behind text
    draw = ImageDraw.Draw(qr_img)
    draw.rectangle(
        [box_pos, (box_pos[0] + box_size, box_pos[1] + box_size)],
        fill=back_color,
    )

    # Calculate font size to fit text in box
    if font_size is None:
        # Auto-calculate font size
        font_size = text_area_size // max(len(text.split('\n')), 1) // 2

    # Try to load a nice font, fall back to default
    try:
        font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", font_size)
    except OSError:
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", font_size)
        except OSError:
            font = ImageFont.load_default()

    # Get text bounding box
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]

    # Center text in QR
    text_x = (size - text_width) // 2
    text_y = (size - text_height) // 2

    # Draw text
    draw.text((text_x, text_y), text, fill=font_color, font=font)

    # Save result
    output_path = Path(output_path)
    qr_img.save(output_path)
    logger.info("Saved QR with text: %s", output_path)
    return output_path


def generate_qr_with_logo(
    data: str,
    logo_path: str | Path,
    output_path: str | Path,
    size: int = 500,
    logo_scale: float = 0.3,
    fill_color: str = "black",
    back_color: str = "white",
) -> Path:
    """
    Generate a QR code with a logo embedded in the center.

    The logo is placed in the center of the QR code. QR codes have error
    correction (we use HIGH/30%) which allows up to 30% of the code to be
    obscured while still being scannable.

    Args:
        data: Text/URL to encode in the QR code.
        logo_path: Path to the logo image to embed.
        output_path: File path to save the final image.
        size: Final QR code size in pixels.
        logo_scale: Logo size as fraction of QR size (0.1-0.4 recommended).
        fill_color: QR code foreground color.
        back_color: QR code background color.

    Returns:
        Path: Saved output file.

    Raises:
        FileNotFoundError: If logo file doesn't exist.
        ValueError: If logo_scale is out of range.
    """
    logo_path = Path(logo_path)
    if not logo_path.exists():
        raise FileNotFoundError(f"Logo image not found: {logo_path}")

    if not (0.1 <= logo_scale <= 0.4):
        raise ValueError("logo_scale should be between 0.1 and 0.4 for reliable scanning.")

    logger.info("Generating QR with embedded logo: %s", logo_path)

    # Generate QR code
    qr_img = generate_qr(
        data,
        qr_size=size,
        fill_color=fill_color,
        back_color=back_color,
    )

    # Open and resize logo
    logo = Image.open(logo_path).convert("RGBA")
    logo_size = int(size * logo_scale)
    logo = logo.resize((logo_size, logo_size), Image.LANCZOS)

    # Calculate center position
    pos_x = (size - logo_size) // 2
    pos_y = (size - logo_size) // 2

    # Create a white background box for the logo (improves scannability)
    box_padding = 10
    box_size = logo_size + box_padding * 2
    box_pos = ((size - box_size) // 2, (size - box_size) // 2)

    # Draw white rectangle behind logo
    from PIL import ImageDraw
    draw = ImageDraw.Draw(qr_img)
    draw.rectangle(
        [box_pos, (box_pos[0] + box_size, box_pos[1] + box_size)],
        fill=back_color,
    )

    # Paste logo onto QR code
    qr_img.paste(logo, (pos_x, pos_y), logo)

    # Save result
    output_path = Path(output_path)
    qr_img.save(output_path)
    logger.info("Saved QR with logo: %s", output_path)
    return output_path
