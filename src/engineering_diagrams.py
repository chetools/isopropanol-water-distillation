"""Vector engineering diagrams for the tutorial.

The drawings are generated as inline SVG so labels stay sharp at any zoom, the
page prints cleanly, and no external assets are needed.  Colours come from
:mod:`src.theme`, so the diagrams sit on the dark application background
instead of punching a white rectangle through it.

Every diagram is published through :func:`figure`, which numbers it and
attaches a caption -- a figure a reader can refer to by number is worth far
more than a floating picture.
"""

from html import escape

import src.theme as theme

# --- Diagram-local palette, derived from the shared application theme -------
_BG_TOP = theme.SURFACE
_BG_BOTTOM = "#1a2536"
_UNIT_TOP = "#2a3b53"
_UNIT_BOTTOM = "#22314605"
_FRAME = theme.BORDER_STRONG
_TITLE = theme.TEXT
_SUBTITLE = theme.TEXT_DIM
_BODY = theme.TEXT_MUTED
_MUTED = theme.TEXT_DIM
_RULE = theme.BORDER_STRONG

_STREAM = theme.ACCENT
_HEAT = theme.HEAT
_GREEN = theme.FEED_BRIGHT


def _start(title: str, subtitle: str, height: int) -> list[str]:
    """Open an SVG canvas with shared defs, frame, title and subtitle."""
    return [f"""
<div style="margin:0.9rem 0 0.4rem 0; width:100%; overflow-x:auto">
<svg viewBox="0 0 1000 {height}" width="100%" role="img"
     aria-label="{escape(title)}" xmlns="http://www.w3.org/2000/svg"
     style="min-width:0;max-width:1180px;display:block;margin:auto;font-family:{theme.FONT_STACK}">
  <title>{escape(title)}</title><desc>{escape(subtitle)}</desc>
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="{_BG_TOP}"/><stop offset="1" stop-color="{_BG_BOTTOM}"/>
    </linearGradient>
    <linearGradient id="unit" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="{_UNIT_TOP}"/><stop offset="1" stop-color="{_BG_BOTTOM}"/>
    </linearGradient>
    <filter id="shadow" x="-20%" y="-20%" width="140%" height="140%">
      <feDropShadow dx="0" dy="2" stdDeviation="2.5" flood-color="#000000" flood-opacity="0.45"/>
    </filter>
    <marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="8" markerHeight="8" orient="auto-start-reverse">
      <path d="M 0 0 L 10 5 L 0 10 z" fill="{_STREAM}"/>
    </marker>
    <marker id="heat-arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="8" markerHeight="8" orient="auto-start-reverse">
      <path d="M 0 0 L 10 5 L 0 10 z" fill="{_HEAT}"/>
    </marker>
    <marker id="green-arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="8" markerHeight="8" orient="auto-start-reverse">
      <path d="M 0 0 L 10 5 L 0 10 z" fill="{_GREEN}"/>
    </marker>
    <marker id="thin-arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
      <path d="M 0 0 L 10 5 L 0 10 z" fill="{_MUTED}"/>
    </marker>
  </defs>
  <rect x="4" y="4" width="992" height="{height - 8}" rx="8" fill="url(#bg)" stroke="{_FRAME}"/>
  <text x="36" y="42" fill="{_TITLE}" font-size="22" font-weight="700">{escape(title)}</text>
  <text x="36" y="67" fill="{_SUBTITLE}" font-size="13.5">{escape(subtitle)}</text>
"""]


def _finish(parts: list[str]) -> str:
    parts.append("</svg></div>")
    return "".join(parts)


def _node(x: int, y: int, w: int, h: int, title: str, subtitle: str = "",
          accent: str = theme.ACCENT) -> str:
    """A labelled equipment or process block."""
    title_y = y + h / 2 - (7 if subtitle else -5)
    sub = (
        f'<text x="{x + w / 2}" y="{title_y + 23}" text-anchor="middle" '
        f'fill="{_MUTED}" font-size="12.5">{escape(subtitle)}</text>'
        if subtitle else ""
    )
    return f"""
  <g filter="url(#shadow)">
    <rect x="{x}" y="{y}" width="{w}" height="{h}" rx="5" fill="url(#unit)" stroke="{accent}" stroke-width="1.8"/>
    <text x="{x + w / 2}" y="{title_y}" text-anchor="middle" fill="{_TITLE}" font-size="15.5" font-weight="700">{escape(title)}</text>
    {sub}
  </g>"""


def _stream(x1: int, y1: int, x2: int, y2: int, label: str, detail: str = "",
            heat: bool = False, green: bool = False) -> str:
    """An arrowed process stream with a label and optional detail line."""
    color = _HEAT if heat else (_GREEN if green else _STREAM)
    marker = "heat-arrow" if heat else ("green-arrow" if green else "arrow")
    mx, my = (x1 + x2) / 2, (y1 + y2) / 2
    horizontal = abs(x2 - x1) >= abs(y2 - y1)
    label_y = my - 10 if horizontal else my
    anchor = "middle" if horizontal else ("start" if mx < 500 else "end")
    dx = 0 if anchor == "middle" else (12 if anchor == "start" else -12)
    detail_markup = (
        f'<text x="{mx + dx}" y="{label_y + 18}" text-anchor="{anchor}" '
        f'fill="{_MUTED}" font-size="12">{escape(detail)}</text>' if detail else ""
    )
    return f"""
  <path d="M {x1} {y1} L {x2} {y2}" fill="none" stroke="{color}" stroke-width="3" marker-end="url(#{marker})"/>
  <text x="{mx + dx}" y="{label_y}" text-anchor="{anchor}" fill="{color}" font-size="13.5" font-weight="700">{escape(label)}</text>
  {detail_markup}"""


