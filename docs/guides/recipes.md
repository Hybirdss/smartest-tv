# Recipes — Feature Combinations That Change How You Use TV

Individual features are useful. Combinations are where stv becomes something you can't live without.

Each recipe is copy-pastable. Try one tonight.

---

## 1. The Bedtime Autopilot

You say "good night" and your entire house shuts down gracefully.

```bash
# Step 1: Switch to ambient audio, screens off
stv audio play "rain sounds for sleeping" --rooms bedroom

# Step 2: Set a timer — TV turns off in 45 minutes
stv scene sleep

# Step 3: Kill every other TV in the house
stv --all off --tv bedroom   # spare the bedroom (sleep scene handles it)
```

**With Claude/OpenClaw:** Just say "good night" — the AI chains all three.

**Why this works:** `audio play` keeps sound but kills the screen light. `scene sleep` adds the auto-off timer. `--all off` catches any TV someone left on in the kitchen.

---

## 2. Kids Mode with Parental Intelligence

Kids get their content. You get the data.

```bash
# Morning: activate kids mode on the kids' TV
stv scene kids --tv kids-room

# Evening: how much did they watch today?
stv screen-time --period day

# Weekly check: are they binge-watching?
stv insights --period week
```

**The combo:** `scene kids` sets safe volume + age-appropriate content. `screen-time` tells you the exact minutes. `insights` catches binge patterns (3+ episodes of the same show in one day).

**With Claude:** "How much TV did the kids watch this week?" → Claude calls `tv_insights("week", "screen_time")` and gives you a plain English answer.

---

## 3. The House DJ

Friends are over. Everyone's a DJ. Music plays everywhere.

```bash
# Everyone adds their songs
stv queue add youtube "Gangnam Style"          # you
stv queue add spotify "Blinding Lights"        # friend 1
stv queue add youtube "Superstition Stevie"    # friend 2

# Play on every TV, screens off (just speakers)
stv audio play "queue" --rooms living-room,kitchen

# Someone in the kitchen wants it louder
stv audio volume kitchen 40

# Skip a bad pick
stv queue skip

# Party's over
stv audio stop
```

**Why this works:** `queue` turns stv into a jukebox. `audio play` kills the screens so you're not staring at YouTube UI. Per-room volume means the kitchen can be louder than the living room.

---

## 4. The Subscription Auditor

Are you paying for Netflix and barely using it?

```bash
# Monthly viewing report
stv insights --period month

# How much is Netflix actually costing you per hour?
stv sub-value netflix --cost 17.99

# Compare with YouTube Premium
stv sub-value youtube --cost 13.99

# What if you just watched trending stuff on free YouTube?
stv whats-on youtube
```

**Output example:**
```
Netflix: $8.50/hour
  2 plays · ~1.5h this month
  Verdict: consider_canceling

YouTube: $1.20/hour
  15 plays · ~3.8h this month
  Verdict: good_value
```

**With Claude:** "Should I cancel Netflix?" → Claude runs both sub-value analyses and gives you a recommendation based on your actual viewing data.

---

## 5. The Digital Signage (Free)

Turn any smart TV into an info display. Restaurants, offices, home dashboards.

```bash
# Option A: Info cards on the TV
stv display dashboard "Time:21:30" "Weather:18°C Cloudy" "WiFi:192.168.1.1" "Next:Team standup 9am"

# Option B: Full-screen clock (great for meeting rooms)
stv display clock

# Option C: Your Grafana dashboard on the living room TV
stv display url https://grafana.local/d/home-dashboard

# Option D: Persistent message (restaurant menu, welcome sign)
stv display message "Welcome to Seoul BBQ" --bg "#1a1a2e" --color "#e94560"
```

**On ALL TVs at once:**
```bash
# Same dashboard on every screen in the office
stv --all display dashboard "Status:All Systems Go" "Deploys:3 today" "Uptime:99.97%"
```

**Why this costs nothing:** Commercial digital signage is $20-50/month per screen. stv + any smart TV = free.

---

## 6. The Remote Movie Night

Friends across the city (or the world). Everyone watches the same thing at the same time.

```bash
# Setup: friends run stv on their machines
# Friend 1: stv serve --port 8910
# Friend 2: stv serve --port 8910

# You add them as remote TVs
stv multi add alex --platform remote --url http://alex-ip:8911
stv multi add jamie --platform remote --url http://jamie-ip:8911

# Create a watch party group
stv group create movie-night living-room alex jamie

# Notify everyone
stv --group movie-night notify "Wednesday S1E1 starting in 60 seconds!"

# Sync play — all TVs start at the same time
stv --group movie-night play netflix "Wednesday" s1e1

# Same volume everywhere
stv --group movie-night volume 25
```

**Why this is different from Netflix Party / Teleparty:** Those need browser extensions and break constantly. This is TV-native deep linking — the actual Netflix app opens on everyone's actual TV.

---

## 7. Morning Routine → Night Routine (The Full Day)

Script your TV for the entire day with cron.

