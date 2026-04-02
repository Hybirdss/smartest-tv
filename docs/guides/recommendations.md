# Recommendations and What's On

stv can fetch trending content and generate personalized recommendations based on your watch history.

## What's trending

```bash
stv whats-on             # Netflix Top 10 + YouTube Trending
stv whats-on netflix     # Netflix only
stv whats-on youtube     # YouTube only
stv whats-on netflix -n 5   # top 5
```

Via MCP:

```
tv_whats_on()                          → both platforms
tv_whats_on(platform="netflix")        → Netflix Top 10
tv_whats_on(platform="youtube", limit=5)
```

Returns formatted text:

```
Netflix Top 10:
   1. Squid Game  — TV Shows
   2. The Diplomat  — TV Shows
   ...

YouTube Trending:
   1. [MrBeast] I Spent 7 Days Buried Alive  — 12.4M views
   ...
```

## Personalized recommendations

Via MCP:

```
tv_recommend()                    → 5 recommendations based on history
tv_recommend(mood="chill")        → filter by mood
tv_recommend(mood="action", limit=10)
```

Supported moods: `chill`, `action`, `kids`, `random`

Example output:

```
Based on your recent watching (Frieren, The Witcher, Squid Game):

  1. Arcane                          Netflix   — Similar dark fantasy tone
  2. Baby Shark Dance                YouTube   — Quick kids content break
  3. Demon Slayer                    Netflix   — Matches your anime watching
```

The recommendation engine combines watch history patterns with trending data.
Set `STV_LLM_URL` to a local Ollama endpoint for AI-powered reason generation.

## Watch history

```bash
stv history          # last 10 plays
stv history -n 20    # last 20
```

Via MCP:

```
tv_history(limit=10) → list[dict]
```

Each entry:

```json
{
  "platform": "netflix",
  "query": "Frieren",
  "content_id": "82656797",
  "time": 1743700000,
  "season": 2,
  "episode": 8
}
```

`season` and `episode` are only present for Netflix TV shows.
