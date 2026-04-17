"""TV as Display — serve HTML content on the TV screen.

Turns the TV into a living-room display for dashboards, clocks, messages,
photo slideshows, and more. Works by:

  1. Generating self-contained HTML for a given content type
  2. Serving it on a local HTTP server (non-blocking background thread)
  3. Returning a LAN URL that ``stv cast <url>`` can open on the TV

Example::

    from smartest_tv.display import generate_html, serve

    html = generate_html("clock", {"format": "24h"})
    url, stop = serve(html, port=8765)
    # stv cast <url>  → TV now shows a full-screen clock
    # stop()          → shut down the server when done

All HTML is self-contained (inline CSS/JS only, no CDN) so it works on any
TV's built-in browser without internet access.
"""

from __future__ import annotations

import html as _html
import re
import socket
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Callable
from urllib.parse import urlparse

# ---------------------------------------------------------------------------
# Input sanitisation — these fields are attacker-controllable via MCP
# ---------------------------------------------------------------------------

_CSS_COLOR_RE = re.compile(r"^[#a-zA-Z0-9(),.\s%-]{1,32}$")
_SAFE_IFRAME_SCHEMES = {"http", "https"}


def _safe_color(raw: str, default: str) -> str:
    """Validate a caller-supplied CSS colour value.

    We only need to block the `value;}` style-attribute break-out — a
    strict character allow-list catches that without having to enumerate
    every legal CSS colour form.
    """
    if isinstance(raw, str) and _CSS_COLOR_RE.match(raw):
        return raw
    return default


def _safe_iframe_url(raw: str) -> str:
    """Gate iframe URLs to http/https only.

    `file://`, `javascript:`, `data:`, and schemeless inputs that
    `urlparse` may misread all fall through to `about:blank`. This
    prevents an MCP agent from pointing the TV browser at internal
    admin panels (`http://router.local/admin`) or local files.
    """
    if not isinstance(raw, str):
        return "about:blank"
    parsed = urlparse(raw)
    if parsed.scheme.lower() not in _SAFE_IFRAME_SCHEMES or not parsed.netloc:
        return "about:blank"
    # Re-quote the URL for attribute context — urlparse accepts
    # anything before reassembly, so belt-and-braces escape here.
    return _html.escape(raw, quote=True)


def _safe_css_url(raw: str) -> str:
    """Return a CSS ``url(...)`` operand that cannot break out of its
    string literal.

    ``background-image: url('{raw}')`` is a stored-XSS vector if ``raw``
    contains ``')`` followed by ``</style><script>``. Restrict to the
    same http/https scheme gate as iframes and additionally strip any
    quote or paren characters that would break the CSS string.
    """
    if not isinstance(raw, str):
        return ""
    parsed = urlparse(raw)
    if parsed.scheme.lower() not in _SAFE_IFRAME_SCHEMES or not parsed.netloc:
        return ""
    if any(c in raw for c in "'\"()<>\\\r\n"):
        return ""
    return raw

# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _get_local_ip() -> str:
    """Return the machine's LAN IP (not 127.0.0.1).

    Uses the UDP socket trick: connect to a routable address and read the
    local side of the socket — no packets are actually sent.
    Falls back to ``127.0.0.1`` on any error.
    """
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


# ---------------------------------------------------------------------------
# HTML generation
# ---------------------------------------------------------------------------

_BASE_HTML = """\
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{title}</title>
  <style>
    *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
    html, body {{
      width: 100%; height: 100%;
      overflow: hidden;
      background: {bg};
      font-family: 'Helvetica Neue', Arial, sans-serif;
      -webkit-font-smoothing: antialiased;
    }}
    {extra_css}
  </style>
</head>
<body>
{body}
{script}
</body>
</html>"""