def _equation_box(x: int, y: int, w: int, lines: list[str]) -> str:
    """A boxed set of equations; the first line is the heading."""
    h = 28 + 23 * len(lines)
    text = "".join(
        f'<text x="{x + 16}" y="{y + 28 + 22 * i}" '
        f'fill="{_TITLE if i == 0 else _BODY}" font-size="{13.5 if i == 0 else 12.5}" '
        f'font-weight="{700 if i == 0 else 400}">{escape(line)}</text>'
        for i, line in enumerate(lines)
    )
    return (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="5" '
            f'fill="{theme.rgba(theme.BACKGROUND, 0.55)}" stroke="{_RULE}"/>{text}')


def _label(x: int, y: int, text: str, color: str = _BODY, size: float = 13,
           anchor: str = "start", weight: int = 400) -> str:
    return (f'<text x="{x}" y="{y}" text-anchor="{anchor}" fill="{color}" '
            f'font-size="{size}" font-weight="{weight}">{escape(text)}</text>')


def _axes(x0: int, y0: int, width: int, height: int, x_label: str, y_label: str) -> str:
    """A plain pair of plot axes with arrowheads, for schematic graphs."""
    return f"""
  <path d="M {x0} {y0 - height} L {x0} {y0} L {x0 + width} {y0}" fill="none"
        stroke="{_RULE}" stroke-width="2"/>
  {_label(x0 + width, y0 + 26, x_label, _BODY, 13, "end", 600)}
  <text x="{x0 - 22}" y="{y0 - height + 4}" fill="{_BODY}" font-size="13" font-weight="600"
        transform="rotate(-90 {x0 - 22} {y0 - height + 4})" text-anchor="end">{escape(y_label)}</text>"""


# ---------------------------------------------------------------------------
# Figure publication
# ---------------------------------------------------------------------------

def figure(svg: str, number: str, caption: str) -> str:
    """Wrap a diagram with its figure number and caption.

    A numbered, captioned figure can be referenced from the prose
    ("as Figure 5.2 shows"), which is what makes a diagram part of the
    argument rather than decoration beside it.
    """
    return (
        f'{svg}<div class="figure-caption"><b>Figure {escape(number)}</b> &mdash; '
        f'{escape(caption)}</div>'
    )


# ---------------------------------------------------------------------------
# Chapter 1 - orientation
# ---------------------------------------------------------------------------

def whole_column_balance_svg() -> str:
    p = _start("Whole-column material and energy balance envelope",
               "Arrows define the sign convention used in every derivation", 510)
    p.append(f'<rect x="245" y="92" width="510" height="310" fill="{theme.rgba(theme.ACCENT, 0.05)}" '
             f'stroke="{_RULE}" stroke-width="2" stroke-dasharray="9 7"/>')
    p.append(_label(270, 120, "CONTROL VOLUME", _SUBTITLE, 12.5, weight=700))
    p.append(_node(390, 130, 220, 62, "TOTAL CONDENSER", "vapour to liquid"))
    p.append(_node(390, 224, 220, 76, "TRAY COLUMN", "N equilibrium stages", theme.EQUILIBRIUM))
    p.append(_node(390, 332, 220, 62, "PARTIAL REBOILER", "liquid to vapour", theme.FEED_BRIGHT))
    p.append(_stream(55, 262, 390, 262, "FEED", "F, z_F, h_F"))
    p.append(_stream(610, 151, 925, 151, "DISTILLATE", "D, x_D, h_D"))
    p.append(_stream(610, 371, 925, 371, "BOTTOMS", "B, x_B, h_B"))
    p.append(_stream(500, 130, 500, 82, "Q_C out", "positive magnitude", heat=True))
    p.append(_stream(500, 458, 500, 394, "Q_R in", "positive magnitude", heat=True))
    p.append(_equation_box(45, 414, 395, [
        "Independent steady-state balances",
        "Total:  F = D + B",
        "IPA:    F z_F = D x_D + B x_B"]))
    p.append(_equation_box(560, 414, 395, [
        "Energy on one common reference",
        "F h_F + Q_R = D h_D + B h_B + Q_C",
        "No accumulation, reaction, or heat loss"]))
    return _finish(p)


def model_map_svg() -> str:
    p = _start("From specifications to a buildable column",
               "Information flow, and the boundary between process and equipment design", 420)
    nodes = [
        (45, 125, "FEED + SPECS", "F, z_F, h_F, P; x_D, x_B, R", theme.ACCENT),
        (275, 125, "THERMODYNAMICS", "NRTL gamma, Psat, h, H", theme.EQUILIBRIUM),
        (505, 125, "STAGE SOLVER", "MESH + difference points", theme.FEED_BRIGHT),
        (735, 125, "PROCESS RESULTS", "N, feed tray, L_n, V_n, Q_C, Q_R", theme.STAGE),
        (505, 270, "EQUIPMENT DESIGN", "hydraulics, shell, exchangers", theme.HEAT),
        (735, 270, "COST + SAFETY", "TAC, operability, safeguards", theme.DANGER),
    ]
    for x, y, title, sub, color in nodes:
        p.append(_node(x, y, 205, 82, title, sub, color))
    for x in (250, 480, 710):
        p.append(f'<path d="M{x} 166 L{x + 25} 166" stroke="{_MUTED}" stroke-width="3" marker-end="url(#thin-arrow)"/>')
    p.append(f'<path d="M837 207 C837 245 710 250 710 270" stroke="{_MUTED}" stroke-width="3" fill="none" marker-end="url(#thin-arrow)"/>')
    p.append(f'<path d="M710 311 L735 311" stroke="{_MUTED}" stroke-width="3" marker-end="url(#thin-arrow)"/>')
    p.append(_equation_box(45, 255, 400, [
        "Always close the balances first",
        "F = D + B;   F z_F = D x_D + B x_B",
        "F h_F + Q_R = D h_D + B h_B + Q_C"]))
    return _finish(p)


