# Failover Monitor

Active-Standby 구조에서 Primary 서버의 상태를 모니터링하고 장애 발생 시 자동으로 Standby 서버의 서비스를 활성화하는 시스템입니다.

## 주요 기능

- **네트워크 상태 모니터링**: 게이트웨이와 Primary 서버의 연결 상태를 지속적으로 확인
- **자동 장애 조치**: Primary 서버 다운 시 지정된 서비스들을 자동으로 시작
- **자동 복구**: Primary 서버 복구 시 Standby 서비스들을 자동으로 중지
- **systemd 통합**: 시스템 서비스로 등록되어 부팅 시 자동 시작
- **상세한 로깅**: 모든 모니터링 활동과 장애 조치 내역을 기록

## 시스템 요구사항

- Linux 운영체제 (systemd 지원)
- Python 3.6 이상
- root 권한 (서비스 제어를 위해 필요)
- 네트워크 연결 (ping 명령어 사용)

## 설치 방법

1. 프로젝트 파일을 다운로드합니다:
   ```bash
   git clone <repository-url>
   cd failover-monitor
   ```

2. 설정 파일을 환경에 맞게 수정합니다:
   ```bash
   vi config.json
   ```

3. 설치 스크립트를 실행합니다:
   ```bash
   chmod +x install.sh
   sudo ./install.sh
   ```

## 설정 방법

`config.json` 파일을 편집하여 환경에 맞게 설정합니다:

```json
{
  "gateway_ip": "192.168.1.1",           // 네트워크 게이트웨이 IP
  "active_ip": "192.168.1.2",          // Primary 서버 IP
  "ping_interval": 3,                    // ping 체크 간격 (초)
  "ping_fail_threshold": 3,              // 장애 판정 임계값
  "services_to_manage": [                // 관리할 서비스 목록
    "cloudflared.service"
  ]
}
```

### 설정 항목 설명

- **gateway_ip**: 네트워크 연결 상태를 확인할 게이트웨이 IP 주소
- **active_ip**: 모니터링할 Primary 서버의 IP 주소
- **ping_interval**: ping 체크를 수행할 간격 (초 단위)
- **ping_fail_threshold**: 연속 ping 실패 횟수가 이 값에 도달하면 장애로 판정
- **services_to_manage**: 장애 조치 시 시작/중지할 systemd 서비스 목록

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
# 현재 모니터링 상태 확인
cat /var/run/failover_monitor_state
```

상태 값:
- `unknown`: 초기 상태 또는 알 수 없는 상태
- `active_alive`: Primary 서버가 정상 동작 중
- `active_dead`: Primary 서버 다운, Standby 서비스 활성화됨

## 동작 원리

1. **네트워크 연결 확인**: 먼저 게이트웨이에 ping을 보내 자신의 네트워크 연결 상태를 확인합니다.

2. **Primary 서버 모니터링**: 네트워크가 정상인 경우 Primary 서버에 ping을 보내 상태를 확인합니다.

3. **장애 감지**: 연속으로 설정된 임계값만큼 ping이 실패하면 Primary 서버 장애로 판정합니다.

4. **Standby 활성화**: 장애 감지 시 설정된 서비스들을 자동으로 시작합니다.

5. **자동 복구**: Primary 서버가 다시 응답하면 Standby 서비스들을 자동으로 중지합니다.

## 디렉토리 구조

```
/opt/failover-monitor/
├── failover_monitor.py    # 메인 모니터링 스크립트
└── config.json           # 설정 파일

/var/log/
└── failover_monitor.log  # 로그 파일

/var/run/
└── failover_monitor_state # 현재 상태 파일

/etc/systemd/system/
└── failover-monitor.service # systemd 서비스 파일
```

## 문제 해결

### 서비스가 시작되지 않는 경우

1. Python 설치 상태 확인:
   ```bash
   python3 --version
   ```

2. 권한 확인:
   ```bash
   ls -la /opt/failover-monitor/
   ```

3. 설정 파일 문법 확인:
   ```bash
   python3 -m json.tool /opt/failover-monitor/config.json
   ```

### 로그에 오류가 표시되는 경우

1. 네트워크 연결 확인:
   ```bash
   ping -c 3 192.168.1.1  # 게이트웨이 IP로 변경
   ping -c 3 192.168.1.2  # Primary 서버 IP로 변경
   ```

2. 서비스 권한 확인:
   ```bash
   systemctl list-units | grep cloudflared  # 관리 대상 서비스 확인
   ```

### 설정 변경 후 재시작

```bash
sudo systemctl restart failover-monitor
```

## 보안 고려사항

- 이 서비스는 root 권한으로 실행됩니다 (systemctl 명령어 사용을 위해)
- 설정 파일에는 민감한 정보가 포함될 수 있으므로 적절한 파일 권한을 설정하세요
- 방화벽 설정에서 ping(ICMP) 패킷이 허용되는지 확인하세요

## 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다.

## 지원

문제나 질문이 있으시면 GitHub Issues를 통해 문의해 주세요.