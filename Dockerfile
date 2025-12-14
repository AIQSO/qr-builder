FROM python:3.11-slim

WORKDIR /app

# Environment configuration
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV QR_BUILDER_HOST=0.0.0.0
ENV QR_BUILDER_PORT=8000
ENV QR_BUILDER_ENV=production
ENV QR_BUILDER_AUTH_ENABLED=false

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy application files
COPY pyproject.toml README.md ./
COPY qr_builder ./qr_builder
COPY server.py ./

# Install Python dependencies
RUN pip install --no-cache-dir -e .

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash appuser && \
    chown -R appuser:appuser /app
USER appuser

# Expose the application port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import httpx; httpx.get('http://localhost:8000/health', timeout=5).raise_for_status()" || exit 1

# Run the API server (can also use server.py for web interface)
CMD ["uvicorn", "qr_builder.api:app", "--host", "0.0.0.0", "--port", "8000"]
