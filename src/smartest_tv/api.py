"""REST API server for remote TV control.

Runs alongside the MCP server to allow remote stv instances to control
this machine's TV. Used by RemoteDriver on the other end.

    stv serve                 # MCP on :8910, API on :8911
    stv serve --port 9000     # MCP on :9000, API on :9001
"""

from __future__ import annotations

import asyncio
import json
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from typing import Any

from smartest_tv.apps import resolve_app
from smartest_tv.config import get_tv_config
from smartest_tv.drivers.base import TVDriver
from smartest_tv.drivers.factory import create_driver


# Module-level driver cache (shared with the API handler)
_driver: TVDriver | None = None
_driver_lock = threading.Lock()


def _get_driver() -> TVDriver:
    """Get or create the local TV driver."""
    global _driver
    with _driver_lock:
        if _driver is not None:
            return _driver

        _driver = create_driver()
        return _driver


def _run_async(coro):
    """Run an async function from sync context."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as pool:
                future = pool.submit(asyncio.run, coro)
                return future.result(timeout=30)
        return loop.run_until_complete(coro)
    except RuntimeError:
        return asyncio.run(coro)


class ApiHandler(BaseHTTPRequestHandler):
    """REST API handler for remote TV control."""

    def log_message(self, format, *args):
        pass  # Suppress request logging

    def _read_json(self) -> dict:
        length = int(self.headers.get("Content-Length", 0))
        if length:
            body = self.rfile.read(length)
            return json.loads(body)
        return {}

    def _respond(self, code: int, data: Any) -> None:
        body = json.dumps(data, ensure_ascii=False).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def _error(self, code: int, msg: str) -> None:
        self._respond(code, {"error": msg})

    # -- Routes ---------------------------------------------------------------

    def do_GET(self):
        path = self.path.rstrip("/")

        if path == "/api/ping":
            tv = get_tv_config()
            self._respond(200, {
                "status": "ok",
                "name": tv.get("name", "stv"),
                "platform": tv.get("platform", ""),
            })

        elif path == "/api/status":
            try:
                d = _get_driver()

                async def _do():
                    await d.connect()
                    s = await d.status()
                    return {
                        "current_app": s.current_app,
                        "volume": s.volume,
                        "muted": s.muted,
                        "sound_output": s.sound_output,
                    }
                self._respond(200, _run_async(_do()))
            except Exception as e:
                self._error(500, str(e))

        elif path == "/api/info":
            try:
                d = _get_driver()

                async def _do():
                    await d.connect()
                    i = await d.info()
                    return {
                        "platform": i.platform,
                        "model": i.model,
                        "firmware": i.firmware,
                        "name": i.name,
                    }
                self._respond(200, _run_async(_do()))
            except Exception as e:
                self._error(500, str(e))

        elif path == "/api/volume":
            try:
                d = _get_driver()

                async def _do():
                    await d.connect()
                    return {"volume": await d.get_volume(), "muted": await d.get_muted()}
                self._respond(200, _run_async(_do()))
            except Exception as e:
                self._error(500, str(e))

        elif path == "/api/apps":
            try:
                d = _get_driver()

                async def _do():
                    await d.connect()
                    apps = await d.list_apps()
                    return {"apps": [{"id": a.id, "name": a.name} for a in apps]}
                self._respond(200, _run_async(_do()))
            except Exception as e:
                self._error(500, str(e))

        else:
            self._error(404, f"Unknown endpoint: {path}")

    def do_POST(self):
        path = self.path.rstrip("/")
        data = self._read_json()

        try:
            d = _get_driver()

            if path == "/api/launch":
                app = data.get("app", "")
                content_id = data.get("content_id")

                async def _do():
                    await d.connect()
                    app_id, name = resolve_app(app, d.platform)
                    if content_id:
                        if app.lower() == "netflix":
                            try:
                                await d.close_app(app_id)
                                await asyncio.sleep(2)
                            except Exception:
                                pass
                        await d.launch_app_deep(app_id, content_id)
                        return {"launched": name, "content_id": content_id}
                    else:
                        await d.launch_app(app_id)
                        return {"launched": name}

                self._respond(200, _run_async(_do()))

            elif path == "/api/close":
                app = data.get("app", "")

                async def _do():
                    await d.connect()
                    app_id, name = resolve_app(app, d.platform)
                    await d.close_app(app_id)
                    return {"closed": name}

                self._respond(200, _run_async(_do()))

            elif path == "/api/volume":
                async def _do():
                    await d.connect()
                    if "level" in data:
                        await d.set_volume(int(data["level"]))
                        return {"volume": data["level"]}
                    elif data.get("action") == "up":
                        await d.volume_up()
                        return {"action": "up"}
                    elif data.get("action") == "down":
                        await d.volume_down()
                        return {"action": "down"}
                    return {"error": "specify level or action"}

                self._respond(200, _run_async(_do()))

            elif path == "/api/mute":
                async def _do():
                    await d.connect()
                    mute = data.get("mute")
                    if mute is None:
                        mute = not await d.get_muted()
                    await d.set_mute(bool(mute))
                    return {"muted": mute}

                self._respond(200, _run_async(_do()))

            elif path == "/api/power":
                async def _do():
                    await d.connect()
                    action = data.get("action", "off")
                    if action == "on":
                        await d.power_on()
                    else:
                        await d.power_off()
                    return {"power": action}

                self._respond(200, _run_async(_do()))

            elif path == "/api/notify":
                msg = data.get("message", "")

                async def _do():
                    await d.connect()
                    await d.notify(msg)
                    return {"notified": msg}

                self._respond(200, _run_async(_do()))

            elif path == "/api/screen":
                async def _do():
                    await d.connect()
                    action = data.get("action", "off")
                    if action == "on":
                        await d.screen_on()
                    else:
                        await d.screen_off()
                    return {"screen": action}

                self._respond(200, _run_async(_do()))

            elif path == "/api/media":
                async def _do():
                    await d.connect()
                    action = data.get("action", "play")
                    if action == "pause":
                        await d.pause()
                    elif action == "stop":
                        await d.stop()
                    else:
                        await d.play()
                    return {"media": action}

                self._respond(200, _run_async(_do()))

            else:
                self._error(404, f"Unknown endpoint: {path}")

        except Exception as e:
            self._error(500, str(e))

    def do_OPTIONS(self):
        """Handle CORS preflight."""
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()


def start_api_server(host: str = "127.0.0.1", port: int = 8911) -> HTTPServer:
    """Start the REST API server in a background thread.

    Returns the server instance (call .shutdown() to stop).
    """
    server = HTTPServer((host, port), ApiHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server
