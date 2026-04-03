"""HTTP + subprocess helpers for smartest-tv.

Replaces raw subprocess.run(["curl", ...]) calls with a structured helper
that provides consistent error handling, configurable timeouts, and logging.

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


def curl(
    url: str,
    headers: dict[str, str] | None = None,
    method: str = "GET",
    data: str | None = None,
    timeout: int | None = None,
) -> HttpResult:
    """Make an HTTP request via curl.

    Args:
        url: The URL to request.
        headers: Optional HTTP headers.
        method: HTTP method (GET, POST, etc.).
        data: Request body (for POST).
        timeout: Override the default timeout (STV_HTTP_TIMEOUT).

    Returns:
        HttpResult with ok=True on success, ok=False on any failure.
    """
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