# ---------------------------------------------------------------------------
# Chapter 2 - phase equilibrium
# ---------------------------------------------------------------------------

def nrtl_local_composition_svg() -> str:
    p = _start("Why an activity coefficient is needed: local composition",
               "Hydrogen bonding makes a molecule's neighbourhood differ from the bulk average", 400)

    def cell(cx, cy, label, sub, pattern, accent):
        out = [f'<rect x="{cx}" y="{cy}" width="250" height="190" rx="8" '
               f'fill="{theme.rgba(theme.BACKGROUND, 0.5)}" stroke="{accent}" stroke-width="1.8"/>']
        out.append(_label(cx + 125, cy + 26, label, accent, 14.5, "middle", 700))
        for row, cols in enumerate(pattern):
            for col, kind in enumerate(cols):
                x = cx + 38 + col * 43
                y = cy + 58 + row * 40
                if kind == "W":
                    out.append(f'<circle cx="{x}" cy="{y}" r="11" fill="{theme.rgba(theme.ACCENT, 0.75)}" stroke="{theme.ACCENT}"/>')
                    out.append(_label(x, y + 4, "W", theme.BACKGROUND, 10.5, "middle", 700))
                else:
                    out.append(f'<circle cx="{x}" cy="{y}" r="11" fill="{theme.rgba(theme.STAGE, 0.75)}" stroke="{theme.STAGE}"/>')
                    out.append(_label(x, y + 4, "A", theme.BACKGROUND, 10.5, "middle", 700))
        out.append(_label(cx + 125, cy + 176, sub, _MUTED, 12, "middle"))
        return "".join(out)

    random_pattern = [["W", "A", "W", "A", "W"], ["A", "W", "A", "W", "A"], ["W", "A", "W", "A", "W"]]
    local_pattern = [["W", "W", "A", "A", "W"], ["W", "W", "A", "A", "A"], ["W", "W", "W", "A", "A"]]

    p.append(cell(70, 105, "Random mixing (ideal)", "every neighbour equally likely", random_pattern, theme.TEXT_FAINT))
    p.append(cell(375, 105, "Local composition (real)", "like molecules cluster", local_pattern, theme.EQUILIBRIUM))
    p.append(f'<path d="M330 200 L370 200" stroke="{_MUTED}" stroke-width="3" marker-end="url(#thin-arrow)"/>')
    p.append(_equation_box(660, 108, 285, [
        "NRTL encodes the clustering",
        "tau_ij = B_ij / T   (interaction energy)",
        "G_ij = exp(-alpha tau_ij)  (non-randomness)",
        "gamma -> 1 when tau -> 0",
        "A = isopropanol, W = water"]))
    p.append(_label(70, 340, "Consequence: y is no longer proportional to x, the y(x) curve bends, and it can cross y = x.",
                    _BODY, 13.5))
    p.append(_label(70, 364, "That crossing is the azeotrope, and no number of equilibrium stages can pass it at fixed pressure.",
                    theme.STAGE, 13.5, weight=600))
    return _finish(p)


def txy_anatomy_svg() -> str:
    p = _start("Anatomy of the T-x-y diagram and the azeotropic barrier",
               "Reading the phase envelope, and why distillation stops at the azeotrope", 470)
    x0, y0, w, h = 110, 390, 560, 280
    p.append(_axes(x0, y0, w, h, "IPA mole fraction x, y", "Temperature"))

    # Schematic bubble and dew curves with a minimum-boiling azeotrope near x=0.67.
    bubble = "M 110 170 C 230 250, 330 320, 485 332 C 560 337, 620 300, 670 240"
    dew = "M 110 170 C 250 195, 380 268, 485 332 C 570 336, 630 296, 670 240"
    p.append(f'<path d="{bubble}" fill="none" stroke="{theme.ACCENT}" stroke-width="3"/>')
    p.append(f'<path d="{dew}" fill="none" stroke="{theme.VAPOR}" stroke-width="3"/>')
    p.append(f'<path d="{bubble} L 670 240 C 630 296, 570 336, 485 332 C 380 268, 250 195, 110 170 Z" '
             f'fill="{theme.rgba(theme.ACCENT, 0.10)}" stroke="none"/>')

    p.append(_label(150, 150, "water boiling point", theme.TEXT_MUTED, 12))
    p.append(_label(690, 232, "IPA boiling point", theme.TEXT_MUTED, 12))
    p.append(_label(215, 218, "superheated vapour", theme.VAPOR, 12.5, weight=600))
    p.append(_label(255, 300, "two-phase", theme.TEXT_MUTED, 12.5, weight=600))
    p.append(_label(160, 355, "subcooled liquid", theme.ACCENT, 12.5, weight=600))
    p.append(_label(330, 246, "dew curve  T(y)", theme.VAPOR, 12.5, weight=600))
    p.append(_label(300, 335, "bubble curve  T(x)", theme.ACCENT, 12.5, weight=600))

    # Azeotrope
    p.append(f'<circle cx="485" cy="332" r="7" fill="{theme.STAGE}" stroke="{theme.BACKGROUND}" stroke-width="2"/>')
    p.append(f'<path d="M485 332 L485 390" stroke="{theme.STAGE}" stroke-width="1.8" stroke-dasharray="5 4"/>')
    p.append(_label(485, 412, "x_azeo", theme.STAGE, 13, "middle", 700))
    p.append(_label(497, 320, "azeotrope: bubble and dew curves touch, y = x", theme.STAGE, 12.5, weight=600))

    # Barrier shading
    p.append(f'<rect x="485" y="120" width="185" height="270" fill="{theme.rgba(theme.DANGER, 0.10)}" stroke="none"/>')
    p.append(_label(578, 140, "unreachable from a", theme.DANGER, 12, "middle", 600))
    p.append(_label(578, 156, "water-rich feed", theme.DANGER, 12, "middle", 600))

    p.append(_equation_box(700, 175, 265, [
        "How to read a vertical cut",
        "below bubble curve: all liquid",
        "above dew curve: all vapour",
        "between: L and V at the two",
        "curve intersections at that T"]))
    p.append(_label(110, 440, "A minimum-boiling azeotrope is the LOW point of the envelope, so it leaves the column as distillate.",
                    _BODY, 13))
    return _finish(p)


