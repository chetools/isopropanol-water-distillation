"""Tests for the presentation layer: diagrams, units, and tutorial structure."""

import re

import numpy as np
import pytest

import src.engineering_diagrams as diagrams
import src.theme as theme
from src.tutorial import CHAPTERS
from src.units import from_canonical, to_canonical, unit_options

DIAGRAMS = [name for name in dir(diagrams) if name.endswith("_svg")]


def test_every_diagram_is_reachable_from_a_chapter():
    """No orphaned drawings: each SVG must be imported by some chapter module."""
    imported = set()
    for _, module in CHAPTERS:
        imported |= {n for n in dir(module) if n.endswith("_svg")}
    orphans = sorted(set(DIAGRAMS) - imported)
    assert not orphans, f"diagrams defined but never rendered: {orphans}"


@pytest.mark.parametrize("name", DIAGRAMS)
def test_diagram_renders_well_formed_dark_svg(name):
    svg = getattr(diagrams, name)()
    assert svg.strip().startswith("<div")
    assert svg.rstrip().endswith("</svg></div>")
    assert svg.count("<svg") == 1
    assert "<title>" in svg and "role=\"img\"" in svg
    # Diagrams sit on the dark app background, so no hardcoded white fills.
    assert "#ffffff" not in svg.lower(), f"{name} still uses a light fill"


def test_figure_wrapper_numbers_and_captions():
    out = diagrams.figure("<svg></svg>", "5.2", "A caption.")
    assert "Figure 5.2" in out and "A caption." in out


def test_theme_rgba_round_trips_a_known_colour():
    assert theme.rgba("#38bdf8", 0.5) == "rgba(56, 189, 248, 0.5)"


def test_square_plotly_layout_does_not_pixel_lock_the_axes():
    """scaleanchor survives fullscreen as a postage-stamp subplot; do not use it."""
    import src.plotting as plots
    layout = plots._layout("t", "x", "y", x_range=(0.0, 1.0), square=True)
    assert layout["xaxis"]["range"] == [0.0, 1.0]
    assert layout["yaxis"]["range"] == [0.0, 1.0]
    assert layout["xaxis"].get("scaleanchor") is None
    assert layout["yaxis"].get("scaleanchor") is None
    assert layout["xaxis"].get("constrain") != "domain"
    assert layout["yaxis"].get("constrain") != "domain"


def test_app_css_defines_every_class_the_ui_emits():
    css = theme.app_css()
    for klass in ("metric-card", "metric-title", "metric-value", "metric-sub",
                  "locked-badge", "unlocked-badge", "computed-value",
                  "spec-name", "figure-caption"):
        assert f".{klass}" in css, f"missing CSS for .{klass}"


# ---------------------------------------------------------------------------
# Array-aware unit conversion (chapter 4.5 of the refactor)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("quantity", ["flow", "temperature", "enthalpy", "duty",
                                      "pressure", "length", "composition"])
def test_conversions_accept_arrays_and_match_elementwise(quantity):
    values = np.linspace(0.05, 0.95, 7) if quantity == "composition" else np.linspace(1.0, 90.0, 7)
    for unit in unit_options(quantity):
        vector = from_canonical(values, quantity, unit)
        assert isinstance(vector, np.ndarray)
        elementwise = np.array([from_canonical(float(v), quantity, unit) for v in values])
        assert np.allclose(vector, elementwise, rtol=1e-14)
        assert np.allclose(to_canonical(vector, quantity, unit), values, rtol=1e-12)


def test_scalar_conversion_still_returns_a_scalar():
    got = from_canonical(0.5, "composition", "mole %")
    assert isinstance(got, float) and got == pytest.approx(50.0)


# ---------------------------------------------------------------------------
# Tutorial structure
# ---------------------------------------------------------------------------

def test_every_chapter_exposes_a_render_entry_point():
    assert len(CHAPTERS) == 9
    for title, module in CHAPTERS:
        assert callable(getattr(module, "render", None)), f"{title} has no render()"


def test_chapters_declare_learning_objectives():
    """Chapter 0 is reference material; every taught chapter states objectives."""
    for title, module in CHAPTERS[1:]:
        objectives = getattr(module, "OBJECTIVES", ())
        assert len(objectives) >= 3, f"{title} declares too few objectives"


