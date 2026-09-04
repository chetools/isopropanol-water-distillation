"""Textbook furniture: numbered equations and figures, and structured blocks.

A chapter is built through a :class:`Chapter` instance, which owns the numbering
for that chapter.  Numbering matters more than it looks: once an equation is
``(2.7)``, the prose three paragraphs later can say "substitute (2.4) into
(2.6)" instead of "substitute the earlier expression into the one above", and a
derivation becomes checkable rather than merely readable.

One Streamlit constraint shapes this whole module: **Streamlit does not run its
KaTeX pass over content inside a raw HTML block.**  Wrapping prose in a styled
``<div>`` therefore turns every ``$...$`` in it back into literal dollar signs.
Every helper below consequently renders through plain markdown, and any styling
that would need an HTML wrapper is achieved with a bordered container and a
coloured lead-in instead.
"""

import re
from dataclasses import dataclass, field

import streamlit as st

import src.theme as theme
from src.source_links import github_symbol_link

_HTML_TO_MARKDOWN = (
    (re.compile(r"</?b>"), "**"),
    (re.compile(r"</?i>"), "*"),
    (re.compile(r"</?code>"), "`"),
    (re.compile(r"<br\s*/?>"), "  \n"),
)


def _as_markdown(text: str) -> str:
    """Convert the small set of inline HTML tags used here into markdown.

    Keeps the callout text authorable with ``<b>``/``<i>``/``<code>`` while
    still going through Streamlit's markdown (and therefore KaTeX) pipeline.
    """
    for pattern, replacement in _HTML_TO_MARKDOWN:
        text = pattern.sub(replacement, text)
    return text


