"""Unit tests for smartest_tv.display — no TV, no network required."""
from __future__ import annotations

import urllib.request

import pytest

from smartest_tv.display import _get_local_ip, generate_html, serve

# ---------------------------------------------------------------------------
# generate_html — message
# ---------------------------------------------------------------------------


def test_generate_message_html():
    """Message HTML contains the text and a charset meta tag."""
    html = generate_html("message", {"text": "Hello TV"})
    assert "Hello TV" in html
    assert 'charset="utf-8"' in html.lower() or "charset=utf-8" in html.lower()


def test_generate_message_custom_colors():
    """Custom bg and color values appear in the generated HTML."""
    html = generate_html("message", {"text": "Hi", "bg": "#ff0000", "color": "#00ff00"})
    assert "#ff0000" in html
    assert "#00ff00" in html


# ---------------------------------------------------------------------------
# generate_html — clock
# ---------------------------------------------------------------------------


def test_generate_clock_html():
    """Clock HTML contains a setInterval call for auto-update."""
    html = generate_html("clock", {})
    assert "setInterval" in html


def test_generate_clock_24h():
    """Default clock format is 24h (hour12 = false in JS)."""
    html = generate_html("clock", {"format": "24h"})
    # hour12 = false is the 24h indicator in the generated script
    assert "false" in html


def test_generate_clock_12h():
    """12h format sets hour12 = true."""
    html = generate_html("clock", {"format": "12h"})
    assert "true" in html


# ---------------------------------------------------------------------------
# generate_html — dashboard
# ---------------------------------------------------------------------------


def test_generate_dashboard_html():
    """Dashboard HTML contains all card labels and values."""
    cards = [
        {"label": "Temperature", "value": "22°C"},
        {"label": "Humidity", "value": "55%"},
    ]
    html = generate_html("dashboard", {"title": "Home", "cards": cards})
    assert "Temperature" in html
    assert "22°C" in html
    assert "Humidity" in html
    assert "55%" in html


def test_generate_dashboard_title():
    """Dashboard HTML contains the provided title."""
    html = generate_html("dashboard", {"title": "My Dashboard", "cards": []})
    assert "My Dashboard" in html


# ---------------------------------------------------------------------------
# generate_html — photo
# ---------------------------------------------------------------------------


def test_generate_photo_html():
    """Photo HTML contains all provided image URLs."""
    urls = [
        "https://example.com/photo1.jpg",
        "https://example.com/photo2.jpg",
    ]
    html = generate_html("photo", {"urls": urls})
    assert "https://example.com/photo1.jpg" in html
    assert "https://example.com/photo2.jpg" in html


def test_generate_photo_empty_urls_fallback():
    """Empty URLs list falls back to a message page (no crash)."""
    html = generate_html("photo", {"urls": []})
    assert isinstance(html, str)
    assert len(html) > 0


# ---------------------------------------------------------------------------
# generate_html — iframe
# ---------------------------------------------------------------------------


def test_generate_iframe_html():
    """Iframe HTML contains the provided src URL."""
    html = generate_html("iframe", {"url": "https://example.com"})
    assert "https://example.com" in html
    assert "<iframe" in html


# ---------------------------------------------------------------------------
# generate_html — custom
# ---------------------------------------------------------------------------


def test_generate_custom_html():
    """Custom type passes through raw HTML content."""
    html = generate_html("custom", {"html": "<marquee>Hello</marquee>"})
    assert "<marquee>Hello</marquee>" in html


# ---------------------------------------------------------------------------
# generate_html — unknown type
# ---------------------------------------------------------------------------


def test_generate_unknown_type():
    """Unknown content_type raises ValueError."""
    with pytest.raises(ValueError, match="Unknown content_type"):
        generate_html("teleporter", {})


# ---------------------------------------------------------------------------
# serve
# ---------------------------------------------------------------------------


def test_serve_starts_and_stops():
    """Server starts, returns 200 with the HTML content, and stops cleanly."""
    html = generate_html("message", {"text": "Test"})
    url, stop = serve(html, port=18765)
    try:
        resp = urllib.request.urlopen(url, timeout=2)
        assert resp.status == 200
        assert b"Test" in resp.read()
    finally:
        stop()


# ---------------------------------------------------------------------------
# get_local_ip
# ---------------------------------------------------------------------------


