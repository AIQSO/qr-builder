"""
qr_builder.cli
--------------

Command-line interface for QR Builder.

Usage examples:
    qr-builder qr "https://example.com" qr.png --size 600
    qr-builder embed bg.jpg "https://example.com" out.png --scale 0.3 --position bottom-right
"""

from __future__ import annotations

import argparse
import logging
from pathlib import Path

from .core import (
    embed_qr_in_image,
    generate_artistic_qr,
    generate_qart,
    generate_qr_only,
    generate_qr_with_logo,
    generate_qr_with_text,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="qr-builder",
        description="Generate QR codes or embed them into images.",
    )

    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Set log level (default: INFO)",
    )

    sub = parser.add_subparsers(dest="command", required=True)

    # Standalone QR
    qr_only = sub.add_parser("qr", help="Generate a standalone QR code.")
    qr_only.add_argument("data", help="Text/URL to encode.")
    qr_only.add_argument("output", help="Output file path (PNG recommended).")
    qr_only.add_argument("--size", type=int, default=500)
    qr_only.add_argument("--fill-color", default="black")
    qr_only.add_argument("--back-color", default="white")

    # Embed QR
    embed = sub.add_parser("embed", help="Embed QR into an image.")
    embed.add_argument("background", help="Background image path.")
    embed.add_argument("data", help="Text/URL to encode.")
    embed.add_argument("output", help="Output path (PNG recommended).")
    embed.add_argument("--scale", type=float, default=0.3)
    embed.add_argument(
        "--position",
        default="center",
        choices=[
            "center",
            "top-left",
            "top-right",
            "bottom-left",
            "bottom-right",
        ],
    )
    embed.add_argument("--margin", type=int, default=20)
    embed.add_argument("--fill-color", default="black")
    embed.add_argument("--back-color", default="white")

    # QR with logo in center
    logo_qr = sub.add_parser("logo", help="Generate QR code with logo embedded in center.")
    logo_qr.add_argument("logo", help="Path to logo image.")
    logo_qr.add_argument("data", help="Text/URL to encode.")
    logo_qr.add_argument("output", help="Output file path (PNG recommended).")
    logo_qr.add_argument("--size", type=int, default=500, help="QR code size in pixels.")
    logo_qr.add_argument("--logo-scale", type=float, default=0.25, help="Logo size as fraction of QR (0.1-0.4).")
    logo_qr.add_argument("--fill-color", default="black", help="QR foreground color.")
    logo_qr.add_argument("--back-color", default="white", help="QR background color.")

    # QR with text/words in center
    text_qr = sub.add_parser("text", help="Generate QR code with text/words embedded in center.")
    text_qr.add_argument("text", help="Text/words to display in center.")
    text_qr.add_argument("data", help="Text/URL to encode.")
    text_qr.add_argument("output", help="Output file path (PNG recommended).")
    text_qr.add_argument("--size", type=int, default=500, help="QR code size in pixels.")
    text_qr.add_argument("--text-scale", type=float, default=0.3, help="Text area as fraction of QR (0.1-0.4).")
    text_qr.add_argument("--fill-color", default="black", help="QR foreground color.")
    text_qr.add_argument("--back-color", default="white", help="QR background color.")
    text_qr.add_argument("--font-color", default="black", help="Text color.")
    text_qr.add_argument("--font-size", type=int, default=None, help="Font size (auto if not set).")

    # Artistic QR - image IS the QR code
    artistic = sub.add_parser("artistic", help="Generate artistic QR where image IS the QR code.")
    artistic.add_argument("image", help="Path to image to transform into QR.")
    artistic.add_argument("data", help="Text/URL to encode.")
    artistic.add_argument("output", help="Output file path (PNG recommended).")
    artistic.add_argument("--bw", action="store_true", help="Black & white instead of colorized.")
    artistic.add_argument("--contrast", type=float, default=1.0, help="Image contrast (default 1.0, try 1.2-1.5).")
    artistic.add_argument("--brightness", type=float, default=1.0, help="Image brightness (default 1.0, try 1.1-1.2).")
    artistic.add_argument("--version", type=int, default=10, help="QR version: 5=small, 10=medium, 15=large (default 10).")
    artistic.add_argument("--preset", choices=["small", "medium", "large", "hd"], help="Quality preset (overrides other settings).")

    # QArt - halftone/dithered style
    qart = sub.add_parser("qart", help="Generate QArt-style halftone QR code.")
    qart.add_argument("image", help="Path to image to transform.")
    qart.add_argument("data", help="Text/URL to encode.")
    qart.add_argument("output", help="Output file path (PNG recommended).")
    qart.add_argument("--version", type=int, default=10, help="QR version 1-40 (default 10).")
    qart.add_argument("--point-size", type=int, default=8, help="Point size in pixels (default 8).")
    qart.add_argument("--no-dither", action="store_true", help="Disable dithering.")
    qart.add_argument("--fast", action="store_true", help="Fast mode (data bits only).")
    qart.add_argument("--color", nargs=3, type=int, metavar=("R", "G", "B"), help="QR color as RGB values.")

    # Batch embed (directory-based)
    batch = sub.add_parser(
        "batch-embed", help="Embed the same QR into all images in a directory."
    )
    batch.add_argument("input_dir", help="Directory containing background images.")
    batch.add_argument("data", help="Text/URL to encode.")
    batch.add_argument("output_dir", help="Directory to write output images.")
    batch.add_argument("--scale", type=float, default=0.3)
    batch.add_argument(
        "--position",
        default="center",
        choices=[
            "center",
            "top-left",
            "top-right",
            "bottom-left",
            "bottom-right",
        ],
    )
    batch.add_argument("--margin", type=int, default=20)
    batch.add_argument("--fill-color", default="black")
    batch.add_argument("--back-color", default="white")
    batch.add_argument(
        "--glob",
        default="*.png",
        help="Glob pattern for input images (default: *.png).",
    )

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    logging.basicConfig(
        level=getattr(logging, args.log_level.upper()),
        format="%(levelname)s: %(message)s",
    )

    if args.command == "qr":
        generate_qr_only(
            args.data,
            args.output,
            size=args.size,
            fill_color=args.fill_color,
            back_color=args.back_color,
        )
    elif args.command == "embed":
        embed_qr_in_image(
            background_image_path=args.background,
            data=args.data,
            output_path=args.output,
            qr_scale=args.scale,
            position=args.position,
            margin=args.margin,
            fill_color=args.fill_color,
            back_color=args.back_color,
        )
    elif args.command == "logo":
        generate_qr_with_logo(
            data=args.data,
            logo_path=args.logo,
            output_path=args.output,
            size=args.size,
            logo_scale=args.logo_scale,
            fill_color=args.fill_color,
            back_color=args.back_color,
        )
    elif args.command == "text":
        generate_qr_with_text(
            data=args.data,
            text=args.text,
            output_path=args.output,
            size=args.size,
            text_scale=args.text_scale,
            fill_color=args.fill_color,
            back_color=args.back_color,
            font_color=args.font_color,
            font_size=args.font_size,
        )
    elif args.command == "artistic":
        # Handle presets
        presets = {
            "small": {"version": 5, "contrast": 1.5, "brightness": 1.2},
            "medium": {"version": 10, "contrast": 1.3, "brightness": 1.1},
            "large": {"version": 15, "contrast": 1.3, "brightness": 1.0},
            "hd": {"version": 20, "contrast": 1.2, "brightness": 1.0},
        }
        if args.preset:
            p = presets[args.preset]
            version = p["version"]
            contrast = p["contrast"]
            brightness = p["brightness"]
        else:
            version = args.version
            contrast = args.contrast
            brightness = args.brightness

        generate_artistic_qr(
            data=args.data,
            image_path=args.image,
            output_path=args.output,
            colorized=not args.bw,
            contrast=contrast,
            brightness=brightness,
            version=version,
        )
    elif args.command == "qart":
        generate_qart(
            data=args.data,
            image_path=args.image,
            output_path=args.output,
            version=args.version,
            point_size=args.point_size,
            dither=not args.no_dither,
            only_data=args.fast,
            fill_color=tuple(args.color) if args.color else None,
        )
    elif args.command == "batch-embed":
        from glob import glob
        from os import makedirs
        from os.path import basename, splitext

        input_dir = Path(args.input_dir)
        output_dir = Path(args.output_dir)
        makedirs(output_dir, exist_ok=True)

        pattern = str(input_dir / args.glob)
        for in_path in glob(pattern):
            name = basename(in_path)
            stem, ext = splitext(name)
            out_name = f"{stem}_qr{ext or '.png'}"
            out_path = output_dir / out_name
            embed_qr_in_image(
                background_image_path=in_path,
                data=args.data,
                output_path=out_path,
                qr_scale=args.scale,
                position=args.position,
                margin=args.margin,
                fill_color=args.fill_color,
                back_color=args.back_color,
            )
    else:
        parser.print_help()