def generate_html(content_type: str, data: dict | None = None) -> str:  # noqa: C901
    """Generate a self-contained HTML page for the given content type.

    Parameters
    ----------
    content_type:
        One of ``"message"``, ``"clock"``, ``"dashboard"``, ``"photo"``,
        ``"iframe"``, ``"custom"``.
    data:
        Configuration dict whose keys depend on *content_type*. See module
        docstring for per-type details. ``None`` falls back to all defaults.

    Returns
    -------
    str
        A complete, self-contained HTML document (no external dependencies).
    """
    data = data or {}

    # ------------------------------------------------------------------
    # message — large centered text, ideal for notifications
    # ------------------------------------------------------------------
    if content_type == "message":
        text = _html.escape(str(data.get("text", "")))
        bg = _safe_color(data.get("bg", ""), "#111111")
        color = _safe_color(data.get("color", ""), "#ffffff")

        extra_css = ""
        body = f"""\
<div style="
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100vw;
  height: 100vh;
  padding: 4vw;
">
  <p style="
    color: {color};
    font-size: 8vw;
    font-weight: 700;
    line-height: 1.2;
    text-align: center;
    letter-spacing: -0.02em;
    word-break: break-word;
    text-shadow: 0 2px 24px rgba(0,0,0,0.6);
  ">{text}</p>
</div>"""
        script = ""

        return _BASE_HTML.format(
            title="Message",
            bg=bg,
            extra_css=extra_css,
            body=body,
            script=script,
        )

    # ------------------------------------------------------------------
    # clock — full-screen digital clock with date, auto-updates every second
    # ------------------------------------------------------------------
    elif content_type == "clock":
        fmt = data.get("format", "24h")
        hour12 = "true" if fmt == "12h" else "false"

        extra_css = ""
        body = """\
<div style="
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  width: 100vw;
  height: 100vh;
  gap: 2vw;
">
  <div id="clock" style="
    color: #ffffff;
    font-size: 20vw;
    font-weight: 200;
    letter-spacing: -0.03em;
    line-height: 1;
    font-variant-numeric: tabular-nums;
    text-shadow: 0 0 80px rgba(255,255,255,0.15);
  ">00:00:00</div>
  <div id="date" style="
    color: #888888;
    font-size: 3.5vw;
    font-weight: 300;
    letter-spacing: 0.15em;
    text-transform: uppercase;
  "></div>
</div>"""
        script = f"""\
<script>
  var hour12 = {hour12};
  function pad(n) {{ return String(n).padStart(2, '0'); }}
  function tick() {{
    var now = new Date();
    var h = now.getHours();
    var m = now.getMinutes();
    var s = now.getSeconds();
    var suffix = '';
    if (hour12) {{
      suffix = h >= 12 ? ' PM' : ' AM';
      h = h % 12 || 12;
    }}
    document.getElementById('clock').textContent =
      pad(h) + ':' + pad(m) + ':' + pad(s) + suffix;
    document.getElementById('date').textContent =
      now.toLocaleDateString(undefined, {{
        weekday: 'long', year: 'numeric',
        month: 'long', day: 'numeric'
      }});
  }}
  tick();
  setInterval(tick, 1000);
</script>"""

        return _BASE_HTML.format(
            title="Clock",
            bg="#111111",
            extra_css=extra_css,
            body=body,
            script=script,
        )

    # ------------------------------------------------------------------
    # dashboard — info cards grid, readable from sofa distance
    # ------------------------------------------------------------------
    elif content_type == "dashboard":
        # Every caller-supplied string is attacker-controllable via MCP;
        # HTML-escape each field for its destination context.
        raw_title = str(data.get("title", "Dashboard"))
        title_html = _html.escape(raw_title)
        cards: list[dict] = data.get("cards", [])

        cards_html = ""
        for card in cards:
            label = _html.escape(str(card.get("label", "")))
            value = _html.escape(str(card.get("value", "")))
            cards_html += f"""\
<div style="
  background: #1e1e1e;
  border: 1px solid #2a2a2a;
  border-radius: 1.2vw;
  padding: 2.5vw 3vw;
  display: flex;
  flex-direction: column;
  gap: 1vw;
  min-width: 0;
">
  <div style="
    color: #888888;
    font-size: 1.6vw;
    font-weight: 500;
    letter-spacing: 0.12em;
    text-transform: uppercase;
  ">{label}</div>
  <div style="
    color: #ffffff;
    font-size: 4.5vw;
    font-weight: 600;
    letter-spacing: -0.02em;
    line-height: 1.1;
    word-break: break-word;
  ">{value}</div>
</div>
"""

        extra_css = ""
        body = f"""\
<div style="
  display: flex;
  flex-direction: column;
  width: 100vw;
  height: 100vh;
  padding: 4vw;
  gap: 3vw;
">
  <h1 style="
    color: #ffffff;
    font-size: 3.5vw;
    font-weight: 700;
    letter-spacing: -0.02em;
    flex-shrink: 0;
  ">{title_html}</h1>
  <div style="
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(28vw, 1fr));
    gap: 2vw;
    flex: 1;
    align-content: start;
  ">
    {cards_html}
  </div>
</div>"""
        script = ""

        return _BASE_HTML.format(
            title=title_html,
            bg="#111111",
            extra_css=extra_css,
            body=body,
            script=script,
        )

    # ------------------------------------------------------------------
    # photo — CSS-only crossfade slideshow
    # ------------------------------------------------------------------
    elif content_type == "photo":
        raw_urls: list[str] = data.get("urls", [])
        interval: int = int(data.get("interval", 5))

        # Drop any URL that fails the CSS-url safety gate — the template
        # below puts the URL inside url('{...}'), where ') + <tag>" would
        # otherwise escape the <style> block.
        urls = [u for u in (_safe_css_url(u) for u in raw_urls) if u]

        if not urls:
            # Fallback: blank dark screen with a message
            return generate_html("message", {"text": "No photos", "bg": "#111111"})

        n = len(urls)
        # Each image fades in, holds, then fades out.  The total cycle is
        # n * interval seconds.  Each image is visible for (1/n) of the cycle.
        total = n * interval
        step_pct = 100 / n          # percentage of the cycle per image
        fade_pct = min(10.0, step_pct * 0.2)   # 20 % of slot for fade

        keyframes = ""
        images_html = ""
        for i, url in enumerate(urls):
            offset = i * step_pct   # when this image's slot starts (%)

            # Build keyframe: fade-in at offset, hold, fade-out at offset+step
            kf_in_start = offset
            kf_in_end = offset + fade_pct
            kf_out_start = offset + step_pct - fade_pct
            kf_out_end = offset + step_pct

            # Wrap percentages that exceed 100 by splitting into two keyframes
            # is complex; instead keep values in [0,100] and let the last
            # image's fade-out coincide with 100 %.
            kf_out_end = min(kf_out_end, 100.0)

            keyframes += f"""\
@keyframes slide{i} {{
  0%   {{ opacity: 0; }}
  {kf_in_start:.2f}%  {{ opacity: 0; }}
  {kf_in_end:.2f}%  {{ opacity: 1; }}
  {kf_out_start:.2f}%  {{ opacity: 1; }}
  {kf_out_end:.2f}%  {{ opacity: 0; }}
  100% {{ opacity: 0; }}
}}
"""
            images_html += f"""\
<div style="
  position: absolute; inset: 0;
  background-image: url('{url}');
  background-size: cover;
  background-position: center;
  animation: slide{i} {total}s linear infinite;
"></div>
"""

        extra_css = keyframes
        body = f"""\
<div style="position: relative; width: 100vw; height: 100vh; background: #000;">
  {images_html}
</div>"""
        script = ""

        return _BASE_HTML.format(
            title="Photos",
            bg="#000000",
            extra_css=extra_css,
            body=body,
            script=script,
        )

    # ------------------------------------------------------------------
    # iframe — embed any URL full-screen
    # ------------------------------------------------------------------
    elif content_type == "iframe":
        # Scheme-gate: http/https only. Rejects javascript:, file:,
        # data:, and unparsable inputs — see _safe_iframe_url.
        url = _safe_iframe_url(data.get("url", ""))
        # fullscreen=True is the only sensible option on a TV; kept as param
        # for API completeness.

        extra_css = ""
        body = f"""\
<iframe
  src="{url}"
  style="
    position: fixed;
    inset: 0;
    width: 100vw;
    height: 100vh;
    border: none;
  "
  allowfullscreen
></iframe>"""
        script = ""

        return _BASE_HTML.format(
            title="Web",
            bg="#111111",
            extra_css=extra_css,
            body=body,
            script=script,
        )

    # ------------------------------------------------------------------
    # custom — raw HTML pass-through wrapped in dark boilerplate
    # ------------------------------------------------------------------
    elif content_type == "custom":
        raw_html = data.get("html", "")

        extra_css = ""
        body = f"""\
<div style="
  width: 100vw;
  height: 100vh;
  color: #ffffff;
  font-size: 3vw;
">
  {raw_html}
</div>"""
        script = ""

        return _BASE_HTML.format(
            title="Custom",
            bg="#111111",
            extra_css=extra_css,
            body=body,
            script=script,
        )

    else:
        raise ValueError(
            f"Unknown content_type {content_type!r}. "
            "Choose from: message, clock, dashboard, photo, iframe, custom."
        )