# ---------------------------------------------------------------------------
# Chapter 3 - flash
# ---------------------------------------------------------------------------

def flash_balance_svg() -> str:
    p = _start("Single equilibrium-flash balance envelope",
               "One feed splits into coexisting liquid and vapour phases", 430)
    p.append(f'<rect x="235" y="92" width="530" height="250" fill="{theme.rgba(theme.ACCENT, 0.05)}" '
             f'stroke="{_RULE}" stroke-width="2" stroke-dasharray="9 7"/>')
    p.append(f'<path d="M430 150 A70 28 0 0 1 570 150 L570 275 A70 28 0 0 1 430 275 Z" '
             f'fill="{_UNIT_TOP}" stroke="{theme.TEXT_MUTED}" stroke-width="2.5"/>')
    p.append(f'<path d="M431 225 Q500 247 569 225 L569 275 A70 28 0 0 1 431 275 Z" '
             f'fill="{theme.rgba(theme.ACCENT, 0.45)}" stroke="{theme.ACCENT}" stroke-width="1.5"/>')
    p.append(_label(500, 190, "FLASH DRUM", _TITLE, 17, "middle", 700))
    p.append(_label(500, 214, "T, P;  y_i = K_i x_i", _MUTED, 12.5, "middle"))
    p.append(_stream(55, 215, 420, 215, "FEED", "F, z_i, h_F"))
    p.append(_stream(580, 163, 925, 112, "VAPOUR", "V = beta F, y_i, H"))
    p.append(_stream(580, 270, 925, 320, "LIQUID", "L = (1-beta) F, x_i, h", green=True))
    p.append(_stream(500, 77, 500, 145, "Q into flash", "Q = 0 if adiabatic", heat=True))
    p.append(_equation_box(70, 354, 390, [
        "Material closure", "F = L + V", "z_i = (1-beta) x_i + beta y_i"]))
    p.append(_equation_box(540, 354, 390, [
        "Energy closure", "h_F + Q/F = (1-beta) h + beta H", "beta is restricted to 0 <= beta <= 1"]))
    return _finish(p)


def rachford_rice_svg() -> str:
    p = _start("Shape of the Rachford-Rice function, and the phase test",
               "Why a bracketed root is safe: g(beta) is monotonically decreasing between poles", 450)
    x0, y0, w, h = 130, 330, 560, 200
    p.append(f'<path d="M {x0} {y0 - h} L {x0} {y0 + 60} " fill="none" stroke="{_RULE}" stroke-width="2"/>')
    p.append(f'<path d="M {x0 - 40} {y0} L {x0 + w} {y0}" fill="none" stroke="{_RULE}" stroke-width="2" marker-end="url(#thin-arrow)"/>')
    p.append(_label(x0 + w, y0 + 26, "vapour fraction  beta", _BODY, 13, "end", 600))
    p.append(_label(x0 - 12, y0 - h - 6, "g(beta)", _BODY, 13, "end", 600))

    # beta = 0 and beta = 1 boundaries
    for bx, tag in ((x0, "0"), (x0 + 430, "1")):
        p.append(f'<path d="M{bx} {y0 - h} L{bx} {y0 + 40}" stroke="{_RULE}" stroke-width="1.4" stroke-dasharray="5 5"/>')
        p.append(_label(bx, y0 + 58, f"beta = {tag}", _MUTED, 12.5, "middle", 600))

    # The monotone decreasing curve crossing zero inside [0,1]
    p.append(f'<path d="M 130 200 C 210 232, 260 288, 320 322 C 380 356, 430 392, 560 424" '
             f'fill="none" stroke="{theme.ACCENT}" stroke-width="3"/>')
    p.append(f'<circle cx="332" cy="330" r="7" fill="{theme.STAGE}" stroke="{theme.BACKGROUND}" stroke-width="2"/>')
    p.append(_label(345, 316, "the root: two-phase solution", theme.STAGE, 12.5, weight=600))

    p.append(f'<circle cx="130" cy="200" r="6" fill="{theme.FEED_BRIGHT}"/>')
    p.append(_label(142, 190, "g(0) = sum z_i (K_i - 1)", theme.FEED_BRIGHT, 12.5, weight=600))
    p.append(f'<circle cx="560" cy="424" r="6" fill="{theme.VAPOR}"/>')
    p.append(_label(548, 444, "g(1) = sum z_i (K_i - 1)/K_i", theme.VAPOR, 12.5, "end", 600))

    p.append(_equation_box(715, 105, 250, [
        "Phase test before solving",
        "g(0) <= 0  ->  all liquid",
        "g(1) >= 0  ->  all vapour",
        "opposite signs -> two phases",
        "",
        "g'(beta) <= 0 always, so the",
        "bracketed root is unique."]))
    p.append(_label(130, 415, "Solve on 0 <= beta <= 1 only after the phase test; outside that interval the root is not physical.",
                    _BODY, 13))
    return _finish(p)


