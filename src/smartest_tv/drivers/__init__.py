"""TV platform drivers."""

from smartest_tv.drivers.base import TVDriver

__all__ = ["TVDriver"]

# Platform drivers are imported lazily to avoid hard-dependency errors at import
# time when optional extras are not installed. Use explicit imports if you need
# them directly:
#   from smartest_tv.drivers.lg import LGDriver
#   from smartest_tv.drivers.roku import RokuDriver
