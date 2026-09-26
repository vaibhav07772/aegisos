# ═══════════════════════════════════════════════
# AegisOS API — Production Dockerfile
# ═══════════════════════════════════════════════
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DEFAULT_TIMEOUT=120

WORKDIR /app

# ─── System deps ───
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc g++ build-essential curl \
    && rm -rf /var/lib/apt/lists/*

# ─── Python deps (cached) ───
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ─── Source ───
COPY src/ ./src/
COPY configs/ ./configs/
COPY main.py .
COPY streamlit_app.py .

# ─── Create sandbox ───
RUN mkdir -p sandbox data logs reports

# ─── Non-root user ───
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000 8501

HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# ─── Default: run API ───
CMD ["uvicorn", "src.serving.app:app", "--host", "0.0.0.0", "--port", "8000"]