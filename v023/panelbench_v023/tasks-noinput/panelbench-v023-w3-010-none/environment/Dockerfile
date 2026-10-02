FROM ubuntu:24.04

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Shell and Python for the agent (the agent phase is offline, so tools are baked in)
RUN apt-get update && apt-get install -y --no-install-recommends python3 python3-pil python3-numpy ca-certificates curl git coreutils \
    && rm -rf /var/lib/apt/lists/*

# OpenHands SDK baked in (Harbor skips its install step when this venv imports openhands.sdk); pinned for reproducibility
RUN uv python install 3.12 && uv venv /opt/openhands-sdk-venv --python 3.12 \
    && VIRTUAL_ENV=/opt/openhands-sdk-venv uv pip install openhands-sdk==1.50.1 openhands-tools==1.50.1 fastapi \
    && /opt/openhands-sdk-venv/bin/python -c "import openhands.sdk"

WORKDIR /workspace
