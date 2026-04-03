# smartest-tv

[![PyPI](https://img.shields.io/pypi/v/stv)](https://pypi.org/project/stv/)
[![Downloads](https://img.shields.io/pypi/dm/stv)](https://pypi.org/project/stv/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://python.org)
[![Tests](https://img.shields.io/badge/tests-169%20passed-brightgreen)](tests/)

[English](../../README.md) | **한국어** | [中文](README.zh.md) | [日本語](README.ja.md) | [Español](README.es.md) | [Deutsch](README.de.md) | [Português](README.pt-br.md) | [Français](README.fr.md)

**TV에 말하세요. 알아듣습니다.**

| stv 없이 | stv 있으면 |
|:--------:|:---------:|
| 폰에서 넷플릭스 앱 열기 | `stv play netflix "Dark" s1e1` |
| 작품 검색 | (자동 처리) |
| 시즌 선택 | (자동 계산) |
| 에피소드 선택 | (딥링크 연결) |
| 재생 탭 | |
| **~30초** | **~3초** |

<p align="center">
  <a href="https://github.com/Hybirdss/smartest-tv/releases/download/v0.3.0/KakaoTalk_20260403_051617935.mp4">
    <img src="../../docs/assets/demo.gif" alt="smartest-tv demo" width="720">
  </a>
</p>

*소리와 함께 전체 영상 보기*

## 빠른 시작

```bash
pip install stv
stv setup          # TV 자동 탐색, 페어링, 완료
```

## 사람들이 stv로 하는 것들

### "이 링크를 TV로 캐스트해줘"

친구가 유튜브 링크를 보냈다. 붙여넣기 한다. TV에서 재생된다.

```bash
stv cast https://youtube.com/watch?v=dQw4w9WgXcQ
stv cast https://netflix.com/watch/81726716
stv cast https://open.spotify.com/track/3bbjDFVu9BtFtGD2fZpVfz
```

### "파티용 노래 대기열 만들어줘"

모두가 자기 곡을 추가한다. TV가 순서대로 재생한다.

```bash
stv queue add youtube "Gangnam Style"
stv queue add youtube "Despacito"
stv queue add spotify "playlist:Friday Night Vibes"
stv queue play                     # 순서대로 재생 시작
stv queue skip                     # 다음 곡
```

### "뭐 볼지 모르겠어"

30분 동안 넷플릭스 스크롤하지 말고. 트렌딩을 물어봐라. 추천을 받아라.

```bash
stv whats-on netflix               # 지금 인기 상위 10개
stv recommend --mood chill         # 시청 기록 기반 추천
stv recommend --mood action        # 다른 분위기, 다른 추천
```

### "영화 볼 분위기"

명령 하나로 분위기 세팅: 볼륨, 알림, 콘텐츠.

```bash
stv scene movie-night              # 볼륨 20, 시네마 모드
stv scene kids                     # 볼륨 15, Cocomelon 재생
stv scene sleep                    # 환경음, 자동 꺼짐
stv scene create date-night        # 나만의 scene 만들기
```

### "모든 곳에서 동시 재생"

CLI 하나로 집 안 모든 TV를 제어한다. 동시 재생도 된다.

```bash
stv multi list                     # living-room (LG), bedroom (Samsung), friend (remote)
stv play netflix "The Crown" --tv bedroom
stv --all play youtube "lo-fi beats"    # 집 안 모든 TV에서 동시 재생
stv --group party play netflix "Wednesday" s1e1  # 싱크 파티 모드
stv --all off                      # 모든 TV 꺼짐
```

### "끊긴 데서 이어서 봐야지"

```bash
stv next                           # 마지막 에피소드부터 이어서
stv next "Breaking Bad"            # 특정 작품 이어서
stv history                        # 뭘 봤는지 기록 확인
```

## stv와 함께하는 하루

**오전 7시** -- 알람 울린다. "뭐가 트렌딩이지?" `stv whats-on youtube`로 아침 뉴스 확인. TV가 재생된다.

**오전 8시** -- 아이들이 일어난다. `stv scene kids` -- 볼륨 15, Cocomelon 시작.

**낮 12시** -- 친구가 넷플릭스 링크를 보낸다. `stv cast https://netflix.com/watch/...` -- TV에서 바로 재생.

**오후 6시 30분** -- 퇴근. `stv scene movie-night` -- 볼륨 낮추고, 시네마 모드.

**오후 7시** -- "뭐 볼까?" `stv recommend --mood chill` -- The Queen's Gambit 추천.

**오후 9시** -- 친구들이 온다. `stv --group party play netflix "Wednesday" s1e1`으로 거실과 침실 TV 동기화. 다들 `stv queue add ...` 실행 -- TV가 순서대로 재생.

**오후 11시 30분** -- "잘 자." `stv scene sleep` -- 환경음, 45분 후 TV 꺼짐.

<details>
<summary><b>stv는 어떻게 HTTP 요청 한 번으로 넷플릭스 에피소드를 찾는가?</b></summary>

Netflix 서버는 `<script>` 태그 안에 `__typename:"Episode"` 메타데이터를 서버 렌더링합니다. 시즌 내 에피소드 ID는 연속된 정수입니다. 타이틀 페이지에 `curl` 요청 한 번으로 모든 시즌의 에피소드 ID를 추출할 수 있습니다. Playwright도, 헤드리스 브라우저도, API 키도, 로그인도 필요 없습니다.

결과는 세 단계로 캐시됩니다:
1. **로컬 캐시** -- `~/.config/smartest-tv/cache.json`, 즉시 반환 (~0.1초)
2. **커뮤니티 캐시** -- GitHub raw CDN을 통한 크라우드소싱 ID (40개 이상 사전 등록), 서버 비용 없음
3. **웹 검색 폴백** -- Brave Search로 알 수 없는 타이틀 ID를 자동 발견

</details>

<details>
<summary><b>딥링크 -- stv가 TV와 통신하는 방식</b></summary>

각 드라이버가 콘텐츠 ID를 플랫폼 고유 형식으로 변환합니다:

| TV | 프로토콜 | 딥링크 형식 |
|----|----------|------------|
| LG webOS | SSAP WebSocket (:3001) | `contentId` via DIAL / `params.contentTarget` |
| Samsung Tizen | WebSocket (:8001) | `run_app(id, "DEEP_LINK", meta_tag)` |
| Android / Fire TV | ADB TCP (:5555) | `am start -d 'netflix://title/{id}'` |
| Roku | HTTP ECP (:8060) | `POST /launch/{ch}?contentId={id}` |

이 모든 것을 직접 신경 쓸 필요가 없습니다. 드라이버가 알아서 처리합니다.

</details>

<details>
<summary><b>지원 플랫폼</b></summary>

| 플랫폼 | 드라이버 | 상태 |
|--------|---------|------|
| LG webOS | [bscpylgtv](https://github.com/chros73/bscpylgtv) | **테스트 완료** |
| Samsung Tizen | [samsungtvws](https://github.com/xchwarze/samsung-tv-ws-api) | 커뮤니티 테스트 중 |
| Android / Fire TV | [adb-shell](https://github.com/JeffLIrion/adb-shell) | 커뮤니티 테스트 중 |
| Roku | HTTP ECP | 커뮤니티 테스트 중 |

</details>

## 설치

```bash
pip install stv                 # LG (기본)
pip install "stv[samsung]"      # Samsung Tizen
pip install "stv[android]"      # Android TV / Fire TV
pip install "stv[all]"          # 전부 다
```

## 모든 것과 연동

| 연동 | 어떻게 동작하나 |
|------|--------------|
| **Claude Code** | "Breaking Bad s1e1 틀어줘" -- TV에서 바로 재생 |
| **OpenClaw** | 텔레그램: "집에 왔어" -- scene + 추천 + 재생 |
| **Home Assistant** | 문 열림 -- TV 켜짐 -- 트렌딩 목록 표시 |
| **Cursor / Codex** | AI가 코드 짜는 동안 쉬면서 TV 제어 |
| **cron / 스크립트** | 오전 7시: 침실 TV에 뉴스. 오후 9시: 아이 TV 꺼짐 |
| **모든 MCP 클라이언트** | stdio 또는 HTTP로 18개 도구 사용 |

### MCP 서버

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

원격 접근을 위한 HTTP 서버로 실행:

```bash
stv serve --port 8910              # http://localhost:8910/sse 로 SSE
stv serve --transport streamable-http
```

### OpenClaw

```bash
clawhub install smartest-tv
```

## 문서

| | |
|---|---|
| [시작하기](../../docs/getting-started/installation.md) | 모든 TV 브랜드 최초 설정 |
| [콘텐츠 재생](../../docs/guides/playing-content.md) | play, cast, search, queue, resolve |
| [Scene](../../docs/guides/scenes.md) | 프리셋: movie-night, kids, sleep, 커스텀 |
| [멀티 TV](../../docs/guides/multi-tv.md) | `--tv` 옵션으로 여러 TV 제어 |
| [싱크 & 파티](../../docs/guides/sync-party.md) | 모든 TV 동시 재생, 원격 워치 파티 |
| [AI 에이전트](../../docs/guides/ai-agents.md) | Claude, Cursor, OpenClaw MCP 설정 |
| [추천](../../docs/guides/recommendations.md) | AI 기반 콘텐츠 추천 |
| [CLI 레퍼런스](../../docs/reference/cli.md) | 모든 명령어와 옵션 |
| [MCP 도구](../../docs/reference/mcp-tools.md) | 파라미터 포함 MCP 도구 18개 전체 |
| [OpenClaw](../../docs/integrations/openclaw.md) | ClawHub 스킬 + 텔레그램 시나리오 |

## 기여

Samsung, Roku, Android TV 드라이버는 실제 기기 테스트가 필요합니다. 이런 TV를 갖고 있다면 피드백이 정말 소중합니다.

```bash
pip install -e ".[dev]"
python -m pytest tests/ -v         # 169개 테스트, TV 불필요
```

좋아하는 작품을 커뮤니티 캐시에 추가하고 싶다면? [캐시 기여하기](../../docs/contributing/cache-contributions.md)를 참고하세요.

새 TV 드라이버를 작성하고 싶다면? [드라이버 개발](../../docs/contributing/driver-development.md)을 참고하세요.

## 라이선스

MIT

<!-- mcp-name: io.github.Hybirdss/smartest-tv -->
