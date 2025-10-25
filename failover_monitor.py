#!/usr/bin/env python3
import os
import json
import time
import subprocess
import logging
import requests

CONFIG_PATH = "/opt/failover-monitor/tunnels.json"
LOG_FILE = "/var/log/failover_monitor.log"

logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)


def ping(host: str, count: int = 1, timeout: int = 1) -> bool:
    """Ping host to check if reachable."""
    try:
        result = subprocess.run(
            ["ping", "-c", str(count), "-W", str(timeout), host],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        return result.returncode == 0
    except Exception as e:
        logging.error(f"Ping error: {e}")
        return False


def check_tunnel_status(account_id: str, tunnel_id: str, token: str) -> tuple[bool, bool]:
    """Check Cloudflare tunnel status via API.

    Returns:
        tuple[bool, bool]: (is_healthy, should_stop_service)
        - is_healthy: True if tunnel status is 'healthy'
        - should_stop_service: True if multiple different client_ids are found
    """
    url = f"https://api.cloudflare.com/client/v4/accounts/{account_id}/cfd_tunnel/{tunnel_id}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        data = response.json()
        if "result" in data:
            result = data["result"]

            # Check tunnel status
            status = result.get("status", "")
            is_healthy = status == "healthy"
            logging.info(f"Tunnel {tunnel_id} status: {status}")

            # Check connections for multiple client_ids
            connections = result.get("connections", [])
            client_ids = set()
            for conn in connections:
                client_id = conn.get("client_id")
                if client_id:
                    client_ids.add(client_id)

            should_stop_service = len(client_ids) >= 2

            if should_stop_service:
                logging.info(
                    f"Tunnel {tunnel_id} has {len(client_ids)} different client_ids: {list(client_ids)}")
            else:
                logging.info(
                    f"Tunnel {tunnel_id} has {len(client_ids)} unique client_id(s)")

            return is_healthy, should_stop_service
        else:
            logging.error(
                f"Unexpected API response for tunnel {tunnel_id}: {data}")
            return False, False

    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to check tunnel {tunnel_id} status: {e}")
        return False, False
    except json.JSONDecodeError as e:
        logging.error(
            f"Failed to parse API response for tunnel {tunnel_id}: {e}")
        return False, False


def systemctl(action: str, service_name: str):
    """Run systemctl command."""
    try:
        subprocess.run(["systemctl", action, service_name], check=True)
        logging.info(f"Service {service_name} -> {action}")
    except subprocess.CalledProcessError as e:
        logging.error(f"Failed to {action} {service_name}: {e}")


def main():
    # Load tunnel configurations
    with open(CONFIG_PATH, "r") as f:
        config = json.load(f)

    gateway_ip = config["gateway_ip"]
    tunnels = config["tunnels"]
    check_interval = config.get("check_interval", 3)  # 기본값 3초

    logging.info("Cloudflare Tunnel Monitor started.")
    logging.info(f"Gateway IP: {gateway_ip}")
    logging.info(f"Monitoring {len(tunnels)} tunnel(s)")
    logging.info(f"Check interval: {check_interval} seconds")

    # Main monitoring loop
    while True:
        # 1. 게이트웨이 핑 체크 - 네트워크 연결 상태 확인
        if not ping(gateway_ip):
            logging.warning(
                f"Gateway {gateway_ip} unreachable. Skipping tunnel monitoring.")
            time.sleep(check_interval)
            continue

        # 2. 각 터널 상태 확인
        for tunnel in tunnels:
            account_id = tunnel["account_id"]
            tunnel_id = tunnel["tunnel_id"]
            token = tunnel["token"]
            service = tunnel["service"]

            # Check tunnel status and client connections
            is_healthy, should_stop_service = check_tunnel_status(
                account_id, tunnel_id, token)

            if should_stop_service:
                # Multiple client_ids detected - stop local service
                logging.info(
                    f"Multiple client_ids detected for tunnel {tunnel_id}. Stopping local service {service}")
                systemctl("stop", service)
            elif not is_healthy:
                # Tunnel is unhealthy - start local service
                logging.error(
                    f"Tunnel {tunnel_id} is down. Starting local service {service}")
                systemctl("start", service)

        # Wait before next check
        time.sleep(check_interval)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logging.exception(f"Critical failure: {e}")
