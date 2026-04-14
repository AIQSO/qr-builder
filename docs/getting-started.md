# Getting Started

## Prerequisites

- Python 3.10 or newer
- `pip` (or `uv`/`pipx`)
- Optional: Docker for the containerized API

## Install

### From PyPI (recommended)

```bash
pip install qr-builder
```

### From source

```bash
git clone https://github.com/AIQSO/qr-builder.git
cd qr-builder
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
```

### Optional extras

| Extra | What it adds | When to use |
|-------|--------------|-------------|
| `artistic` | `amzqr`, `pyqart` | Logo-in-QR and pixel-art QR styles |
| `dev` | pytest, ruff, mypy, pip-audit, deptry, pip-tools | Contributing or running the audit pipeline |

```bash
pip install "qr-builder[artistic]"
pip install "qr-builder[artistic,dev]"
```

## First QR code

```python
from qr_builder import generate_qr

img = generate_qr("https://example.com", qr_size=500)
img.save("hello.png")
```

## Embed a QR into an existing image

```python
from qr_builder import embed_qr_in_image

embed_qr_in_image(
    background_path="flyer.jpg",
    data="https://example.com/promo",
    output_path="flyer_qr.png",
    qr_scale=0.25,          # QR will be 25% of the shorter background side
    position="bottom-right", # center | top-left | top-right | bottom-left | bottom-right
    margin=40,              # pixels from the edge
)
```

## Run the HTTP API

```bash
qr-builder-api                              # dev server (reload enabled)
# or
uvicorn qr_builder.api:app --host 0.0.0.0 --port 8000
```

Test it:

```bash
curl -X POST http://localhost:8000/qr \
  -H "Content-Type: application/json" \
  -d '{"data": "https://example.com", "qr_size": 400}' \
  --output qr.png
```

## Run via Docker

```bash
docker build -t qr-builder-api .
docker run -p 8000:8000 qr-builder-api
```

Or with `docker compose`:

```bash
docker compose up --build
```

## Configuration

All runtime settings are driven by environment variables (prefixed `QR_BUILDER_`). Copy `.env.example` to `.env` and edit. Key variables:

| Variable | Default | Purpose |
|----------|---------|---------|
| `QR_BUILDER_HOST` | `0.0.0.0` | API bind host |
| `QR_BUILDER_PORT` | `8000` | API port |
| `QR_BUILDER_AUTH_ENABLED` | `false` | Enable API-key auth |
| `QR_BUILDER_BACKEND_SECRET` | *(empty)* | Webhook secret (required in production) |
| `QR_BUILDER_ALLOWED_ORIGINS` | `*` | CORS allowlist (set explicit domains in production) |

See [`.env.example`](https://github.com/AIQSO/qr-builder/blob/main/.env.example) for the full list.

## Next steps

- [API Reference](API.md) for full endpoint documentation
- [Next.js Integration](NEXTJS_INTEGRATION.md) for hosted-SaaS patterns