def test_layout_converts_inline_html_so_latex_survives():
    """Callout text is authored with <b>/<i>; it must reach markdown, not raw HTML.

    Streamlit skips its KaTeX pass inside raw HTML blocks, so a callout rendered
    as HTML would turn every $...$ into literal dollar signs.
    """
    from src.tutorial.layout import _as_markdown

    converted = _as_markdown("<b>Result</b> uses <i>x</i> and <code>Q_C</code>")
    assert converted == "**Result** uses *x* and `Q_C`"
    assert "<" not in converted


# ---------------------------------------------------------------------------
# Streamlit Cloud stale-module guard
# ---------------------------------------------------------------------------

def test_reload_guard_covers_every_src_module():
    """Every importable src module must appear in app.py's reload order.

    Streamlit Community Cloud can serve a stale already-imported module after a
    redeploy.  A module missing from the guard is refreshed only by luck, which
    is how the array-aware units.from_canonical once ran against a copy that
    still did float(value).
    """
    import ast
    from pathlib import Path

    root = Path(__file__).resolve().parents[1]

    on_disk = set()
    for path in (root / "src").rglob("*.py"):
        if path.name == "__init__.py":
            parent = path.parent
            if parent.name != "src":
                on_disk.add(f"src.{parent.name}")
            continue
        relative = path.relative_to(root).with_suffix("")
        on_disk.add(".".join(relative.parts))

    tree = ast.parse((root / "app.py").read_text(encoding="utf-8"))
    listed = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and any(
            getattr(t, "id", "") == "_MODULE_RELOAD_ORDER" for t in node.targets
        ):
            listed = {
                element.value for element in node.value.elts
                if isinstance(element, ast.Constant)
            }

    assert listed, "app.py no longer defines _MODULE_RELOAD_ORDER"
    missing = sorted(on_disk - listed)
    assert not missing, f"src modules absent from the reload guard: {missing}"


def test_reload_guard_lists_dependencies_before_dependents():
    """units and theme must be refreshed before anything that imports them."""
    import ast
    from pathlib import Path

    tree = ast.parse((Path(__file__).resolve().parents[1] / "app.py").read_text(encoding="utf-8"))
    order = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and any(
            getattr(t, "id", "") == "_MODULE_RELOAD_ORDER" for t in node.targets
        ):
            order = [e.value for e in node.value.elts if isinstance(e, ast.Constant)]

    for dependency, dependent in (
        ("src.units", "src.plotting"),
        ("src.units", "src.ui"),
        ("src.units", "src.process_audit"),
        ("src.units", "src.sizing_dashboard"),
        ("src.theme", "src.engineering_diagrams"),
        ("src.theme", "src.plotting"),
        ("src.thermo", "src.column"),
        ("src.tutorial.layout", "src.tutorial"),
    ):
        assert order.index(dependency) < order.index(dependent), (
            f"{dependency} must be reloaded before {dependent}"
        )


# ---------------------------------------------------------------------------
# Figure legibility and LaTeX validity
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("name", DIAGRAMS)
def test_diagram_labels_do_not_collide(name):
    """No two labels may sit on top of each other.

    Estimated glyph boxes, so it is approximate -- but overlapping captions are
    the single thing that most makes a figure look unfinished, and checking all
    fifteen drawings takes a second where eyeballing does not.
    """
    from tests._svg_geometry import area, boxes, overlaps

    found = boxes(getattr(diagrams, name)())
    collisions = []
    for i in range(len(found)):
        for j in range(i + 1, len(found)):
            if not overlaps(found[i], found[j]):
                continue
            ax0, ay0, ax1, ay1, _ = found[i]
            bx0, by0, bx1, by1, _ = found[j]
            intersection = ((min(ax1, bx1) - max(ax0, bx0))
                            * (min(ay1, by1) - max(ay0, by0)))
            smaller = min(area(found[i]), area(found[j])) or 1.0
            if intersection / smaller > 0.12:
                collisions.append(f"{found[i][4]!r} overlaps {found[j][4]!r}")
    assert not collisions, f"{name}: " + "; ".join(collisions)


@pytest.mark.parametrize("name", DIAGRAMS)
def test_diagram_content_stays_inside_the_canvas(name):
    """Labels must sit within the declared viewBox, or they are clipped away."""
    import re

    svg = getattr(diagrams, name)()
    width, height = (float(v) for v in
                     re.search(r'viewBox="0 0 ([\d.]+) ([\d.]+)"', svg).groups())
    from tests._svg_geometry import boxes

    for x0, y0, x1, y1, text in boxes(svg):
        assert -2 <= y0 and y1 <= height + 2, f"{name}: {text!r} outside vertically"
        assert -2 <= x0 and x1 <= width + 60, f"{name}: {text!r} outside horizontally"


