# Cloudflare Tunnel Monitor

Cloudflare Zero Trust 터널의 상태를 모니터링하고 터널이 다운되었을 때 자동으로 로컬 백업 서비스를 시작하는 시스템입니다.

## 주요 기능

- **Cloudflare API 모니터링**: Cloudflare Zero Trust 터널의 실시간 상태를 API를 통해 확인
- **다중 터널 지원**: 여러 개의 Cloudflare 계정/터널을 동시에 모니터링
- **자동 장애 조치**: 터널이 unhealthy 상태가 되면 지정된 로컬 서비스를 자동으로 시작
- **네트워크 연결 확인**: 게이트웨이 ping 체크를 통한 로컬 네트워크 상태 확인
- **systemd 통합**: 시스템 서비스로 등록되어 부팅 시 자동 시작
- **상세한 로깅**: 모든 모니터링 활동과 장애 조치 내역을 기록

## 시스템 요구사항

- Linux 운영체제 (systemd 지원)
- Python 3.6 이상
- python3-requests 패키지
- root 권한 (서비스 제어를 위해 필요)
- 인터넷 연결 (Cloudflare API 접근)

## 설치 방법

1. 프로젝트 파일을 다운로드합니다:
   ```bash
   git clone https://github.com/bomsinae/failover-monitor.git
   cd failover-monitor
   ```

2. 설치 스크립트를 실행합니다:
   ```bash
   chmod +x install.sh
   sudo ./install.sh
   ```

3. 설정 파일을 환경에 맞게 수정합니다:
   ```bash
   sudo nano /opt/failover-monitor/tunnels.json
   ```

## 설정 방법

`/opt/failover-monitor/tunnels.json` 파일을 편집하여 모니터링할 터널들을 설정합니다:

```json
{
  "gateway_ip": "192.168.1.1",
  "check_interval": 3,
  "tunnels": [
    {
      "account_id": "your_cloudflare_account_id_1",
      "tunnel_id": "your_tunnel_id_1",
      "token": "your_api_token_1",
      "service": "cloudflared_1"
    },
    {
      "account_id": "your_cloudflare_account_id_2", 
      "tunnel_id": "your_tunnel_id_2",
      "token": "your_api_token_2",
      "service": "cloudflared_2"
    }
  ]
}
```

### 설정 항목 설명

- **gateway_ip**: 네트워크 연결 상태를 확인할 게이트웨이 IP 주소
- **check_interval**: 터널 상태 확인 간격 (초 단위, 기본값: 3초)
- **tunnels**: 모니터링할 터널들의 배열
  - **account_id**: Cloudflare 계정 ID (대시보드 우측 하단에서 확인 가능)
  - **tunnel_id**: 모니터링할 Cloudflare 터널의 ID
  - **token**: Cloudflare API 토큰 (터널 읽기 권한 필요)
  - **service**: 터널 다운 시 시작할 로컬 systemd 서비스명

### Cloudflare API 토큰 생성

1. Cloudflare 대시보드 → Manage account → Account API Tokens
2. "Create Token" 클릭
3. Custom token 선택
4. 권한 설정:
   - Account: Cloudflare Tunnel:Read

## 사용 방법

### 서비스 시작/중지/상태 확인

```bash
# 서비스 시작
sudo systemctl start failover-monitor

# 서비스 중지
sudo systemctl stop failover-monitor

# 서비스 상태 확인
sudo systemctl status failover-monitor

# 자동 시작 활성화/비활성화
sudo systemctl enable failover-monitor
sudo systemctl disable failover-monitor
```

### 로그 확인

```bash
# 실시간 로그 보기
sudo tail -f /var/log/failover_monitor.log

# 전체 로그 확인
sudo cat /var/log/failover_monitor.log

# systemd 로그 확인
sudo journalctl -u failover-monitor -f
```

### 현재 상태 확인

```bash
# 실시간 로그 보기 (터널 상태 및 서비스 시작 여부 확인)
sudo tail -f /var/log/failover_monitor.log

# 서비스들의 현재 상태 확인
systemctl status cloudflared  # 설정한 서비스명으로 변경
```

## 동작 원리

1. **네트워크 연결 확인**: 먼저 게이트웨이에 ping을 보내 자신의 네트워크 연결 상태를 확인합니다.

2. **터널 상태 확인**: 네트워크가 정상인 경우 Cloudflare API를 통해 각 터널의 상태를 주기적으로 확인합니다.

3. **API 요청**: `https://api.cloudflare.com/client/v4/accounts/{account_id}/cfd_tunnel/{tunnel_id}` 엔드포인트를 사용하여 터널 상태를 조회합니다.

4. **상태 판정**: API 응답에서 `"status": "healthy"`인지 확인합니다.