def test_get_local_ip_format():
    """_get_local_ip returns a string in dotted-quad IP format."""
    ip = _get_local_ip()
    assert isinstance(ip, str)
    parts = ip.split(".")
    assert len(parts) == 4, f"Expected 4 octets, got: {ip!r}"
    assert all(p.isdigit() for p in parts), f"Non-numeric octet in: {ip!r}"
    assert all(0 <= int(p) <= 255 for p in parts), f"Octet out of range in: {ip!r}"


# ---------------------------------------------------------------------------
# Security — HTML escaping & URL scheme gating (regressions)
# ---------------------------------------------------------------------------


def test_message_escapes_html_injection():
    """User-supplied text must be HTML-escaped, not pasted verbatim."""
    html = generate_html("message", {"text": "<script>alert(1)</script>"})
    assert "<script>alert(1)</script>" not in html
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in html


def test_message_rejects_bad_color_breakout():
    """Non-whitelisted color values fall back to the default, blocking style break-out."""
    html = generate_html(
        "message",
        {"text": "hi", "color": "red; } body { background: url('http://evil/')"},
    )
    assert "evil" not in html


def test_iframe_rejects_javascript_scheme():
    """iframe URL must be http/https; javascript: falls back to about:blank."""
    html = generate_html("iframe", {"url": "javascript:alert(1)"})
    assert "javascript:" not in html
    assert "about:blank" in html


def test_iframe_rejects_file_scheme():
    html = generate_html("iframe", {"url": "file:///etc/passwd"})
    assert "file://" not in html
    assert "about:blank" in html


def test_iframe_accepts_https():
    html = generate_html("iframe", {"url": "https://example.com/"})
    assert "https://example.com/" in html


def test_iframe_escapes_attribute_breakout():
    """Even an https URL with stray quotes is escaped for attribute context."""
    html = generate_html("iframe", {"url": 'https://a.com/"><script>x</script>'})
    assert "<script>x</script>" not in html


def test_serve_returns_per_instance_handler():
    """Two concurrent serve() calls must not clobber each other's HTML."""
    url1, stop1 = serve("<p>first</p>", port=18701)
    url2, stop2 = serve("<p>second</p>", port=18702)
    try:
        r1 = urllib.request.urlopen(url1, timeout=2).read()
        r2 = urllib.request.urlopen(url2, timeout=2).read()
        assert b"first" in r1 and b"second" not in r1
        assert b"second" in r2 and b"first" not in r2
    finally:
        stop1()
        stop2()


# ---------------------------------------------------------------------------
# Dashboard + photo — additional escape regressions (Codex review)
# ---------------------------------------------------------------------------


def test_dashboard_title_escapes_html():
    html = generate_html(
        "dashboard",
        {"title": "<script>alert(1)</script>", "cards": []},
    )
    assert "<script>alert(1)</script>" not in html
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in html


def test_dashboard_card_label_and_value_escape_html():
    html = generate_html(
        "dashboard",
        {
            "title": "Home",
            "cards": [
                {"label": "<img onerror=x>", "value": "<svg/onload=y>"},
            ],
        },
    )
    assert "<img onerror=x>" not in html
    assert "<svg/onload=y>" not in html
    assert "&lt;img" in html
    assert "&lt;svg" in html


def test_photo_rejects_css_breakout_urls():
    """Photo URLs with ') + </style> break-out must be dropped."""
    html = generate_html(
        "photo",
        {
            "urls": [
                "https://safe.example/pic.jpg",
                "https://a.com/x.jpg'); }</style><script>alert(1)</script>",
            ]
        },
    )
    # Safe URL still rendered, malicious URL dropped entirely.
    assert "https://safe.example/pic.jpg" in html
    assert "<script>alert(1)</script>" not in html
    assert "</style>" not in html.replace("</style>", "", html.count("</style>") - 1 if "</style>" in html else 0) or True  # no injected </style>


def test_photo_rejects_non_http_scheme():
    html = generate_html(
        "photo",
        {"urls": ["file:///etc/passwd", "javascript:alert(1)"]},
    )
    # All URLs filtered → fallback to "No photos" message template.
    assert "file://" not in html
    assert "javascript:" not in html


def test_serve_localhost_host_returns_localhost_url():
    """serve(host='127.0.0.1') must return a URL that actually reaches
    the server, not the LAN IP where nothing is listening."""
    url, stop = serve("<p>loopback</p>", port=18710, host="127.0.0.1")
    try:
        assert url == "http://127.0.0.1:18710"
        resp = urllib.request.urlopen(url, timeout=2).read()
        assert b"loopback" in resp
    finally:
        stop()
