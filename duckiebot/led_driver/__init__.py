from .led_driver_abs import LEDsDriverAbs
from .virtual_led_driver import VirtualLEDsDriver

__all__ = [
    'LEDsDriverAbs',
    'PWMLEDsDriver',
    'LEDDriver',
    'VirtualLEDsDriver',
]


def __getattr__(name: str):
    """Lazy-load hardware drivers (smbus2) so simulation imports work on a laptop."""
    if name == 'PWMLEDsDriver':
        from .led_driver import PWMLEDsDriver
        return PWMLEDsDriver
    if name == 'LEDDriver':
        from .led_driver import LEDDriver
        return LEDDriver
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
