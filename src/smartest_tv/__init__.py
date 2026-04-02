"""smartest-tv — Control any smart TV with natural language."""

from smartest_tv.server import mcp


def mcp_main():
    mcp.run(transport="stdio")
