<h1 align="center">
  <br>
  📺
  <br>
  smartest-tv
  <br>
</h1>

<h4 align="center">당신의 TV가 기다려온 CLI.</h4>

<p align="center">
  <b>이름으로 넷플릭스 재생. URL 캐스트. 멀티룸 오디오. AI 컨시어지. 전부 터미널에서.</b>
</p>

<p align="center">
  <a href="https://pypi.org/project/stv/"><img src="https://img.shields.io/pypi/v/stv?style=flat-square&color=blue" alt="PyPI"></a>
  <a href="https://pypi.org/project/stv/"><img src="https://img.shields.io/pypi/dm/stv?style=flat-square&color=green" alt="Downloads"></a>
  <a href="../../tests/"><img src="https://img.shields.io/badge/tests-211%20passed-brightgreen?style=flat-square" alt="Tests"></a>
  <a href="../../LICENSE"><img src="https://img.shields.io/badge/license-MIT-yellow?style=flat-square" alt="MIT License"></a>
  <a href="https://python.org"><img src="https://img.shields.io/badge/python-3.11+-3776ab?style=flat-square&logo=python&logoColor=white" alt="Python"></a>
  <a href="https://modelcontextprotocol.io"><img src="https://img.shields.io/badge/MCP-21%20tools-8A2BE2?style=flat-square" alt="MCP Tools"></a>
</p>

<p align="center">
  <a href="../../README.md">English</a> · <b>한국어</b> · <a href="README.zh.md">中文</a> · <a href="README.ja.md">日本語</a> · <a href="README.es.md">Español</a> · <a href="README.de.md">Deutsch</a> · <a href="README.pt-br.md">Português</a> · <a href="README.fr.md">Français</a>
</p>

<br>

<p align="center"><code>pip install stv && stv setup</code></p>

<p align="center"><sub>로컬 네트워크에서 동작합니다. 클라우드 없음. API 키 없음. 구독 없음.</sub></p>

<br>

---

<br>

<table align="center">
<tr>
<th>😩 stv 없이</th>
<th>😎 stv 있으면</th>
</tr>
<tr>
<td>

1. 리모컨 집어들기
2. 넷플릭스 앱 열기
3. 작품 검색
4. 시즌 선택
5. 에피소드 선택
6. 재생 누르기

**~30초**

</td>
<td>

```bash
stv play netflix "Dark" s1e1
```

**~3초**

</td>
</tr>
</table>

<br>

---

## ✨ 무엇을 할 수 있나요

<table>
<tr>
<td width="33%" valign="top">

### 🎬 이름으로 재생
```bash
stv play netflix "Dark" s1e1
stv play youtube "baby shark"
stv play spotify "chill vibes"
```
이름만 말하면 됩니다. stv가 ID를 찾고, 앱을 열고, 재생을 시작합니다.

</td>
<td width="33%" valign="top">

### 🔗 URL 캐스트
```bash
stv cast https://youtu.be/dQw4w
stv cast https://netflix.com/watch/...
stv cast https://open.spotify.com/...
```
친구가 링크를 보냈다. 붙여넣기하면 TV에서 재생됩니다.

</td>
<td width="33%" valign="top">

### 🎵 대기열 & 파티
```bash
stv queue add youtube "Gangnam Style"
stv queue add spotify "Blinding Lights"
stv queue play
```
모두가 자기 곡을 추가합니다. TV가 순서대로 재생합니다.

</td>
</tr>
<tr>
<td width="33%" valign="top">

### 🎭 장면 프리셋
```bash
stv scene movie-night   # 볼륨 20, 시네마 모드
stv scene kids          # 볼륨 15, Cocomelon
stv scene sleep         # 환경음, 자동 꺼짐
```
명령 하나로 분위기가 완성됩니다.

</td>
<td width="33%" valign="top">

### 🔊 멀티룸 오디오
```bash
stv audio play "lo-fi beats"
stv audio volume kitchen 30
stv audio stop
```
화면 꺼짐. 음악은 모든 곳에서.<br>**무료 Sonos.**

</td>
<td width="33%" valign="top">

### 📺 TV를 디스플레이로
```bash
stv display message "저녁 먹어요!"
stv display clock
stv display dashboard "Temp:22°C"
```
대시보드, 시계, 안내판.<br>**월 0원.**

</td>
</tr>
<tr>
<td width="33%" valign="top">

