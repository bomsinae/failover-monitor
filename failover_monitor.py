#!/usr/bin/env python3
import os
import json
import time
import subprocess
import logging
from datetime import datetime

CONFIG_PATH = "/opt/failover-monitor/config.json"
STATE_FILE = "/var/run/failover_monitor_state"
LOG_FILE = "/var/log/failover_monitor.log"

logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)


def init_state():
    """Reset state on startup."""
    with open(STATE_FILE, "w") as f:
        f.write("unknown")
    logging.info("State file initialized to 'unknown' on startup.")


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


def systemctl(action: str, service_name: str):
    """Run systemctl command."""
    try:
        subprocess.run(["systemctl", action, service_name], check=True)
        logging.info(f"Service {service_name} -> {action}")
    except subprocess.CalledProcessError as e:
        logging.error(f"Failed to {action} {service_name}: {e}")


def read_state() -> str:
    """Read last known state (active_alive or active_dead)."""
    try:
        with open(STATE_FILE, "r") as f:
            return f.read().strip()
    except FileNotFoundError:
        return "unknown"


def write_state(state: str):
    """Save current state."""
    with open(STATE_FILE, "w") as f:
        f.write(state)


def main():
    init_state()

    # Load config
    with open(CONFIG_PATH, "r") as f:
        config = json.load(f)

    gateway_ip = config["gateway_ip"]
    active_ip = config["active_ip"]
    services = config["services_to_manage"]
    interval = config["ping_interval"]
    threshold = config["ping_fail_threshold"]

    fail_count = 0
    last_state = read_state()

    logging.info("Failover Monitor started.")

    while True:
        # 1️⃣ 게이트웨이 체크 - 내 네트워크 상태 확인
        if not ping(gateway_ip):
            logging.warning("Gateway unreachable. Skipping active monitoring.")
            time.sleep(interval)
            continue

        # 2️⃣ Active 서버 체크
        if ping(active_ip):
            fail_count = 0
            if last_state != "active_alive":
                logging.info(
                    "Active server is back online. Stopping standby services.")
                for svc in services:
                    systemctl("stop", svc)
                write_state("active_alive")
                last_state = "active_alive"
        else:
            fail_count += 1
            logging.warning(
                f"Ping to active failed ({fail_count}/{threshold})")

            if fail_count >= threshold and last_state != "active_dead":
                logging.error(
                    "Active server is down. Starting local standby services.")
                for svc in services:
                    systemctl("start", svc)
                write_state("active_dead")
                last_state = "active_dead"

        time.sleep(interval)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logging.exception(f"Critical failure: {e}")
