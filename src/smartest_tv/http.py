"""HTTP + subprocess helpers for smartest-tv.

Replaces raw subprocess.run(["curl", ...]) calls with a structured helper
that provides consistent error handling, configurable timeouts, and logging.

When the curl binary is absent (Home Assistant slim containers ship without
it), ``curl()`` transparently falls back to a pure-Python urllib client with
matching semantics — before v1.3.0 those environments failed every resolve
and RemoteDriver call silently.

Also wraps yt-dlp calls with proper error handling.
"""

from __future__ import annotations

import json
import logging
import os
import shutil
import subprocess
from dataclasses import dataclass

log = logging.getLogger("smartest-tv")

# Configurable timeouts via environment variables
HTTP_TIMEOUT = int(os.environ.get("STV_HTTP_TIMEOUT", "10"))
SUBPROCESS_TIMEOUT = int(os.environ.get("STV_SUBPROCESS_TIMEOUT", "15"))
YTDLP_TIMEOUT = int(os.environ.get("STV_YTDLP_TIMEOUT", "30"))

_USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"


@dataclass
class HttpResult:
    """Result from an HTTP request."""
    ok: bool
    body: str
    status_code: int | None = None
    error: str | None = None


_warned_curl_fallback = False


def _urllib_fetch(
    url: str,
    headers: dict[str, str] | None = None,
    method: str = "GET",
    data: str | None = None,
    timeout: int | None = None,
) -> HttpResult:
    """Pure-Python fallback used when the curl binary is not installed.

    Mirrors the flags ``curl -s -L --compressed --max-time t``:
      - follows redirects (POST degrades to GET on 301/302, like curl)
      - sends Accept-Encoding and transparently decompresses gzip/deflate
      - HTTP error statuses return the body with ok=True (curl without
        ``-f`` exits 0 and prints the body — callers parse it)
      - transport errors / timeouts return ok=False
    """
    import gzip
    import urllib.error
    import urllib.request
    import zlib

    t = timeout or HTTP_TIMEOUT
    req_headers = {"User-Agent": _USER_AGENT, "Accept-Encoding": "gzip, deflate"}
    for k, v in (headers or {}).items():
        req_headers[k] = v
    if method == "POST" and data is not None and "Content-Type" not in (headers or {}):
        req_headers["Content-Type"] = "application/json"

    body_bytes = data.encode() if data is not None else None
    # Parity with the subprocess path: only POST is special-cased there;
    # anything else is a plain GET.
    req_method = "POST" if method == "POST" else "GET"
    req = urllib.request.Request(url, data=body_bytes, headers=req_headers, method=req_method)

    try:
        with urllib.request.urlopen(req, timeout=t) as resp:
            raw = resp.read()
            encoding = (resp.headers.get("Content-Encoding") or "").lower()
            status = resp.getcode()
    except urllib.error.HTTPError as e:
        # curl -s (no -f) treats HTTP errors as success with the body.
        try:
            raw = e.read()
        except Exception:  # noqa: BLE001 — body may already be consumed
            raw = b""
        encoding = ""
        status = e.code
    except urllib.error.URLError as e:
        reason = getattr(e, "reason", e)
        log.debug("urllib fallback %s failed: %s", url, reason)
        return HttpResult(ok=False, body="", error=str(reason))
    except TimeoutError:
        log.warning("urllib fallback %s timed out after %ds", url, t)
        return HttpResult(ok=False, body="", error=f"timeout ({t}s)")
    except OSError as e:
        log.debug("urllib fallback %s OS error: %s", url, e)
        return HttpResult(ok=False, body="", error=str(e))

    if encoding == "gzip":
        try:
            raw = gzip.decompress(raw)
        except OSError:
            pass  # leave as-is; callers treat undecodable bodies as errors
    elif encoding == "deflate":
        try:
            raw = zlib.decompress(raw)
        except zlib.error:
            try:
                raw = zlib.decompress(raw, -zlib.MAX_WBITS)  # raw deflate
            except zlib.error:
                pass

    return HttpResult(ok=True, body=raw.decode("utf-8", errors="replace"), status_code=status)


