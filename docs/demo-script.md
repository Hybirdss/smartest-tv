# Demo GIF Recording Script

Terminal recording for README hero GIF. Shows the "talk to your TV" moment.

## Setup Before Recording

- Terminal: clean, dark theme, large font (16-18pt)
- Window size: 80x24 (standard)
- Tool: [vhs](https://github.com/charmbracelet/vhs) or asciinema + gifski
- TV must be on and paired (`stv setup` already done)
- Netflix app closed beforehand

## VHS Tape (automated recording)

```tape
# demo.tape — record with: vhs demo.tape
Output docs/demo.gif
Set FontSize 18
Set Width 960
Set Height 540
Set Theme "Catppuccin Mocha"
Set Padding 20

# Scene 1: Show we're talking to Claude
Type "claude"
Enter
Sleep 3s

# Scene 2: Natural language request
Type "Play Frieren season 2 episode 8 on Netflix"
Sleep 1s
Enter

# Scene 3: Claude works (skill resolves Netflix ID)
Sleep 6s

# Scene 4: TV responds
# At this point the terminal shows:
#   Closed Netflix.
#   Launched Netflix with content: 82656797
# And the TV is playing Frieren S2E8

Sleep 3s
```

## Manual Recording (if VHS not available)

### Frame-by-frame

| Time | Screen | What's happening |
|------|--------|-----------------|
| 0:00 | `$` cursor blinking | Clean terminal, ready |
| 0:01 | `$ claude` | User launches Claude Code |
| 0:03 | Claude prompt ready | Claude Code is running |
| 0:04 | User types: `Play Frieren season 2 episode 8 on Netflix` | Natural language, one line |
| 0:06 | Claude thinking... | Skill activates, searches Netflix |
| 0:09 | `Closed Netflix.` | Close-then-relaunch pattern |
| 0:10 | `Launched Netflix with content: 82656797` | Deep link sent to TV |
| 0:11 | Pause — let it breathe | **TV is now playing Frieren** |
| 0:14 | End | Total: ~14 seconds |

### Key moments to capture

1. **The input** — one natural English sentence, nothing technical
2. **The output** — clean, minimal, "it just worked"
3. **No config, no IDs, no flags** — user never sees `82656797`

## Recording Tips

- Type at human speed (not instant) — feels more real
- Don't show the Netflix ID lookup steps — the magic is that it's invisible
- If Claude shows tool calls, that's fine — it shows the AI working
- 14 seconds max — GIF should loop cleanly
- Crop to just the terminal — no desktop chrome

## Alternative: CLI-only demo (no Claude)

Simpler GIF showing raw CLI power:

```tape
# demo-cli.tape
Output docs/demo-cli.gif
Set FontSize 18
Set Width 800
Set Height 300
Set Theme "Catppuccin Mocha"

Type "stv launch netflix 82656797"
Sleep 0.5s
Enter
Sleep 2s
# Output: Launched Netflix with content: 82656797
Sleep 2s
```

But the Claude version is way more impressive for README.

## Where to put it

```markdown
# In README.md, after the tagline:

![demo](docs/demo.gif)
```