### 📊 시청 분석
```bash
stv insights
stv screen-time
stv sub-value netflix --cost 17.99
```
넷플릭스가 월 18달러 값어치를 하고 있나요?

</td>
<td width="33%" valign="top">

### 🌐 동기화 파티
```bash
stv --all play youtube "lo-fi beats"
stv --group party play netflix "Wed..."
stv --all off   # 잘 자요
```
모든 TV. 동시에. 원격 친구도 함께.

</td>
<td width="33%" valign="top">

### 🤖 AI 컨시어지
```
"편안한 거 틀어줘"
→ tv_recommend → tv_play
→ Playing The Queen's Gambit
```
MCP 도구 21개. 문장 하나면 충분합니다.

</td>
</tr>
</table>

---

## 🤖 AI에게 TV를 맡기세요

stv는 **MCP 서버**입니다. Claude, GPT, Cursor 등 MCP 클라이언트라면 자연어로 TV를 제어할 수 있습니다.

<table>
<tr>
<td width="50%" valign="top">

**설정 (한 줄이면 됩니다):**

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

또는 [OpenClaw](../../docs/integrations/openclaw.md)로:
```bash
clawhub install smartest-tv
```

</td>
<td width="50%" valign="top">

**그냥 말하면 됩니다:**

```
You: "집에 왔어, 영화 볼 준비해줘"

Claude: 🎬 영화 모드 켜졌습니다.
  볼륨 → 20, 시네마 모드 켜짐.
  
  시청 기록 기반 추천:
  1. The Queen's Gambit (Netflix)
  2. Ozark (Netflix)
  3. Squid Game S2 (Netflix)

You: "1번 틀어줘, 주방 TV엔 시계 띄워줘"

Claude: ✓ The Queen's Gambit 재생 중
         ✓ 주방 TV에 시계 표시됨
```

</td>
</tr>
</table>

<details>
<summary><b>MCP 도구 21개 전체 목록</b></summary>
<br>

| 카테고리 | 도구 | 설명 |
|---------|------|------|
| **재생** | `tv_play` | 이름으로 검색 후 재생 |
| | `tv_cast` | URL 캐스트 |
| | `tv_next` | 이어서 보기 |
| | `tv_launch` | ID로 앱 실행 |
| | `tv_resolve` | 콘텐츠 ID만 조회 |
| **탐색** | `tv_whats_on` | 트렌딩 콘텐츠 |
| | `tv_recommend` | 개인화 추천 |
| **제어** | `tv_power` | 켜기/끄기 |
| | `tv_volume` | 볼륨 조회/설정/단계/음소거 |
| | `tv_screen` | 화면 켜기/끄기 |
| | `tv_notify` | 토스트 알림 |
| | `tv_status` | 현재 상태 |
| **정리** | `tv_queue` | 재생 대기열 |
| | `tv_scene` | 장면 프리셋 |
| | `tv_history` | 시청 기록 |
| **분석** | `tv_insights` | 시청 통계 |
| | `tv_display` | TV를 디스플레이로 |
| | `tv_audio` | 멀티룸 오디오 |
| **멀티 TV** | `tv_sync` | 모든 TV에서 재생 |
| | `tv_list_tvs` | TV 목록 |
| | `tv_groups` | TV 그룹 |

</details>

---

## 📅 stv와 함께하는 하루

| 시간 | 무슨 일이 일어나나 |
|------|-----------------|
| **오전 7시** | 주방 TV에 `stv display dashboard "Weather:18°C" "Meeting:10am"` |
| **오전 8시** | `stv scene kids --tv kids-room` — Cocomelon, 볼륨 15 |
| **낮 12시** | 친구가 넷플릭스 링크를 보냄 → `stv cast <url>` |
| **오후 5시** | `stv screen-time` → 오늘 아이가 2시간 15분 시청 |
| **오후 6시 30분** | `stv scene movie-night` — 볼륨 20, 시네마 모드 |
| **오후 7시** | `stv recommend --mood chill` → Ozark 추천 |
| **오후 9시** | `stv audio play "friday vibes" -p spotify` — 모든 곳에서 음악 |
| **오후 10시** | `stv --group party play netflix "Wednesday" s1e1` — 동기화 |
| **오후 11시 30분** | `stv scene sleep` → `stv --all off` — 잘 자요 |

---

## 🔥 킬러 조합