def flash_algorithm_svg() -> str:
    p = _start("Nested non-ideal adiabatic-flash algorithm",
               "The inner material/equilibrium solve must converge at every outer enthalpy trial", 465)
    nodes = [
        (55, 120, "BRACKET T", "T_low, T_high", theme.ACCENT),
        (275, 120, "NRTL K-VALUES", "K_i = gamma_i Psat_i / P", theme.EQUILIBRIUM),
        (505, 120, "RACHFORD-RICE", "root beta in [0,1]", theme.FEED_BRIGHT),
        (735, 120, "UPDATE x, y, gamma", "iterate to tolerance", theme.STAGE),
        (505, 270, "ENTHALPY RESIDUAL", "r_H = h_F - [(1-b)h + bH]", theme.HEAT),
        (735, 270, "CONVERGED STATE", "T, beta, x, y, h, H", theme.DANGER),
    ]
    for x, y, title, sub, color in nodes:
        p.append(_node(x, y, 205, 78, title, sub, color))
    for x in (260, 480, 710):
        p.append(f'<path d="M{x} 159 L{x + 15} 159" stroke="{_MUTED}" stroke-width="3" marker-end="url(#thin-arrow)"/>')
    p.append(f'<path d="M837 198 C837 245 650 230 620 270" stroke="{_MUTED}" stroke-width="3" fill="none" marker-end="url(#thin-arrow)"/>')
    p.append(f'<path d="M710 309 L735 309" stroke="{_MUTED}" stroke-width="3" marker-end="url(#thin-arrow)"/>')
    p.append(f'<path d="M505 309 C390 400 140 395 140 198" stroke="{_HEAT}" stroke-width="2.5" fill="none" stroke-dasharray="8 6" marker-end="url(#heat-arrow)"/>')
    p.append(_label(280, 398, "outer bracketed T update while |r_H| > tolerance", _HEAT, 12.5, weight=700))
    p.append(f'<path d="M835 120 C835 85 610 82 610 120" stroke="{theme.EQUILIBRIUM}" stroke-width="2.5" fill="none" stroke-dasharray="7 5" marker-end="url(#thin-arrow)"/>')
    p.append(_label(720, 78, "inner gamma-composition iteration", theme.EQUILIBRIUM, 12, "middle"))
    return _finish(p)


# ---------------------------------------------------------------------------
# Chapter 4 - McCabe-Thiele
# ---------------------------------------------------------------------------

def mccabe_balance_svg() -> str:
    p = _start("McCabe-Thiele section envelopes",
               "The operating-line slope and intercept follow from these stream balances", 505)
    p.append(f'<line x1="500" y1="88" x2="500" y2="472" stroke="{_RULE}" stroke-width="2"/>')
    p.append(_label(250, 112, "RECTIFYING SECTION", theme.ACCENT, 16, "middle", 700))
    p.append(_label(750, 112, "STRIPPING SECTION", theme.FEED_BRIGHT, 16, "middle", 700))
    p.append(f'<rect x="120" y="145" width="260" height="180" fill="{theme.rgba(theme.ACCENT, 0.06)}" stroke="{_RULE}" stroke-width="2" stroke-dasharray="8 6"/>')
    p.append(_node(155, 195, 190, 78, "UPPER SECTION", "+ total condenser"))
    p.append(_stream(250, 355, 250, 273, "V, y_n+1", "enters from below"))
    p.append(_stream(180, 273, 180, 355, "L, x_n", "leaves downward", green=True))
    p.append(_stream(322, 220, 445, 220, "D, x_D", "product"))
    p.append(f'<rect x="620" y="145" width="260" height="180" fill="{theme.rgba(theme.FEED, 0.06)}" stroke="{_RULE}" stroke-width="2" stroke-dasharray="8 6"/>')
    p.append(_node(655, 195, 190, 78, "LOWER SECTION", "+ partial reboiler", theme.FEED_BRIGHT))
    p.append(_stream(700, 126, 700, 195, "L-bar, x_m", "enters from above", green=True))
    p.append(_stream(800, 195, 800, 126, "V-bar, y_m+1", "leaves upward"))
    p.append(_stream(822, 246, 945, 246, "B, x_B", "product"))
    p.append(_equation_box(55, 375, 400, [
        "Rectifying balance",
        "V = L + D;   V y_n+1 = L x_n + D x_D",
        "y_n+1 = [R/(R+1)] x_n + x_D/(R+1)"]))
    p.append(_equation_box(545, 375, 400, [
        "Stripping balance",
        "L-bar = V-bar + B;   L-bar x_m = V-bar y_m+1 + B x_B",
        "y_m+1 = (L-bar/V-bar) x_m - (B/V-bar) x_B"]))
    return _finish(p)


