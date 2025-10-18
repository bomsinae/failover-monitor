#!/bin/bash
set -e

INSTALL_DIR="/opt/failover-monitor"
SERVICE_FILE="/etc/systemd/system/failover-monitor.service"
LOG_FILE="/var/log/failover_monitor.log"
STATE_FILE="/var/run/failover_monitor_state"

echo "=== Installing Failover Monitor ==="

# 1. 설치 디렉토리 생성
sudo mkdir -p $INSTALL_DIR
sudo cp failover_monitor.py config.json $INSTALL_DIR/
sudo chmod +x $INSTALL_DIR/failover_monitor.py

# 2. 로그/상태 파일 준비
sudo touch $LOG_FILE
sudo touch $STATE_FILE
sudo chmod 666 $LOG_FILE $STATE_FILE

# 3. systemd 유닛 설치
sudo cp failover-monitor.service $SERVICE_FILE
sudo systemctl daemon-reload
sudo systemctl enable failover-monitor
sudo systemctl restart failover-monitor

echo "✅ Installation complete."
echo "Log file: $LOG_FILE"
echo "Service: systemctl status failover-monitor"
