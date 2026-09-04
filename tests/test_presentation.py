"""Tests for the presentation layer: diagrams, units, and tutorial structure."""

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
