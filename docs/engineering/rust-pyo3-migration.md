# Rust + PyO3 마이그레이션 계획 — stv

> 상태: 초안 (리뷰 완료, 구현 전)
> 기준 커밋: v1.2.1 (`d11bdaf`)
> 원칙: **HA 통합과 CLI/MCP 사용자 경험은 100% 동작 유지. 전환 기간 내내 Python 폴백 병행.
> 게이트를 통과하지 못한 프로토콜은 절대 강제 전환하지 않는다.**

---

## 0. 요약

| 항목 | 결정 |
|---|---|
| 최종 형태 | Rust 코어 크레이트(`stv-core`) + PyO3 확장(`stv-py`) + Rust CLI/MCP/serve 바이너리(`stv-cli`) |
| Python에 남는 것 | HA 커스텀 통합(`custom_components/smartest_tv/`), 얇은 shim(`smartest_tv` 패키지 — 임포트 표면 100% 유지), 전환 기간 동안의 Python 구현(폴백) |
| 배포 | PyPI `stv` (maturin, **abi3-py311** wheel: manylinux x86_64/aarch64 + macOS) — HA는 기존 경로 그대로 |
| 전환 제어 | `STV_BACKEND=auto|rust|python` (기본 `auto` = 플랫폼별 졸업 테이블), **플랫폼별 독립 전환** |
| 폴백 제거 | stv 3.0 (전 플랫폼 소크 통과 + 6개월 무회귀 후에만) |
| 성능은 목적 아님 | TV WS 왕복이 병목. 목적은 배포 단일화(#14류 소멸), 의존성 동결(#6류 소멸), MCP 시작 지연 |

---

## 1. 현황 인벤토리 (2026-08-16 전수 검증)

### 1.1 모듈 지도 (10,646줄)

| 모듈 | 줄 | 역할 | Rust 이식 |
|---|---|---|---|
| `cli.py` | 1,977 | click CLI, 45+ 커맨드/그룹 | Stage 5 (clap) |
| `_engine/resolve.py` | 1,095 | 컨텐츠 ID 해석 (Netflix 스크래핑, yt-dlp, Spotify, JustWatch, Laftel) | Stage 1-2 |
| `server.py` | 871 | fastmcp MCP 서버 (21 도구) | Stage 5 (rmcp 또는 수동 JSON-RPC) |
| `ui/*` | 1,494 | rich TUI/랜더링/NL 파서 | Stage 5 (ratatui) — `ui/nl.py`(169줄, 33 테스트) 먼저 |
| `cache.py` | 573 | 캐시/히스토리/커뮤니티 fallback (GitHub raw) | Stage 1-2 |
| `display.py` | 558 | TV 브라우저에 HTML 대시보드 (:8765 HTTP 서버) | Stage 1-2 (HTML 생성은 바이트 동일성 스냅샷) |
| `config.py` | 492 | config.toml (v1.2.1 TOML 안전화 완료) | Stage 1-2 |
| `insights.py` | 378 | 시청 통계 | Stage 1-2 |
| `api.py` | 368 | REST 서버 :8911 (RemoteDriver 상대) | Stage 5 (axum, **계약 동결**) |
| `resolve.py` | 365 | 엔진 위 얇은 디스패처 | shim 유지 |
| `setup.py` | 343 | 마법사, 플랫폼별 페어링 | Stage 5 |
| `drivers/*` | ~700 | base/remote/browser/factory | base→shim, factory→shim+백엔드 선택 |
| `_engine/drivers/*` | 3,121-α | LG/Samsung/Android/Roku 프로토콜 | **Stage 1 핵심** |
| `scenes/sync/cast/audio` | 482 | 씬 프리셋, 병렬 브로드캐스트, URL 파싱, 멀티룸 | Stage 1-2 |

### 1.2 서드파티 라이브러리 프로토콜 해부 (venv 소스 직접 검증)

**Samsung — samsungtvws (우리가 쓰는 경로만)**
- `wss://{host}:8002/api/v2/channels/samsung.remote.control?name={base64(name)}&token={token}`
- 첫 접속 응답 `data.token`을 파일 첫 줄로 저장(`samsung_{ip}.token`), 이후 URL에 실어 재인증 우회
- 명령 = JSON 텍스트 프레임: `SendRemoteKey.click("KEY_VOLUP")` → `{"method":"ms.remote.control","params":{"Cmd":"Click","DataOfCmd":"KEY_VOLUP",...}}`, `ChannelEmitCommand.launch_app(app_id, "DEEP_LINK", meta_tag)` → `ed.apps.launch` 페이로드 (PR #7/#10 확정)
- REST: `https://host:8002/ws/apps/{appId}` (close), `/ws/device/` (info) — 셀프서명 인증서 수용 필요
- **`samsungtvws/encrypted/`(커스텀 3라운드 Rijndael + AES + DH)은 우리 경로가 전혀 사용 안 함을 확인** → Rust에서 재구현 불필요 (가장 큰 리스크 사전 제거). `[encrypted]` extra는 사실상 사장(死藏) 의존성

**Android TV Remote v2 — androidtvremote2**
- 포트: 6466(원격 API) / 6467(페어링), 모두 TLS. TV 인증서는 셀프서명 → 클라이언트도 임의 인증서 수용
- 클라이언트 인증서: RSA-2048, **serial=1000**, CN={client_name}(우리는 "smartest-tv"), BasicConstraints CA:TRUE, SAN DNS:{client_name}, 유효기간 10년, 키 PEM은 PKCS#1(TraditionalOpenSSL) → `cert.pem`/`key.pem`을 `CONFIG_DIR/android-cert/`에 저장. **인증서는 존재하면 재사용(재생성 금지)** — 재생성하면 재페어링 강제됨
- 프레이밍: **varint 길이 프리픽스 + protobuf** (`remotemessage.proto` — louis49/androidtv-remote, Apache-2.0 / `polo.proto` — Google POLO)
- 페어링 시퀀스(정확히 재현해야 함):
  1. `pairing_request{client_name, service_name="atvremote"}` → `pairing_request_ack`
  2. `options{preferred_role=INPUT, encoding=HEX, symbol_length=6}` → `options`
  3. `configuration{client_role=INPUT, encoding=HEX, symbol_length=6}` → `configuration_ack` (이때 TV에 PIN 표시)
  4. PIN 6자리 hex. `secret = SHA256( hex(client_N) || "0"+hex(client_E) || hex(server_N) || "0"+hex(server_E) || hex(pin[2:]) )`, **`pin[0:2] == secret[0]` 검증** 후 `secret.secret = secret_bytes` 전송 → `secret_ack`
  - N/E는 각각 클라이언트/서버 인증서의 RSA public key modulus/exponent (대문자 hex; exponent는 "0"+hex 접두로 최소 2바이트 보장)
- 원격 채널: `RemoteMessage` protobuf — key code 이벤트, launch_app, current_app/volume_info/is_on 푸시 콜백

**LG webOS — aiowebostv**
- `ws://{host}:3000`, JSON. `register` 페이로드 = 고정 manifest(권한 28종 + 서명) + `pairingType: "PROMPT"` + `client-key`(있으면)
- 페어링 = TV 화면 승인 → 응답 `payload["client-key"]` 영속(`lg_key.json`). legacy bscpylgtv `.db` 마이그레이션 로직 존재
- **`_SmarTestWebOsClient` 하드닝(webOS 24/25, 이슈 #4)**: connect 시 8개 상태 구독(power/current_app/muted/volume/apps/inputs/sound_output/media_foreground_app)을 병렬 생성 후 결과 수집에서 `WebOsTvCommandError` 전체를 억제 → 401/403/서비스부재가 **구독 누락으로만** degrade되고 connect는 살아남음. 타임아웃은 전파. 이 의미론을 정확히 복제
- 명령: `ssap://` URI + payload (`media.controls.play`, `apps.launch` params로 유튜브 contentTarget, 넷플릭스 DIAL body 등)

**Roku — ECP**: 이미 순수 aiohttp 셀프 구현 (:8060 XML). SSDP 위치 헤더 파싱 포함.

**DIAL**: 이미 셀프 구현 — SSDP M-SEARCH `urn:dial-multiscreen-org:service:dial:1` → `Application-URL` → POST.

**외부 바이너리 의존 (Rust에서도 유지/대체)**
- `curl` 서브프로세스 (http.py — resolve 스크래핑, RemoteDriver, 커뮤니티 캐시) → **Rust: reqwest로 대체** (동일 UA/리다이렉트/compress 동작)
- `yt-dlp` 서브프로세스 (YouTube 해석) → 유지 (Rust에서도 spawn)

### 1.3 파일/계약 동결 목록 (사용자 가시 상태 — 바이트/의미 호환 필수)

| 파일/계약 | 소유자 | 비고 |
|---|---|---|
| `config.toml` | config.py | v1.2.1 인용 키 + 유니코드 sanitize 유지 |
| `cache.json` | cache.py | `docs/reference/cache-format.md` — 히스토리 포함 |
| `queue.json`, 씬 파일 | playback/scenes | |
| `lg_key.json`, `samsung_{ip}.token`, `android-cert/{cert,key}.pem` | 각 드라이버 | Rust가 기존 파일을 그대로 읽고 갱신 (크리덴셜 마이그레이션 없음이 목표) |
| REST `/api/{ping,status,info,volume,apps,launch,close,mute,power,notify,screen,media}` | api.py | 구버전 Python stv ↔ 신버전 Rust serve 상호운영 동결 |
| `smartest_tv` 임포트 표면 | HA 통합 | §3.2 목록 |

---

## 2. 딥리뷰 발견 (마이그레이션 전 수정 · Stage 0에 포함)

### P0 — 전환 전 반드시 수정 (Python 오라클이어야 신뢰 가능)

1. **Android 발견이 ADB 5555만 스캔** (`_engine/discovery.py::_adb_scan`, `setup.py` 포트 프로브).
   드라이버는 Remote Protocol v2(6466/6467)로 이미 전환됐는데, 발견은 ADB 디버깅을 켠 TV만 잡는다 → 대부분의 Android TV가 `stv setup`/HA 검색에서 보이지 않음 (이슈 #15 신고자처럼 수동 IP 입력 강제). **6466/6467 TCP 프로브로 교체**(5555는 레거시로 병행 가능).
2. **`api.py`가 `HTTPServer`(직렬) 사용**. 느린 TV 명령(Samsung `set_volume` 배치 ≈2.5–5s, connect 타임아웃 10s)이 모든 REST 요청을 블로킹 — remote/파티 모드에서 건강검사까지 멈춘다. `ThreadingHTTPServer`로 교체.
3. **`curl` 서브프로세스 의존** (http.py). HA 컨테이너(slim 베이스)에 curl이 없으면 resolve가 **조용히** 실패한다. 최소한 curl 부재 감지 시 명확한 에러 + `urllib` 폴백. (Rust 전환 시 reqwest로 근본 소멸이지만, 그때까지 HA 사용자의 play_media가 영향)

### P1 — 계획에 반영
4. `SamsungDriver.set_volume` 하한 리셋 전략(항상 50×VOLDOWN 후 N×VOLUP) — 상태 읽기 불가한 Tizen 제약 하의 설계. Rust에서도 동일 유지하되, 사용자 커스텀 최대 볼륨 옵션은 3.0+ 과제.
5. WoL이 `255.255.255.255`만 — 일부 AP가 글로벌 브로드캐스트를 차단. 서브넷 브로드캐스트 폴백 추가 고려.
6. `server.py::_get_driver`가 asyncio lock 내부에서 `connect()` — 느린 connect가 모든 MCP 도구 호출을 블로킹(최대 10s+).
7. Android `set_volume`이 keypress를 inter-delay 없이 연사 — 일부 TV에서 입력 유실 가능. 30–50ms 간격 권장.
8. `media_player.py` 인터럽트 핸들러가 `entity._attr_state` 직접 접근 — HA 내부 표면이지만 현재 동작함. 3.0에서 공개 API로 정리.

### 정상 확인 (Rust에서 그대로 보존할 핵심 의미론)
- LG webOS 24/25 구독 실패 억제 하드닝 (§1.2)
- Netflix DIAL 우회 → `DEEP_LINK` 폴백 (이슈 #8 대응)
- HA 페어링 플로우 v1.2.1 (PIN 단계, `STV_CONFIG_DIR` 크리덴셜)
- `STV_CONFIG_DIR`/`STV_HTTP_TIMEOUT` 등 환경변수 전체 (§6 체크리스트)

---

## 3. 목표 아키텍처

### 3.1 크레이트 레이아웃

```
stv-rs/                       (워크스페이스)
├─ crates/
│  ├─ stv-core/               # 프로토콜+도메인, pure Rust (pyo3 의존 금지)
│  │  ├─ src/driver/{mod,lg,samsung,android,roku,remote,browser}.rs
│  │  ├─ src/proto/           # vendored .proto (louis49) + prost 빌드
│  │  ├─ src/resolve/         # 컨텐츠 해석 + 스크래핑 (골든 HTML 픽스처)
│  │  ├─ src/{config,cache,apps,dial,discovery,wol}.rs
│  │  └─ src/sim/             # ★ 가짜 TV 프로토콜 시뮬레이터 (§5)
│  ├─ stv-py/                 # PyO3 cdylib (maturin) — 코어 재노출만
│  └─ stv-cli/                # clap CLI + rmcp MCP + axum serve (Stage 5)
```

- `stv-core`는 **tokio 런타임을 내부 소유**(global `OnceLock<Runtime>`), 모든 공개 API는 동기(블로킹) 함수로 노출. 이유: PyO3 경계에서 가장 단순·검증된 동시성 모델 (아래).
- 의존성: `tokio, tokio-tungstenite, rustls(+danger-accept-any-client-cert), rustls-pemfile, rsa, rcgen/x509-cert, prost, serde, serde_json, toml, reqwest(rustls), sha2, regex, thiserror, rand`
- **순수 Rust 고수**: OpenSSL 링크 금지 (manylinux/musl/aarch64 매트릭스 단순화). RSA는 `rsa` 크레이트로 생성/파싱(PKCS#1 PEM 호환).

### 3.2 Python 경계 — 임포트 표면 동결 (HA가 실제로 쓰는 것 전수 조사 결과)

HA 통합(`custom_components/smartest_tv/`)이 import하는 것은 정확히 이 6개뿐:
`create_driver`(factory), `add_tv`/`get_tv_config`(config), `resolve_app`(apps), `resolve`(resolve), `launch_content`(playback), 그리고 반환된 driver 객체의 17개 async 메서드.

→ `smartest_tv` 패키지는 이 표면을 **시그니처·예외 타입·반환 데이터클래스까지 동일하게** 유지한다:

```python
# smartest_tv/drivers/factory.py (shim)
def create_driver(tv_name=None) -> TVDriver:
    backend = _pick_backend(_platform_of(tv_name))   # STV_BACKEND + 졸업 테이블
    if backend == "rust":
        from ._rust_driver import RustDriverShim
        return RustDriverShim(tv_name)
    from smartest_tv._engine.drivers...              # 기존 경로 (폴백)
```

```python
class RustDriverShim(TVDriver):
    def __init__(...): self._r = stv_py.driver_new(...)   # PyO3
    async def connect(self):
        await asyncio.to_thread(self._r.connect)           # GIL은 Rust 측 allow_threads로 해제
    async def status(self):
        return TVStatus(**await asyncio.to_thread(self._r.status))  # pydict → 동일 dataclass
```

- **왜 `pyo3` 실험적 async 코루틴이 아니라 `asyncio.to_thread`인가**: 실험 기능(0.21+ `experimental-async-await`)은 ABI 불안정·에러 전파 검증 부족. to_thread는 HA/CPython 표준 경로이며, Rust 블로킹 호출은 전부 `Python::allow_threads`로 GIL을 놓아 HA 이벤트 루프를 절대 블로킹하지 않는다 (요청-별 스레드는 to_thread 풀).
- **푸시 콜백**(LG 구독/Android current_app): Rust가 `Py<PyAny>` 콜백 보유 + 전용 OS 스레드에서 `loop.call_soon_threadsafe` 로 전달. connect 시 shim이 `asyncio.get_running_loop()`를 넘긴다. 이 경로만이 HA 이벤트 루프 안전성 요구사항.
- 예외 매핑: Rust `thiserror` → shim에서 Python 타입으로 변환 (`NotPairedError(RuntimeError, "Not paired with this TV. ..."` — #15 메시지 포함, `ImportError` 계열은 shim에서 발생시키지 않음 = 코어가 내장돼 #14류 소멸).
- 데이터클래스(`TVStatus/TVInfo/App`)는 **shim이 소유**하고 Rust는 pydict만 반환 — ABI 버전 어긋남 원천 차단.

### 3.3 백엔드 선택 그래프

```
STV_BACKEND=python  ─→ 전부 Python (비상 롤백)
STV_BACKEND=rust    ─→ 전부 Rust
STV_BACKEND=auto (기본) ─→ 플랫폼별 졸업 테이블:
    lg: rust     (Stage 4 소크 통과 시점부터)
    samsung: rust
    roku: rust
    android: python → rust (포트 페어링 실기 검증 후)
    remote/browser: rust (HTTP 전용이라 저위험)
```
테이블은 `smartest_tv/_backend.py` 하나에 상수로 — HA 재시작 없이 env로 전체 강제 전환 가능.

---

## 4. 프로토콜 포트 매트릭스

| 프로토콜 | 난이도 | 핵심 리스크 | 검증 방법 (게이트) |
|---|---|---|---|
| Roku ECP | 하 | 없음 (HTTP+XML) | 시뮬레이터 + 실기 |
| DIAL/SSDP | 하 | 멀티캐스트 수신 타이밍 | 시뮬레이터 + 골든 SSDP 응답 |
| WoL | 하 | 없음 | 단위 |
| Samsung wss | 중 | 셀프서명 TLS 수용, 토큰 파일 라운드트립, Tizen 파편화 | 시뮬레이터(wss 서버) + 토큰 재사용 시나리오 + 실기 |
| LG SSAP | 중상 | **webOS 24/25 구독-실패 억제 의미론**, PROMPT 페어링 | 시뮬레이터(401 주입 포함) + **사용자 실기 LG(192.168.200.101) 소크** |
| Android v2 | 상 | POLO 시크릿 계산 바이트 정확성, RSA 인증서 호환, protobuf | 시뮬레이터(TLS+POLO 완전 구현) + 기존 cert.pem 재사용 테스트 + 실기 |
| resolve 스크래핑 | 중 | Brave/DDG HTML 회귀, yt-dlp JSON | 골든 HTML 스냅샷 20+ 케이스, 파이썬과 diff |
| display HTML | 중 | 생성 HTML 바이트 동일성 | 스냅샷 테스트 |
| config/cache | 하 | 파일 포맷 | 파이썬-러스트 상호 읽기 테스트 |

---

## 5. 단계별 실행 (게이트 명시)

### Stage 0 — 오라클 고도화 + P0 수정 (구현 2–3일)
1. §2 P0-1/2/3 수정 (Python, 즉시 릴리스 가능한 1.3.0)
2. **프로토콜 시뮬레이터 구축** (`tests/sim/`): LG SSAP 서버(ws, 401 주입 가능), Samsung wss 서버(토큰 발급), Android TLS+POLO 서버, Roku ECP 서버 — 전부 Python/asyncio, 현재 드라이버가 실제로 통과하는지 증명(현재 구현을 시뮬레이터로 돌리는 테스트 추가)
3. **실기 트래픽 캡처**: `STV_RECORD=dir` 훅으로 사용자 소유 TV(LG 확보)의 실제 프레임 기록 → 골든 픽스처. Samsung/Android는 시뮬레이터+기존 테스트 페이로드
4. 골든 캡처: resolve HTML 20+, config/cache 파일 상호변환 세트
- **게이트 0**: 404 기존 테스트 + 시뮬레이터 통합 테스트 전부 green. 1.3.0 릴리스.

### Stage 1 — stv-core 구현 (1–2주)
- 드라이버 5종 + config/cache/apps/dial/discovery/resolve/display 이식
- `stv-core` 단위테스트: 골든 픽스처 대응 (프레임 바이트 비교 포함)
- vendored .proto에서 prost 생성 (`protoc`는 CI에 고정 버전)
- **게이트 1**: 시뮬레이터 테스트를 Rust에서 100% 통과 (프레임 레벨 비교: Rust가 보낸 바이트 ≡ Python이 보낸 바이트)

### Stage 2 — 차등(differential) 검증 (1주)
- 하나의 테스트 드라이버가 Python 드라이버와 Rust 드라이버를 같은 시나리오로 구동 → 상태/명령 순서/에러 타입 전체 diff
- 파일 호환: Python이 쓴 config/cache/크리덴셜을 Rust가 읽고 갱신, 역방향 동일
- **게이트 2**: 전 시나리오 diff 0 (에러 메시지 텍스트까지 — #14/#15에서 배운 교훈: 메시지가 제품이다)

### Stage 3 — PyO3 + HA 통합 (3–5일)
- stv-py + shim, `pytest-homeassistant-custom-component`로 HA 실환경 테스트 (config_flow 페어링 포함)
- 기존 HA 페어링 테스트(스텁)는 그대로 두되, 실 shim 위에서 재실행
- maturin CI 매트릭스: `cp311-abi3` × {manylinux_2_28 x86_64, manylinux_2_28 aarch64(RPi 필수), musllinux x86_64(선택), macOS arm64/x86_64}
- **게이트 3**: HA 테스트 전부 green + 모든 매트릭스 wheel 빌드 성공 + `pip install stv==2.0a1 && stv doctor` 클린 venv E2E

### Stage 4 — 실기 섀도우 소크 (2–4주 캘린더)
- 대상: 사용자 LG(확보), Android TV(확보 필요 — 없으면 시뮬레이터+커뮤니티 베타), Samsung/Roku는 커뮤니티 베타
- 야간 소크: `stv doctor --loop`로 양백엔드 동일 명령 실행·결과 diff 로깅, 연결 유지 72h, 재부팅/전원꺼짐 회복, 페어링 재시나리오(토큰 삭제 후 재페어링)
- 베타 배포: `stv 2.0b1` — **기본 auto에서 android만 python 유지**, README에 롤백 안내
- **게이트 4 (플랫폼별)**: 72h 무결차 + 실기 시나리오 전통과 + 베타 사용자 회귀 0건 2주 → 해당 플랫폼 졸업 테이블 rust로

### Stage 5 — CLI/MCP/serve Rust 전환 (1주, 독립 배포 가능)
- clap CLI(커맨드 표면/출력 포맷 동결 — `--fmt json` 스키마 동일), rmcp MCP(도구 21개 시그니처 동결), axum serve(REST 계약 동결, 구버전 Python RemoteDriver 클라이언트로 상호운영 테스트)
- wheel에 바이너리 포함 + `stv` 엔트리포인트가 바이너리 exec (uvx/pipx 사용자는 변화 없음)
- **게이트 5**: 스킬(`skills/stv-concierge`) 전 커맨드 스크립트가 바이너리로 동일 동작

### 2.0.0 안정 릴리스 → 3.0에서 Python 폴백 제거 (조건: 전 플랫폼 6개월 무회귀)

---

## 6. 호환성 체크리스트 (빠뜨리면 안 되는 것)

- [ ] 환경변수 전목록: `STV_CONFIG_DIR, STV_BACKEND, STV_HTTP_TIMEOUT, STV_SUBPROCESS_TIMEOUT, STV_YTDLP_TIMEOUT, STV_API_KEY, STV_CORS_ORIGIN, STV_REGION, TV_PLATFORM, TV_IP, TV_MAC`
- [ ] `media_id` 포맷 `platform:query[:sNeN]` 정규식 동일
- [ ] HA `SCAN_INTERVAL` 30s, 3연속 실패 백오프 의미론 동일
- [ ] 크리덴셜 경로: `CONFIG_DIR/{android-cert/, samsung_IP.token, lg_key.json}` + `.db` 레거시 백업 마이그레이션
- [ ] 에러 메시지: "Not paired with this TV. …"(#15), 의존성 안내(#14), "MAC address required for Wake-on-LAN"
- [ ] `stv serve` 보안 정책: 0.0.0.0 바인드 시 STV_API_KEY 강제
- [ ] 커뮤니티 캐시 fallback URL + `community-cache.json` 포맷
- [ ] 라이선스:
  - aiowebostv **Apache-2.0** — REGISTRATION_PAYLOAD 상수 사용 시 NOTICE 고지
  - androidtvremote2 **Apache-2.0** — 재배포 .proto(remotemessage/polo) vendoring + 출처 고지
  - samsungtvws **LGPL-3.0** — ⚠️ 코드 복사 금지. Rust 구현은 와이어 관찰 기반 클린룸(페이로드 JSON 구조는 사실(fact)이며 표현물이 아님). 리뷰 시 samsungtvws 소스를 나란히 보지 않고 문서화된 페이로드로 작성

## 7. 리스크 레지스터 (상위 8)

| # | 리스크 | 확률 | 영향 | 완화 |
|---|---|---|---|---|
| 1 | Android POLO 페어링 바이트 불일치 | 중 | 큼(해당 TV 전체) | 시뮬레이터 프레임 비교 + 기존 cert 재사용 테스트 + **android는 마지막 졸업** |
| 2 | webOS 페더웨어 파편화 (24/25 권한) | 중 | 큼 | 사용자 실기 소크 + 구독-억제 의미론 단위테스트 + python 폴백 유지 |
| 3 | GIL/교착으로 HA 루프 블로킹 | 저 | 치명 | to_thread+allow_threads 원칙, 모든 블로킹 호출에 타임아웃, HA 실환경 테스트 |
| 4 | abi3 wheel 매트릭스 실패(RPi) | 중 | 중 | Stage 3부터 CI 매트릭스, aarch64 게이트 최우선 |
| 5 | 스크래핑 회귀(Brave/DDG 마크업 변경) | 높 | 중(기존과 동일 위험) | 골든 HTML + diff 테스트, 회귀 시 python과 동일하게 실패하는지 확인(신규 리스크 0) |
| 6 | Tizen 파편화(토큰/REST 응답 변형) | 중 | 중 | 시뮬레이터 변형 케이스 + 커뮤니티 베타 |
| 7 | 크리덴셜 파일 파손 | 저 | 큼 | 상호변환 테스트 + 쓰기는 atomic(기존 `_atomic_write_text` 의미론) |
| 8 | 전환 중 이중 유지보수 부담 | 높 | 중 | 플랫폼별 졸업으로 기간 최소화, 신기능은 Rust에만 |

## 8. 중단/후퇴 기준 (abort criteria)

- 게이트 2(차등 diff 0)를 2회 시도 후에도 미달인 프로토콜 → 해당 플랫폼은 Python 영구 유지, 나머지만 전환 (하이브리드가 계획의 일부)
- 소크에서 Python에 없는 회귀 1건 → 해당 플랫폼 즉시 테이블 롤백 + `STV_BACKEND` 공지
- HA 실환경 테스트에서 이벤트 루프 블로킹 1건 감지 → 게이트 3 재통과까지 배포 금지
- Python 폴백 제거(3.0)는 "전 플랫폼 6개월 무회귀" 하드 조건 — 충족 못하면 3.0 없음

## 9. 규모 추정

| 단계 | 구현 | 검증 포함 |
|---|---|---|
| Stage 0 | 2–3일 | 3–4일 |
| Stage 1 | 7–10일 | 12일 |
| Stage 2 | 3일 | 7일 |
| Stage 3 | 3–5일 | 7일 |
| Stage 4 | — | 2–4주(캘린더) |
| Stage 5 | 5–7일 | 10일 |
| **합계** | ~4주 구현 | **6–9주 캘린더** |

Rust 코드량 추정: 코어 ~6–8k줄, py shim +400줄(신규), 기존 Python 삭제는 3.0까지 보류.