def q_line_family_svg() -> str:
    p = _start("The q-line family: how feed condition rotates the feed locus",
               "All five lines pass through (z_F, z_F) on the 45-degree diagonal", 470)
    x0, y0, size = 130, 390, 290
    p.append(_axes(x0, y0, size + 60, size + 40, "liquid composition x", "vapour composition y"))
    p.append(f'<path d="M {x0} {y0} L {x0 + size} {y0 - size}" stroke="{_MUTED}" stroke-width="1.6" stroke-dasharray="6 5"/>')
    p.append(_label(x0 + size + 6, y0 - size - 4, "y = x", _MUTED, 12.5, weight=600))
    p.append(f'<path d="M {x0} {y0} C {x0 + 70} {y0 - 130}, {x0 + 150} {y0 - 205}, {x0 + size} {y0 - size}" '
             f'fill="none" stroke="{theme.ACCENT}" stroke-width="2.5"/>')
    p.append(_label(x0 + 92, y0 - 172, "equilibrium curve", theme.ACCENT, 12.5, weight=600))

    fx, fy = x0 + 140, y0 - 140     # the feed point on the diagonal
    lines = [
        (fx, fy - 115, fx, fy, "q > 1", "subcooled liquid", theme.EQUILIBRIUM, -6, -122),
        (fx, fy - 118, fx, fy, "q = 1", "saturated liquid", theme.ACCENT, 42, -104),
        (fx + 108, fy - 92, fx, fy, "0 < q < 1", "two-phase feed", theme.FEED_BRIGHT, 116, -96),
        (fx + 122, fy, fx, fy, "q = 0", "saturated vapour", theme.STAGE, 130, 4),
        (fx + 118, fy + 78, fx, fy, "q < 0", "superheated vapour", theme.HEAT, 126, 88),
    ]
    slopes = [
        (fx - 2, fy - 118, fx + 2, fy + 30),          # near-vertical, leaning back
        (fx, fy - 120, fx, fy + 28),                  # vertical
        (fx + 112, fy - 96, fx - 56, fy + 48),        # negative steep
        (fx + 126, fy, fx - 60, fy),                  # horizontal
        (fx + 120, fy + 84, fx - 58, fy - 40),        # positive shallow
    ]
    for (sx1, sy1, sx2, sy2), (_, _, _, _, tag, sub, color, lx, ly) in zip(slopes, lines):
        p.append(f'<path d="M{sx1} {sy1} L{sx2} {sy2}" stroke="{color}" stroke-width="2.5"/>')
        p.append(_label(fx + lx + 8, fy + ly, tag, color, 12.5, weight=700))
        p.append(_label(fx + lx + 8, fy + ly + 15, sub, _MUTED, 11.5))

    p.append(f'<circle cx="{fx}" cy="{fy}" r="7" fill="{theme.DIFFERENCE}" stroke="{theme.BACKGROUND}" stroke-width="2"/>')
    p.append(_label(fx - 12, fy + 22, "(z_F, z_F)", theme.DIFFERENCE, 12.5, "end", 700))

    p.append(_equation_box(555, 120, 400, [
        "q-line equation",
        "y = [q/(q-1)] x - z_F/(q-1)",
        "q = liquid fraction of the feed after",
        "an isenthalpic flash at column pressure",
        "",
        "slope = q/(q-1):  q=1 vertical, q=0 horizontal"]))
    p.append(_label(555, 330, "The operating lines must intersect ON the q-line.", _BODY, 13, weight=600))
    p.append(_label(555, 352, "That intersection point fixes the minimum reflux pinch", _MUTED, 12.5))
    p.append(_label(555, 370, "and the optimum feed-stage location.", _MUTED, 12.5))
    return _finish(p)


# ---------------------------------------------------------------------------
# Chapter 5 - Ponchon-Savarit
# ---------------------------------------------------------------------------

def mesh_stage_svg() -> str:
    p = _start("One equilibrium stage: the complete MESH envelope",
               "Every stage closes material, equilibrium, summation and enthalpy equations", 500)
    p.append(f'<rect x="170" y="110" width="420" height="230" fill="{theme.rgba(theme.EQUILIBRIUM, 0.06)}" '
             f'stroke="{_RULE}" stroke-width="2" stroke-dasharray="9 7"/>')
    p.append(_node(300, 184, 170, 82, "STAGE n", "T_n, P_n; equilibrium", theme.EQUILIBRIUM))
    p.append(_stream(65, 145, 300, 205, "L_n-1 enters", "x_n-1, h_n-1", green=True))
    p.append(_stream(65, 315, 300, 245, "V_n+1 enters", "y_n+1, H_n+1"))
    p.append(_stream(470, 205, 695, 145, "V_n leaves", "y_n, H_n"))
    p.append(_stream(470, 245, 695, 315, "L_n leaves", "x_n, h_n", green=True))
    p.append(_equation_box(625, 110, 330, [
        "M - component balance",
        "L_n-1 x_n-1 + V_n+1 y_n+1",
        "  = L_n x_n + V_n y_n"]))
    p.append(_equation_box(625, 226, 330, [
        "E, S, H closures",
        "y_i = K_i(T,P,x) x_i;  sum x = sum y = 1",
        "L_n-1 h_n-1 + V_n+1 H_n+1",
        "  = L_n h_n + V_n H_n"]))
    p.append(_equation_box(55, 375, 515, [
        "Total balance",
        "L_n-1 + V_n+1 = L_n + V_n",
        "Residuals must be checked stage by stage, not only globally."]))
    return _finish(p)


