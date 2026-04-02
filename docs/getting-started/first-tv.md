# Your First TV Session

You've run `stv setup` and `stv status` shows your TV. Here's how to use stv from day one.

## Play something

```bash
stv play netflix "Frieren" s2e8
stv play youtube "baby shark"
stv play spotify "Ye White Lines"
```

stv resolves the content ID automatically (from cache or the web) and deep-links directly to the episode, video, or track.

## Basic controls

```bash
stv volume 25          # set volume
stv mute               # toggle mute
stv pause              # pause playback
stv play               # resume playback
stv off                # standby
```

## Continue where you left off

```bash
stv next               # next episode of most recently watched Netflix show
stv next "Frieren"     # next episode of a specific show
stv history            # see what you've watched
```

## Search without playing

```bash
stv search netflix "Money Heist"     # title ID + all seasons + episode counts
stv search youtube "lofi hip hop"    # top 3 results
stv resolve netflix "The Witcher" s2e5   # just the episode ID
```

## Send a notification

```bash
stv notify "Dinner's ready"
```

Sends a toast notification that appears on the TV screen.

## Cast a URL

If you have a streaming link, cast it directly:

```bash
stv cast https://www.netflix.com/watch/82656797
stv cast https://www.youtube.com/watch?v=dQw4w9WgXcQ
stv cast https://open.spotify.com/track/3bbjDFVu9BtFtGD2fZpVfz
```

## Check TV info

```bash
stv status     # current app, volume, mute state
stv info       # model, firmware, IP, platform
stv doctor     # connectivity and app availability check
```

## Next steps

- [Playing Content](../guides/playing-content.md) — full guide to play, cast, search, and queue
- [CLI Reference](../reference/cli.md) — every command with all options
- [AI Agents](../guides/ai-agents.md) — connect Claude, Cursor, or any MCP client
