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

from .core import generate_qr_only, embed_qr_in_image, generate_qr_with_logo, generate_artistic_qr


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

    # Artistic QR - image IS the QR code
    artistic = sub.add_parser("artistic", help="Generate artistic QR where image IS the QR code.")
    artistic.add_argument("image", help="Path to image to transform into QR.")
    artistic.add_argument("data", help="Text/URL to encode.")
    artistic.add_argument("output", help="Output file path (PNG recommended).")
    artistic.add_argument("--bw", action="store_true", help="Black & white instead of colorized.")
    artistic.add_argument("--contrast", type=float, default=1.0, help="Image contrast (default 1.0).")
    artistic.add_argument("--brightness", type=float, default=1.0, help="Image brightness (default 1.0).")
    artistic.add_argument("--version", type=int, default=10, help="QR version 1-40 (default 10).")

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
    elif args.command == "artistic":
        generate_artistic_qr(
            data=args.data,
            image_path=args.image,
            output_path=args.output,
            colorized=not args.bw,
            contrast=args.contrast,
            brightness=args.brightness,
            version=args.version,
        )
    elif args.command == "batch-embed":
        from glob import glob
        from os import makedirs
        from os.path import basename, splitext, join

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
