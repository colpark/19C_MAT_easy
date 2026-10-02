# PanelBench MCP tool gateway (light; no models). FastMCP streamable HTTP on :8000/mcp.
FROM python:3.12-slim
RUN pip install --no-cache-dir "mcp==1.27.0"
COPY gateway.py /opt/gateway/gateway.py
WORKDIR /opt/gateway
EXPOSE 8000
ENTRYPOINT ["python", "/opt/gateway/gateway.py"]