```bash
# ~/.config/smartest-tv/crontab-examples.sh

# 7:00 AM — Morning news on bedroom TV
0 7 * * * stv play youtube "YTN 24시간 뉴스" --tv bedroom

# 7:30 AM — Dashboard with today's info
30 7 * * * stv display dashboard "날씨:18°C" "일정:팀미팅 10시" --tv living-room

# 8:00 AM — Kids wake up
0 8 * * * stv scene kids --tv kids-room

# 6:30 PM — Home from work, movie mood
30 18 * * * stv scene movie-night

# 9:00 PM — Kids TV off
0 21 * * * stv off --tv kids-room

# 11:00 PM — Everything off, sleep sounds in bedroom
0 23 * * * stv --all off && stv audio play "white noise" --rooms bedroom
```

**Why this matters:** Your TV schedule runs itself. No remote needed. No app needed. Just time-based automation that works even when you forget.

---

## 8. The AI Concierge (Claude + OpenClaw)

The most powerful mode. Natural language controls everything.

**Claude Code (MCP):**
```
You: "I just got home. What should I watch?"
Claude: [calls tv_scene("run", "movie-night")]
        [calls tv_recommend("chill")]
        "Movie night mode on. Based on your history, here are 5 picks:
         1. The Queen's Gambit (Netflix) — you liked Dark and Stranger Things
         2. ..."
You: "Play number 1"
Claude: [calls tv_play("netflix", "The Queen's Gambit")]
        "Playing The Queen's Gambit on Netflix."
```

**OpenClaw (Telegram):**
```
You (Telegram): "집에 왔어"
Bot: movie-night scene 실행 완료. 추천:
     1. 더 글로리 (Netflix)
     2. ...
     뭐 볼까요?
You: 1번
Bot: 더 글로리 재생 중.
```

**Complex multi-step (Claude):**
```
You: "Friends are coming at 9. Set up music in the kitchen and living room,
      and put a welcome message on the hallway TV."
Claude: [calls tv_audio("play", "friday night vibes", "spotify", rooms=["kitchen", "living-room"])]
        [calls tv_display("message", {"text": "Welcome! 🎉", ...}, tv_name="hallway")]
        "Music playing in kitchen and living room (screens off).
         Welcome message on hallway TV."
```

**The meta point:** stv has 21 MCP tools. AI agents can compose them freely. You describe what you want in natural language, and the AI figures out which tools to chain and in what order.

---

## 9. The Binge-Watch Autopilot

Start a show. stv remembers where you are. Forever.

```bash
# Start Breaking Bad
stv play netflix "Breaking Bad" s1e1

# ... days later ...
# "Where was I?"
stv next "Breaking Bad"
# → Playing Breaking Bad S1E2

# ... a week later ...
stv next
# → Playing Breaking Bad S1E5 (it just knows)

# Finished? Get a recommendation for what's next
stv recommend --mood action
# → Based on: Breaking Bad, Dark
#   1. Ozark (Netflix)
#   2. Narcos (Netflix)
#   ...
```

**With sync:** When you switch TVs, history follows.
```bash
# Started on living room, continue on bedroom
stv next "Breaking Bad" --tv bedroom
```

---

## 10. The Smart Cafe / Bar

Turn stv into a commercial music + display system for zero cost.

```bash
# Music on all speakers (no screen glare)
stv audio play "cafe jazz playlist" -p spotify

# Menu / promo on the main TV
stv display message "Today's Special: Iced Americano ₩3,500" --bg "#2d1b14" --color "#f5deb3"

# Different vibe for different times
# Morning: calm jazz
stv audio play "morning cafe jazz" -p spotify
# Evening: upbeat
stv audio play "friday night bar vibes" -p spotify

# Close up shop
stv --all off
```

**Compared to commercial solutions:** Soundtrack Your Brand is $35/month. Raydiant digital signage is $25/month per screen. stv is free, open source, and you own it.

---

## Combining with Shell Scripts

Any recipe above can be a one-liner or a script.

```bash
# ~/.local/bin/home-mode
#!/bin/bash
stv scene movie-night
stv recommend --mood chill --format json | head -1
echo "Movie night ready. Check recommendations above."

# ~/.local/bin/sleep-mode
#!/bin/bash
stv --all off
stv audio play "rain sounds" --rooms bedroom
echo "Good night."

# ~/.local/bin/party-mode
#!/bin/bash
stv audio play "$1" --rooms living-room,kitchen
stv display message "🎵 Now Playing" --bg "#000" --color "#0f0" --tv hallway
echo "Party started: $1"
```

```bash
# Usage
home-mode
sleep-mode
party-mode "lo-fi beats"
```

---

## Quick Reference: What Combines With What

| Want to... | Combine... |
|-----------|-----------|
| Music everywhere, no screens | `audio play` + per-room `audio volume` |
| Watch party with friends | `group create` + `sync play` + `notify` |
| Track kids' viewing | `scene kids` + `screen-time` + `insights` |
| Automate your day | cron + any stv command |
| AI handles everything | MCP tools + Claude/OpenClaw natural language |
| Free digital signage | `display dashboard/message/clock` + `--all` |
| Smart bedtime | `scene sleep` + `audio play` + `--all off` |
| Subscription audit | `sub-value` + `insights --period month` |
| TV follows you room to room | `next --tv bedroom` (history is shared) |
| Restaurant/cafe system | `audio play` + `display message` + cron |
