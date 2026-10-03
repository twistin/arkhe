FROM ghcr.io/astral-sh/uv:0.9.5 AS uv
FROM python:3.12-slim-bookworm
COPY --from=uv /uv /uvx /bin/
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy PATH="/opt/arkhe/.venv/bin:$PATH" PYTHONUNBUFFERED=1
RUN apt-get update && apt-get install -y --no-install-recommends sqlite3 && rm -rf /var/lib/apt/lists/*
WORKDIR /opt/arkhe
COPY pyproject.toml uv.lock README.md ./
COPY src/ ./src/
RUN uv sync --locked --no-dev --no-editable && \
    groupadd --gid 10001 arkhe && useradd --uid 10001 --gid 10001 --no-create-home arkhe && \
    mkdir -p /datos/docente && chown -R arkhe:arkhe /datos
USER 10001:10001
ENTRYPOINT ["python", "-m", "docente_ai.web.container"]
CMD ["serve", "--server", "--public-host", "arkhe.ejemplo.es", "--workspace", "/datos/docente"]
