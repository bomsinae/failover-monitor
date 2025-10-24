#!/bin/bash
set -e

INSTALL_DIR="/opt/failover-monitor"
SERVICE_FILE="/etc/systemd/system/failover-monitor.service"
LOG_FILE="/var/log/failover_monitor.log"
STATE_FILE="/var/run/failover_monitor_state"

echo "=== Installing Cloudflare Tunnel Monitor ==="

# Python requests 모듈 확인 및 설치
if ! python3 -c "import requests" 2>/dev/null; then
    echo "Installing Python requests module..."
    sudo apt-get update
    sudo apt-get install -y python3-requests
fi

# 1. 설치 디렉토리 생성
sudo mkdir -p $INSTALL_DIR
sudo cp failover_monitor.py tunnels.json $INSTALL_DIR/
sudo chmod +x $INSTALL_DIR/failover_monitor.py

# 2. 로그 파일 준비 (상태 파일은 터널별로 생성됨)
sudo touch $LOG_FILE
sudo chmod 666 $LOG_FILE

# 3. systemd 유닛 설치
sudo cp failover-monitor.service $SERVICE_FILE
sudo systemctl daemon-reload
sudo systemctl enable failover-monitor

echo "✅ Installation complete."
echo ""
echo "⚠️  IMPORTANT: Edit the tunnel configuration file:"
echo "   sudo nano $INSTALL_DIR/tunnels.json"
echo ""
echo "   Replace the placeholder values with your actual:"
echo "   - account_id: Your Cloudflare account ID"
echo "   - tunnel_id: Your Cloudflare tunnel ID"
echo "   - token: Your Cloudflare API token"
echo "   - service: Your local cloudflared service name"
echo ""
echo "After configuration, start the service:"
echo "   sudo systemctl start failover-monitor"
echo ""
echo "Monitor logs:"
echo "   sudo tail -f $LOG_FILE"
