# CGV 예매 오픈 감시 프로그램

Python 기반으로 CGV 예매 상태를 주기적으로 감시하고, **예매 가능 상태가 처음 감지될 때만** Telegram 알림을 보내는 도구입니다.

## 기능
- 영화명/극장명/날짜/포맷 기준 감시 대상 설정
- `requests`로 주기적 페이지 조회
- `beautifulsoup4` 기반 파싱
- 예매 상태 판별 (`예매 불가`, `예매준비중`, `예매 가능`)
- 중복 알림 방지 (`watcher_state.json`에 마지막 상태 저장)
- 네트워크/파싱/Telegram 오류 로깅
- `.env` 환경변수 기반 설정
- 클래스 분리 구조 (`parser`, `notifier`, `scheduler`)
- 단위 테스트 가능한 구조

## 프로젝트 구조

```text
.
├─ cgv_watcher/
│  ├─ models.py
│  ├─ parser.py
│  ├─ notifier.py
│  ├─ scheduler.py
│  ├─ state_store.py
│  └─ watcher.py
├─ tests/
├─ .env.example
├─ main.py
└─ requirements.txt
```

## Windows 실행 방법

### 1) Python 설치
- Python 3.10+ 권장

### 2) 가상환경 생성 및 활성화 (PowerShell)
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 3) 의존성 설치
```powershell
pip install -r requirements.txt
```

### 4) 설정 파일 작성
`.env.example`을 복사해 `.env` 파일을 생성하고 값을 채우세요.

```powershell
Copy-Item .env.example .env
```

필수 값:
- `CGV_MOVIE_NAME=프로젝트 헤일메리`
- `CGV_THEATER_NAME=용산아이파크몰`
- `CGV_DATE=2026-03-29`
- `CGV_FORMAT=IMAX` (원하면 공백 가능)
- `TELEGRAM_BOT_TOKEN=<your_bot_token>`
- `TELEGRAM_CHAT_ID=<numeric_chat_id_or_@channel_username>`

선택 값:
- `CGV_URL` (기본 `https://cgv.co.kr/cnm/movieBook`)
- `POLL_INTERVAL_SECONDS` (기본 60)
- `STATE_FILE` (기본 `watcher_state.json`)

### 5) 실행
```powershell
python main.py
```

## 테스트 실행
```powershell
python -m unittest discover -s tests -p "test_*.py"
```

## 구현 참고
- CGV 페이지 구조가 변경되면 상태 판별 로직이 실패할 수 있습니다.
- 이 경우 로그(`HTML structure may have changed`)를 확인하고 `parser.py`의 토큰/선택 로직을 조정하세요.

- 403/차단이 지속될 경우 HTML 크롤링 대신 CGV 공식 앱 알림, 공식 API 제공 여부, 또는 다른 공식 알림 채널을 검토하세요.
