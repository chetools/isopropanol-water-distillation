"""One source of truth for colour, type scale, and layout across the whole app.

Plotly figures (:mod:`src.plotting`), the SVG engineering drawings
(:mod:`src.engineering_diagrams`) and the Streamlit CSS all read from here, so
a palette change lands everywhere at once instead of being re-typed as literal
hex codes in three places.

The palette is a Tailwind-style slate/sky ramp chosen to sit on the dark
application background declared in ``.streamlit/config.toml``.
"""

# --- Surfaces ---------------------------------------------------------------
BACKGROUND = "#0f172a"      # page
SURFACE = "#1e293b"         # cards, plot interiors
SURFACE_RAISED = "#243449"  # hover / emphasised panels
BORDER = "#334155"
BORDER_STRONG = "#475569"
GRID = "#334155"

# --- Text -------------------------------------------------------------------
TEXT = "#f8fafc"
TEXT_MUTED = "#cbd5e1"
TEXT_DIM = "#94a3b8"
TEXT_FAINT = "#64748b"

# --- Semantic accents -------------------------------------------------------
ACCENT = "#38bdf8"          # primary / liquid phase / rectifying
ACCENT_DEEP = "#0ea5e9"
VAPOR = "#f87171"           # vapour phase
FEED = "#10b981"            # feed streams and q-line
FEED_BRIGHT = "#34d399"
HEAT = "#fb923c"            # duties, heat flows
STAGE = "#facc15"           # tie lines, construction
STAGE_DEEP = "#eab308"
DIFFERENCE = "#a855f7"      # difference points, key states
DIFFERENCE_SOFT = "#c084fc"
STRIPPING = "#f97316"
DANGER = "#ef4444"
EQUILIBRIUM = "#a78bfa"

#: Ordered categorical ramp for any series without a semantic meaning.
SERIES = (ACCENT, VAPOR, FEED, STAGE, DIFFERENCE, HEAT, EQUILIBRIUM, DANGER)

# --- Typography -------------------------------------------------------------
FONT_STACK = "Inter, 'Segoe UI', system-ui, -apple-system, Arial, sans-serif"
MONO_STACK = "'JetBrains Mono', 'Cascadia Code', Consolas, monospace"

FONT_SECTION = 22
FONT_SUBSECTION = 17
FONT_BODY = 15
FONT_CAPTION = 13
FONT_MICRO = 11

# --- Layout -----------------------------------------------------------------
RADIUS = 10
RADIUS_SMALL = 6
PLOT_HEIGHT = 620   # includes room for the bottom legend block
CONTENT_MAX_WIDTH = 1520


def rgba(hex_color: str, alpha: float) -> str:
    """``#38bdf8`` plus an alpha channel, as a CSS/Plotly ``rgba()`` string."""
    value = hex_color.lstrip("#")
    r, g, b = (int(value[i:i + 2], 16) for i in (0, 2, 4))
    return f"rgba({r}, {g}, {b}, {alpha})"


