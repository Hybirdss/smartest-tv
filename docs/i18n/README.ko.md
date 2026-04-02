# smartest-tv

[English](../../README.md) | **한국어** | [中文](README.zh.md) | [日本語](README.ja.md) | [Español](README.es.md) | [Deutsch](README.de.md) | [Português](README.pt-br.md) | [Français](README.fr.md)

TV에 말하세요. 알아듣습니다.

스마트 TV를 자연어로 제어하는 CLI와 AI 에이전트 스킬. Netflix, YouTube, Spotify 딥링크 — 보고 싶은 걸 말하면 재생됩니다.

> "프리렌 2기 8화 틀어줘"
>
> *넷플릭스가 열리고 해당 에피소드가 재생됩니다.*

**LG**, **Samsung**, **Android TV**, **Fire TV**, **Roku** 지원.

## 설치

```bash
pip install "smartest-tv[lg]"      # LG webOS
pip install "smartest-tv[samsung]" # Samsung Tizen
pip install "smartest-tv[android]" # Android TV / Fire TV
pip install "smartest-tv[all]"     # 전체
```

## CLI

```bash
export TV_IP=192.168.1.100

tv status                          # 현재 상태 (앱, 볼륨, 음소거)
tv launch netflix 82656797         # 넷플릭스 특정 콘텐츠 재생
tv launch youtube dQw4w9WgXcQ     # 유튜브 영상 재생
tv launch spotify spotify:album:x # 스포티파이 재생
tv volume 25                       # 볼륨 설정
tv mute                            # 음소거 토글
tv apps --format json              # 설치된 앱 목록
tv notify "밥 먹어~"                # TV 화면에 알림
tv off                             # TV 끄기
```

모든 명령에 `--format json` 사용 가능 — AI 에이전트를 위한 구조화 출력.

## AI 에이전트 스킬

Claude Code에 스킬 설치:

```bash
cd smartest-tv && ./install-skills.sh
```

그 다음, Claude에게 자연어로 말하세요:

```
나: 프리렌 2기 8화 넷플릭스에서 틀어줘
나: 아이한테 유튜브 틀어줘
나: Ye 새 앨범 스포티파이로 틀어
나: 화면 끄고 재즈 틀어
나: 잘 자
```

스킬이 어려운 부분을 처리합니다 — 넷플릭스 에피소드 ID 찾기, yt-dlp로 유튜브 검색, 스포티파이 URI 해석 — 그리고 `tv` CLI를 호출하여 TV를 제어합니다.

## 딥링크

smartest-tv의 핵심 차별점입니다. 다른 도구는 넷플릭스를 *열기만* 합니다. 우리는 *프리렌 36화를 재생*합니다.

같은 콘텐츠 ID가 모든 TV 플랫폼에서 작동합니다:

```bash
tv launch netflix 82656797       # LG든 Samsung이든 Roku든 동일
tv launch youtube dQw4w9WgXcQ    # 동일
tv launch spotify spotify:album:x  # 동일
```

## 실제 사용 사례

**새벽 2시.** 침대에서 Claude에게 말합니다: "프리렌 이어서 틀어줘." 거실 TV가 켜지고, 넷플릭스가 열리고, 에피소드가 시작됩니다. 리모컨을 찾을 필요 없습니다.

**토요일 아침.** "아기한테 코코멜론 틀어줘." 유튜브에서 찾아 TV에서 재생됩니다. 아침 준비를 계속하세요.

**친구들이 왔을 때.** "게임 모드, HDMI 2, 볼륨 줄여." 한 문장으로 세 가지 변경.

## 라이선스

MIT