@dataclass
class Chapter:
    """Owns equation, figure, and step numbering for one tutorial chapter."""

    number: int
    title: str
    objectives: tuple[str, ...] = ()
    _equations: int = field(default=0, init=False)
    _figures: int = field(default=0, init=False)
    _labels: dict = field(default_factory=dict, init=False)

    # -- structure ----------------------------------------------------------

    def open(self) -> None:
        """Render the chapter's learning objectives."""
        if not self.objectives:
            return
        with st.container(border=True):
            st.markdown(":blue[**After this section you should be able to**]")
            st.markdown("\n".join(f"- {o}" for o in self.objectives))

    def prose(self, markdown: str) -> None:
        st.markdown(_as_markdown(markdown))

    def heading(self, text: str) -> None:
        st.markdown(f"##### {text}")

    # -- numbered equations -------------------------------------------------

    def eq(self, latex: str, label: str | None = None) -> str:
        """Render a numbered display equation and return its tag, e.g. ``(2.4)``.

        The number sits in its own narrow column rather than in a KaTeX
        ``\\tag``: inside Streamlit's centred display block a ``\\tag`` is
        positioned absolutely and lands on top of the equation itself.
        """
        self._equations += 1
        tag = f"{self.number}.{self._equations}"
        if label:
            self._labels[label] = tag
        body, number = st.columns([22, 3], vertical_alignment="center")
        with body:
            st.latex(latex)
        number.markdown(
            f'<div style="text-align:right;color:{theme.TEXT_DIM};'
            f'font-size:{theme.FONT_CAPTION}px;">({tag})</div>',
            unsafe_allow_html=True,
        )
        return f"({tag})"

    def ref(self, label: str) -> str:
        """Cross-reference a previously labelled equation."""
        return f"({self._labels.get(label, '?')})"

    # -- numbered figures ---------------------------------------------------

    def _caption(self, tag: str, caption: str) -> None:
        st.caption(f"**Figure {tag}** — {_as_markdown(caption)}")

    def figure(self, svg: str, caption: str) -> str:
        """Render a numbered, captioned diagram and return its tag."""
        self._figures += 1
        tag = f"{self.number}.{self._figures}"
        st.markdown(svg, unsafe_allow_html=True)
        self._caption(tag, caption)
        return f"Figure {tag}"

    def chart(self, fig, caption: str, key: str) -> str:
        """Render a live Plotly figure with the same numbering as the drawings."""
        self._figures += 1
        tag = f"{self.number}.{self._figures}"
        st.plotly_chart(fig, width="stretch", key=key)
        self._caption(tag, caption)
        return f"Figure {tag}"

    # -- derivation blocks --------------------------------------------------

    def derivation(self, title: str) -> None:
        st.markdown(f"**Derivation {self.number}.{self._equations + 1} — {title}**")

    def step(self, index: int, title: str, body: str) -> None:
        """One numbered step of a derivation.

        Plain markdown by necessity -- see the module docstring: a styled HTML
        wrapper here would silently break every ``$...$`` in ``body``.
        """
        st.markdown(f"**Step {index} — {title}.** {_as_markdown(body)}")

    # -- callouts -----------------------------------------------------------

    @staticmethod
    def _callout(lead: str, markdown: str) -> None:
        with st.container(border=True):
            st.markdown(lead)
            st.markdown(_as_markdown(markdown))

    @classmethod
    def key_result(cls, markdown: str) -> None:
        cls._callout(":green[**Key result**]", markdown)

    @classmethod
    def caution(cls, markdown: str) -> None:
        cls._callout(":orange[**Caution**]", markdown)

    @staticmethod
    def assumptions(rows: list[tuple[str, str, str]]) -> None:
        """An assumption / consequence / failure-mode table."""
        header = "| Assumption | What it buys | How it fails |\n|---|---|---|\n"
        body = "\n".join(f"| {a} | {b} | {c} |" for a, b, c in rows)
        st.markdown(header + body)

    @staticmethod
    def self_check(question: str, answer: str) -> None:
        with st.expander(f"Self-check — {question}"):
            st.markdown(_as_markdown(answer))

    # -- code correspondence ------------------------------------------------

    @staticmethod
    def code(equation: str, snippet: str, path: str, symbol: str,
             note: str = "") -> None:
        """Side-by-side panel: the printed equation, and the lines that run it.

        This panel is only honest because the implementation was written in
        array form to mirror the mathematics; before that refactoring the two
        columns would not have matched.
        """
        left, right = st.columns([1, 1], gap="medium")
        with left:
            st.markdown("**The equation**")
            st.latex(equation)
            if note:
                st.caption(note)
        with right:
            st.markdown("**The code**")
            st.code(snippet, language="python")
            link = github_symbol_link("full source", path, symbol)
            if link:
                st.caption(link)

    @staticmethod
    def source(label: str, path: str, symbol: str) -> None:
        link = github_symbol_link(label, path, symbol)
        if link:
            st.markdown(f"- {link}")

    # -- live worked example ------------------------------------------------

    @staticmethod
    def worked_example(title: str, rows: list[tuple[str, str, str]]) -> None:
        """Substitute the current run's numbers into the equation just derived.

        Each row is ``(symbol, substitution, result)``.  Turning the algebra
        into arithmetic a reader can check by hand is what separates a worked
        example from a restatement of the result.
        """
        st.markdown(f"**Worked example — {title}**  *(live values from this run)*")
        header = "| Quantity | Substitution | Result |\n|---|---|---|\n"
        body = "\n".join(f"| {s} | `{sub}` | **{res}** |" for s, sub, res in rows)
        st.markdown(header + body)


def nomenclature_table(rows: list[tuple[str, str, str, str]]) -> None:
    """Symbol / meaning / SI unit / first appearance."""
    header = "| Symbol | Meaning | Canonical unit | Introduced |\n|---|---|---|---|\n"
    st.markdown(header + "\n".join(f"| {a} | {b} | {c} | {d} |" for a, b, c, d in rows))


def sign_convention_box() -> None:
    """Stated once, referenced by every energy balance in the tutorial."""
    with st.container(border=True):
        st.markdown(":green[**Sign convention, used everywhere below**]")
        st.markdown(
            "$Q_C$ and $Q_R$ are stored as **positive magnitudes**. Condenser heat "
            "*leaves* the column and reboiler heat *enters* it, so the direction is "
            "carried by which side of the balance they appear on:"
        )
        st.latex(r"F h_F + Q_R = D h_D + B h_B + Q_C")
        st.markdown(
            "Enthalpies share one reference state: pure saturated liquid at "
            "$25\\,^\\circ\\mathrm{C}$, where $h_i = 0$. Mixing an enthalpy from "
            "another reference into these equations is the most common way to get a "
            "plausible-looking but wrong duty."
        )