def app_css() -> str:
    """The application stylesheet, derived from the palette above.

    Deliberately does *not* restate the background and text colours that
    ``.streamlit/config.toml`` already sets -- overriding the theme in two
    places is how they drift apart.  Only component styling lives here.
    """
    return f"""
<style>
  :root {{
    --surface: {SURFACE};
    --surface-raised: {SURFACE_RAISED};
    --border: {BORDER};
    --accent: {ACCENT};
    --text-dim: {TEXT_DIM};
    --text-faint: {TEXT_FAINT};
    --radius: {RADIUS}px;
  }}

  /* ---- KPI cards ---- */
  .metric-card {{
    background: var(--surface);
    border: 1px solid var(--border);
    border-left: 3px solid var(--accent);
    border-radius: var(--radius);
    padding: 14px 16px 15px 16px;
    margin-bottom: 10px;
    transition: border-color 120ms ease, transform 120ms ease;
  }}
  .metric-card:hover {{
    border-color: {BORDER_STRONG};
    border-left-color: var(--accent);
    transform: translateY(-1px);
  }}
  .metric-title {{
    font-size: {FONT_CAPTION}px;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    color: var(--text-dim);
    font-weight: 600;
    line-height: 1.3;
  }}
  .metric-value {{
    font-size: 27px;
    font-weight: 700;
    color: var(--accent);
    margin-top: 6px;
    line-height: 1.15;
  }}
  .metric-unit {{
    font-size: {FONT_CAPTION}px;
    font-weight: 500;
    color: var(--text-dim);
  }}
  .metric-sub {{
    font-size: {FONT_CAPTION}px;
    color: var(--text-faint);
    margin-top: 5px;
    line-height: 1.35;
  }}

  /* ---- Specification lock badges ---- */
  .locked-badge, .unlocked-badge {{
    display: inline-block;
    padding: 2px 8px;
    border-radius: {RADIUS_SMALL}px;
    font-size: {FONT_MICRO}px;
    font-weight: 600;
    vertical-align: middle;
  }}
  .locked-badge {{
    background: {rgba(FEED, 0.18)};
    color: {FEED_BRIGHT};
    border: 1px solid {FEED};
  }}
  .unlocked-badge {{
    background: {rgba(TEXT_DIM, 0.12)};
    color: {TEXT_MUTED};
    border: 1px solid {BORDER_STRONG};
    font-weight: 500;
  }}
  .spec-name {{
    font-size: {FONT_BODY}px;
    font-weight: 600;
    margin-right: 6px;
  }}
  .computed-value {{
    font-size: 21px;
    font-weight: 700;
    color: var(--accent);
    margin: 2px 0 0 0;
  }}

  /* ---- Figures ---- */
  .figure-caption {{
    font-size: {FONT_CAPTION}px;
    color: var(--text-dim);
    text-align: center;
    margin: -2px auto 18px auto;
    max-width: 62ch;
    line-height: 1.5;
  }}
  .figure-caption b {{ color: {TEXT_MUTED}; }}

  /* ---- Plot headings ---- */
  .plot-heading {{
    text-align: center;
    font-size: {FONT_SUBSECTION}px;
    font-weight: 700;
    color: {TEXT};
    margin: 4px 0 2px 0;
  }}

  /* ---- Learn-tab prose rhythm ---- */
  .lesson-objectives {{
    background: {rgba(ACCENT, 0.07)};
    border: 1px solid {rgba(ACCENT, 0.35)};
    border-radius: var(--radius);
    padding: 12px 18px;
    margin-bottom: 16px;
  }}
  .lesson-objectives ul {{ margin-bottom: 0; }}
  .key-result {{
    background: {rgba(FEED, 0.07)};
    border-left: 3px solid {FEED};
    border-radius: {RADIUS_SMALL}px;
    padding: 10px 16px;
    margin: 14px 0;
  }}
  .caution {{
    background: {rgba(HEAT, 0.08)};
    border-left: 3px solid {HEAT};
    border-radius: {RADIUS_SMALL}px;
    padding: 10px 16px;
    margin: 14px 0;
  }}
  .derivation-step {{
    border-left: 2px solid {BORDER_STRONG};
    padding-left: 16px;
    margin: 8px 0 8px 4px;
  }}

  /* ---- Charts fill their column ---- */
  .stPlotlyChart {{ margin-left: auto; margin-right: auto; width: 100% !important; }}
  .stPlotlyChart > div, .stPlotlyChart .js-plotly-plot, .stPlotlyChart .plot-container {{
    width: 100% !important;
  }}

  /* McCabe–Thiele (widget key xy_*): keep a square frame so y = x is 45°.
     Plotly scaleanchor is not used; it collapses after fullscreen. */
  [class*="st-key-xy_"] {{
    width: 100% !important;
    aspect-ratio: 1 / 1 !important;
    min-height: 0 !important;
  }}
  [class*="st-key-xy_"] .js-plotly-plot,
  [class*="st-key-xy_"] .plot-container,
  [class*="st-key-xy_"] .svg-container {{
    width: 100% !important;
    height: 100% !important;
  }}
  [data-testid="stFullScreenFrame"] [class*="st-key-xy_"] {{
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    width: min(100vw - 3rem, 100vh - 3rem) !important;
    height: min(100vw - 3rem, 100vh - 3rem) !important;
    max-width: calc(100vw - 3rem);
    max-height: calc(100vh - 3rem);
    aspect-ratio: 1 / 1 !important;
    margin: 0;
  }}

  /* ---- Readable measure on very wide screens ---- */
  .main .block-container,
  [data-testid="stMainBlockContainer"],
  .stMainBlockContainer {{
    max-width: {CONTENT_MAX_WIDTH}px !important;
    margin-left: auto !important;
    margin-right: auto !important;
    padding-left: clamp(1.25rem, 3vw, 2.5rem) !important;
    padding-right: clamp(1.25rem, 3vw, 2.5rem) !important;
    padding-top: 1.25rem !important;
    padding-bottom: 3.5rem !important;
  }}

  /* ---- Tabs ---- */
  button[data-baseweb="tab"] {{
    font-size: {FONT_BODY}px !important;
    font-weight: 600 !important;
  }}
  [data-testid="stTabs"] [data-baseweb="tab-list"] {{
    gap: 4px;
    border-bottom: 1px solid var(--border);
  }}

  /* ---- Dividers ---- */
  hr {{ margin: 1.6rem 0 !important; border-color: {BORDER} !important; }}
</style>
"""
