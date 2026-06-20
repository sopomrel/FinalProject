"""Corner LED patterns — front/back/left/right by navigation state."""

from typing import Iterable, Tuple

# Duckiebot corner indices (1 is unused):
#   [0] front-left     [2] front-right
#   [3] back-left      [4] back-right
ALL_LEDS = (0, 2, 3, 4)
FRONT_LEDS = (0, 2)
BACK_LEDS = (3, 4)
LEFT_LEDS = (0, 3)
RIGHT_LEDS = (2, 4)

COLOR_OFF = (0, 0, 0)
COLOR_GREEN = (0, 255, 0)
COLOR_RED = (255, 0, 0)
COLOR_BLUE = (0, 0, 255)
COLOR_TURN = (255, 180, 0)   # yellow-orange

FLASH_PERIOD_S = 0.5


def _apply_colour(leds, index: int, colour: Tuple[int, int, int]) -> None:
    r, g, b = colour
    leds.set_rgb(index, [r / 255, g / 255, b / 255])


def _apply_group(leds, indices: Iterable[int], colour: Tuple[int, int, int]) -> None:
    for idx in indices:
        _apply_colour(leds, idx, colour)


def _all_off(leds) -> None:
    _apply_group(leds, ALL_LEDS, COLOR_OFF)


def _flash_on(now: float, period: float = FLASH_PERIOD_S) -> bool:
    """True on the first half of each flash cycle."""
    return int(now / period) % 2 == 0


def show_forward_leds(leds) -> None:
    """Lane follow / straight driving — front corners green."""
    if leds is None:
        return
    try:
        _all_off(leds)
        _apply_group(leds, FRONT_LEDS, COLOR_GREEN)
    except Exception:
        pass


def show_stopped_leds(leds) -> None:
    """Wait at line / obstacle — back corners red."""
    if leds is None:
        return
    try:
        _all_off(leds)
        _apply_group(leds, BACK_LEDS, COLOR_RED)
    except Exception:
        pass


def show_turn_leds(leds, side: str, now: float) -> None:
    """Left/right turn — that side flashes yellow-orange every 0.5 s."""
    if leds is None:
        return
    indices = LEFT_LEDS if side == 'left' else RIGHT_LEDS
    try:
        _all_off(leds)
        if _flash_on(now):
            _apply_group(leds, indices, COLOR_TURN)
    except Exception:
        pass


def show_victory_leds(leds, now: float) -> None:
    """Victory dance — all corners blue, toggling every 0.5 s."""
    if leds is None:
        return
    try:
        if _flash_on(now):
            _apply_group(leds, ALL_LEDS, COLOR_BLUE)
        else:
            _all_off(leds)
    except Exception:
        pass


def show_done_leds(leds) -> None:
    """Mission complete — solid blue on all corners."""
    if leds is None:
        return
    try:
        _apply_group(leds, ALL_LEDS, COLOR_BLUE)
    except Exception:
        pass
