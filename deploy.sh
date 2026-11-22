#!/usr/bin/env bash
# ==============================================================================
# One-Click Deployment Script for Campus Helpdesk Assistant
# Milestone 2 | SCSE4041 Prompt Engineering | Team Invictus
# Deploys Streamlit app + Cloudflare High-Speed Secure HTTPS Tunnel
# ==============================================================================

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_ROOT"

echo "=== 1. Checking Python Virtual Environment ==="
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
    .venv/bin/pip install -r requirements.txt
fi

echo "=== 2. Starting Streamlit Server on Port 8501 ==="
pkill -f "streamlit run app.py" 2>/dev/null || true
nohup .venv/bin/streamlit run app.py --server.port 8501 --server.headless true > /tmp/streamlit.log 2>&1 &
sleep 2

echo "=== 3. Setting Up Cloudflare Tunnel ==="
if [ ! -f "/tmp/cf_bin/cloudflared" ]; then
    mkdir -p /tmp/cf_bin
    curl -fsSL https://github.com/cloudflare/cloudflared/releases/download/2026.11.1/cloudflared-darwin-arm64.tgz | tar -xz -C /tmp/cf_bin
fi

pkill -f "cloudflared tunnel" 2>/dev/null || true
nohup /tmp/cf_bin/cloudflared tunnel --protocol http2 --url http://localhost:8501 > /tmp/tunnel.log 2>&1 &

echo "=== 4. Waiting for Public HTTPS URL ==="
for i in {1..20}; do
    if grep -q "trycloudflare.com" /tmp/tunnel.log 2>/dev/null; then
        TUNNEL_URL=$(grep -o 'https://[-a-z0-9]*\.trycloudflare\.com' /tmp/tunnel.log | head -n 1)
        echo ""
        echo "============================================================"
        echo " 🚀 DEPLOYMENT SUCCESSFUL!"
        echo " 🌐 LIVE PUBLIC URL: $TUNNEL_URL"
        echo "============================================================"
        echo " Faculty Credentials: ID: faculty | Password: faculty123"
        echo "============================================================"
        exit 0
    fi
    sleep 1
done

echo "Tunnel started. Check /tmp/tunnel.log for URL."