def test_diagram_subscripts_are_typeset_not_literal():
    """z_F must render as z with a subscript, not as the characters 'z_F'."""
    svg = diagrams.whole_column_balance_svg()
    assert 'dy="0.3em"' in svg, "subscripts are not being shifted"
    assert "z_F" not in svg, "a literal underscore survived into the markup"


def test_subscripts_avoid_baseline_shift_for_firefox():
    """baseline-shift is unimplemented in Firefox and must not be relied on.

    It works in Chrome and Safari, so a regression here would look fine in two
    of the three target browsers and silently flatten every subscript in the
    third.
    """
    for name in DIAGRAMS:
        svg = getattr(diagrams, name)()
        assert "baseline-shift" not in svg, f"{name} uses baseline-shift"


def test_subscript_shift_is_cancelled_so_later_text_stays_on_the_baseline():
    """Each dy shift must be undone, or the rest of the label drifts downward."""
    markup = diagrams._math("F, z_F, h_F at T_b")
    assert markup.count('dy="0.3em"') == markup.count('dy="-0.3em"')


def test_no_diagram_contains_a_blank_line():
    """A blank line ends the raw-HTML block in Streamlit markdown.

    When that happened the title rendered and the entire drawing silently
    disappeared, which is why every diagram is emitted as a single line.
    """
    for name in DIAGRAMS:
        svg = getattr(diagrams, name)()
        assert len(svg.splitlines()) == 1, f"{name} is not flattened to one line"


def test_every_latex_command_is_a_real_katex_command():
    """Catch bogus commands produced by string concatenation.

    Adjacent Python string literals are folded by the parser, so a fragment
    ending in \qquad followed by one starting with y_i yields \qquady, which
    KaTeX renders as red error text in the middle of the equation.
    """
    import ast
    from pathlib import Path

    known = set("""
    frac dfrac tfrac sqrt sum prod int lim inf sup max min log ln exp sin cos tan
    alpha beta gamma delta epsilon varepsilon zeta eta theta vartheta kappa lambda
    mu nu xi pi rho sigma tau upsilon phi varphi chi psi omega
    Gamma Delta Theta Lambda Xi Pi Sigma Upsilon Phi Psi Omega
    partial nabla infty cdot cdots ldots dots times div pm mp approx neq ne leq le
    geq ge ll gg equiv sim simeq propto in notin subset supset cup cap emptyset
    forall exists rightarrow leftarrow Rightarrow Leftarrow Longrightarrow
    Longleftarrow to gets mapsto left right big Big bigg Bigg langle rangle
    lvert rvert vert Vert quad qquad space enspace hspace vspace
    text textbf textit textrm mathrm mathbf mathit mathcal mathbb mathsf operatorname
    underbrace overbrace underline overline hat widehat bar vec tilde dot ddot
    begin end array matrix pmatrix bmatrix cases aligned align split
    tag label ref circ degree prime displaystyle textstyle color textcolor phantom
    """.split())

    root = Path(__file__).resolve().parents[1]
    token = re.compile(r"\\([A-Za-z]+)")
    bad = []
    for path in list((root / "src").rglob("*.py")) + [root / "app.py"]:
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            name = getattr(node.func, "attr", getattr(node.func, "id", ""))
            values = [kw.value for kw in node.keywords if kw.arg == "equation"]
            if name in {"eq", "latex"}:
                values += list(node.args)
            for arg in values:
                if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                    for command in token.findall(arg.value):
                        if command not in known:
                            bad.append(f"{path.name}:{node.lineno} \{command}")
    assert not bad, "unknown LaTeX commands: " + "; ".join(bad)


# ---------------------------------------------------------------------------
# Cross-browser safety
# ---------------------------------------------------------------------------

def test_markup_avoids_features_that_break_in_a_target_browser():
    """Guard the specific features that differ across Chrome, Safari and Firefox.

    Each of these renders correctly in at least one engine, so a regression
    would look fine locally while quietly degrading elsewhere.
    """
    import src.theme as app_theme

    svg = "".join(getattr(diagrams, name)() for name in DIAGRAMS)
    css = app_theme.app_css()

    assert "baseline-shift" not in svg, (
        "baseline-shift is not implemented in Firefox; use dy instead"
    )
    assert "auto-start-reverse" not in svg, (
        "orient=auto-start-reverse needs Safari 15+; use orient=auto and "
        "point each arrow outward instead"
    )
    for prefix in ("-webkit-", "-moz-", "-ms-"):
        assert prefix not in svg and prefix not in css, f"vendor prefix {prefix}"
    assert ":has(" not in css, "the :has() selector is too new to rely on"
    assert not re.search(r"#[0-9a-fA-F]{8}\b", svg), (
        "eight-digit hex colours are inconsistently supported in SVG attributes"
    )


