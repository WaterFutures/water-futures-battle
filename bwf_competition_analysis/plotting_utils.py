import plotly.graph_objects as go

def _hex_to_rgb(color: str) -> tuple[int, int, int]:
    color = color.lstrip('#')
    return int(color[0:2], 16), int(color[2:4], 16), int(color[4:6], 16)


def make_opaque(color: str, alpha: float) -> str:
    """Convert a hex color into an rgba() string with the given alpha."""
    r, g, b = _hex_to_rgb(color)
    return f'rgba({r}, {g}, {b}, {alpha})'


def get_scale(color: str, n_steps: int, light_color: str = '#FFFFFF') -> list[str]:
    """Build a sequential ramp (light -> dark) of n_steps hex colors ending in `color`."""
    r0, g0, b0 = _hex_to_rgb(light_color)
    r1, g1, b1 = _hex_to_rgb(color)
    ramp = []
    for i in range(n_steps):
        t = ((i + 1) / n_steps) ** 1.5
        r = round(r0 + t * (r1 - r0))
        g = round(g0 + t * (g1 - g0))
        b = round(b0 + t * (b1 - b0))
        ramp.append(f'#{r:02X}{g:02X}{b:02X}')
    return ramp


# Base discrete colors for plots based on the Water-Futures palette (blue-green)
WF_BLUE = '#3059D1'
WF_GREEN = '#009344'
WF_ORANGE = '#E8960C'
WF_GREY = '#64748B'
WF_RED = '#D63434'
WF_PURPLE = '#7B3FC3'
WF_LIGHTGREY = '#E7E6E6'
WF_CYAN = '#19D3F3'
WF_PINK = '#FF6692'
WF_LIME = '#B6E880'
WF_MAGENTA = '#FF97FF'
WF_YELLOW = '#FECB52'
WF_BROWN = '#8C564B'
WF_NAVY = '#1B2A4A'

# Fill versions
WF_BLUE_FILL = make_opaque(WF_BLUE, 0.2)
WF_GREEN_FILL = make_opaque(WF_GREEN, 0.5)

# Sequential ramps (light -> dark), one per hue, for heatmaps; index i is
# the fill for bucket i.
WF_PURPLE_RAMP = get_scale(WF_PURPLE, 4)
WF_BLUE_RAMP = get_scale(WF_BLUE, 4)
WF_GREEN_RAMP = get_scale(WF_GREEN, 4)

# 12 symbols for the 12 competing teams
TEAMS_SYMBOLS = [
    'circle',
    'square',
    'diamond',
    'cross',
    'x',
    'triangle-up',
    'triangle-down',
    'triangle-left',
    'triangle-right',
    'pentagon',
    'star',
    'hexagram',
]
TEAM00_SYMBOL = 'star-diamond'

TEAMS_COLORS = [
    WF_BLUE,
    WF_RED,
    WF_GREEN,
    WF_PURPLE,
    WF_ORANGE,
    WF_CYAN,
    WF_PINK,
    WF_LIME,
    WF_MAGENTA,
    WF_YELLOW,
    WF_BROWN,
    WF_NAVY,
]
TEAM00_COLORS = WF_GREY

# ============================================================
# CONSTANTS — edit only these
# ============================================================
PX_PER_IN = 96      # Kaleido's fixed CSS-pixel reference for vector export
PT_PER_IN = 72      # PostScript/DTP point (what "9pt font" means)
TEXPT_PER_IN = 72.27  # TeX's own point unit (what \the\linewidth reports)

JOURNAL_FONT_FAMILY = 'Arial'
JOURNAL_FONT_SIZE_PT = 9

FONT_SCALE = dict(
    tick=8/9,
    axis_title=11/10,
    legend=1.0,
    legend_title=11/10,
    annotation=8/9,
)

# Measured directly from \the\linewidth in the actual template (see log dump)
SINGLE_COL_TEXPT = 247.79752   # inside \begin{figure}
FULL_WIDTH_TEXPT = 514.99507   # inside \begin{figure*}

# ============================================================
# HELPERS
# ============================================================
def pt_to_px(size_pt):
    """PostScript pt -> Kaleido px (used for font/line sizes)."""
    return size_pt * PX_PER_IN / PT_PER_IN

def texpt_to_px(size_texpt):
    """TeX pt (\\linewidth units) -> Kaleido px (used for figure width/height)."""
    return size_texpt * PX_PER_IN / TEXPT_PER_IN

def font(role, family=JOURNAL_FONT_FAMILY):
    return dict(family=family, size=pt_to_px(JOURNAL_FONT_SIZE_PT * FONT_SCALE[role]))

# ============================================================
# THE ONE FUNCTION YOU CALL
# ============================================================
def apply_journal_formatting(fig, column='single', frac=1.0, ratio=1.6) -> go.Figure:
    """
    column : 'single' or 'full' — which \\linewidth this figure sits in
    frac   : fraction of \\linewidth, matching \\includegraphics[width=frac\\linewidth]
    ratio  : width / height aspect ratio (>1 = wider than tall, <1 = taller than wide)
    """
    base_texpt = {'single': SINGLE_COL_TEXPT, 'full': FULL_WIDTH_TEXPT}[column]
    width_px = texpt_to_px(base_texpt * frac)
    height_px = width_px / ratio

    fig.update_layout(
        template="plotly_white",
        width=width_px,
        height=height_px,
        font=font('tick'),
        legend=dict(
            font=font('legend'),
            title_font=font('legend_title'),
        ),
    )
    fig.update_xaxes(title_font=font('axis_title'), tickfont=font('tick'))
    fig.update_yaxes(title_font=font('axis_title'), tickfont=font('tick'))

    return fig