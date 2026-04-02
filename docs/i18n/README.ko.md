# smartest-tv

[English](../../README.md) | **한국어** | [中文](README.zh.md) | [日本語](README.ja.md) | [Español](README.es.md) | [Deutsch](README.de.md) | [Português](README.pt-br.md) | [Français](README.fr.md)

**TV에 말하세요. 알아듣습니다.**

스마트 TV를 자연어로 제어하는 CLI와 AI 에이전트 스킬. Netflix, YouTube, Spotify 딥링크 — 보고 싶은 걸 말하면 재생됩니다. 개발자 모드 불필요. API 키 불필요. `stv setup` 한 번이면 끝.

> "프리렌 2기 8화 틀어줘"
>
> *넷플릭스가 열리고 해당 에피소드가 바로 재생됩니다.*

**LG** (테스트 완료), **Samsung**, **Android TV / Fire TV**, **Roku** (커뮤니티 테스트 중) 지원.

## 설치

```bash
pip install stv
```

끝입니다. LG는 추가 설치 없이 바로 됩니다.

```bash
pip install "stv[samsung]"  # Samsung Tizen
pip install "stv[android]"  # Android TV / Fire TV
pip install "stv[all]"      # 전부 다
```

## 제로 설정 시작

딱 한 번만 실행하면 됩니다:

```bash
stv setup
```

네트워크에서 TV를 자동 탐색하고, 플랫폼(LG? Samsung? Roku?)을 자동 감지하고, 자동으로 페어링합니다. 개발자 모드 필요 없고, IP 주소 찾아 헤맬 필요 없습니다. 설정은 `~/.config/smartest-tv/config.toml`에 저장됩니다. 이후로는 그냥 쓰면 됩니다.

뭔가 이상하다 싶으면 `stv doctor`가 정확히 뭐가 문제인지 알려줍니다.

## CLI

```bash
stv status                          # 현재 상태 (앱, 볼륨, 음소거)
stv launch netflix 82656797         # 넷플릭스 특정 콘텐츠 재생
stv launch youtube dQw4w9WgXcQ     # 유튜브 영상 재생
stv launch spotify spotify:album:x  # 스포티파이 재생
stv volume 25                       # 볼륨 설정
stv mute                            # 음소거 토글
stv apps --format json              # 설치된 앱 목록
stv notify "밥 먹어~"               # TV 화면에 알림
stv off                             # TV 끄기
```

모든 명령에 `--format json` 사용 가능 — AI 에이전트를 위한 구조화 출력.

## AI 에이전트 스킬

stv는 AI 어시스턴트에게 TV 제어 방법을 가르쳐주는 스킬 5개를 포함합니다. Claude Code에 한 번에 설치하세요:

```bash
cd smartest-tv && ./install-skills.sh
```

그러면 이런 게 됩니다:

```
나: 프리렌 2기 8화 넷플릭스에서 틀어줘
나: 아기한테 코코멜론 틀어줘
나: Ye 새 앨범 스포티파이로 틀어
나: 화면 끄고 재즈 틀어
나: 잘 자
```

스킬이 어려운 부분을 처리합니다 — 넷플릭스 에피소드 ID 찾기, yt-dlp로 유튜브 검색, 스포티파이 URI 해석 — 그리고 `stv` CLI를 호출해서 TV를 제어합니다.

### 스킬 목록

| 스킬 | 역할 |
|------|------|
| `tv-shared` | CLI 레퍼런스, 인증, 설정, 공통 패턴 |
| `tv-netflix` | Playwright로 에피소드 ID 조회 |
| `tv-youtube` | yt-dlp로 영상 검색 및 해석 |
| `tv-spotify` | 앨범/트랙/플레이리스트 URI 해석 |
| `tv-workflow` | 복합 액션: 영화 모드, 아이 모드, 수면 타이머 |

## 딥링크가 뭐가 다른가

다른 도구들은 넷플릭스를 *열기만* 합니다. stv는 *프리렌 36화를 재생*합니다. 이게 핵심 차이입니다.