def ponchon_construction_svg() -> str:
    p = _start("Ponchon-Savarit construction geometry",
               "How one stage is stepped: tie line, then ray through the difference point", 520)
    x0, y0 = 120, 430
    p.append(_axes(x0, y0, 600, 330, "IPA composition x, y", "molar enthalpy"))

    vapor = "M 130 190 C 260 205, 420 232, 600 258"
    liquid = "M 130 372 C 270 366, 430 350, 600 336"
    p.append(f'<path d="{vapor}" fill="none" stroke="{theme.VAPOR}" stroke-width="3"/>')
    p.append(f'<path d="{liquid}" fill="none" stroke="{theme.ACCENT}" stroke-width="3"/>')
    p.append(_label(612, 254, "H_V(y)", theme.VAPOR, 13, weight=700))
    p.append(_label(612, 334, "h_L(x)", theme.ACCENT, 13, weight=700))

    # Difference point above the vapour curve
    dx, dy = 470, 122
    p.append(f'<circle cx="{dx}" cy="{dy}" r="8" fill="{theme.DIFFERENCE}" stroke="{theme.BACKGROUND}" stroke-width="2"/>')
    p.append(_label(dx + 14, dy - 6, "Delta_D = (x_D,  h_D + Q_C/D)", theme.DIFFERENCE, 13, weight=700))

    # Stage n: liquid point, tie line up to paired vapour, then ray to difference point
    lx, ly = 300, 358           # liquid x_n on h_L
    vx, vy = 395, 233           # paired vapour y_n on H_V
    nx, ny = 250, 216           # next vapour y_n+1 located by the ray

    p.append(f'<path d="M{lx} {ly} L{vx} {vy}" stroke="{theme.STAGE}" stroke-width="2.8"/>')
    p.append(_label((lx + vx) / 2 + 10, (ly + vy) / 2 + 6, "1. tie line (equilibrium)", theme.STAGE, 12.5, weight=700))

    p.append(f'<path d="M{dx} {dy} L{nx} {ny}" stroke="{theme.DIFFERENCE_SOFT}" stroke-width="2.4" stroke-dasharray="7 5"/>')
    p.append(f'<path d="M{dx} {dy} L{lx} {ly}" stroke="{theme.DIFFERENCE_SOFT}" stroke-width="2.4" stroke-dasharray="7 5"/>')
    p.append(_label(316, 172, "2. ray through Delta_D", theme.DIFFERENCE_SOFT, 12.5, weight=700))

    for cx, cy, tag, color, pos in ((lx, ly, "x_n", theme.ACCENT, 18),
                                    (vx, vy, "y_n", theme.VAPOR, -12),
                                    (nx, ny, "y_n+1", theme.VAPOR, -12)):
        p.append(f'<circle cx="{cx}" cy="{cy}" r="6" fill="{color}" stroke="{theme.BACKGROUND}" stroke-width="1.6"/>')
        p.append(_label(cx, cy + pos, tag, color, 12.5, "middle", 700))
    p.append(_label(nx - 92, ny + 32, "3. intersection with H_V", _MUTED, 12))
    p.append(_label(nx - 92, ny + 48, "gives the next stage", _MUTED, 12))

    p.append(_equation_box(700, 150, 265, [
        "Why collinearity is the balance",
        "V_n+1 - L_n = D  (invariant)",
        "h_dD = (V H - L h)/(V - L)",
        "     = h_D + Q_C/D",
        "",
        "Lever rule on the ray returns",
        "L and V, so flows need not be",
        "assumed constant."]))
    p.append(_label(120, 478, "Switch from Delta_D to Delta_B once the construction crosses the feed line; the three points Delta_D, F, Delta_B are collinear.",
                    _BODY, 13))
    return _finish(p)


# ---------------------------------------------------------------------------
# Chapter 6 - equipment
# ---------------------------------------------------------------------------

def tray_hydraulics_svg() -> str:
    p = _start("Tray hydraulics: the area split and the operating window",
               "Diameter follows from vapour load; the window is bounded by flooding and weeping", 470)

    # Plan view of the tray
    p.append(f'<circle cx="235" cy="245" r="130" fill="{theme.rgba(theme.ACCENT, 0.08)}" stroke="{theme.ACCENT}" stroke-width="2.5"/>')
    p.append(f'<path d="M 148 148 A 130 130 0 0 0 148 342 Z" fill="{theme.rgba(theme.FEED, 0.28)}" stroke="{theme.FEED_BRIGHT}" stroke-width="2"/>')
    p.append(_label(178, 250, "downcomer", theme.FEED_BRIGHT, 11.5, "middle", 700))
    p.append(_label(283, 232, "ACTIVE AREA", theme.ACCENT, 13, "middle", 700))
    p.append(_label(283, 250, "(bubbling / perforated)", _MUTED, 11.5, "middle"))
    p.append(f'<path d="M148 148 L148 342" stroke="{theme.STAGE}" stroke-width="3"/>')
    p.append(_label(120, 138, "weir", theme.STAGE, 12, "middle", 700))
    p.append(_label(235, 396, "plan view of one tray", _SUBTITLE, 12.5, "middle", 600))

    p.append(_equation_box(400, 108, 300, [
        "Area and diameter",
        "A_active = V_vol / u_design",
        "A_total  = A_active / (1 - f_dc)",
        "D_c = sqrt(4 A_total / pi)",
        "",
        "u_flood = C sqrt((rho_L - rho_V)/rho_V)",
        "u_design = f_flood x u_flood"]))

    # Operating window
    wx, wy, ww, wh = 730, 360, 220, 190
    p.append(f'<rect x="{wx}" y="{wy - wh}" width="{ww}" height="{wh}" fill="{theme.rgba(theme.FEED, 0.10)}" stroke="{_RULE}"/>')
    p.append(f'<rect x="{wx}" y="{wy - wh}" width="{ww}" height="34" fill="{theme.rgba(theme.DANGER, 0.25)}"/>')
    p.append(_label(wx + ww / 2, wy - wh + 22, "FLOODING", theme.DANGER, 12, "middle", 700))
    p.append(f'<rect x="{wx}" y="{wy - 34}" width="{ww}" height="34" fill="{theme.rgba(theme.HEAT, 0.25)}"/>')
    p.append(_label(wx + ww / 2, wy - 12, "WEEPING / DUMPING", theme.HEAT, 12, "middle", 700))
    p.append(_label(wx + ww / 2, wy - wh / 2 + 5, "stable operation", theme.FEED_BRIGHT, 13, "middle", 700))
    p.append(_label(wx + ww / 2, wy + 26, "vapour load", _BODY, 12.5, "middle", 600))
    p.append(_label(wx - 10, wy - wh - 12, "70-85% of flood is a starting point, not a design.", _MUTED, 11.5))
    return _finish(p)


