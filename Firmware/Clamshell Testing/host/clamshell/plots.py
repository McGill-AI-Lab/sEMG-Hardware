"""
==============================================================================
 plots.py  —  shared chart styling and figure saving (matplotlib)
==============================================================================

LIBRARY: matplotlib
-------------------
matplotlib draws charts. The objects you meet here:
  - Figure : the whole image.               fig = plt.figure(...)
  - Axes   : one plot area inside it.       ax.plot(x, y), ax.set_xlabel(...)
  - "Agg"  : a backend that renders to PNG files without opening a window.
             The report uses it; the live window (live.py) uses an
             interactive backend instead.

STYLE RULES USED IN EVERY CHART
-------------------------------
- Colour follows the ENTITY, never its position: CH1 is always the same
  blue, CH5 always the same magenta, 500 SPS always the same colour, in
  every chart of the report.
- One y-axis per chart. Different quantities go in separate panels.
- Thin lines, light grid, muted axes, so the data stands out.
- Every chart is drawn twice, for a light and a dark page background. The
  report shows the one that matches the reader's system setting.
==============================================================================
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")                           # render to files, never open a window (must come before pyplot)
import matplotlib.pyplot as plt                 # noqa: E402  (import after choosing the backend)
from matplotlib.colors import LinearSegmentedColormap  # noqa: E402
from matplotlib.ticker import FuncFormatter, LogLocator, NullFormatter  # noqa: E402


from .palette import DARK, LIGHT, Theme, channel_color, rate_color  # noqa: E402,F401  (colours live in palette.py)

THEMES = (LIGHT, DARK)                          # every figure is drawn in both


def diverging_cmap(theme: Theme):
    """Blue -> grey -> red colour map for values in [-1, 1] (correlation)."""
    return LinearSegmentedColormap.from_list("div", list(theme.diverging))


def new_figure(theme: Theme, nrows: int = 1, ncols: int = 1, width: float = 7.6, height: float = 3.0,
               sharex: bool = False, sharey: bool = False):
    """
    Create a figure with `nrows x ncols` panels, already styled for `theme`.
    Returns (fig, axes) where axes is always a flat list.
    """
    plt.rcParams.update({                                              # defaults for text created later
        "axes.titlecolor": theme.ink,                                  # panel titles (all positions: left/center/right)
        "axes.labelcolor": theme.ink2,                                 # axis labels
        "text.color": theme.ink,                                       # any other text
        "font.family": "sans-serif",                                   # system sans, like the report page
    })
    fig, axes = plt.subplots(nrows, ncols, figsize=(width, height * nrows), sharex=sharex, sharey=sharey,
                             squeeze=False, constrained_layout=True)   # constrained_layout avoids overlapping labels
    fig.patch.set_facecolor(theme.surface)                             # figure background
    flat = [ax for row in axes for ax in row]                          # 2-D grid -> flat list
    for ax in flat:                                                    # style every panel
        style_axes(ax, theme)
    return fig, flat


def style_axes(ax, theme: Theme):
    """Recessive grid and axes in the theme colours."""
    ax.set_facecolor(theme.surface)                                    # panel background
    for side in ("top", "right"):                                      # remove the box's top/right edges
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):                                    # keep left/bottom as thin axis lines
        ax.spines[side].set_color(theme.base)
        ax.spines[side].set_linewidth(0.8)
    ax.tick_params(colors=theme.muted, labelsize=8, length=3, width=0.6)   # small muted ticks
    ax.grid(True, color=theme.grid, linewidth=0.6)                     # hairline grid
    ax.set_axisbelow(True)                                             # grid behind the data
    ax.xaxis.label.set_color(theme.ink2)                               # axis label colours
    ax.yaxis.label.set_color(theme.ink2)
    ax.xaxis.label.set_size(9)
    ax.yaxis.label.set_size(9)
    ax.title.set_color(theme.ink)                                      # panel title
    ax.title.set_size(10)


def legend(ax, theme: Theme, **kw):
    """A small legend with theme colours (only call it when there are >= 2 series)."""
    kw.setdefault("fontsize", 8)                                       # small text unless the caller chose a size
    lg = ax.legend(frameon=False, labelcolor=theme.ink2, **kw)         # no box, secondary ink
    return lg


def plain_log_labels(ax):
    """
    On logarithmic axes, write ticks as plain numbers (0.02, 0.1, 1, 10, 100)
    instead of matplotlib's default "2 x 10^-2" style, and add ticks at 2 and 5
    within each decade so short ranges still get labels.
    """
    fmt = FuncFormatter(lambda v, _: f"{v:g}")                         # "%g" = shortest plain representation
    for axis, scale in ((ax.xaxis, ax.get_xscale()), (ax.yaxis, ax.get_yscale())):
        if scale != "log":                                             # only log axes need this
            continue
        if type(axis.get_major_locator()).__name__ == "FixedLocator":  # explicit ticks (e.g. gains): keep them
            axis.set_major_formatter(fmt)
            continue
        axis.set_major_locator(LogLocator(base=10, subs=(1.0, 2.0, 5.0)))   # ticks at 1, 2, 5 x 10^k
        axis.set_major_formatter(fmt)                                  # plain numbers
        axis.set_minor_formatter(NullFormatter())                      # no labels on minor ticks


def save_both(builder, out_dir: Path, stem: str) -> dict:
    """
    Draw a chart in both themes and save it as PNG.

    `builder(theme)` must return a matplotlib Figure. Returns
    {"light": "figures/<stem>_light.png", "dark": ".../<stem>_dark.png"} with
    paths relative to the run folder, ready for the HTML report.
    """
    out_dir.mkdir(parents=True, exist_ok=True)                         # make figures/ if needed
    paths = {}                                                         # result
    for theme in THEMES:                                               # light, then dark
        fig = builder(theme)                                           # draw
        for ax in fig.axes:                                            # every panel ...
            plain_log_labels(ax)                                       # ... gets readable log-axis numbers
        p = out_dir / f"{stem}_{theme.name}.png"                       # file name
        fig.savefig(p, dpi=170, facecolor=theme.surface)               # write PNG
        plt.close(fig)                                                 # free memory (important in long runs)
        paths[theme.name] = f"{out_dir.name}/{p.name}"                 # relative path for the HTML
    return paths