5. **장애 조치**: 터널이 unhealthy 상태인 경우 해당 터널의 백업 서비스를 자동으로 시작합니다.

> **참고**: 터널이 healthy 상태일 때는 별도의 작업을 수행하지 않습니다. 오직 터널이 다운되었을 때만 로컬 서비스를 시작합니다.

## 디렉토리 구조

```
/opt/failover-monitor/
├── failover_monitor.py    # 메인 모니터링 스크립트
└── tunnels.json          # 터널 설정 파일

/var/log/
└── failover_monitor.log  # 로그 파일

/etc/systemd/system/
└── failover-monitor.service # systemd 서비스 파일
```

## 문제 해결

### 서비스가 시작되지 않는 경우

1. Python 및 requests 모듈 설치 확인:
   ```bash
   python3 --version
   python3 -c "import requests; print('requests module OK')"
   ```

2. 권한 확인:
   ```bash
   ls -la /opt/failover-monitor/
   ```

3. 설정 파일 문법 확인:
   ```bash
   python3 -m json.tool /opt/failover-monitor/tunnels.json
   ```

### API 오류가 발생하는 경우

1. API 토큰 권한 확인:
   ```bash
   # 터널 목록 조회 테스트 (실제 값으로 교체)
   curl -H "Authorization: Bearer YOUR_API_TOKEN" \
        "https://api.cloudflare.com/client/v4/accounts/YOUR_ACCOUNT_ID/cfd_tunnel"
   ```

2. 네트워크 연결 확인:
   ```bash
   curl -I https://api.cloudflare.com
   ```

3. 터널 ID 확인:
   ```bash
   # Cloudflare 대시보드에서 터널 ID를 복사하거나
   # cloudflared tunnel list 명령어로 확인
   ```

### 서비스 제어 오류가 발생하는 경우

1. 백업 서비스 상태 확인:
   ```bash
   systemctl list-units | grep cloudflared
   systemctl status cloudflared_1  # 설정한 서비스명으로 변경
   ```

2. 서비스 파일 존재 확인:
   ```bash
   ls -la /etc/systemd/system/ | grep cloudflared
   ```

### 설정 변경 후 재시작

```bash
sudo systemctl restart failover-monitor
```

## 보안 고려사항

- **API 토큰 보안**: tunnels.json 파일에는 민감한 API 토큰이 포함되므로 적절한 파일 권한을 설정하세요
  ```bash
  sudo chmod 600 /opt/failover-monitor/tunnels.json
  ```
- **Root 권한**: 이 서비스는 systemctl 명령어 사용을 위해 root 권한으로 실행됩니다
- **방화벽**: Cloudflare API (443 포트)에 대한 외부 연결이 허용되는지 확인하세요
- **API 제한**: Cloudflare API 요청 제한을 고려하여 모니터링 간격을 적절히 설정하세요 (기본 3초)

## 주의사항

1. **서비스 자동 중지 없음**: 터널이 복구되어도 로컬 서비스를 자동으로 중지하지 않습니다.
2. **중복 서비스 시작**: 터널이 다운될 때마다 서비스 시작 명령을 실행합니다 (이미 실행 중이어도).
3. **빠른 체크 간격**: 기본 3초 간격으로 체크하므로 API 사용량에 주의하세요.


## 로그 출력 예제
```
2025-10-24 10:30:15 [INFO] Cloudflare Tunnel Monitor started.
2025-10-24 10:30:15 [INFO] Gateway IP: 192.168.1.1
2025-10-24 10:30:15 [INFO] Monitoring 2 tunnel(s)
2025-10-24 10:30:15 [INFO] Check interval: 3 seconds
2025-10-24 10:30:16 [INFO] Tunnel abc123 status: healthy
2025-10-24 10:30:16 [INFO] Tunnel def456 status: healthy
2025-10-24 10:30:19 [WARNING] Gateway 192.168.1.1 unreachable. Skipping tunnel monitoring.
2025-10-24 10:30:22 [INFO] Tunnel abc123 status: down
2025-10-24 10:30:22 [ERROR] Tunnel abc123 is down. Starting local service cloudflared_1
2025-10-24 10:30:25 [INFO] Tunnel abc123 status: healthy
2025-10-24 10:30:28 [INFO] Tunnel abc123 status: down
2025-10-24 10:30:28 [ERROR] Tunnel abc123 is down. Starting local service cloudflared_1
```

> **참고**: 터널이 healthy 상태로 복구되어도 로컬 서비스를 중지하지 않습니다. 필요시 수동으로 서비스를 중지해야 합니다.

## 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다.

## 지원

문제나 질문이 있으시면 GitHub Issues를 통해 문의해 주세요.