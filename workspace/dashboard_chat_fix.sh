#!/bin/bash
# Dashboard Chat Fix Script
# Run this to restart the dashboard service and load the v2.4 code with chat history fix

echo "=== Dashboard Chat Fix ==="
echo ""
echo "Step 1: Checking current dashboard status..."
sudo systemctl status vola-dashboard --no-pager -l

echo ""
echo "Step 2: Stopping dashboard (if running)..."
sudo systemctl stop vola-dashboard

echo ""
echo "Step 3: Starting dashboard with v2.4 code..."
sudo systemctl start vola-dashboard

echo ""
echo "Step 4: Verifying dashboard is running..."
sleep 2
sudo systemctl status vola-dashboard --no-pager -l

echo ""
echo "Step 5: Testing chat API..."
curl -s http://localhost:8083/api/status | python3 -c "import json,sys; d=json.load(sys.stdin); print(f'Messages loaded: {len(d.get(\"messages\", []))}')"

echo ""
echo "=== Done ==="
echo "The dashboard should now show chat messages at http://localhost:8083"
