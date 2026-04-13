---
name: stv-concierge
description: >
  Natural-language TV control via the stv CLI. Use for any request about
  playing, pausing, resuming, or stopping content on a smart TV; controlling
  volume or mute; switching to Netflix, YouTube, Spotify, Disney+, Apple TV+,
  or Prime Video; binge-watching a series; casting a URL to the TV; or anything
  the user says like "거실 TV 켜줘", "뭐 보여줘", "TV 꺼", "볼륨 낮춰",
  "몰아보기", "다음 화", "좋은 밤", "영화 볼게", "노래 틀어줘",
  "play / pause / volume / resume / Netflix / YouTube / Spotify".
---

# stv-concierge

Dispatch natural-language TV requests to `stv` without writing prose.
Always run the CLI command directly. Never describe what you would do — just do it.

## When to use

- "play Dark on Netflix" / "넷플릭스에서 다크 틀어줘"
- "pause" / "일시정지"
- "resume" / "다시 틀어줘"
- "volume down" / "볼륨 낮춰" / "좀 작게"
- "volume up" / "볼륨 높여" / "좀 크게"
- "mute" / "음소거"
- "turn the TV off" / "TV 꺼" / "거실 TV 꺼줘"
- "good night" / "잘 자"
- "next episode" / "다음 화" / "이어서 봐"
- "what's on?" / "뭐 보여줘" / "뭐 볼 만한 거 있어?"
- "binge watch Squid Game" / "오징어 게임 몰아보기"
- "put on some music" / "노래 틀어줘"
- "play lo-fi on YouTube" / "유튜브에서 로파이 틀어줘"
- "movie night" / "영화 모드"
- "cast this URL"

## How to use

Map the user's intent to a single `stv` command and run it immediately.

| User says | Command |
|-----------|---------|
| "play Dark on Netflix" | `stv play netflix "Dark"` |
| "play Dark s1e3" | `stv play netflix "Dark" s1e3` |
| "pause" | `stv pause` |
| "resume" / "다시 틀어줘" | `stv resume` |
| "volume down" / "볼륨 낮춰" | `stv volume down` |
| "mute" / "음소거" | `stv mute` |
| "TV 꺼" / "good night" / "잘 자" | `stv off` |
| "next episode" / "다음 화" | `stv next` |
| "뭐 보여줘" / "what's trending?" | `stv whats-on` |
| "오징어 게임 몰아보기" | `stv play netflix "Squid Game"` |
| "movie night" / "영화 모드" | `stv scene movie-night` |
| "cast https://youtu.be/..." | `stv cast <url>` |
| "play Frieren" (platform unknown) | `stv play "Frieren"` |

No TV configured? `stv` opens content in your browser automatically — no setup needed.

## Install check

If `stv` is not on PATH, run `pip install stv` once and retry the command.
