# ==============================================================================
# Production Dockerfile for Job-Manager Backend (ai-service directory)
# Includes Python 3.12, Linux Tectonic LaTeX Compiler, and System Fonts
# ==============================================================================

FROM python:3.12-slim-bookworm

# 1. Install system utilities and LaTeX font packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    fontconfig \
    libfontconfig1 \
    fonts-lmodern \
    fonts-font-awesome \
    gcc \
    python3-dev \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# 2. Install pre-built static Tectonic binary for Linux x86_64
RUN curl -fsSL https://github.com/tectonic-typesetting/tectonic/releases/download/tectonic%400.15.0/tectonic-0.15.0-x86_64-unknown-linux-musl.tar.gz \
    | tar -xz -C /usr/local/bin/ \
    && chmod 755 /usr/local/bin/tectonic

# 3. Set up Tectonic cache directories
ENV TECTONIC_CACHE_DIR=/opt/tectonic-cache \
    XDG_CACHE_HOME=/opt/tex-cache \
    PYTHONUNBUFFERED=1

RUN mkdir -p /opt/tectonic-cache /opt/tex-cache && chmod -R a+rwx /opt/tectonic-cache /opt/tex-cache

# 4. Set application working directory
WORKDIR /app

# 5. Copy code
COPY . /app/

# 6. Install Python dependencies and package
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir ".[dashboard,ai]" "psycopg[binary]>=3.1.18" psycopg2-binary uvicorn[standard]

# 7. Expose default port
EXPOSE 8000

# 8. Start FastAPI with dynamic PORT support (defaulting to 8000)
CMD ["sh", "-c", "uvicorn cv_tailor.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
