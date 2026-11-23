# Pinned to Python 3.12, matching the project's declared runtime support.
FROM python:3.12.8-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Create a dedicated, unprivileged runtime identity before copying application code.
RUN groupadd --gid 10001 paytrack \
    && useradd --uid 10001 --gid paytrack --create-home --shell /usr/sbin/nologin paytrack

# Copy only dependency metadata and the package marker first. This preserves the
# dependency-installation layer when implementation files change.
COPY pyproject.toml ./
COPY app/paytrack/__init__.py ./app/paytrack/__init__.py
RUN python -m pip install --upgrade "pip==24.3.1" \
    && python -m pip install .

# Install the complete application without re-resolving production dependencies.
COPY app ./app
RUN python -m pip install --no-deps . \
    && chown --recursive paytrack:paytrack /app

USER paytrack

EXPOSE 8000

# No curl package is required solely for health checks; Python is already present.
HEALTHCHECK --interval=30s --timeout=3s --start-period=15s --retries=3 \
    CMD python -c "from urllib.request import urlopen; urlopen('http://127.0.0.1:8000/health', timeout=2)"

CMD ["python", "-m", "uvicorn", "paytrack.main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers"]