def curl(
    url: str,
    headers: dict[str, str] | None = None,
    method: str = "GET",
    data: str | None = None,
    timeout: int | None = None,
) -> HttpResult:
    """Make an HTTP request via curl (urllib fallback if curl is absent).

    Args:
        url: The URL to request.
        headers: Optional HTTP headers.
        method: HTTP method (GET, POST, etc.).
        data: Request body (for POST).
        timeout: Override the default timeout (STV_HTTP_TIMEOUT).

    Returns:
        HttpResult with ok=True on success, ok=False on any failure.
    """
    if shutil.which("curl") is None:
        global _warned_curl_fallback
        if not _warned_curl_fallback:
            _warned_curl_fallback = True
            log.warning(
                "curl binary not found — using the built-in Python HTTP "
                "fallback (install curl for best performance)"
            )
        return _urllib_fetch(url, headers, method, data, timeout)

    t = timeout or HTTP_TIMEOUT
    args = [
        "curl", "-s", "-L", "--compressed",
        "--max-time", str(t),
        "-H", f"User-Agent: {_USER_AGENT}",
    ]

    if headers:
        for k, v in headers.items():
            args.extend(["-H", f"{k}: {v}"])

    if method == "POST":
        args.extend(["-X", "POST"])
        if data:
            args.extend(["-d", data])
            if "Content-Type" not in (headers or {}):
                args.extend(["-H", "Content-Type: application/json"])

    args.append(url)

    try:
        result = subprocess.run(
            args,
            capture_output=True,
            text=True,
            timeout=SUBPROCESS_TIMEOUT,
        )
        body = result.stdout or ""
        if result.returncode != 0:
            err = result.stderr.strip() if result.stderr else f"curl exit code {result.returncode}"
            log.debug("curl %s failed: %s", url, err)
            return HttpResult(ok=bool(body), body=body, error=err)
        return HttpResult(ok=True, body=body)

    except subprocess.TimeoutExpired:
        log.warning("curl %s timed out after %ds", url, SUBPROCESS_TIMEOUT)
        return HttpResult(ok=False, body="", error=f"timeout ({SUBPROCESS_TIMEOUT}s)")

    except FileNotFoundError:
        log.error("curl not found in PATH")
        return HttpResult(ok=False, body="", error="curl not found")

    except OSError as e:
        log.error("curl %s OS error: %s", url, e)
        return HttpResult(ok=False, body="", error=str(e))


def ytdlp(
    args: list[str],
    timeout: int | None = None,
) -> HttpResult:
    """Run a yt-dlp command with proper error handling.

    Args:
        args: yt-dlp arguments (without the 'yt-dlp' binary name).
        timeout: Override YTDLP_TIMEOUT.

    Returns:
        HttpResult with the stdout as body.
    """
    if not shutil.which("yt-dlp"):
        return HttpResult(ok=False, body="", error="yt-dlp not found. Install: pip install yt-dlp")

    t = timeout or YTDLP_TIMEOUT
    cmd = ["yt-dlp"] + args

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=t,
        )
        body = result.stdout.strip() if result.stdout else ""
        if result.returncode != 0:
            err = result.stderr.strip() if result.stderr else f"yt-dlp exit code {result.returncode}"
            log.debug("yt-dlp failed: %s", err)
            return HttpResult(ok=bool(body), body=body, error=err)
        return HttpResult(ok=True, body=body)

    except subprocess.TimeoutExpired:
        log.warning("yt-dlp timed out after %ds", t)
        return HttpResult(ok=False, body="", error=f"timeout ({t}s)")

    except OSError as e:
        log.error("yt-dlp OS error: %s", e)
        return HttpResult(ok=False, body="", error=str(e))


def curl_json(url: str, data: dict | None = None, timeout: int | None = None) -> dict | None:
    """POST JSON to a URL and parse the JSON response.

    Returns the parsed dict on success, None on any failure.
    """
    r = curl(
        url,
        method="POST" if data else "GET",
        data=json.dumps(data) if data else None,
        headers={"Content-Type": "application/json"} if data else None,
        timeout=timeout,
    )
    if not r.ok or not r.body:
        return None
    try:
        return json.loads(r.body)
    except (json.JSONDecodeError, ValueError):
        return None
