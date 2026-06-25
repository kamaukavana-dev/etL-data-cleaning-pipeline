FROM python:3.11-slim AS builder

ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /build
COPY requirements.txt /build/requirements.txt
RUN python -m venv /opt/venv \
    && /opt/venv/bin/pip install --upgrade pip \
    && /opt/venv/bin/pip install -r /build/requirements.txt

FROM python:3.11-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

ENV PATH="/opt/venv/bin:$PATH"

RUN groupadd --system app && useradd --system --gid app --home-dir /app app

COPY --from=builder /opt/venv /opt/venv

COPY src /app/src
COPY config /app/config
COPY emails /app/emails
COPY data/raw /app/data/raw
COPY .env.example /app/.env.example

RUN mkdir -p /app/data/processed /app/data/reports /app/data/exports /app/logs /app/tmp \
    && chown -R app:app /app

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD python -c "import pathlib; p=pathlib.Path('/app/config/thresholds.yaml'); raise SystemExit(0 if p.exists() else 1)"

USER app

CMD ["python", "-m", "src.main"]