# ---------------------------------------------------------------------------
# HTTP server
# ---------------------------------------------------------------------------

def _make_handler(html: str) -> type[BaseHTTPRequestHandler]:
    """Build a handler class bound to *html*.

    A previous version stored the HTML on the class (``_Handler.html_content``);
    two concurrent ``serve()`` calls overwrote each other, so TV1 ended up
    showing TV2's page. Per-invocation class closes over the string directly.
    """

    class _Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:  # noqa: N802
            body = html.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, format: str, *args: object) -> None:  # noqa: A002
            pass  # suppress access logs

    return _Handler


def serve(
    html: str,
    port: int = 8765,
    host: str = "",
) -> tuple[str, Callable[[], None]]:
    """Start a non-blocking HTTP server that serves *html* at ``/``.

    Parameters
    ----------
    html:
        The HTML string to serve (typically from :func:`generate_html`).
    port:
        Local port to listen on (default ``8765``).
    host:
        Bind address. ``""`` (default) auto-selects: the LAN IP that the
        TV can actually reach, so a phone on the same Wi-Fi can fetch it.
        Pass ``"127.0.0.1"`` to restrict to the local machine (useful for
        development or when piping through stv's cast URL on the same box).

    Returns
    -------
    url:
        ``"http://<LAN-IP>:<port>"`` — the address the TV can reach.
    stop_fn:
        Zero-argument callable; call it to shut down the server.

    Example::

        url, stop = serve(html, port=8765)
        # open url on TV via: stv cast <url>
        stop()   # when done
    """
    ip = _get_local_ip()
    bind = host if host else ip
    handler_cls = _make_handler(html)
    server = HTTPServer((bind, port), handler_cls)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    # When the caller restricts the bind (e.g. 127.0.0.1), the returned
    # URL must match — otherwise ``stv cast <url>`` resolves to the LAN
    # IP, the TV dials in on a socket that is not listening, and the
    # cast silently fails.
    reachable = ip if bind in ("", "0.0.0.0") else bind
    url = f"http://{reachable}:{port}"
    return url, server.shutdown
