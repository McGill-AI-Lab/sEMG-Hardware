"""
==============================================================================
 palette.py  —  chart colours, shared by the report (plots.py) and the live
                window (live.py)
==============================================================================

Kept separate from plots.py on purpose: plots.py switches matplotlib to the
file-only "Agg" backend, while the live window needs an interactive backend.
This module imports nothing from matplotlib, so both can use it.

The colours are a validated categorical palette (checked for colour-blind
separation, in this exact order). Rules:
  - colour follows the ENTITY: CH1 is always slot 1, 500 SPS always slot 1;
  - status colours (good / warning / critical) are reserved for verdicts and
    always appear next to a text label (PASS / WARN / FAIL), never alone.
==============================================================================
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Theme:
    """All the colours a chart needs for one page background. frozen=True makes it read-only."""
    name: str                     # "light" or "dark"
    surface: str                  # chart background
    ink: str                      # titles and values
    ink2: str                     # secondary text (axis labels)
    muted: str                    # tick labels, reference lines
    grid: str                     # gridlines
    base: str                     # axis lines
    series: tuple                 # 8 categorical colours, fixed order
    diverging: tuple              # (negative pole, neutral midpoint, positive pole)
    good: str = "#0ca30c"         # PASS
    warning: str = "#fab219"      # WARN
    critical: str = "#d03b3b"     # FAIL


LIGHT = Theme("light", "#fcfcfb", "#0b0b0b", "#52514e", "#898781", "#e1e0d9", "#c3c2b7",
              ("#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#6250d6", "#e34948"),
              ("#1c5cab", "#f0efec", "#b8302f"))
DARK = Theme("dark", "#1a1a19", "#f0efec", "#c3c2b7", "#898781", "#2c2c2a", "#383835",
             ("#3987e5", "#d95926", "#199e70", "#c98500", "#d55181", "#0ca30c", "#9085e9", "#e66767"),
             ("#5598e7", "#383835", "#e66767"))

RATE_SLOT = {500: 0, 2000: 1, 4000: 2, 1000: 3, 8000: 4, 16000: 5, 32000: 6}   # fixed colour slot per data rate


def channel_color(theme: Theme, ch: int) -> str:
    """Colour of channel `ch` (1..8): CH1 -> slot 1 ... CH8 -> slot 8."""
    return theme.series[(ch - 1) % 8]


def rate_color(theme: Theme, rate: int) -> str:
    """Colour of a data rate (unknown rates share the last slot)."""
    return theme.series[RATE_SLOT.get(rate, 7)]


def verdict_color(theme: Theme, verdict: str) -> str:
    """Status colour for a verdict word; neutral grey for INFO/SKIP."""
    return {"PASS": theme.good, "WARN": theme.warning, "FAIL": theme.critical}.get(verdict, theme.muted)


VERDICT_ICON = {"PASS": "✓", "WARN": "!", "FAIL": "✕", "INFO": "i", "SKIP": "–"}   # icon shown next to every verdict
