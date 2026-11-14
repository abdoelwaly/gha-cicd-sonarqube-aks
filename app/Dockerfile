# syntax=docker/dockerfile:1.7

# ---- build: install the package into an isolated virtualenv
FROM python:3.13-slim AS build
ENV PIP_NO_CACHE_DIR=1 PIP_DISABLE_PIP_VERSION_CHECK=1
WORKDIR /src
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
COPY pyproject.toml ./
COPY src ./src
RUN pip install .

# ---- runtime: slim image, non-root user, no build tools
FROM python:3.13-slim
ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1
RUN groupadd --system --gid 10001 app \
 && useradd --system --uid 10001 --gid app --no-create-home app
COPY --from=build /opt/venv /opt/venv
USER 10001:10001
EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=3s CMD python -c "import urllib.request,sys; urllib.request.urlopen('http://127.0.0.1:8080/healthz'); sys.exit(0)"
CMD ["uvicorn", "orders_api.main:app", "--host", "0.0.0.0", "--port", "8080", "--no-access-log"]
