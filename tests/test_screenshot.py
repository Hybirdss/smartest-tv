"""Screenshot behavior at the driver and MCP boundaries."""

from unittest.mock import AsyncMock

import pytest

pytest.importorskip("aiowebostv")
pytest.importorskip("fastmcp")

from smartest_tv import server  # noqa: E402
from smartest_tv._engine.drivers.lg import LGDriver  # noqa: E402


@pytest.mark.asyncio
async def test_lg_rejects_screenshot_from_another_host():
    driver = LGDriver("192.0.2.10")
    driver._ensure = AsyncMock(return_value=type("Client", (), {
        "request": AsyncMock(return_value={"imageUri": "https://example.com:3001/capture.jpg"})
    })())

    with pytest.raises(RuntimeError, match="unexpected screenshot image URI"):
        await driver.screenshot()


@pytest.mark.asyncio
async def test_mcp_screenshot_returns_image(monkeypatch):
    jpeg = b"\xff\xd8\xfftest"
    driver = type("Driver", (), {"screenshot": AsyncMock(return_value=jpeg)})()
    monkeypatch.setattr(server, "_get_driver", AsyncMock(return_value=driver))

    result = await server.tv_screenshot("Living Room")

    assert result.data == jpeg
    assert result._format == "jpeg"
    server._get_driver.assert_awaited_once_with("Living Room")