같은 콘텐츠 ID가 모든 TV 플랫폼에서 작동합니다:

```bash
stv launch netflix 82656797                          # LG든 Samsung이든 Roku든 동일
stv launch youtube dQw4w9WgXcQ                       # 동일
stv launch spotify spotify:album:5poA9SAx0Xiz1cd17f  # 동일
```

플랫폼마다 딥링크 형식이 다르지만 드라이버가 알아서 변환합니다. 신경 쓸 필요 없습니다.

## 지원 플랫폼

| 플랫폼 | 드라이버 | 연결 방식 | 상태 |
|--------|---------|----------|------|
| LG webOS | [bscpylgtv](https://github.com/chros73/bscpylgtv) | WebSocket :3001 | **테스트 완료** |
| Samsung Tizen | [samsungtvws](https://github.com/xchwarze/samsung-tv-ws-api) | WebSocket :8002 | 커뮤니티 테스트 중 |
| Android / Fire TV | [adb-shell](https://github.com/JeffLIrion/adb-shell) | ADB TCP :5555 | 커뮤니티 테스트 중 |
| Roku | HTTP ECP | REST :8060 | 커뮤니티 테스트 중 |

LG가 주요 테스트 플랫폼입니다. Samsung, Android TV, Roku도 작동해야 합니다 — 어떤 플랫폼도 개발자 모드가 필요 없습니다 — 사용 경험을 알려주시면 반영하겠습니다.

## 설정 파일

설정은 `~/.config/smartest-tv/config.toml`에 저장됩니다. `stv setup` 후 이런 모습입니다:

```toml
[tv]
platform = "lg"
ip = "192.168.1.100"
mac = "AA:BB:CC:DD:EE:FF"   # 선택사항, Wake-on-LAN용
```

첫 연결 시 TV에 페어링 요청이 표시됩니다. 한 번 수락하면 키가 저장되고 다시는 묻지 않습니다.

## 실제 사용 사례

**새벽 2시.** 침대에서 Claude에게 말합니다: "프리렌 이어서 틀어줘." 거실 TV가 켜지고, 넷플릭스가 열리고, 에피소드가 시작됩니다. 리모컨을 건드리지도 않았고, 눈도 제대로 안 뜬 상태였습니다.

**토요일 아침.** "아기한테 코코멜론 틀어줘." 유튜브에서 찾아 TV에서 재생됩니다. 아침 준비를 계속하세요. 커피가 식기 전에.

**친구들이 왔을 때.** "게임 모드, HDMI 2, 볼륨 줄여." 한 문장으로 세 가지 변경. 아무도 눈치채기 전에 완료.

**요리 중.** "화면 끄고 재즈 틀어." 화면이 꺼지고 음악이 흐릅니다. 메뉴 뒤지고 앱 찾고 그럴 필요 없이.

**잠들기 전.** "45분 후에 꺼줘." TV가 스스로 꺼집니다. 당신은 아닙니다.

## MCP 서버

Claude Desktop, Cursor 등 MCP 클라이언트용 — 선택 사항이고, CLI가 주 인터페이스입니다:

```json
{
  "mcpServers": {
    "tv": {
      "command": "uvx",
      "args": ["stv"]
    }
  }
}
```

18개 도구 제공. 설정은 `~/.config/smartest-tv/config.toml`에서 자동으로 읽습니다.

## 아키텍처

```
사용자 (자연어)
  → AI + 스킬 (yt-dlp / Playwright / 검색으로 콘텐츠 ID 찾기)
    → stv CLI (포맷 변환 및 전송)
      → 드라이버 (WebSocket / ADB / HTTP)
        → TV
```

## 기여하기

Samsung, Android TV, Roku **드라이버**가 가장 임팩트 있는 기여 포인트입니다. [드라이버 인터페이스](src/smartest_tv/drivers/base.py)가 정의되어 있으니 `TVDriver`를 구현해서 PR 주세요.

Disney+, Hulu, Prime Video 등 새 스트리밍 서비스용 **스킬**도 환영합니다.

## 라이선스

MIT
