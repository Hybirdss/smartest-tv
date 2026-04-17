"""Defence against malicious SSDP responses.

Any device on the LAN can answer the SSDP M-SEARCH. A hostile neighbour
could advertise a friendlyName laced with Rich-markup control chars,
terminal escapes, or CRLF header splits. The sanitiser must scrub those
before the name lands in config.toml or gets rendered in the UI.
"""
from __future__ import annotations

from smartest_tv._engine.discovery import _extract_name, _sanitize_name


def test_sanitize_strips_rich_markup():
    assert _sanitize_name("[red]evil[/red] TV") == "redevilred TV"


def test_sanitize_strips_angle_brackets():
    assert _sanitize_name("<script>x</script>") == "scriptxscript"


def test_sanitize_caps_length():
    assert len(_sanitize_name("A" * 500)) == 64


def test_sanitize_strips_crlf_and_trailing_headers():
    # A malicious SSDP response could inject a second header via \r\n.
    raw = "Nice TV\r\nCache-Control: attacker-controlled"
    assert _sanitize_name(raw) == "Nice TV"


def test_extract_name_scrubs_friendlyname_injection():
    ssdp = (
        "HTTP/1.1 200 OK\r\n"
        "friendlyName: <img src=x onerror=alert(1)>Living Room TV\r\n"
        "\r\n"
    )
    name = _extract_name(ssdp, "10.0.0.5", "samsung")
    assert "<" not in name and ">" not in name
    assert "Living Room TV" in name


def test_extract_name_falls_back_when_all_scrubbed_empty():
    ssdp = "HTTP/1.1 200 OK\r\nfriendlyName: <><><>\r\n\r\n"
    name = _extract_name(ssdp, "10.0.0.6", "roku")
    # All chars got scrubbed -> empty -> falls through to brand fallback
    assert name == "Roku TV (10.0.0.6)"
