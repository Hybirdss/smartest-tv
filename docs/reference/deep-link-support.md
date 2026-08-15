# Deep-link support by platform and app

> Status: **best effort, hardware-dependent.** Deep linking into a specific
> title inside a streaming app is not a documented Samsung API — each app
> interprets (or ignores) launch parameters independently. This page tracks
> what we know and what stv does about it. See
> [issue #8](https://github.com/Hybirdss/smartest-tv/issues/8) for the
> ongoing confirmation work.

## How stv launches content on Samsung Tizen

1. **DIAL first (Netflix, YouTube)** — `launch_app_deep()` POSTs a DIAL
   launch body to the TV's `Application-URL`. The launch parameters are
   interpreted by the *app*, not the OS, which sidesteps Tizen-side
   `metaTag` handling entirely.
2. **`ed.apps.launch` with `action_type: DEEP_LINK` fallback** — the
   WebSocket payload SamsungTVWS-style remotes send
   (`ChannelEmitCommand.launch_app(app_id, "DEEP_LINK", meta_tag)`).
   If DIAL is unavailable (TV doesn't answer M-SEARCH, app has no DIAL
   receiver) this still *launches the app*; whether it also navigates to
   the title depends on the app and firmware.

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
the app** — you just pick the title manually on the app's home screen.
The driver logs which path it took; if you see launches without
navigation on your hardware, add a 👍/data point to issue #8.

## SmartThings fallback (not implemented)

For apps whose deep links are restricted (Netflix et al.), Samsung's
SmartThings API can pass a *search string* to YouTube — confirmed working
by the #6 reporter. Implementing a SmartThings route would need a
SmartThings API key and device registration; tracked in issue #8.

## References

- [Samsung Smart Hub Preview (official deep-link surface)](https://developer.samsung.com/smarttv/develop/guides/smart-hub-preview/implementing-public-preview.html)
- [Samsung Dev Forum: How to deeplink to Tizen TV apps](https://forum.developer.samsung.com/t/how-deeplink-to-tizen-tv-apps/18518)
- [xchwarze/samsung-tv-ws-api APPLICATIONS.md](https://github.com/xchwarze/samsung-tv-ws-api/blob/master/APPLICATIONS.md)