def test_diagrams_declare_an_intrinsic_aspect_ratio():
    """Safari has mis-sized viewBox-only SVGs inside flex parents.

    Declaring aspect-ratio alongside the viewBox pins the height in every
    engine; the two always agree, so it is a safe belt-and-braces measure.
    """
    for name in DIAGRAMS:
        svg = getattr(diagrams, name)()
        height = re.search(r'viewBox="0 0 1000 ([\d.]+)"', svg).group(1)
        assert f"aspect-ratio:1000/{height}" in svg, f"{name} lacks aspect-ratio"


def test_diagrams_are_accessible():
    """Screen readers need a title and an accessible name on each figure."""
    for name in DIAGRAMS:
        svg = getattr(diagrams, name)()
        assert 'role="img"' in svg, f"{name} missing role"
        assert "<title>" in svg and "<desc>" in svg, f"{name} missing title/desc"
        assert 'aria-label="' in svg, f"{name} missing aria-label"


# ---------------------------------------------------------------------------
# The azeotrope figure must agree with the model it illustrates
# ---------------------------------------------------------------------------

def test_txy_anatomy_is_drawn_from_the_real_vle_curves():
    """The schematic must show the model's own numbers, not sketched curves."""
    import src.thermo as thermo

    svg = diagrams.txy_anatomy_svg()
    vle = thermo.get_vle_curves(101325.0, 161)

    assert f"{float(vle['x_azeo']):.4f}" in svg, "azeotrope composition not shown"
    assert f"{float(vle['T_azeo_C']):.2f}" in svg, "azeotrope temperature not shown"
    assert f"{float(vle['T_bubble_C'][0]):.1f}" in svg, "water boiling point not shown"
    assert f"{float(vle['T_bubble_C'][-1]):.1f}" in svg, "IPA boiling point not shown"
    # Two polylines: the bubble branch and the dew branch.
    assert svg.count("<polyline") == 2


def test_txy_anatomy_shows_a_minimum_boiling_azeotrope():
    """The azeotrope must plot below both pure boiling points.

    On the canvas y grows downward, so 'below in temperature' is a LARGER y.
    Getting this inverted would draw a maximum-boiling azeotrope, which is the
    wrong physics for IPA/water.
    """
    svg = diagrams.txy_anatomy_svg()
    circles = re.findall(r'<circle cx="([\d.]+)" cy="([\d.]+)" r="([\d.]+)"', svg)
    assert len(circles) >= 3, "expected the two pure points and the azeotrope"

    pure = [(float(x), float(y)) for x, y, r in circles if float(r) == 4.0]
    azeo = [(float(x), float(y)) for x, y, r in circles if float(r) == 5.5]
    assert len(pure) == 2 and len(azeo) == 1

    (_, y_azeo), = azeo
    for _, y_pure in pure:
        assert y_azeo > y_pure, "azeotrope is not the minimum-boiling point"


def test_txy_dew_curve_sits_on_the_correct_side_of_the_bubble_curve():
    """Below the azeotrope the vapour is IPA-rich, above it water-rich.

    That reversal is what makes the envelope pinch at the azeotrope, and it is
    the detail most often drawn wrongly.
    """
    import src.thermo as thermo

    vle = thermo.get_vle_curves(101325.0, 161)
    x, y, x_azeo = vle["x"], vle["y"], float(vle["x_azeo"])

    left = (x > 0.05) & (x < x_azeo - 0.05)
    right = (x > x_azeo + 0.05) & (x < 0.98)
    assert (y[left] > x[left]).all(), "vapour should be IPA-rich below the azeotrope"
    assert (y[right] < x[right]).all(), "vapour should be water-rich above the azeotrope"


def test_diagram_overbars_are_real_glyphs_not_hyphenated_words():
    """L-bar must render as L with a macron, the way a textbook prints it."""
    assert "\u0304" in diagrams._math("L-bar")
    assert "-bar" not in diagrams._math("V-bar = L-bar - B")
    assert diagrams._math("rebar") == "rebar", "over-eager overbar substitution"
    svg = diagrams.mccabe_balance_svg()
    assert "-bar" not in svg, "a literal '-bar' survived into the drawing"
