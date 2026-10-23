
FROM node:24-bookworm-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 python3-venv python3-pip git curl ca-certificates gh \
    && rm -rf /var/lib/apt/lists/*

RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

RUN git clone --depth 1 \
    https://github.com/M0-AR/agent-reach-mcp.git \
    /opt/agent-reach-mcp \
    && pip install --no-cache-dir /opt/agent-reach-mcp

RUN npm install -g supergateway mcporter

ENV PORT=10000

CMD ["sh", "-c", "supergateway --stdio 'agent-reach-mcp' --outputTransport streamableHttp --host 0.0.0.0 --port ${PORT:-10000} --healthEndpoint /health --tools doctor --tools read_url --tools search --tools trending --tools stock_quote --tools get_details --tools transcribe"]
