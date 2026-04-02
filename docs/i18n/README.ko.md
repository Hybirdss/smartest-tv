# smartest-tv

[![PyPI](https://img.shields.io/pypi/v/stv)](https://pypi.org/project/stv/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://python.org)

[English](../../README.md) | **한국어** | [中文](README.zh.md) | [日本語](README.ja.md) | [Español](README.es.md) | [Deutsch](README.de.md) | [Português](README.pt-br.md) | [Français](README.fr.md)

**TV에 말하세요. 알아듣습니다.**

다른 도구들은 넷플릭스를 *열기만* 합니다. smartest-tv는 *프리렌 2기 8화를 재생*합니다.

<p align="center">
  <img src="../../docs/assets/hero.png" alt="The Evolution of TV Control" width="720">
</p>

## 빠른 시작

```bash
pip install stv
stv setup          # TV 자동 탐색, 페어링, 완료
```

끝입니다. 개발자 모드 불필요. API 키 불필요. 환경변수 불필요. 보고 싶은 걸 말하면 됩니다.

## 무엇을 할 수 있나요?

```
나: 넷플릭스에서 프리렌 2기 8화 틀어줘
나: 아기한테 상어 가족 틀어줘
나: Ye 새 앨범 스포티파이로 틀어
나: 화면 끄고 재즈 틀어
나: 잘 자
```

AI가 콘텐츠 ID(넷플릭스 에피소드, 유튜브 영상, Spotify URI)를 찾아 `stv`를 호출하면, TV에서 바로 재생됩니다.

### See it in action

<p align="center">
  <a href="https://github.com/Hybirdss/smartest-tv/releases/download/v0.3.0/KakaoTalk_20260403_051617935.mp4">
    <img src="../../docs/assets/demo.gif" alt="smartest-tv demo" width="720">
  </a>
</p>

*Click for full video with sound*

## 설치

```bash
pip install stv                 # LG (기본, 바로 사용 가능)
pip install "stv[samsung]"      # Samsung Tizen
pip install "stv[android]"      # Android TV / Fire TV
pip install "stv[all]"          # 전부 다
```

## CLI

```bash
stv play netflix "Frieren" s2e8 --title-id 81726714   # 검색 + 한 번에 재생
stv play youtube "baby shark"                          # 검색 + 재생
stv resolve netflix "Jujutsu Kaisen" s3e10 --title-id 81278456  # ID만 조회
stv launch netflix 82656797         # 특정 콘텐츠로 딥링크 (ID를 알 때)
stv status                          # 현재 상태, 볼륨, 음소거 여부
stv volume 25                       # 볼륨 설정
stv mute                            # 음소거 토글
stv apps --format json              # 앱 목록 (구조화 출력)
stv notify "밥 먹어~"               # TV 화면에 토스트 알림
stv off                             # 잘 자
```

모든 명령에 `--format json` 사용 가능 — 스크립트와 AI 에이전트를 위한 설계.

### 콘텐츠 해석

`stv resolve`는 스트리밍 ID를 대신 찾아줍니다. `stv play`는 같은 작업을 하고 한 번에 TV에서도 재생합니다.

```bash
stv resolve netflix "Frieren" s2e8 --title-id 81726714    # → 82656797
stv resolve youtube "lofi hip hop"                         # → dQw4w9WgXcQ (yt-dlp 이용)
stv resolve spotify spotify:album:5poA9SAx0Xiz1cd17fWBLS  # → 그대로 전달
```

넷플릭스 해석은 타이틀 페이지에서 에피소드 메타데이터를 단 한 번의 `curl` 요청으로 스크래핑합니다 — Playwright도, 브라우저도, 로그인도 필요 없습니다. 모든 시즌이 한 번에 해석되어 로컬에 캐시됩니다. 두 번째 조회는 즉시 완료됩니다 (~0.1초).

### 캐시

ID를 한 번 찾으면 `~/.config/smartest-tv/cache.json`에 영구적으로 캐시됩니다. 수동으로 캐시를 채울 수도 있습니다:

```bash
stv cache set netflix "Frieren" -s 2 --first-ep-id 82656790 --count 10
stv cache get netflix "Frieren" -s 2 -e 8    # → 82656797
stv cache show                                # 캐시된 ID 전체 보기
```

## 에이전트 스킬

smartest-tv는 AI 어시스턴트에게 TV 제어 방법을 가르쳐주는 스킬 5개를 포함합니다. Claude Code에 한 번에 설치하세요:

```bash
cd smartest-tv && ./install-skills.sh
```

| 스킬 | 역할 |
|------|------|
| `tv-shared` | CLI 레퍼런스, 인증, 설정, 공통 패턴 |
| `tv-netflix` | HTTP 스크래핑으로 에피소드 ID 조회 |
| `tv-youtube` | yt-dlp로 영상 검색 및 포맷 해석 |
| `tv-spotify` | 앨범/트랙/플레이리스트 URI 해석 |
| `tv-workflow` | 복합 액션: 영화 모드, 아이 모드, 수면 타이머 |

스킬은 일반 마크다운 파일입니다. 어떤 에이전트에든 몇 분이면 이식할 수 있습니다.

## 호환 에이전트

셸 명령을 실행할 수 있는 AI 에이전트라면 모두 됩니다:

**Claude Code** · **OpenCode** · **Cursor** · **Codex** · **OpenClaw** · **Goose** · **Gemini CLI** · 또는 그냥 `bash`

## 실제 사용 사례

**새벽 2시.** 침대에서 Claude에게 말합니다: "프리렌 이어서 틀어줘." 거실 TV가 켜지고, 넷플릭스가 열리고, 에피소드가 시작됩니다. 리모컨을 건드리지도 않았고, 눈도 제대로 안 뜬 상태였습니다.

**토요일 아침.** "아기한테 코코멜론 틀어줘." 유튜브에서 찾아 TV에서 재생됩니다. 아침 준비를 계속하세요.

**친구들이 왔을 때.** "게임 모드, HDMI 2, 볼륨 줄여." 한 문장으로 세 가지 변경, 아무도 눈치채기 전에 완료.

**요리 중.** "화면 끄고 재즈 틀어." 화면이 꺼지고 음악이 흐릅니다.

**잠들기 전.** "45분 수면 타이머." TV가 스스로 꺼집니다. 당신은 아닙니다.

## smartest-tv란 무엇인가

- **딥링크 리졸버** — 넷플릭스 에피소드 ID, 유튜브 영상, Spotify URI를 찾아줍니다
- **만능 리모컨** — 4개 TV 플랫폼을 하나의 CLI로 제어
- **AI 네이티브** — 사람만이 아니라 에이전트가 호출하도록 설계

## smartest-tv가 아닌 것

- 리모컨 앱이 아닙니다 (채널 탐색, 방향키 조작 없음)
- HDMI-CEC 컨트롤러가 아닙니다
- 화면 미러링 도구가 아닙니다

<details>
<summary><strong>딥링크</strong> — 실제로 어떻게 동작하는가</summary>

동일한 콘텐츠 ID가 모든 TV 플랫폼에서 작동합니다:

```bash
stv launch netflix 82656797                           # LG, Samsung, Roku, Android TV
stv launch youtube dQw4w9WgXcQ                        # 동일
stv launch spotify spotify:album:5poA9SAx0Xiz1cd17f   # 동일
```

각 드라이버가 콘텐츠 ID를 플랫폼별 딥링크 형식으로 변환합니다:

| TV | 딥링크 전송 방식 |
|----|---------------|
| LG webOS | SSAP WebSocket: contentId (Netflix DIAL) / params.contentTarget (YouTube) |
| Samsung | WebSocket: `run_app(id, "DEEP_LINK", meta_tag)` |
| Android / Fire TV | ADB: `am start -d 'netflix://title/{id}'` |
| Roku | HTTP: `POST /launch/{ch}?contentId={id}` |

이런 내부 구현을 직접 다룰 필요는 없습니다. 드라이버가 알아서 처리합니다.

</details>

<details>
<summary><strong>플랫폼</strong> — 지원 TV 및 드라이버</summary>

| 플랫폼 | 드라이버 | 연결 방식 | 상태 |
|--------|---------|----------|------|
| LG webOS | [bscpylgtv](https://github.com/chros73/bscpylgtv) | WebSocket :3001 | **테스트 완료** |
| Samsung Tizen | [samsungtvws](https://github.com/xchwarze/samsung-tv-ws-api) | WebSocket :8002 | 커뮤니티 테스트 중 |
| Android / Fire TV | [adb-shell](https://github.com/JeffLIrion/adb-shell) | ADB TCP :5555 | 커뮤니티 테스트 중 |
| Roku | HTTP ECP | REST :8060 | 커뮤니티 테스트 중 |

LG가 주요 테스트 플랫폼입니다. 어떤 플랫폼도 개발자 모드가 필요 없습니다.

</details>

## 무설정 시작

```bash
stv setup
```

네트워크에서 TV를 자동으로 탐색하고, 플랫폼을 감지하고, 자동으로 페어링한 뒤, 모든 설정을 `~/.config/smartest-tv/config.toml`에 저장합니다. 뭔가 이상하다 싶으면 `stv doctor`가 정확히 무엇이 문제인지 알려줍니다.

```toml
[tv]
platform = "lg"
ip = "192.168.1.100"
mac = "AA:BB:CC:DD:EE:FF"   # 선택사항, Wake-on-LAN용
```

최초 연결 시 TV에 페어링 요청이 표시됩니다. 한 번 수락하면 키가 저장되고 다시는 묻지 않습니다.

## MCP 서버

Claude Desktop, Cursor 등 MCP 클라이언트용 — 선택 사항이며, CLI가 주 인터페이스입니다:

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

## 아키텍처

```
사용자 (자연어)
  → AI + stv resolve (HTTP 스크래핑 / yt-dlp / 캐시로 콘텐츠 ID 탐색)
    → stv play (딥링크 포맷 변환 및 전송)
      → 드라이버 (WebSocket / ADB / HTTP)
        → TV
```

<p align="center">
  <img src="../../docs/assets/mascot.png" alt="smartest-tv mascot" width="256">
</p>

## 기여하기

| 상태 | 영역 | 필요한 작업 |
|------|------|------------|
| **사용 가능** | LG webOS 드라이버 | 테스트 완료, 정상 작동 |
| **테스트 필요** | Samsung, Android TV, Roku 드라이버 | 실제 기기 사용 보고 환영 |
| **기여 환영** | Disney+ 스킬 | 딥링크 ID 해석 구현 |
| **기여 환영** | Hulu, Prime Video 스킬 | 딥링크 ID 해석 구현 |

[드라이버 인터페이스](src/smartest_tv/drivers/base.py)가 정의되어 있습니다 — 플랫폼에 맞게 `TVDriver`를 구현해서 PR을 열어주세요.

## 라이선스

MIT
