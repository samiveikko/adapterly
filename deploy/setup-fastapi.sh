#!/bin/bash
# FastAPI Deployment Script for Adapterly
# Run as root on the production server

set -e

echo "=== FastAPI Deployment for Adapterly ==="
echo ""

# Configuration
APP_DIR="/var/www/workflow-server"
VENV_DIR="$APP_DIR/venv"
SERVICE_FILE="/etc/systemd/system/fastapi.service"

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "Please run as root (sudo)"
    exit 1
fi

# Step 1: Install Python dependencies
echo "1. Installing FastAPI dependencies..."
$VENV_DIR/bin/pip install fastapi uvicorn[standard] httpx pydantic-settings aiosqlite sqlalchemy[asyncio] --quiet
echo "   Done."

# Step 2: Copy systemd service file
echo "2. Setting up systemd service..."
cp $APP_DIR/deploy/fastapi.service $SERVICE_FILE
chmod 644 $SERVICE_FILE
systemctl daemon-reload
echo "   Done."

# Step 3: Enable and start FastAPI service
echo "3. Starting FastAPI service..."
systemctl enable fastapi
systemctl restart fastapi
sleep 2

# Check if service is running
if systemctl is-active --quiet fastapi; then
    echo "   FastAPI service is running."
else
    echo "   ERROR: FastAPI service failed to start!"
    echo "   Check logs: journalctl -u fastapi -f"
    exit 1
fi

# Step 4: Test FastAPI health endpoint
echo "4. Testing FastAPI health..."
HEALTH=$(curl -s http://127.0.0.1:8001/health 2>/dev/null || echo "failed")
if echo "$HEALTH" | grep -q "healthy"; then
    echo "   Health check passed: $HEALTH"
else
    echo "   ERROR: Health check failed!"
    echo "   Response: $HEALTH"
    exit 1
fi

# Step 5: Update nginx configuration
echo "5. Updating nginx configuration..."
echo ""
echo "   MANUAL STEP REQUIRED:"
echo "   Add the following to your nginx server block:"
echo ""
echo "   # In /etc/nginx/sites-available/<your-app>.conf"
echo "   # Add inside server { } block:"
echo ""
cat $APP_DIR/deploy/nginx-fastapi.conf | grep -A 100 "location /mcp/v1/"
echo ""
echo "   Then run: sudo nginx -t && sudo systemctl reload nginx"
echo ""

# Step 6: Final test
echo "6. Deployment complete!"
echo ""
echo "   FastAPI: http://127.0.0.1:8001"
echo "   Service: systemctl status fastapi"
echo "   Logs:    journalctl -u fastapi -f"
echo ""
echo "   After nginx config, test with:"
echo "   curl -X POST https://<your-domain>/mcp/v1/ \\"
echo "     -H 'Authorization: Bearer YOUR_API_KEY' \\"
echo "     -H 'Content-Type: application/json' \\"
echo "     -d '{\"jsonrpc\":\"2.0\",\"id\":1,\"method\":\"tools/list\"}'"
