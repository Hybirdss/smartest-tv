# Deep-link support by platform and app

> Status: **best effort, hardware-dependent.** Deep linking into a specific
> title inside a streaming app is not a documented Samsung API — each app
> interprets (or ignores) launch parameters independently. This page tracks
> what we know and what stv does about it. See
> [issue #8](https://github.com/Hybirdss/smartest-tv/issues/8) for the
> ongoing confirmation work.

## How stv launches content on Samsung Tizen

`launch_app_deep()` walks a best-first ladder and **returns a
`LaunchResult`** saying what the TV actually did — the CLI prints it, the
Home Assistant integration logs it (and fails the `play_media` service
call when nothing started; see
[issue #20](https://github.com/Hybirdss/smartest-tv/issues/20)).

1. **DIAL (Netflix, YouTube)** — POSTs a DIAL launch body to the TV's
   `Application-URL`. The launch parameters are interpreted by the
   *app*, not the OS, which sidesteps Tizen-side `metaTag` handling
   entirely. → `LaunchResult.DIAL`
2. **`ed.apps.launch` with `action_type: DEEP_LINK`, then verify** — the
   WebSocket payload SamsungTVWS-style remotes send
   (`ChannelEmitCommand.launch_app(app_id, "DEEP_LINK", meta_tag)`).
   The send is fire-and-forget on the wire, so the driver now polls the
   REST app-status endpoint (`applications/{id}`) instead of trusting
   it. → `DEEP_LINK` (app running) or `DEEP_LINK_UNVERIFIED` (model
   exposes no usable status endpoint — we say so instead of guessing).
3. **Escalation when the app provably did not start** — the Tizen 9
   "silently ignored" behavior: REST `applications/{id}` POST (the path
   #20's TV honors when DEEP_LINK does nothing), then plain
   `NATIVE_LAUNCH`. → `APP_ONLY` (app up, pick the title manually) or
   `NATIVE`, and `FAILED` when every rung was refused.

## Observed behavior matrix (anecdotal, needs confirmation)

Confirmation reports welcome — please open an issue with TV model,
firmware (Tizen version), and app.

| App | DIAL route | `DEEP_LINK` metaTag | Notes |
|---|---|---|---|
| Netflix | ✅ `Netflix` DIAL body | Tizen ≤8: honored · **Tizen 9: reported ignored** | App always launches; title navigation varies |
| YouTube | ✅ search-string via DIAL | historically honored | SmartThings search pass-through reported working (textninja, #6) |
| Disney+ | ❌ no DIAL receiver | **Tizen 9: reported ignored** | App launches; no auto-navigate |
| Spotify | ❌ | `spotify:{type}:{id}` reported working | |
| Prime Video | ❌ | mixed reports | |

## What this means for `stv play`

If the TV ignores `metaTag`, `stv play netflix "Title"` still **launches
the app** through the escalation ladder — you just pick the title
manually on the app's home screen — and the CLI/HA log now *says so*
(`APP_ONLY`, referencing issue #8) instead of reporting success. If you
see launches without navigation on your hardware, add a 👍/data point to
issue #8.

| Outcome | Meaning | Where you see it |
|---|---|---|
| `DIAL` | Launched through the app's DIAL receiver | info line |
| `DEEP_LINK` | WS deep link, app verified running | info line |
| `DEEP_LINK_UNVERIFIED` | Sent, but this model can't be queried | warning |
| `APP_ONLY` | App running, title not deep-linked | warning (issue #8) |
| `NATIVE` | Fell back to a plain app launch | warning |
| `FAILED` | TV refused every path | error; HA action fails |

`#20`'s UE55CU8000 report: HA `play_media` completed "successfully" while
the TV stayed on HDMI — pre-fix, none of the paths were verified or
reported. If you hit that today, the action now fails loudly with the
ladder outcome in the log.

## SmartThings fallback (not implemented)

For apps whose deep links are restricted (Netflix et al.), Samsung's
SmartThings API can pass a *search string* to YouTube — confirmed working
by the #6 reporter. Implementing a SmartThings route would need a
SmartThings API key and device registration; tracked in issue #8.

## References

- [Samsung Smart Hub Preview (official deep-link surface)](https://developer.samsung.com/smarttv/develop/guides/smart-hub-preview/implementing-public-preview.html)
- [Samsung Dev Forum: How to deeplink to Tizen TV apps](https://forum.developer.samsung.com/t/how-deeplink-to-tizen-tv-apps/18518)
- [xchwarze/samsung-tv-ws-api APPLICATIONS.md](https://github.com/xchwarze/samsung-tv-ws-api/blob/master/APPLICATIONS.md)