<table>
<tr>
<td width="33%" valign="top">

**🌙 취침 자동화**
```bash
stv audio play "rain" --rooms bedroom
stv scene sleep
stv --all off
```
환경음, 화면 꺼짐, 자동 타이머, 나머지 TV 전부 종료.

</td>
<td width="33%" valign="top">

**🎧 무료 Sonos**
```bash
stv audio play "lo-fi beats"
stv audio volume kitchen 40
stv audio volume bedroom 15
```
모든 TV가 스피커가 됩니다. 방마다 볼륨 조절. 화면은 꺼짐.

</td>
<td width="33%" valign="top">

**💰 구독 점검**
```bash
stv sub-value netflix --cost 17.99
# → $8.50/hr — 해지를 고려하세요

stv sub-value youtube --cost 13.99
# → $1.20/hr — 가성비 좋음
```

</td>
</tr>
</table>

> [**레시피 10개 더 보기 →**](../../docs/guides/recipes.md)

---

## ⚙️ 동작 원리

```
  "Play Dark S1E1"
        │
        ▼
  ┌─── 해석 ──────────┐
  │ 캐시 → API → 웹   │  content_id
  │  0.1s   1s   3s  │──────────────▶ 📺 TV 재생
  └───────────────────┘       │
                         딥링크 연결
                    LG / Samsung / Roku / Android
```

이름을 말하면 stv가 콘텐츠 ID를 찾아 TV 앱에 딥링크로 연결합니다. 브라우저 자동화 없음, API 키 없음, 클라우드 의존 없음. 결과는 캐시되어 반복 재생 시 즉시 실행됩니다.

---

## 📦 설치

```bash
pip install stv                    # LG webOS (기본)
pip install "stv[samsung]"         # Samsung Tizen
pip install "stv[android]"         # Android TV / Fire TV
pip install "stv[all]"             # 전부 다
```

```bash
stv setup                          # TV 자동 탐색 + 페어링
```

> **LG webOS** · **Samsung Tizen** · **Android TV / Fire TV** · **Roku** 지원

---

## 🔌 연동 지원

| 연동 | 방법 |
|-----|------|
| **Claude Code / Cursor** | MCP 설정 추가 → `"Dark s1e1 틀어줘"` |
| **OpenClaw** | `clawhub install smartest-tv` → 텔레그램 봇 |
| **Home Assistant** | 자동화에서 쉘 명령 사용 |
| **cron** | `0 7 * * * stv display dashboard ...` |
| **쉘 스크립트** | `sleep-mode`, `party-mode` 원라이너 |
| **모든 MCP 클라이언트** | 도구 21개, stdio 또는 HTTP (`stv serve`) |

---

## 📚 문서

| | |
|---|---|
| [시작하기](../../docs/getting-started/installation.md) | 모든 TV 브랜드 초기 설정 |
| [콘텐츠 재생](../../docs/guides/playing-content.md) | play, cast, queue, resolve |
| [Scene](../../docs/guides/scenes.md) | movie-night, kids, sleep, 커스텀 |
| [싱크 & 파티](../../docs/guides/sync-party.md) | 멀티 TV, 원격 워치 파티 |
| [레시피](../../docs/guides/recipes.md) | **강력한 기능 조합 10가지** |
| [AI 에이전트](../../docs/guides/ai-agents.md) | Claude, Cursor, OpenClaw MCP 설정 |
| [CLI 레퍼런스](../../docs/reference/cli.md) | 모든 명령어와 옵션 |
| [MCP 도구](../../docs/reference/mcp-tools.md) | 파라미터 포함 21개 도구 전체 |

---

## 🤝 기여하기

테스트 211개. TV 없이도 실행됩니다.

```bash
pip install -e ".[dev]"
python -m pytest tests/ -v
```

Samsung, Roku, Android TV 드라이버는 실제 기기 테스트가 필요합니다. 이런 TV를 갖고 있다면 [여러분의 피드백이 소중합니다](https://github.com/Hybirdss/smartest-tv/issues).

[캐시 기여하기](../../docs/contributing/cache-contributions.md) · [드라이버 개발](../../docs/contributing/driver-development.md)

---

<p align="center">
  <sub>MIT License · Python으로 제작 · 클라우드 불필요</sub>
</p>

<!-- mcp-name: io.github.Hybirdss/smartest-tv -->
