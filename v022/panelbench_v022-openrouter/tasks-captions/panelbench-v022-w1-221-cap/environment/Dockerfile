FROM ubuntu:24.04

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Shell and Python for the agent (the agent phase is offline, so tools must be baked in)
RUN apt-get update && apt-get install -y --no-install-recommends python3 python3-pil python3-numpy ca-certificates curl && rm -rf /var/lib/apt/lists/*

WORKDIR /workspace
