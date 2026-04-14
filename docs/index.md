# qr-builder

Generate and embed QR codes into images via Python, CLI, and FastAPI.

## What it does

- **Generate** standalone QR codes with configurable size and color
- **Embed** QR codes into existing images at any corner or centered
- **Batch-embed** QR codes into many images at once
- Expose all of the above via a **CLI**, a **Python API**, and a **FastAPI** HTTP service

## Install

```bash
pip install qr-builder
```

Optional extras:

```bash
pip install "qr-builder[artistic]"  # adds amzqr + pyqart for logo-embedded / pixel-art QRs
pip install "qr-builder[dev]"       # test, lint, type-check, audit tooling
```

## Quick examples

**CLI:**

```bash
qr-builder qr "https://example.com" --output qr.png
qr-builder embed background.jpg "https://example.com" --output branded.png --position bottom-right
```

**Python:**

```python
from qr_builder import generate_qr, embed_qr_in_image

img = generate_qr("https://example.com")
img.save("qr.png")

embed_qr_in_image("background.jpg", "https://example.com", "branded.png", position="bottom-right")
```

**HTTP API:**

```bash
qr-builder-api          # starts on http://localhost:8000
curl -X POST http://localhost:8000/qr -H "Content-Type: application/json" \
  -d '{"data": "https://example.com"}' --output qr.png
```

## Next steps

- [Getting Started](getting-started.md) — install, first QR, first embed
- [API Reference](API.md) — full HTTP endpoint documentation
- [Next.js Integration](NEXTJS_INTEGRATION.md) — hosted SaaS / webhook patterns
- [GitHub repo](https://github.com/AIQSO/qr-builder) — issues, source, releases