def column_geometry_svg() -> str:
    p = _start("Column height stack-up",
               "Tangent-to-tangent height is a sum of five separately justified allowances", 470)
    cx, top, width = 300, 105, 150
    segments = [
        (58, "Top disengagement", "vapour/liquid separation above the top tray", theme.ACCENT),
        (150, "N_actual x tray spacing", "equilibrium stages / efficiency, then spacing", theme.EQUILIBRIUM),
        (48, "Feed-zone allowance", "distributor, nozzle, inlet device", theme.STAGE),
        (72, "Bottom sump", "reboiler circulation and holdup time", theme.FEED_BRIGHT),
    ]
    y = top
    for height, name, detail, color in segments:
        p.append(f'<rect x="{cx}" y="{y}" width="{width}" height="{height}" '
                 f'fill="{theme.rgba(color, 0.16)}" stroke="{color}" stroke-width="1.8"/>')
        p.append(f'<path d="M{cx + width + 12} {y} L{cx + width + 12} {y + height}" stroke="{color}" stroke-width="1.6"/>')
        p.append(f'<path d="M{cx + width + 6} {y} L{cx + width + 18} {y}" stroke="{color}" stroke-width="1.6"/>')
        p.append(f'<path d="M{cx + width + 6} {y + height} L{cx + width + 18} {y + height}" stroke="{color}" stroke-width="1.6"/>')
        p.append(_label(cx + width + 28, y + height / 2, name, color, 13, weight=700))
        p.append(_label(cx + width + 28, y + height / 2 + 16, detail, _MUTED, 11.5))
        y += height

    p.append(f'<path d="M{cx - 30} {top} L{cx - 30} {y}" stroke="{theme.TEXT_MUTED}" stroke-width="2" marker-start="url(#thin-arrow)" marker-end="url(#thin-arrow)"/>')
    p.append(f'<text x="{cx - 42}" y="{(top + y) / 2}" fill="{theme.TEXT_MUTED}" font-size="13" font-weight="700" '
             f'transform="rotate(-90 {cx - 42} {(top + y) / 2})" text-anchor="middle">H_tangent</text>')

    p.append(_equation_box(60, 330, 230, [
        "Shell thickness screen",
        "t_p = P_D D / (2 S E - 1.2 P_D)",
        "t = max(t_min, t_p + c_A)"]))
    p.append(_label(60, 300, "Preliminary only: heads, wind, seismic,", theme.HEAT, 12))
    p.append(_label(60, 316, "nozzles and code minimums are not included.", theme.HEAT, 12))
    return _finish(p)


def sizing_workflow_svg() -> str:
    p = _start("Auditable sizing and economics calculation chain",
               "Each box maps to a row in the dashboard calculation ledger", 560)
    boxes = [
        (55, 112, "SIMULATION LOADS", "max V, T, x, y, P; Q_C, Q_R", theme.ACCENT),
        (375, 112, "PHASE PROPERTIES", "MW_v, rho_v, rho_L, volumetric V", theme.EQUILIBRIUM),
        (695, 112, "TRAY HYDRAULICS", "u_flood, u_design, areas", theme.FEED_BRIGHT),
        (695, 245, "COLUMN DIAMETER", "D = sqrt(4A/pi)", theme.FEED_BRIGHT),
        (375, 245, "HEIGHT + SHELL", "tray stack, allowances, t, mass", theme.STAGE),
        (55, 245, "HEAT EXCHANGERS", "A = |Q| / (U dT_lm)", theme.HEAT),
        (55, 378, "BARE EQUIPMENT", "shell + trays + condenser + reboiler", theme.HEAT),
        (375, 378, "FIXED CAPITAL", "index x material x install x scope", theme.DANGER),
        (695, 378, "ANNUAL OPEX", "steam + cooling + maintenance", theme.DANGER),
        (375, 486, "TOTAL ANNUALIZED COST", "TAC = CRF x FCI + OPEX", theme.DIFFERENCE),
    ]
    for x, y, title, sub, color in boxes:
        p.append(_node(x, y, 250, 72, title, sub, color))
    arrows = [
        (305, 148, 375, 148), (625, 148, 695, 148), (820, 184, 820, 245),
        (695, 281, 625, 281), (375, 281, 305, 281), (180, 317, 180, 378),
        (305, 414, 375, 414), (625, 414, 695, 414), (820, 450, 625, 510),
        (500, 450, 500, 486),
    ]
    for x1, y1, x2, y2 in arrows:
        p.append(f'<path d="M{x1} {y1} L{x2} {y2}" stroke="{_MUTED}" stroke-width="2.5" fill="none" marker-end="url(#thin-arrow)"/>')
    return _finish(p)


# ---------------------------------------------------------------------------
# Chapter 7 - safety
# ---------------------------------------------------------------------------

def safety_layers_svg() -> str:
    p = _start("Upset propagation and independent protection layers",
               "Example: total loss of condenser cooling while reboiler heat continues", 445)
    nodes = [
        (45, 135, "INITIATING EVENT", "cooling-water loss", theme.HEAT),
        (245, 135, "PHYSICAL RESPONSE", "Q_C down; vapour + P up", theme.STAGE),
        (445, 135, "BPCS + ALARM", "pressure control; operator", theme.ACCENT),
        (645, 135, "INDEPENDENT TRIP", "high-high P removes Q_R", theme.FEED_BRIGHT),
        (825, 135, "RELIEF", "last-resort containment", theme.DANGER),
    ]
    for x, y, title, sub, color in nodes:
        p.append(_node(x, y, 150, 90, title, sub, color))
    for x in (195, 395, 595, 795):
        p.append(f'<path d="M{x} 180 L{x + 50} 180" stroke="{_MUTED}" stroke-width="3" marker-end="url(#thin-arrow)"/>')
    p.append(_equation_box(85, 275, 390, [
        "Dynamic energy inventory",
        "dU/dt = F h_F + Q_R - D h_D - B h_B - Q_C",
        "Cooling loss makes dU/dt positive until heat is removed."]))
    p.append(_equation_box(525, 275, 390, [
        "Relief basis",
        "m_relief >= vapour generation - remaining outlets",
        "Each layer must be verified independent and reliable."]))
    return _finish(p)
